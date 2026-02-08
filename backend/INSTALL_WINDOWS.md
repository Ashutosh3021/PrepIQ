# Windows Installation Guide for PrepIQ Backend

## Fixing PyTorch DLL Errors on Windows

If you're experiencing DLL initialization errors with PyTorch on Windows, follow these steps:

### Option 1: Install CPU-only PyTorch (Recommended)

This avoids DLL issues and is sufficient for most use cases:

```powershell
# Uninstall existing PyTorch
pip uninstall torch torchvision torchaudio

# Install CPU-only version
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
```

### Option 2: Install Specific CPU-only Version

```powershell
pip install torch==2.1.0+cpu torchvision==0.16.0+cpu torchaudio==2.1.0+cpu --index-url https://download.pytorch.org/whl/cpu
```

### Option 3: Install Visual C++ Redistributables

If you need GPU support, install the Visual C++ Redistributables:
- Download from: https://aka.ms/vs/17/release/vc_redist.x64.exe
- Install and restart your computer

### Verify Installation

After installation, verify PyTorch works:

```python
import torch
print(torch.__version__)
print(torch.cuda.is_available())  # Should be False for CPU-only
```

## Backend Startup

The backend has been updated to handle ML model loading failures gracefully:
- PyTorch and spaCy imports are now lazy-loaded
- If ML models fail to load, the backend will start with fallback functionality
- All ML features will use lightweight alternatives if full models aren't available

## Troubleshooting

If you still encounter issues:

1. **Clear pip cache:**
   ```powershell
   pip cache purge
   ```

2. **Reinstall in clean virtual environment:**
   ```powershell
   python -m venv .venv
   .venv\Scripts\Activate.ps1
   pip install -r backend/requirements.txt
   ```

3. **Install CPU-only PyTorch separately:**
   ```powershell
   pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
   ```

4. **Check for conflicting packages:**
   ```powershell
   pip list | findstr torch
   ```
