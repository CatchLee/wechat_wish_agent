import os
import sys

def get_resource_path(relative_path):
    """
    获取资源的绝对路径，兼容开发环境和 PyInstaller 打包后的环境
    """
    # PyInstaller 在运行时会创建 _MEIPASS 临时文件夹
    base_path = getattr(sys, '_MEIPASS', os.path.abspath("."))
    return os.path.join(base_path, relative_path)

DLL_PATH = get_resource_path("src/core/assets/dll/wx_key.dll")
TIMEOUT_SECONDS = 20  # 最大等待时间，超时未获取则失败
