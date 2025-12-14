# Immich Pascal GPU Fork

A fork of [Immich](https://github.com/immich-app/immich) that enables machine learning functionality on Pascal architecture GPUs (GTX 10-series) by downgrading CUDA runtime and patching ONNX models.

## Motivation

Starting from Immich v2.3.1, the official machine learning Docker image switched to CUDA 12 + cuDNN 9 + ONNX Runtime 1.20.1, which requires GPU compute capability 7.0 or higher. This breaks compatibility with Pascal GPUs (compute capability 6.1), such as the GTX 1070.

This fork addresses the compatibility issue by:
- Downgrading to CUDA 11.8 + cuDNN 8
- Pinning ONNX Runtime GPU to version 1.17.1
- Providing tools to patch newer ONNX models (IR v10) down to v9 for runtime compatibility

## Key Changes

### 1. CUDA 11.8 Downgrade for Pascal GPU Support
- **Base Image**: Changed from `nvidia/cuda:12.4.1-cudnn-runtime-ubuntu22.04` to `nvidia/cuda:11.8.0-cudnn8-runtime-ubuntu22.04`
- **ONNX Runtime**: Pinned to `1.17.1` (last version supporting CUDA 11.8)
- **Modified Files**:
  - `machine-learning/Dockerfile`
  - `machine-learning/pyproject.toml`
  - `machine-learning/uv.lock`

### 2. ONNX Model Patching Toolkit
A suite of Python scripts to handle ONNX IR version compatibility:
- **`audit_onnx_compatibility.py`**: Batch scan ONNX models and report IR versions
- **`patch_onnx_models.py`**: Downgrade ONNX IR version from v10 to v9
- **`download_models.py`**: Fetch models from ModelScope (alternative to Hugging Face)
- **`auto_patch_immich_ml.sh`**: One-click orchestration script for the entire patching workflow

**Tools Location**: `machine-learning/tools/`

### 3. Bug Fixes
- Fixed `kubectl cp` destination path to prevent nested directory structures when uploading patched models

## Usage

### Building the Modified Docker Image

```bash
docker build -t immich-machine-learning:pascal \
  -f machine-learning/Dockerfile \
  machine-learning/
```

### Using the ONNX Patching Toolkit

#### Prerequisites
- Python 3.11+
- `uv` package manager
- `kubectl` configured with access to your Immich deployment

#### Quick Start with Auto-Patch Script

```bash
cd machine-learning/tools
chmod +x auto_patch_immich_ml.sh
./auto_patch_immich_ml.sh
```

The script will:
1. Fetch models from the running Immich ML pod via `kubectl`
2. Audit all ONNX models for IR version compatibility
3. Automatically patch incompatible models (IR v10 → v9)
4. Upload patched models back to the pod
5. Trigger model cache reload

#### Manual Patching

```bash
cd machine-learning/tools
uv sync
uv run python audit_onnx_compatibility.py /path/to/cache
uv run python patch_onnx_models.py /path/to/cache
```

### Docker Compose Example

Replace the official `immich-machine-learning` image with your custom build:

```yaml
services:
  immich-machine-learning:
    image: immich-machine-learning:pascal
    volumes:
      - model-cache:/cache
```

## Compatibility

- **Supported GPUs**: NVIDIA Pascal architecture (GTX 1050/1060/1070/1080, etc.)
- **CUDA Compute Capability**: 6.1
- **Tested Environment**: GTX 1070 with CUDA 11.8

## Related Commits

1. `ee129a6` - build(ml): downgrade to CUDA 11.8 for Pascal GPU support
2. `2bb5bbe` - feat(tools): add ONNX model patching toolkit for Immich
3. `1156724` - fix(scripts): correct kubectl cp destination path to prevent nested directories

## Upstream Project

This is a fork of [Immich](https://github.com/immich-app/immich) - a high-performance self-hosted photo and video management solution.

For the original project documentation, visit [https://immich.app](https://immich.app).

## License

This project inherits the AGPLv3 license from the upstream Immich project.
