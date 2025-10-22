"""Slurm planning utilities for generating and validating sbatch scripts."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Mapping, MutableMapping

SBATCH_REQUIRED = ("-p", "-N", "--ntasks", "--time", "--mem")
TIME_PATTERN = re.compile(r"^(?:(\d+)-)?(\d{1,2}):(\d{2})(?::(\d{2}))?$")
MEM_PATTERN = re.compile(r"^(?P<value>\d+)(?P<unit>[KMGTP])$", re.IGNORECASE)


def _parse_time(value: str) -> timedelta:
    value = value.strip()
    match = TIME_PATTERN.match(value)
    if not match:
        raise ValueError(f"Invalid Slurm time format: {value}")
    days, hours, minutes, seconds = match.groups(default="0")
    return timedelta(
        days=int(days or 0),
        hours=int(hours),
        minutes=int(minutes),
        seconds=int(seconds or 0),
    )


def _format_time(value: str, max_value: str | None = None) -> str:
    td = _parse_time(value)
    if max_value:
        max_td = _parse_time(max_value)
        if td > max_td:
            raise ValueError(f"Requested time {value} exceeds partition limit {max_value}")
    total_seconds = int(td.total_seconds())
    days, rem = divmod(total_seconds, 86400)
    hours, rem = divmod(rem, 3600)
    minutes, seconds = divmod(rem, 60)
    formatted = f"{hours:02}:{minutes:02}:{seconds:02}"
    return f"{days}-{formatted}" if days else formatted


def _parse_memory(value: str) -> tuple[int, str]:
    upper = value.strip().upper()
    match = MEM_PATTERN.match(upper)
    if not match:
        raise ValueError(f"Invalid memory format: {value}")
    return int(match.group("value")), match.group("unit")


def _format_memory(value: str | None) -> str:
    if not value:
        raise ValueError("Memory value is required")
    amount, unit = _parse_memory(value)
    return f"{amount}{unit}"


def _ensure_directory(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def _load_partition_policy(policy: Mapping[str, object], partition: str) -> Mapping[str, object]:
    partitions = policy.get("partitions", {}) if policy else {}
    entry = partitions.get(partition, {}) if isinstance(partitions, Mapping) else {}
    return entry if isinstance(entry, Mapping) else {}


def _partition_limits(policy: Mapping[str, object]) -> Mapping[str, object]:
    limits = policy.get("limits", {})
    return limits if isinstance(limits, Mapping) else {}


def _policy_default(policy: Mapping[str, object], key: str) -> str | None:
    defaults = policy.get("defaults", {}) if policy else {}
    if isinstance(defaults, Mapping):
        value = defaults.get(key)
        if value:
            return str(value)
    return None


def _derive_memory(spec: Mapping[str, object]) -> str:
    if spec.get("memory_per_node"):
        return _format_memory(str(spec["memory_per_node"]))
    if spec.get("memory_per_gpu"):
        per_gpu, unit = _parse_memory(str(spec["memory_per_gpu"]))
        cpus_per_task = int(spec.get("cpus_per_task") or 1)
        derived = per_gpu * cpus_per_task
        return f"{derived}{unit}"
    raise ValueError("Unable to determine memory requirement from specification")


@dataclass
class SlurmPlanner:
    """Generate and validate Slurm sbatch scripts."""

    policy: Mapping[str, object] = field(default_factory=dict)
    output_dir: Path | None = None

    def make_sbatch(
        self,
        spec: Mapping[str, object],
        *,
        output_dir: Path | None = None,
        script_name: str | None = None,
    ) -> Path:
        partition = str(spec.get("partition") or "").strip()
        if not partition:
            raise ValueError("Job specification must include 'partition'")
        partition_policy = _load_partition_policy(self.policy, partition)
        limits = _partition_limits(partition_policy)
        default_time = spec.get("time_limit") or spec.get("time") or limits.get("default_time") or "01:00:00"
        formatted_time = _format_time(str(default_time), str(limits.get("max_time") or ""))
        memory = _derive_memory(spec)
        account = spec.get("account") or _policy_default(self.policy, "account")
        qos = None
        extra = spec.get("extra")
        if isinstance(extra, Mapping):
            qos = extra.get("qos")
        requires_qos = partition_policy.get("requires_qos") if isinstance(partition_policy, Mapping) else None
        if requires_qos and not qos:
            qos = requires_qos
        gpus = int(spec.get("gpus") or 0)
        gpu_flags = {}
        if gpus:
            gpu_policy = self.policy.get("gpu_flags", {}) if isinstance(self.policy, Mapping) else {}
            fmt = gpu_policy.get("format", "--gres=gpu:{type}:{count}") if isinstance(gpu_policy, Mapping) else "--gres=gpu:{type}:{count}"
            gpu_type = spec.get("gpu_type") or (gpu_policy.get("type") if isinstance(gpu_policy, Mapping) else "gpu")
            gpu_flags["gres"] = fmt.format(type=str(gpu_type).lower(), count=gpus)
            constraint = gpu_policy.get("requires_constraint") if isinstance(gpu_policy, Mapping) else None
            if constraint:
                gpu_flags["constraint"] = constraint

        directives: list[str] = ["#!/bin/bash"]
        job_name = str(spec.get("job_name") or "job")
        directives.append(f"#SBATCH -J {job_name}")
        directives.append(f"#SBATCH -p {partition}")
        directives.append(f"#SBATCH -N {int(spec.get('nodes') or 1)}")
        ntasks = spec.get("ntasks") or spec.get("tasks")
        if ntasks is None:
            raise ValueError("Job specification must include 'ntasks'")
        directives.append(f"#SBATCH --ntasks={int(ntasks)}")
        cpus_per_task = spec.get("cpus_per_task")
        if cpus_per_task:
            directives.append(f"#SBATCH --cpus-per-task={int(cpus_per_task)}")
        directives.append(f"#SBATCH --time={formatted_time}")
        directives.append(f"#SBATCH --mem={memory}")
        if account:
            directives.append(f"#SBATCH --account={account}")
        mail_type = _policy_default(self.policy, "mail_type")
        mail_user = _policy_default(self.policy, "mail_user")
        if mail_type:
            directives.append(f"#SBATCH --mail-type={mail_type}")
        if mail_user:
            directives.append(f"#SBATCH --mail-user={mail_user}")
        log_dir = Path(spec.get("log_dir") or "logs")
        stdout_name = f"{job_name}_%j.out"
        stderr_name = f"{job_name}_%j.err"
        directives.append(f"#SBATCH -o {log_dir / stdout_name}")
        directives.append(f"#SBATCH -e {log_dir / stderr_name}")
        if gpus:
            directives.append(f"#SBATCH {gpu_flags['gres']}")
            constraint = gpu_flags.get("constraint")
            if constraint:
                directives.append(f"#SBATCH --constraint={constraint}")
        if qos:
            directives.append(f"#SBATCH --qos={qos}")

        body_lines: list[str] = ["", "set -euo pipefail"]
        if spec.get("module_purge", True):
            body_lines.append("module purge")
        for module_name in spec.get("modules", []):
            body_lines.append(f"module load {module_name}")
        exports = spec.get("exports", {})
        if isinstance(exports, Mapping):
            for key, value in exports.items():
                body_lines.append(f"export {key}={value}")
        workdir = spec.get("workdir")
        if workdir:
            body_lines.append(f"cd {workdir}")
        command = spec.get("command")
        if not command:
            raise ValueError("Job specification must include 'command'")
        launcher = spec.get("launcher", "srun")
        body_lines.append(f"{launcher} {command}")

        kind = spec.get("kind") or ("gpu" if gpus else "cpu")
        target_dir = Path(output_dir or self.output_dir or Path.cwd())
        _ensure_directory(target_dir)
        script_base = script_name or f"job_{kind}.sbatch"
        script_path = target_dir / script_base
        script_path.write_text("\n".join(directives + body_lines) + "\n", encoding="utf-8")
        metadata = {
            "job_name": job_name,
            "partition": partition,
            "time_limit": formatted_time,
            "memory": memory,
            "ntasks": int(ntasks),
            "cpus_per_task": int(cpus_per_task) if cpus_per_task else None,
            "gpus": gpus or None,
            "account": account or None,
            "stdout": str(log_dir / stdout_name),
            "stderr": str(log_dir / stderr_name),
            "command": f"{launcher} {command}",
            "generated_at": datetime.utcnow().isoformat() + "Z",
        }
        script_path.with_suffix(".meta.json").write_text(
            json.dumps({k: v for k, v in metadata.items() if v is not None}, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        return script_path

    def validate_sbatch(self, script: Path) -> list[str]:
        script = Path(script)
        if not script.exists():
            raise FileNotFoundError(script)
        lines = script.read_text(encoding="utf-8").splitlines()
        directives = [line for line in lines if line.startswith("#SBATCH")]
        directive_map: MutableMapping[str, str] = {}
        for directive in directives:
            parts = directive.split(maxsplit=2)
            if len(parts) >= 2:
                directive_map[parts[1]] = directive
        issues: list[str] = []
        for flag in SBATCH_REQUIRED:
            if not any(d.startswith(f"#SBATCH {flag}") for d in directives):
                issues.append(f"Missing required directive {flag}")
        partition_line = directive_map.get("-p")
        partition = partition_line.split(maxsplit=2)[-1] if partition_line else ""
        if partition:
            partition_policy = _load_partition_policy(self.policy, partition)
            limits = _partition_limits(partition_policy)
            max_time = limits.get("max_time")
            if max_time:
                time_line = next((d for d in directives if d.startswith("#SBATCH --time=")), "")
                if time_line:
                    requested = time_line.split("=", 1)[1]
                    try:
                        _format_time(requested, str(max_time))
                    except ValueError as exc:
                        issues.append(str(exc))
        if any(d.startswith("#SBATCH --gres=") for d in directives):
            if not any(d.startswith("#SBATCH --constraint") for d in directives):
                issues.append("GPU request missing --constraint directive")
        execution_lines = [line for line in lines if line and not line.startswith("#")]
        if not any(line.startswith(("srun", "mpirun")) for line in execution_lines):
            issues.append("Execution block should invoke srun or mpirun")
        return issues


def make_sbatch(
    spec: Mapping[str, object],
    policy: Mapping[str, object],
    *,
    output_dir: Path | None = None,
    script_name: str | None = None,
) -> Path:
    planner = SlurmPlanner(policy=policy, output_dir=output_dir)
    return planner.make_sbatch(spec, output_dir=output_dir, script_name=script_name)


def validate_sbatch(script: Path, policy: Mapping[str, object]) -> list[str]:
    planner = SlurmPlanner(policy=policy)
    return planner.validate_sbatch(script)
