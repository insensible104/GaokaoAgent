# Project Governance Status

This document keeps the project clean enough for implementation, review, and interview explanation.

## Current Source Of Truth

- Runtime graph: `backend/src/graph/dual_loop_supervisor.py`
- Agent communication protocol: `backend/src/models/agent_communication.py`
- Agent bus and protocol validation: `backend/src/utils/agent_bus.py`
- Post-game deliberation agents: `backend/src/agents/deliberation_agents.py`
- Supervisor policy and trajectory reward: `backend/src/rl/supervisor_policy.py`
- Rollout and preference data pipeline: `backend/src/rl/orchestration_data_pipeline.py`
- Architecture guide: `docs/project_architecture_guide.md`

## What Should Be Versioned

- Source code under `backend/src/`
- Scripts under `backend/scripts/`
- Lightweight config and examples
- Documentation under `docs/` and `backend/docs/`
- Small deterministic tests and smoke tests

## What Should Stay Generated

- `backend/logs/`
- `backend/rl_checkpoints/`
- `outputs/`
- `runs/`
- Chroma/vector indexes under `data/chroma_db/`, `backend/data/chroma_db/`, and `backend/data/rag/`
- Model checkpoint formats such as `.ckpt`, `.pt`, `.pth`, and `.safetensors`

## Data Policy

The admissions CSV/XLSX files are currently treated as project data snapshots, not runtime caches. Before publishing or committing, decide whether they are:

1. checked-in sample data,
2. private local data,
3. or downloadable artifacts reconstructed by processing scripts.

Until that decision is made, do not delete or rewrite them during code cleanup.

## Current Architecture Claim

The project is now a deterministic workflow with a governed multi-agent review layer. The workflow controls state transitions, while agents exchange typed proposal, vote, critique, and summary messages. Protocol violations are stored in state, surfaced to the supervisor observation, and penalized in terminal trajectory reward.

## Next Cleanup Checklist

- Run the smoke tests before major edits.
- Keep source and documentation files as UTF-8. On Windows PowerShell, use
  `Get-Content -Encoding UTF8` when inspecting Chinese text.
- Keep generated training artifacts out of git.
- Add new agent messages through `publish_agent_message()` only.
- Add new deliberation stages with explicit required-message contracts.
- Keep reward components named and inspectable.

## Suggested Commit Scope

For the current architecture milestone, the clean source commit should include:

- `backend/src/models/`
- `backend/src/utils/`
- `backend/src/agents/`
- `backend/src/graph/`
- `backend/src/rl/`
- `backend/src/recommendation/`
- `backend/src/engines/`
- `backend/scripts/`
- `backend/docs/`
- `docs/`
- project config files such as `README.md`, `.gitignore`, `backend/pyproject.toml`, and `docker-compose.yml`

Review separately before adding:

- `data/`
- `backend/data/`
- frontend generated dependency changes
- deleted legacy files under `backend/src/agent/`

Do not add:

- `backend/logs/`
- `backend/rl_checkpoints/`
- vector indexes
- model checkpoints
