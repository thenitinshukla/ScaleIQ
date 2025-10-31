# Test 09 – Leonardo Live Harness

This suite exercises the full HPC workflow on the Leonardo login node by
combining the context retriever, guarded command execution, and LangGraph
planning/execution. Scenarios here execute **real commands** in dry-run mode
(`module`, `git`, `pip`, `sbatch --test-only`, etc.), capture streaming output,
and require the assistant to adapt its plan based on actual results.

Key features:

- Context retrieved from fixture documents plus the live repository tree.
- Guarded command executor that enforces Leonardo safety rules while streaming
  stdout/stderr back to the assistant.
- Full PLAN → tool-call → REPORT loop with telemetry stored per scenario
  (`trace.jsonl`, `commands.jsonl`, `status.log`, `result.json`, and summary).

Run the harness with:

```bash
python hpc_assistant/tests/09_leonardo_live/run_leonardo_live.py
```

Ensure the required environment variables (`VLLM_API_*`) are configured and run
from the Leonardo login node where dry-run commands are permitted.
