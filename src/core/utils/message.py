class Message:
    def __init__(self, create_time:int, message_content:str, sender_name:str):
        self.create_time = create_time
        self.message_content = message_content
        self.sender_name = sender_name