import os
import logging
import datetime
import subprocess
import sys
import importlib.util
# tqdm 将用于进度条显示. 将在依赖检查后导入

# --- 配置路径和日志 ---
# 获取桌面路径
desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")

# 确保桌面路径存在，如果不存在则尝试创建或回退
if not os.path.exists(desktop_path):
    print(f"警告：桌面路径 {desktop_path} 不存在。")
    try:
        os.makedirs(desktop_path, exist_ok=True)
        print(f"已尝试创建桌面目录: {desktop_path}")
    except OSError as e:
        print(f"无法创建桌面目录 {desktop_path} ({e})。日志将保存在当前工作目录。")
        desktop_path = os.getcwd() # 日志回退到当前工作目录

log_file_name = datetime.datetime.now().strftime("%Y%m%d_%H%M%S") + "_backup_file_remover.log"
log_file_path = os.path.join(desktop_path, log_file_name)

# 配置日志记录
# filemode='w' 会在每次运行时覆盖日志文件，'a' 会追加。
logging.basicConfig(filename=log_file_path, level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    filemode='w')

# --- 依赖检查与安装函数 ---
def check_and_install_packages(packages):
    """
    检查指定的 Python 包是否已安装，如果未安装则尝试使用 pip 安装。
    Args:
        packages (list): 需要检查和安装的包名列表。
    Returns:
        bool: 如果所有包都已安装或成功安装则返回 True，否则返回 False。
    """
    all_successful = True
    for package in packages:
        spec = importlib.util.find_spec(package)
        if spec is None:
            print(f"模块 {package} 未安装。正在尝试安装...")
            logging.info(f"模块 {package} 未安装。正在尝试安装...")
            try:
                # 使用 sys.executable 确保为当前 Python 解释器调用 pip
                process = subprocess.Popen(
                    [sys.executable, "-m", "pip", "install", package],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True, # 以文本模式处理输出
                    errors='ignore' # 忽略解码错误
                )
                stdout, stderr = process.communicate()

                if process.returncode == 0:
                    print(f"模块 {package} 已成功安装。")
                    logging.info(f"模块 {package} 已成功安装。")
                else:
                    error_message = f"安装模块 {package} 失败。返回码: {process.returncode}\nPip Stdout: {stdout}\nPip Stderr: {stderr}"
                    print(error_message)
                    logging.error(error_message)
                    all_successful = False
            except FileNotFoundError:
                error_message = f"错误：找不到 pip 命令 (尝试通过 {sys.executable} -m pip 调用)。请确保 pip 已安装并为当前 Python 环境正确配置。"
                print(error_message)
                logging.error(error_message)
                all_successful = False
            except Exception as e:
                error_message = f"安装模块 {package} 时发生未知错误: {e}"
                print(error_message)
                logging.error(error_message)
                all_successful = False
        else:
            # print(f"模块 {package} 已安装。") # 可以取消注释以在控制台显示此信息
            logging.info(f"模块 {package} 已安装。")
    return all_successful

# --- 主要脚本逻辑 ---
# 将 tqdm 添加到必需的包列表中
required_packages = ["psutil", "send2trash", "tqdm"]
print("正在检查所需模块...")
dependencies_ok = check_and_install_packages(required_packages)

if not dependencies_ok:
    message = "一个或多个必需的模块未能安装。脚本可能无法正常运行或将立即退出。"
    print(message)
    logging.critical(message)
    sys.exit("依赖安装失败，程序退出。请检查日志获取详细信息，或尝试手动安装所需模块。")

# 依赖检查通过后，再导入这些模块
try:
    import psutil
    import send2trash
    from tqdm import tqdm # 在确认安装后再导入
except ImportError as e:
    critical_message = f"即使在尝试安装后，导入必需模块时依然出错: {e}。\n请检查日志并确保模块已为 Python 环境 '{sys.executable}' 正确安装。\n脚本将退出。"
    print(critical_message)
    logging.critical(critical_message)
    sys.exit(critical_message)

