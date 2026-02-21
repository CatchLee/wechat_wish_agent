import hashlib

def str2md5(str_value):
    """计算字符串的 MD5 值"""
    return hashlib.md5(str_value.encode('utf-8')).hexdigest()