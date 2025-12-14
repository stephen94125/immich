import os
import shutil
import onnx
from pathlib import Path
from colorama import init, Fore, Style

# 初始化顏色輸出
init(autoreset=True)

# ================= 配置區 =================
# 來源目錄 (原始備份)
INPUT_ROOT = Path("./origin_weights")

# 目標目錄 (修復後準備上傳的版本)
OUTPUT_ROOT = Path("./patched_weights")

# 目標 IR Version (ONNX Runtime 1.17.1 / GTX 1070 相容)
TARGET_IR_VERSION = 9
# ===========================================

def patch_model_in_place(model_path: Path):
    """
    直接讀取並在需要時覆寫目標模型檔案 (In-place patching)
    """
    rel_path = model_path.relative_to(OUTPUT_ROOT)
    
    try:
        # 載入模型 (讀取模式)
        model = onnx.load(model_path)
        current_ir = model.ir_version
        
        if current_ir > TARGET_IR_VERSION:
            print(f"🔧 Fixing: {Fore.CYAN}{rel_path}{Style.RESET_ALL}")
            print(f"   ⚠️  Detected IR v{current_ir} > {TARGET_IR_VERSION}")
            print(f"   ⬇️  Downgrading to IR v{TARGET_IR_VERSION}...")
            
            # 修改 IR 版本
            model.ir_version = TARGET_IR_VERSION
            
            # 覆寫回原檔案
            onnx.save(model, model_path)
            print(f"   ✅ {Fore.GREEN}Patched & Saved.{Style.RESET_ALL}")
            return True
        else:
            # 不需要修改
            # print(f"   ℹ️  {rel_path} is IR v{current_ir} (OK). Skipping.")
            return False
            
    except Exception as e:
        print(f"❌ {Fore.RED}Error processing {rel_path}: {e}{Style.RESET_ALL}")
        return False

def main():
    if not INPUT_ROOT.exists():
        print(f"❌ Error: Input directory not found: {INPUT_ROOT}")
        print("   Please ensure you have downloaded the weights first.")
        return

    print(f"🚀 {Style.BRIGHT}Starting Batch Patching Process{Style.RESET_ALL}")
    print(f"   Source: {INPUT_ROOT}")
    print(f"   Target: {OUTPUT_ROOT}")
    print(f"   Target IR: v{TARGET_IR_VERSION}\n")

    # 1. 複製整個目錄結構 (Clone)
    if OUTPUT_ROOT.exists():
        print(f"🧹 Removing existing patched directory: {OUTPUT_ROOT}")
        shutil.rmtree(OUTPUT_ROOT)
    
    print(f"📦 Cloning '{INPUT_ROOT}' to '{OUTPUT_ROOT}'...")
    shutil.copytree(INPUT_ROOT, OUTPUT_ROOT)
    print("   Clone complete. Starting scan...\n")

    # 2. 遍歷 patched_weights 裡的 ONNX 檔案
    patched_count = 0
    total_count = 0
    
    onnx_files = list(OUTPUT_ROOT.rglob("*.onnx"))
    
    for model_file in onnx_files:
        total_count += 1
        if patch_model_in_place(model_file):
            patched_count += 1

    # 3. 總結報告
    print("-" * 60)
    print(f"📊 {Style.BRIGHT}Summary Report:{Style.RESET_ALL}")
    print(f"   Total Models Scanned : {total_count}")
    print(f"   Patched Models       : {Fore.GREEN}{patched_count}{Style.RESET_ALL}")
    print(f"   Unchanged Models     : {total_count - patched_count}")
    print("-" * 60)
    
    if patched_count > 0:
        print(f"\n✨ {Fore.GREEN}Ready to Upload!{Style.RESET_ALL}")
        print(f"   The directory '{OUTPUT_ROOT}' is now fully compatible.")
        print(f"   Upload command:")
        print(f"   kubectl cp {OUTPUT_ROOT} -n personal <pod>:/cache/")
    else:
        print(f"\n🎉 No patches were needed. Your origin weights are already compatible!")

if __name__ == "__main__":
    main()
