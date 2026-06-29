# Project Instructions

Use research-related skills every time and calibrate research taste before acting.

## Codex Experiment Workflow

Do not launch long ML/DL training directly. Every experiment must follow:

```text
PLAN -> MINI_RUN -> FULL_RUN -> MONITOR -> AUDIT -> HANDOFF
```

- `PLAN`: read README, train/eval scripts, configs, data loaders; define data, model, training, eval, saving, monitoring, stop conditions.
- `MINI_RUN`: run a tiny smoke test for load, shape, device, forward, backward, loss, weight update, eval, checkpoint save/resume.
- `FULL_RUN`: record config, seed, command, output dir, log path, checkpoint policy, best-model rule, baseline and kill criterion.
- `MONITOR`: log loss, validation metrics, GPU memory/utilization, CPU/RAM, elapsed time, checkpoint path, result files.
- `AUDIT`: before any claim, verify ground truth provenance, baseline fairness, result file existence, real metric keys, and scope.
- `HANDOFF`: write what changed, what ran, raw results, failure modes, fixes, and next checks.

PathFinder-specific boundary: product evidence, calibration, plan audit, and delivery readiness are not proof of improved real 2026 admission outcomes unless validated with appropriate data.
