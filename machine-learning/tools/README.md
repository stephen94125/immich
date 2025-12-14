# Immich Machine Learning Model Patcher

This toolkit provides a set of automated scripts to resolve ONNX Runtime compatibility issues in Immich, specifically targeting older GPU architectures (e.g., NVIDIA Pascal / GTX 1070) running ONNX Runtime 1.17.1.

It automates the process of fetching models from your running Immich pod, downgrading their ONNX IR version (from v10 to v9), and re-uploading them.

## 📂 Project Structure

```text
tools/
├── auto_patch_immich_ml.sh       # Main entry point: Orchestrates the entire patch workflow
├── audit_onnx_compatibility.py   # Audits ONNX files for IR version compatibility
├── patch_onnx_models.py          # Clones and patches ONNX files (downgrades IR version)
├── download_from_modelscope.py   # (Optional) Manual downloader for PP-OCRv5 from ModelScope
├── origin_weights/               # (Generated) Local backup of original models from the pod
└── patched_weights/              # (Generated) Modified models ready for upload
```

## 🚀 Quick Start (The "One-Click" Solution)

The bash script `auto_patch_immich_ml.sh` handles everything: finding the pod, downloading weights, running the Python patcher, and uploading the fixed models.

### Prerequisites
- `kubectl` configured with access to your cluster.
- Python 3.10+ with `onnx`, `colorama` (or use `uv` as recommended).
- `tar` installed on your local machine.

### Usage

Run the script with your Kubernetes namespace and Helm release name:

```bash
# Syntax: ./auto_patch_immich_ml.sh <NAMESPACE> <RELEASE_NAME>

# Example:
./auto_patch_immich_ml.sh personal immich
```

**What this script does:**
1.  **Locates** the Immich Machine Learning pod.
2.  **Downloads** the entire `/cache` directory (excluding metadata like `huggingface-xet`).
3.  **Runs** `patch_onnx_models.py` to fix incompatible IR versions.
4.  **Uploads** the patched models back to the pod.

---

## 🛠️ Individual Scripts

If you prefer manual control, you can run the Python scripts individually.

### 1. Audit Models (`audit_onnx_compatibility.py`)

Scans a directory and reports which models are incompatible (IR > 9).

```bash
uv run audit_onnx_compatibility.py origin_weights
```

**Sample Output:**
```text
STATUS          | ACTION          | FILE PATH
------------------------------------------------------------
✅ IR v9 (OK)   | Pass            | clip/ViT-B-32/model.onnx
❌ IR v10 (Too New) | Needs Patching  | ocr/PP-OCRv5_server/detection/model.onnx
```

### 2. Patch Models (`patch_onnx_models.py`)

Clones `origin_weights` to `patched_weights` and applies the IR downgrade patch in-place.

```bash
uv run patch_onnx_models.py
```

### 3. Manual Download (`download_from_modelscope.py`)

If you need to fetch clean `PP-OCRv5_server` weights directly from the source (ModelScope/RapidOCR) instead of from your pod:

```bash
uv run download_from_modelscope.py
```

---

## ⚠️ Notes

*   **Restart Required**: After patching, you must delete/restart the machine-learning pod for changes to take effect:
    ```bash
    kubectl delete pod -n <namespace> -l app.kubernetes.io/component=machine-learning
    ```
*   **Persistent Volume**: This patch modifies files in the pod's PVC (`/cache`). The changes will persist across pod restarts but might be overwritten if you clear the cache or if Immich triggers a fresh model download.

## 📦 Dependencies

Ensure you have the required Python packages installed (or let `uv` handle it):

```toml
# pyproject.toml
[project]
dependencies = [
    "onnx>=1.14.0",
    "colorama>=0.4.6",
    "modelscope>=1.9.0", # Only for the manual downloader
]
```
