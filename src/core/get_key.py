import ctypes
import time
import os
# 如果直接运行当前文件，需要去掉 "core." 的引入前缀
from core.utils.constants import DLL_PATH, TIMEOUT_SECONDS

def extract_wechat_key(pid: int, dll_path: str) -> str:
    """
    注入指定 PID 的微信进程并获取数据库密钥。
    
    Args:
        pid (int): 微信进程 ID
        dll_path (str): wx_key.dll 的文件路径
        
    Returns:
        str: 成功提取到的 64 位 Hex 密钥
        
    Raises:
        Exception: 包含了具体的错误信息
    """
    
    # 1. 路径检查与加载 DLL
    if not os.path.exists(dll_path):
        raise FileNotFoundError(f"DLL 文件未找到: {dll_path}")

    try:
        # 注意: 如果微信是 64 位，你的 Python 解释器也必须是 64 位
        dll = ctypes.CDLL(dll_path)
    except OSError as e:
        raise Exception(f"加载 DLL 失败 (请检查 Python 位数是否为 64 位): {e}")

    # ================= 2. 定义 C 函数签名 =================
    
    # bool InitializeHook(DWORD targetPid);
    dll.InitializeHook.argtypes = [ctypes.c_ulong]
    dll.InitializeHook.restype = ctypes.c_bool

    # bool PollKeyData(char* keyBuffer, int bufferSize);
    dll.PollKeyData.argtypes = [ctypes.c_char_p, ctypes.c_int]
    dll.PollKeyData.restype = ctypes.c_bool

    # bool GetStatusMessage(char* statusBuffer, int bufferSize, int* outLevel);
    dll.GetStatusMessage.argtypes = [ctypes.c_char_p, ctypes.c_int, ctypes.POINTER(ctypes.c_int)]
    dll.GetStatusMessage.restype = ctypes.c_bool

    # bool CleanupHook();
    dll.CleanupHook.argtypes = []
    dll.CleanupHook.restype = ctypes.c_bool

    # const char* GetLastErrorMsg();
    dll.GetLastErrorMsg.argtypes = []
    dll.GetLastErrorMsg.restype = ctypes.c_char_p

    # ================= 3. 执行业务逻辑 =================
    
    print(f"[*] 正在初始化 Hook，目标 PID: {pid}...")
    
    # 步骤 A: 初始化
    if not dll.InitializeHook(pid):
        error_ptr = dll.GetLastErrorMsg()
        error_msg = ctypes.string_at(error_ptr).decode('utf-8', errors='ignore')
        # 初始化失败不需要 Cleanup，直接抛出
        raise Exception(f"初始化失败: {error_msg}")

    # 准备缓冲区
    key_buffer = ctypes.create_string_buffer(128) # 密钥缓冲区
    log_buffer = ctypes.create_string_buffer(512) # 日志缓冲区
    log_level = ctypes.c_int()                    # 日志等级 (输出参数)
    
    start_time = time.time()
    found_key = None

    try:
        print("[*] 开始轮询密钥...")
        while time.time() - start_time < TIMEOUT_SECONDS:
            
            # 步骤 B: 检查密钥 (PollKeyData)
            if dll.PollKeyData(key_buffer, 128):
                found_key = key_buffer.value.decode('utf-8')
                print(f"\n[SUCCESS] 密钥获取成功: {found_key}")
                break # 拿到 Key 了，跳出循环

            # 步骤 C: 检查日志 (GetStatusMessage)
            # 循环读取所有积压的日志，直到返回 False
            while dll.GetStatusMessage(log_buffer, 512, ctypes.byref(log_level)):
                msg = log_buffer.value.decode('utf-8', errors='ignore')
                level = log_level.value
                
                prefix = "[INFO]"
                if level == 1: prefix = "[GOOD]"
                if level == 2: prefix = "[ERROR]"
                
                print(f"  DLL Log -> {prefix} {msg}")

            # 避免 CPU 占用过高
            time.sleep(0.1)
        
        if not found_key:
            raise TimeoutError("获取密钥超时，未在指定时间内捕获到数据库读取操作。")

        return found_key

    except Exception as e:
        raise e  # 向上层抛出异常

    finally:
        # 步骤 D: 必须清理 (CleanupHook)
        # 无论成功还是失败，都要卸载 Shellcode，否则微信可能会崩溃
        print("[*] 清理 Hook 资源...")
        dll.CleanupHook()

def get_wechat_pid():
    import psutil
    for proc in psutil.process_iter(['pid', 'name']):
        if proc.info['name'] == 'Weixin.exe':
            return proc.info['pid']
    return None

def get_key() -> str:
    pid = get_wechat_pid()
    if pid:
        try:
            key = extract_wechat_key(pid, DLL_PATH)
            return key
        except Exception as e:
            print(f"\n错误: {e}")
            return None
    else:
        print("未找到 Weixin.exe 进程，请先登录 PC 微信。")
        return None
# ================= 4. 使用示例 =================

if __name__ == "__main__":
    import sys
    key = get_key()