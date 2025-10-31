# Unsloth Finetuning Checklist

- Repository: `https://github.com/unslothai/unsloth.git`
- Recommended Python: 3.10 with CUDA 11.8 support.
- Inspect modules with `module avail nvhpc` and load the recommended compiler stack (e.g., `module load nvhpc/22.11`) before installation.
- Install requirements:
  ```
  pip install -r requirements.txt
  pip install -e .
  ```
  If required, prefer `python3 -m pip` or `conda run -n <env> pip` to keep installations within a managed environment.
- Prepare datasets under `/leonardo/home/userexternal/<uid>/datasets`.
- For dry-run jobs, use:
  ```
  sbatch --test-only scripts/finetune_booster.sbatch
  ```
- Monitor GPU memory usage with `srun --test-only --ntasks=1 --gres=gpu:1 nvidia-smi`.
