# 实现搜索功能，给定一个输入，给出包含该输入（在备注 / 用户名 / 描述任一属性中包含该字段）的用户列表
import sqlite3
import os
# search_str：搜索关键词
def search_users(db_path, search_str):
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
        query_remark = f"SELECT * FROM {TARGET_TABLE} WHERE remark LIKE ?"
        query_username = f"SELECT * FROM {TARGET_TABLE} WHERE username LIKE ?"
        query_description = f"SELECT * FROM {TARGET_TABLE} WHERE description LIKE ?"
        search_pattern = f"%{search_str}%"

        cursor.execute(query_remark, (search_pattern,))
        results_remark = [dict(row) for row in cursor.fetchall()]
        cursor.execute(query_username, (search_pattern,))
        results_username = [dict(row) for row in cursor.fetchall()]
        cursor.execute(query_description, (search_pattern,))
        results_description = [dict(row) for row in cursor.fetchall()]

        # 合并结果，去重，优先级：备注 > 用户名 > 描述
        id_set = set()
        for res in results_remark:
            if res['id'] not in id_set:
                user_list.append(res)
                id_set.add(res['id'])
        for res in results_username:
            if res['id'] not in id_set:
                user_list.append(res)
                id_set.add(res['id'])
        for res in results_description:
            if res['id'] not in id_set:
                user_list.append(res)
                id_set.add(res['id'])
        
    except sqlite3.Error as e:
        print(f"[-] 数据库操作失败: {e}")
    finally:
        conn.close()
    return user_list

if __name__ == "__main__":
    DB_PATH = ""
    search_str = ""
    results = search_users(DB_PATH, search_str)
    for user in results:
        print(user["remark"] if user["remark"] else user["username"])