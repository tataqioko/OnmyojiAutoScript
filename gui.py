# This Python file uses the following encoding: utf-8
# @author runhey
# github https://github.com/runhey

import os
import sys
import subprocess
from pathlib import Path

# 确保使用内置的Python环境
def ensure_correct_python():
    """确保使用项目内置的Python环境"""
    current_dir = Path(__file__).parent.absolute()
    target_python = current_dir / "toolkit" / "python.exe"
    
    # 检查当前运行的Python是否是目标Python
    current_python = Path(sys.executable).resolve()
    target_python = target_python.resolve()
    
    if current_python != target_python:
        print(f"当前Python: {current_python}")
        print(f"目标Python: {target_python}")
        print("正在切换到内置Python环境...")
        
        # 使用内置Python重新启动脚本
        args = [str(target_python)] + sys.argv
        subprocess.run(args)
        sys.exit(0)

# 在导入其他模块之前检查Python环境
ensure_correct_python()

def check_emulator_connection():
    """快速检查模拟器连接状态"""
    adb_path = Path(__file__).parent / "toolkit" / "Lib" / "site-packages" / "adbutils" / "binaries" / "adb.exe"
    result = subprocess.run([str(adb_path), "devices"], capture_output=True, text=True)
    return "127.0.0.1:16384\tdevice" in result.stdout

def async_setup_emulator():
    """异步设置模拟器连接（后台运行）"""
    import threading
    import time
    import json
    
    def setup_worker():
        print("🔍 后台检查模拟器连接...")
        
        # 项目内置ADB路径
        adb_path = Path(__file__).parent / "toolkit" / "Lib" / "site-packages" / "adbutils" / "binaries" / "adb.exe"
        
        # 检查当前设备连接状态
        if check_emulator_connection():
            print("✅ MuMu模拟器已连接")
            return
        
        print("📱 未检测到MuMu模拟器，尝试启动...")
        
        # 从配置文件读取模拟器路径
        config_path = Path(__file__).parent / "config" / "oas1.json"
        if config_path.exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                emulator_path = config.get("script", {}).get("device", {}).get("emulatorinfo_path", "")
                
                if emulator_path and Path(emulator_path).exists():
                    print(f"🚀 后台启动模拟器: {emulator_path}")
                    subprocess.Popen([emulator_path], shell=True)
                    
                    # 后台等待模拟器启动
                    print("⏳ 后台等待模拟器启动（最多60秒）...")
                    for i in range(12):  # 检查12次，每次5秒
                        time.sleep(5)
                        
                        # 尝试连接ADB
                        subprocess.run([str(adb_path), "connect", "127.0.0.1:16384"], capture_output=True, text=True)
                        
                        # 检查连接状态
                        if check_emulator_connection():
                            print("✅ MuMu模拟器后台连接成功")
                            return
                        
                        print(f"⏳ 等待中... ({(i+1)*5}/60秒)")
                    
                    print("❌ MuMu模拟器启动超时")
                else:
                    print("⚠️ 配置文件中未找到有效的模拟器路径")
            except Exception as e:
                print(f"❌ 读取配置文件失败: {e}")
        
        print("❌ MuMu模拟器连接失败")
        print("请手动：")
        print("1. 启动MuMu模拟器")
        print("2. 确保开发者选项和USB调试已开启")
        print("3. 重新启动GUI程序")
    
    # 启动后台线程
    thread = threading.Thread(target=setup_worker, daemon=True, name="EmulatorSetup")
    thread.start()
    
    # 立即返回，不阻塞GUI启动
    print("🎮 GUI启动中，模拟器连接在后台进行...")

from module.gui.utils import check_admin
from module.gui.context.add import Add
from module.gui.context.settings import Setting
from module.gui.context.process_manager import ProcessManager
from module.gui.context.utils import Utils
from module.gui.register_type.paint_image import PaintImage
from module.gui.register_type.rule_file import RuleFile
from module.gui.fluent_app import FluentApp

if __name__ == "__main__":
    # 检查是不是以管理员身份运行，脚本启动的其他进程会继承权限
    # 但是貌似有问题的这个函数
    # check_admin()
    
    # 异步设置模拟器连接（不阻塞GUI启动）
    print("🎮 阴阳师自动脚本启动中...")
    async_setup_emulator()
    
    # 启动一个UI交互的线程，因为信号槽不可跨进程
    # 后面选择注入上下文快
    app = FluentApp()
    add_config = Add()
    setting = Setting()
    process_manager = ProcessManager()
    utils = Utils()

    app.set_context_property(setting, 'setting')
    app.set_context_property(add_config, 'add_config')
    app.set_context_property(process_manager, 'process_manager')
    app.set_context_property(utils, 'utils')
    app.qml_register_type(PaintImage, 'PaintImage')
    app.qml_register_type(RuleFile, 'RuleFile')
    # 启动一个GUI
    app.run()
