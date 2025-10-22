"""Regex-based error triage utilities."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Callable, Iterable, Optional


@dataclass
class TriageRule:
    rule_id: str
    category: str
    pattern: re.Pattern[str]
    confidence: float
    advice_fn: Callable[[re.Match[str]], list[str]]


class ErrorTriage:
    def __init__(self, rules: Iterable[TriageRule]):
        self.rules = list(rules)

    def classify(self, stderr: str) -> Optional[dict]:
        for rule in self.rules:
            match = rule.pattern.search(stderr)
            if match:
                result = {
                    "category": rule.category,
                    "rule_id": rule.rule_id,
                    "confidence": rule.confidence,
                    "evidence": match.group(0).strip(),
                    "advice": rule.advice_fn(match),
                }
                for key, value in match.groupdict().items():
                    if value and key not in result:
                        result[key] = value
                return result
        return None


def compile_rules() -> list[TriageRule]:
    return [
        TriageRule(
            rule_id="compile.missing_header",
            category="compile",
            pattern=re.compile(r"fatal error:\s+(?P<header>[^:]+): No such file", re.IGNORECASE),
            confidence=0.9,
            advice_fn=lambda m: [
                "Caricare il modulo MPI appropriato (es. module load openmpi)",
                f"Aggiungere l'include path per {m.group('header')} (es. -I$MPI_HOME/include)",
            ],
        ),
        TriageRule(
            rule_id="compile.invalid_flag",
            category="compile",
            pattern=re.compile(r"(unknown|unrecognized) (?:command line )?(?:option|argument): '?(?P<flag>-[^'\s]+)'?", re.IGNORECASE),
            confidence=0.85,
            advice_fn=lambda m: [
                f"Rimuovere o correggere il flag {m.group('flag')}",
                "Verificare la compatibilità del compilatore con l'architettura desiderata",
            ],
        ),
    ]


def link_rules() -> list[TriageRule]:
    return [
        TriageRule(
            rule_id="link.undefined_reference",
            category="link",
            pattern=re.compile(r"undefined reference to `?(?P<symbol>[^'\s]+)'?", re.IGNORECASE),
            confidence=0.85,
            advice_fn=lambda m: [
                f"Aggiungere la libreria che contiene {m.group('symbol')} (es. -l<lib> o target_link_libraries)",
                "Verificare l'ordine delle librerie nella link line",
            ],
        ),
        TriageRule(
            rule_id="link.missing_library",
            category="link",
            pattern=re.compile(r"(?:cannot find) -l(?P<lib>\S+)|(?:library not found for -l)(?P<lib_alt>\S+)", re.IGNORECASE),
            confidence=0.9,
            advice_fn=lambda m: [
                f"Caricare il modulo che fornisce lib{m.group('lib') or m.group('lib_alt')}",
                f"Aggiungere il path alla libreria (es. -L/path/to/{m.group('lib') or m.group('lib_alt')})",
            ],
        ),
    ]


def gpu_rules() -> list[TriageRule]:
    return [
        TriageRule(
            rule_id="gpu.unsupported_architecture",
            category="gpu",
            pattern=re.compile(r"nvcc fatal\s*:.*Unsupported gpu architecture '(?P<arch>[^']+)'", re.IGNORECASE),
            confidence=0.9,
            advice_fn=lambda m: [
                "Allineare le flag -gencode/-arch ad un'architettura supportata (es. -gencode arch=compute_80,code=sm_80)",
                "Caricare il modulo CUDA compatibile con le GPU del cluster",
            ],
        ),
        TriageRule(
            rule_id="gpu.missing_offload_arch",
            category="gpu",
            pattern=re.compile(r"provide --offload-arch", re.IGNORECASE),
            confidence=0.85,
            advice_fn=lambda m: [
                "Aggiungere --offload-arch=<gfx> a clang/hipcc (es. --offload-arch=gfx90a)",
                "Verificare il modulo ROCm/hipcc corretto",
            ],
        ),
    ]


def default_rules() -> list[TriageRule]:
    return compile_rules() + link_rules() + gpu_rules()
