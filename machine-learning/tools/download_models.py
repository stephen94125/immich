import os
import shutil
from pathlib import Path
from modelscope import snapshot_download

# ================= 配置區 =================
# 這裡對應 Immich 的資料夾結構命名
TARGET_MODEL_NAME = "PP-OCRv5_server" 

# 定義要抓的檔案 (ModelScope 裡的原始路徑)
# 根據你提供的截圖與 RapidOCR 倉庫結構：
# Det: onnx/PP-OCRv5/det/ch_PP-OCRv5_server_det.onnx
# Rec: onnx/PP-OCRv5/rec/ch_PP-OCRv5_rec_server_infer.onnx
TARGET_FILES = {
    "detection": "onnx/PP-OCRv5/det/ch_PP-OCRv5_server_det.onnx",
    "recognition": "onnx/PP-OCRv5/rec/ch_PP-OCRv5_rec_server_infer.onnx"
}

DOWNLOAD_ROOT = Path("./downloaded_models")
FINAL_OUTPUT_DIR = DOWNLOAD_ROOT / TARGET_MODEL_NAME
# ===========================================

def main():
    print(f"🚀 Starting download for: {TARGET_MODEL_NAME}")
    
    # 1. 建立乾淨的目標目錄
    if FINAL_OUTPUT_DIR.exists():
        shutil.rmtree(FINAL_OUTPUT_DIR)
    FINAL_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # 2. 構建過濾清單 (只下載這兩個檔案，其他全部無視)
    allow_patterns = list(TARGET_FILES.values())
    
    print(f"🎯 Target files: {allow_patterns}")

    # 3. 從 ModelScope 下載 (會暫存到 cache 目錄，然後 link 到 local_dir)
    # 注意：ModelScope 的 local_dir 會保留原始 repo 結構 (onnx/PP-OCRv5/...)
    temp_download_dir = DOWNLOAD_ROOT / "_temp_raw"
    
    try:
        downloaded_path = snapshot_download(
            repo_id="RapidAI/RapidOCR",
            local_dir=str(temp_download_dir),
            allow_patterns=allow_patterns, 
        )
        print("✅ Download finished. Reorganizing files...")

        # 4. 搬運與重命名
        downloaded_path = Path(downloaded_path)
        
        for role, original_rel_path in TARGET_FILES.items():
            # 原始檔案的絕對路徑
            src_file = downloaded_path / original_rel_path
            
            # 目標資料夾 (e.g., ./downloaded_models/PP-OCRv5_server/detection)
            dest_dir = FINAL_OUTPUT_DIR / role
            dest_dir.mkdir(exist_ok=True)
            
            # 目標檔案 (e.g., model.onnx)
            dest_file = dest_dir / "model.onnx"
            
            if src_file.exists():
                print(f"   📦 Moving {src_file.name} -> {role}/model.onnx")
                shutil.copy2(src_file, dest_file)
            else:
                print(f"   ❌ Error: Expected file not found: {src_file}")

        # 5. 清理暫存目錄 (把那些多餘的空資料夾結構砍了)
        print("🧹 Cleaning up temp files...")
        shutil.rmtree(temp_download_dir)
        
        print(f"\n✨ All done! Files are ready in:\n   {FINAL_OUTPUT_DIR.resolve()}")
        print(f"      ├── detection/model.onnx")
        print(f"      └── recognition/model.onnx")

    except Exception as e:
        print(f"❌ Download failed: {e}")

if __name__ == "__main__":
    main()
