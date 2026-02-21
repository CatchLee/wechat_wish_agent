import hashlib
import hmac
import sqlite3
from pathlib import Path
from Crypto.Cipher import AES
import os
from core.utils.wechat_constants import WeChatDecryptConstants

# 解压单个.db文件
def decrypt_wechat_db(input_path, output_path, hex_key):
    constants = WeChatDecryptConstants()
    page_size = constants.PAGE_SIZE
    salt_size = constants.SALT_SIZE
    iter_count = constants.ITER_COUNT
    key_size = constants.KEY_SIZE
    reserve_size = constants.RESERVE_SIZE
    iv_size = constants.IV_SIZE
    sql_file_header = constants.SQLITE_FILE_HEADER
    # 1. 转换密钥
    raw_key = bytes.fromhex(hex_key)
    
    with open(input_path, "rb") as f:
        data = f.read()
    
    # 2. 获取第一页并提取 Salt (前 16 字节)
    first_page = data[:page_size]
    salt = first_page[:salt_size]
    
    # 3. 派生密钥 (PBKDF2-HMAC-SHA512)
    # 派生加密 Key
    enc_key = hashlib.pbkdf2_hmac("sha512", raw_key, salt, iter_count, key_size)
    # 派生 MAC Key (Salt 异或 0x3a)
    mac_salt = bytes([b ^ 0x3a for b in salt])
    mac_key = hashlib.pbkdf2_hmac("sha512", enc_key, mac_salt, 2, key_size)

    with open(output_path, "wb") as f_out:
        for i in range(len(data) // page_size):
            page_start = i * page_size
            page_data = data[page_start : page_start + page_size]
            
            # 提取 IV 和 密文
            # IV 位于预留空间的前 16 字节
            iv = page_data[page_size - reserve_size : page_size - reserve_size + iv_size]
            
            # 计算需要解密的起始点
            if i == 0:
                # 第一页前 16 字节是 Salt，不参与解密
                content = page_data[salt_size : page_size - reserve_size]
            else:
                content = page_data[: page_size - reserve_size]
            
            # AES-CBC 解密
            cipher = AES.new(enc_key, AES.MODE_CBC, iv)
            decrypted = cipher.decrypt(content)
            
            # 拼接回标准 SQLite 格式
            if i == 0:
                # 第一页写入标准头，并补齐长度
                f_out.write(sql_file_header)
                f_out.write(decrypted)
                f_out.write(b"\0" * reserve_size) # 补全预留位
            else:
                f_out.write(decrypted)
                f_out.write(b"\0" * reserve_size)

    print(f"解密成功！输出文件：{output_path}")

# 解压所有的.db文件
def decrypt_all_db(db_dir, output_dir, hex_key) -> bool:
    base_path = Path(db_dir)
    output_path = Path(output_dir)
    
    if not base_path.exists():
        print(f"❌ 错误：目录不存在 - {db_dir}")
        return False
    
    output_path.mkdir(exist_ok=True)
    
    db_paths = list(base_path.rglob("*.db"))
    db_paths = [f for f in db_paths if f.name.endswith(('.db'))]
    
    output_paths = []
    for path in db_paths:
        last_name = path.stem
        out_file = output_path / f"{last_name}.sqlite"
        output_paths.append(out_file)
    

    if len(db_paths) == 0:
        print(f"⚠️  未找到任何 .db 文件")
        return False
    print(f"📁 找到 {len(db_paths)} 个数据库文件")
    
    for i in range(len(db_paths)):
        db_file = db_paths[i]
        out_file = output_paths[i]
        decrypt_wechat_db(str(db_file), str(out_file), hex_key)
    return True
    
# 使用示例
if __name__ == "__main__":
    MY_HEX_KEY = ""
    DB_DIR = ""
    OUT_DIR = ""
    decrypt_all_db(DB_DIR, OUT_DIR, MY_HEX_KEY)
    