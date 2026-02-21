# 返回一个包含所有联系人的列表
import sqlite3
import os
# TODO 好友判别待完善（可能包含非好友（都在同一个群聊中））
# username不是@chatroom结尾(群聊) / 不是gh_开头(公众号) 就认为是好友
def get_all_users(db_path):
    if not os.path.exists(db_path):
        return None
    ###################################
    # 读取数据
    # 1 连接数据库
    TARGET_TABLE = "Contact"
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor() # 创建游标对象
    user_list = []
    try:
        query = f"SELECT * FROM {TARGET_TABLE} WHERE username NOT LIKE ? AND username NOT LIKE ?"
        params = ('gh_%', '%@chatroom')

        cursor.execute(query, params)
        results = [dict(row) for row in cursor.fetchall()]
        user_list.extend(results)
    except sqlite3.Error as e:
        print(f"[-] 数据库操作失败: {e}")
    finally:
        conn.close()
    return user_list
if __name__ == "__main__":
    DB_PATH = ""
    results = get_all_users(DB_PATH)
    for user in results:
        print(user["remark"] if user["remark"] else (user["nick_name"] if user["nick_name"] else user["username"]))