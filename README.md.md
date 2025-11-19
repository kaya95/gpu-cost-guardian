# GPU Cost Guardian

🚀 **GPU Cost Guardian** is a Python project that monitors idle GPUs and estimates cost waste. Includes a dummy training model to simulate GPU usage for testing.

---

## Features

- Detects GPUs and their utilization
- Simulates killing idle GPUs (`DRY_RUN = True` by default)
- Tracks current and projected cost of idle GPUs
- Includes dummy GPU-heavy training model for testing
- Ready to run in **Google Colab** or local machine

---

## Installation

1. Clone or download this repo
2. (Optional) Create a virtual environment
3. Install requirements:
```bash
pip install torch torchvision torchaudio