def delete_backup_files(confirm=True):
    """
    自动查找 AutoCAD 和 SketchUp 备份文件。
    如果 confirm=True，则在扫描后统一确认是否删除所有找到的文件。
    如果 confirm=False，则自动删除所有找到的文件。
    """
    search_dirs = []
    try:
        for partition in psutil.disk_partitions():
            # 仅包括可读写的物理驱动器，排除如CD-ROM等特殊设备
            # 同时检查挂载点是否确实是一个目录
            if 'rw' in partition.opts.lower() and os.path.isdir(partition.mountpoint):
                search_dirs.append(partition.mountpoint)
            else:
                logging.info(f"跳过非可读写或非目录挂载点: {partition.mountpoint} (opts: {partition.opts})")
    except Exception as e:
        print(f"获取磁盘分区信息失败: {e}")
        logging.error(f"获取磁盘分区信息失败: {e}")
        return 
    
    if not search_dirs:
        print("未找到可扫描的磁盘驱动器。")
        logging.warning("未找到可扫描的磁盘驱动器。脚本将退出。")
        return

    # 定义要排除的目录的基础定义
    exclude_dirs_definitions = [
        os.path.join(os.path.expanduser("~"), "AppData"), # 用户 AppData
    ]
    # 对于系统级目录，如 Program Files, Windows，应该这样获取（以Windows为例）：
    if os.name == 'nt': # 如果是Windows系统
        program_files = os.environ.get('ProgramFiles')
        program_files_x86 = os.environ.get('ProgramFiles(x86)')
        windows_dir = os.environ.get('WINDIR')
        # 确保这些环境变量对应的路径实际存在且是目录
        if program_files and os.path.isdir(program_files): 
            exclude_dirs_definitions.append(program_files)
        if program_files_x86 and os.path.isdir(program_files_x86): 
            exclude_dirs_definitions.append(program_files_x86)
        if windows_dir and os.path.isdir(windows_dir): 
            exclude_dirs_definitions.append(windows_dir)
        
        # 排除所有驱动器根目录下的回收站 ($Recycle.Bin)
        for part_path in search_dirs: 
             common_recycle_bin = os.path.join(part_path, '$Recycle.Bin') 
             if os.path.isdir(common_recycle_bin):
                 exclude_dirs_definitions.append(common_recycle_bin)
    
    # 转换为规范化的绝对路径，并只保留实际存在的目录以提高效率
    exclude_dirs = []
    for p_def in exclude_dirs_definitions:
        if p_def and os.path.isdir(p_def): 
            exclude_dirs.append(os.path.normpath(os.path.abspath(p_def)))
        elif p_def: 
            logging.warning(f"定义的排除路径 '{p_def}' 不是一个有效目录，将被忽略。")
            
    if exclude_dirs:
        logging.info(f"将排除以下已确认存在的目录及其子目录: {exclude_dirs}")
    else:
        logging.info("没有配置或找到有效的排除目录。")

    files_to_delete_candidates = [] # 存储待删除文件列表

    print("\n开始扫描备份文件，请稍候...") # 总的开始信息
    for search_dir in search_dirs:
        # 为每个驱动器打印清晰的开始信息
        print(f"\n===== 开始扫描驱动器: {search_dir} =====")
        logging.info(f"开始扫描驱动器: {search_dir}")

        walk_iterator = os.walk(search_dir, topdown=True, onerror=lambda err: logging.warning(f"无法访问目录中的项 '{err.filename}': {err.strerror}"))
        
        drive_label = search_dir.replace('\\','').replace(':','') # 尝试获取驱动器字母，例如 C, D
        if not drive_label: drive_label = os.path.basename(search_dir.rstrip(os.sep)) # 回退到路径最后一部分
        if not drive_label: drive_label = search_dir # 最坏情况

        with tqdm(walk_iterator, desc=f"扫描 {drive_label}", unit=" 个目录", leave=False, dynamic_ncols=True, ascii=True) as pbar:
            for dirpath, dirnames, filenames in pbar:
                display_path = dirpath
                if len(display_path) > 60: 
                    display_path = "..." + display_path[-57:]
                pbar.set_postfix_str(f"当前: {display_path}", refresh=True)

                current_normalized_dirpath = os.path.normpath(os.path.abspath(dirpath))
                is_excluded = False
                if exclude_dirs: 
                    for excluded_path in exclude_dirs:
                        if current_normalized_dirpath.startswith(excluded_path):
                            is_excluded = True
                            break 
                if is_excluded:
                    dirnames[:] = []  
                    continue          

                for filename in filenames:
                    if filename.endswith((".bak", ".skb")):
                        backup_file = os.path.join(current_normalized_dirpath, filename)
                        base_name, ext = os.path.splitext(backup_file)
                        original_file = ""
                        if ext == ".bak": original_file = base_name + ".dwg"
                        elif ext == ".skb": original_file = base_name + ".skp"
                        else: continue 

                        if os.path.exists(original_file):
                            logging.info(f"候选删除: 找到备份文件 '{backup_file}' (原始文件 '{original_file}' 存在)。")
                            files_to_delete_candidates.append(backup_file)
    
    sys.stderr.write("\n") # 确保 tqdm 清理后换行，为后续打印做准备
    print("所有驱动器扫描完毕。")
    
    if not files_to_delete_candidates:
        print("未找到符合条件的备份文件。")
        logging.info("扫描完毕。未找到符合条件的备份文件。")
        return

    print(f"\n共找到 {len(files_to_delete_candidates)} 个符合条件的备份文件:")
    for i, f_path in enumerate(files_to_delete_candidates, 1):
        print(f"  {i}. {f_path}")
    
    proceed_with_deletion = False
    if confirm:
        try:
            user_response = input(f"\n是否将以上 {len(files_to_delete_candidates)} 个文件全部移动到回收站？ (y/n): ").strip().lower()
            if user_response == 'y':
                proceed_with_deletion = True
            else:
                print("操作已取消，未移动任何文件。")
                logging.info(f"用户选择不移动 {len(files_to_delete_candidates)} 个候选文件。")
        except KeyboardInterrupt: 
            print("\n操作被用户中断（Ctrl+C）。未移动任何文件。")
            logging.warning("操作被用户通过 KeyboardInterrupt 中断。")
            return 
        except EOFError: 
            print("\n输入已结束，操作取消。未移动任何文件。")
            logging.warning("用户结束了输入流 (EOFError)，操作取消。")
            return
    else: 
        print("\nconfirm=False，将自动移动所有找到的文件到回收站。")
        logging.info(f"confirm=False，自动处理 {len(files_to_delete_candidates)} 个候选文件。")
        proceed_with_deletion = True

    if proceed_with_deletion:
        deleted_count = 0
        failed_count = 0
        print("\n正在移动文件到回收站...")
        with tqdm(files_to_delete_candidates, desc="移动文件", unit=" 个文件", dynamic_ncols=True, ascii=True) as delete_pbar:
            for backup_file_to_delete in delete_pbar:
                delete_pbar.set_postfix_str(os.path.basename(backup_file_to_delete), refresh=True)
                try:
                    send2trash.send2trash(backup_file_to_delete)
                    logging.info(f"已移动到回收站: {backup_file_to_delete}")
                    deleted_count += 1
                except Exception as e: 
                    # 在 tqdm 进度条下方清晰打印错误
                    sys.stderr.write(f"\n  移动文件 '{backup_file_to_delete}' 失败: {e}\n")
                    logging.error(f"移动文件 '{backup_file_to_delete}' 到回收站失败: {e}")
                    failed_count += 1
        
        summary_message = f"操作完成。成功移动 {deleted_count} 个文件，失败 {failed_count} 个文件。"
        print(f"\n{summary_message}")
        logging.info(summary_message)

# --- 脚本入口点 ---
if __name__ == "__main__":
    # 确保脚本在被直接运行时，所有打印信息都能在控制台看到
    # （虽然 tqdm 默认打到 stderr，但普通 print 打到 stdout，通常没问题）
    try:
        print("开始执行备份文件清理脚本...")
        logging.info("脚本开始执行。")
        delete_backup_files(confirm=True)
        print(f"\n脚本执行完毕。日志文件已保存到: {log_file_path}")
        logging.info("脚本执行完毕。")
    except Exception as e:
        # 捕获顶层未知错误，记录并打印
        print(f"脚本执行过程中发生意外错误: {e}")
        logging.critical(f"脚本执行过程中发生意外错误: {e}", exc_info=True)