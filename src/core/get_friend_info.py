# 基于wxid获得一个人的基本信息
import sqlite3
from core.utils.friend_info import FriendInfo
def single_user_info(db_path, wxid):
    ###################################
    # 读取数据
    # 1 连接数据库
    TARGET_TABLE = "Contact"
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor() # 创建游标对象
    try:
        query = f"SELECT * FROM {TARGET_TABLE} WHERE username = ?"
        
        # 执行查询，传入目标微信 ID
        cursor.execute(query, (wxid,))
        
        row = cursor.fetchone()
        if not row:
            print(f"[-] 错误：在数据库中未找到微信 ID {wxid} 的用户信息。")
            return None
        
        row = dict(row)
        info = FriendInfo(
            wxid=row["username"],
            alias=row["alias"],
            remark_name=row["remark"],
            description=row["description"]
        )
    except sqlite3.Error as e:
        print(f"[-] 数据库操作失败: {e}")
    finally:
        conn.close()
    return info

if __name__ == "__main__":
    DB_PATH = ""
    wxid = ""
    results = single_user_info(DB_PATH, wxid)
    if results:
        print(results.prompt_str())