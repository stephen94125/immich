import os
import argparse
import onnx
from pathlib import Path
from colorama import init, Fore, Style

# 初始化顏色輸出 (Windows/Linux 通用)
init(autoreset=True)

# ================= 配置區 =================
# 預設目標相容版本 (高於此版本的都會被標紅)
MAX_COMPATIBLE_IR = 9
# ===========================================

def check_ir_version(file_path: Path, root_path: Path):
    try:
        # 只讀取 Header，速度極快，不用載入整個權重
        model = onnx.load(file_path, load_external_data=False)
        ir_ver = model.ir_version
        
        # 格式化輸出
        rel_path = file_path.relative_to(root_path)
        
        if ir_ver > MAX_COMPATIBLE_IR:
            status = f"{Fore.RED}❌ IR v{ir_ver} (Too New){Style.RESET_ALL}"
            action = f"{Fore.YELLOW}Needs Patching{Style.RESET_ALL}"
        else:
            status = f"{Fore.GREEN}✅ IR v{ir_ver} (OK){Style.RESET_ALL}"
            action = f"{Fore.BLACK}{Style.BRIGHT}Pass{Style.RESET_ALL}"
            
        print(f"{status} | {action} | {rel_path}")
        
        return ir_ver
    
    except Exception as e:
        print(f"{Fore.RED}⚠️  Error reading {file_path.name}: {e}{Style.RESET_ALL}")
        return None

def main():
    # 設定參數解析
    parser = argparse.ArgumentParser(description="Scan directory for ONNX models and check IR version compatibility.")
    parser.add_argument(
        "target_dir", 
        type=str, 
        help="The directory containing ONNX models to scan (default: ./origin_weights)"
    )
    
    args = parser.parse_args()
    search_root = Path(args.target_dir)

    if not search_root.exists():
        print(f"{Fore.RED}❌ Directory not found: {search_root}{Style.RESET_ALL}")
        return

    print(f"🔎 Scanning ONNX models in: {Fore.CYAN}{search_root}{Style.RESET_ALL}")
    print(f"   Target Compatibility: IR Version <= {MAX_COMPATIBLE_IR}\n")
    print("-" * 60)
    print(f"{'STATUS':<15} | {'ACTION':<15} | FILE PATH")
    print("-" * 60)

    # 搜尋所有 .onnx 檔案
    onnx_files = sorted(list(search_root.rglob("*.onnx")))
    
    if not onnx_files:
        print(f"{Fore.YELLOW}⚠️  No .onnx files found in {search_root}{Style.RESET_ALL}")
        return

    stats = {"ok": 0, "fail": 0, "total": 0}
    
    for f in onnx_files:
        ver = check_ir_version(f, search_root)
        if ver is not None:
            stats["total"] += 1
            if ver > MAX_COMPATIBLE_IR:
                stats["fail"] += 1
            else:
                stats["ok"] += 1

    print("-" * 60)
    print(f"\n📊 Summary:")
    print(f"   Total Models: {stats['total']}")
    print(f"   Compatible  : {Fore.GREEN}{stats['ok']}{Style.RESET_ALL}")
    print(f"   Incompatible: {Fore.RED}{stats['fail']}{Style.RESET_ALL} (Need Patching)")
    
    if stats["fail"] > 0:
        print(f"\n💡 Tip: Run the patching script on this folder to fix {stats['fail']} issues.")
    elif stats["total"] > 0:
        print(f"\n✨ {Fore.GREEN}Perfect! All models in this directory are compatible.{Style.RESET_ALL}")

if __name__ == "__main__":
    main()
