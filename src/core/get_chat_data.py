# 基于wxid获得和一个人的文字聊天记录
import sqlite3
import zstandard as zstd
import os
from core.utils.str2md5 import str2md5
from core.utils.message import Message

# dbs_paths: 解密后的message数据库文件路径列表
# wxid: 目标微信 ID
# filter_set: 选择保留的消息类型 filter_type = 1 文字消息
def single_user_all_msg(dbs_paths, wxid, filter_set):
    ################################
    # 找到目标表
    # 1. 生成目标表名
    md5_val = str2md5(wxid)
    target_table = f"Msg_{md5_val}"

    print(f"[*] 目标微信 ID: {wxid}")
    print(f"[*] 对应 MD5 表名: {target_table}")

    found_db = None

    # 2. 遍历所有数据库搜索该表
    for db_path in dbs_paths:
        assert os.path.exists(db_path), f"数据库文件 {db_path} 不存在"
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 查询 sqlite_master 表确认该表是否存在
        check_query = "SELECT name FROM sqlite_master WHERE type='table' AND name=?"
        cursor.execute(check_query, (target_table,))
        
        if cursor.fetchone():
            print(f"[+] 在数据库 {db_path} 中找到了表 {target_table}!")
            found_db = db_path
            conn.close()
            break
        conn.close()

    if not found_db:
        print("[-] 错误：在所有提供的数据库中均未找到和{}的聊天记录。".format(wxid))
        exit()
    ###################################
    # 读取数据
    # 1 连接数据库
    conn = sqlite3.connect(found_db)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor() # 创建游标对象
    # 2 查询并返回所有消息
    message_list = []
    try:
        # 2.1 查询消息列表，并获得对应消息内容
        # int int int str/binary
        query = f"SELECT local_type, real_sender_id, create_time, message_content FROM {target_table} ORDER BY create_time DESC"
        cursor.execute(query)
        rows = cursor.fetchall()
        id_set = set()
        # 部分消息内容是经过 Zstd 压缩的二进制数据，解压后才是文本内容
        dctx = zstd.ZstdDecompressor()
        for row in rows:
            # 只保留特定信息
            if row['local_type'] not in filter_set:
                continue
            content = row['message_content']
            if content and type(content) == bytes:
                if content.startswith(b'\x28\xb5\x2f\xfd'): # Zstd 魔法数字
                    try:
                        content = dctx.decompress(content)
                    except zstd.ZstdError as e:
                        print(f"[-] 内容以Zstd 魔法数字，但Zstd 解压失败: {e}")
                else:
                    print(f"[!] 警告：消息内容是二进制数据，但不以Zstd 魔法数字开头，无法正确解压。")
                    print(f"消息前8字节: {content[:8].hex()}")
                    # 尝试直接解码为文本（如果不是压缩数据，可能是纯文本或其他格式）
                    try:
                        content = content.decode('utf-8', errors='ignore')
                    except:
                        pass
            message_list.append(Message(
                message_content=content,
                create_time=row['create_time'],
                sender_name=row['real_sender_id']
            ))
            id_set.add(row['real_sender_id'])
        # 2.2 把local_id转换为发送者wxid
        placeholders = ', '.join(['?'] * len(id_set))
        # 显式查询 rowid，因为它默认不包含在 SELECT * 中
        query = f"SELECT rowid, * FROM Name2Id WHERE rowid IN ({placeholders})"
        cursor.execute(query, tuple(id_set))
        rows = cursor.fetchall()

        localid_to_wxid = {row['rowid']: row['user_name'] for row in rows}
        for msg in message_list:
            if msg.sender_name in localid_to_wxid:
                msg.sender_name = localid_to_wxid[msg.sender_name]
        
    except sqlite3.Error as e:
        print(f"[-] 数据库操作失败: {e}")
    finally:
        conn.close()
    return message_list

# ================= 配置区 =================
    
# ==========================================

if __name__ == "__main__":
    # ================= 配置区 =================
    DB_FILE0 = ""        
    DB_FILE1 = ""   
    DB_FILE2 = ""
    MY_DBS = [DB_FILE0, DB_FILE1, DB_FILE2]
    TARGET_WXID = "" # 替换为实际的微信 ID
    # ==========================================
    message_list = single_user_all_msg(MY_DBS, TARGET_WXID, set({1}))
    for msg in message_list:
        print(f"时间: {msg.create_time}, 发送者: {msg.sender_name}, 内容: {msg.message_content[:50]}...")