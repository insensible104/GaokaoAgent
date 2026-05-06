# Hugging Face Jobs Submission Example

The repository now includes a Jobs-ready GRPO training script:

- `backend/scripts/train_orchestration_grpo_hf_job.py`

When submitting from an environment that supports `hf_jobs()`, use the script content inline or upload the script to a public/private repository first.

## Example payload

```python
hf_jobs("uv", {
    "script": "https://huggingface.co/username/project-assets/resolve/main/train_orchestration_grpo_hf_job.py",
    "script_args": [
        "--dataset-name", "username/gaokao-orchestration-grpo",
        "--model", "Qwen/Qwen2.5-1.5B-Instruct",
        "--hub-model-id", "username/orchestration-grpo-policy",
        "--use-lora",
    ],
    "flavor": "a10g-large",
    "timeout": "4h",
    "secrets": {"HF_TOKEN": "$HF_TOKEN"},
})
```

## Recommended defaults

- flavor: `a10g-large`
- timeout: `4h`
- report backend: `trackio`
- Hub push: always enabled

## Notes

- Jobs containers cannot access your local filesystem directly.
- Upload `train_orchestration_grpo_hf_job.py` to the Hub or another URL first, then reference that URL in `script`.
- The orchestration training datasets should also be uploaded to the Hub for the cleanest workflow.
