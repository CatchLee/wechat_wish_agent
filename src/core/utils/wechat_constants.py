class WeChatDecryptConstants:
    def __init__(self):
        self.SQLITE_FILE_HEADER = b"SQLite format 3\0"
        self.PAGE_SIZE = 4096
        self.ITER_COUNT = 256000
        self.KEY_SIZE = 32
        self.SALT_SIZE = 16
        self.IV_SIZE = 16
        self.HMAC_SIZE = 64
        self.RESERVE_SIZE = 80 # IV(16) + HMAC(64)