@echo off
REM 尝试将活动代码页设置为 UTF-8 (65001)，以更好地支持中文字符输出。
chcp 65001 > nul

REM --- 自动备份文件清理脚本启动器 ---

echo 正在准备启动“自动备份文件清理”工具...
REM 确保 Python 解释器已安装并在系统的 PATH 环境变量中。
REM Python 脚本 (backup_file_remover.py) 将会尝试自动安装它所需的依赖库。

python backup_file_remover.py

echo.
echo 脚本执行完毕。您可以查看桌面上的日志文件。
REM 下面的 "pause" 命令会使此窗口在脚本执行后保持打开，直到用户按下任意键。
pause