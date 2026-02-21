class FriendInfo:
    def __init__(self, wxid, alias, remark_name, description):
        self.wxid = wxid
        self.alias = alias
        self.remark_name = remark_name
        self.description = description

    def prompt_str(self):
        return f"好友信息（昵称：{self.alias}, 备注：{self.remark_name}, 描述：{self.description}）"