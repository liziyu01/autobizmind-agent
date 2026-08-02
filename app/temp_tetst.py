class ChatRequest():
    """对话请求"""
    # 仅类型提示，不是属性
    message: str
    session_id: str

    def __init__(self, message: str, session_id: str):
        self.message = message
        self.session_id = session_id

    def display(self):
        # ❌ ChatRequest.message 依旧不能写！类上没有这个属性
        print(f"self.message = {self.message}")

a = ChatRequest(message="dddddddd", session_id="haodi")
print(a.message)
a.display()