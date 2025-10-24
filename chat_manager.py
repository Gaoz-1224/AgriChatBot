# 对话管理
# 负责管理用户与AI助手之间的对话流程和状态



from langchain.memory import ConversationBufferWindowMemory
from config import MAX_HISTORY

class ChatManager:
    """对话管理类"""
    
    def __init__(self, max_history=MAX_HISTORY):
        """
        初始化对话管理器
        
        参数:
            max_history: 最大保留轮数
        """
        # 使用窗口记忆（只保留最近N轮对话）
        self.memory = ConversationBufferWindowMemory(
            k=max_history,  # 保留最近k轮对话
            return_messages=False  # 返回字符串格式
        )
        
        self.max_history = max_history
        print(f"✅ 对话管理器已初始化（记忆窗口：{max_history}轮）")
    
    def add_user_message(self, message):
        """
        添加用户消息
        
        参数:
            message: 用户输入的消息
        """
        self.memory.save_context(
            {"input": message},
            {"output": ""}  # 先占位，等AI回答后更新
        )
    
    def add_ai_message(self, user_message, ai_message):
        """
        添加AI消息（和对应的用户消息）
        
        参数:
            user_message: 用户消息
            ai_message: AI回答
        """
        self.memory.save_context(
            {"input": user_message},
            {"output": ai_message}
        )
    
    def get_history(self):
        """
        获取对话历史（字符串格式）
        
        返回:
            格式化的对话历史
        """
        # 获取记忆内容
        history = self.memory.load_memory_variables({})
        
        # 返回格式化的历史
        return history.get('history', '')
    
    def get_history_list(self):
        """
        获取对话历史（列表格式）
        
        返回:
            对话列表 [{"role": "user", "content": "..."}, ...]
        """
        history_str = self.get_history()
        
        if not history_str:
            return []
        
        # 解析历史字符串为列表
        messages = []
        lines = history_str.split('\n')
        
        for line in lines:
            if line.startswith('Human: '):
                messages.append({
                    "role": "user",
                    "content": line.replace('Human: ', '')
                })
            elif line.startswith('AI: '):
                messages.append({
                    "role": "assistant",
                    "content": line.replace('AI: ', '')
                })
        
        return messages
    
    def clear_history(self):
        """清空对话历史"""
        self.memory.clear()
        print("✅ 对话历史已清空")
    
    def get_summary(self):
        """
        获取对话摘要信息
        
        返回:
            摘要字典
        """
        history_list = self.get_history_list()
        
        user_count = sum(1 for msg in history_list if msg['role'] == 'user')
        ai_count = sum(1 for msg in history_list if msg['role'] == 'assistant')
        
        return {
            "total_messages": len(history_list),
            "user_messages": user_count,
            "ai_messages": ai_count,
            "current_window": self.max_history
        }

# ===== 测试代码 =====
if __name__ == "__main__":
    # 测试对话管理
    chat = ChatManager(max_history=3)
    
    # 模拟对话
    print("\n模拟对话：")
    chat.add_ai_message("你好", "你好！我是农宝🌾")
    chat.add_ai_message("小麦什么时候播种？", "小麦一般在10月下旬播种...")
    chat.add_ai_message("那施肥呢？", "小麦施肥分为基肥和追肥...")
    chat.add_ai_message("水稻呢？", "水稻的种植...")
    
    # 显示历史
    print("\n当前对话历史：")
    print("="*60)
    print(chat.get_history())
    print("="*60)
    
    # 显示摘要
    print("\n对话摘要：")
    summary = chat.get_summary()
    print(f"  总消息数：{summary['total_messages']}")
    print(f"  用户消息：{summary['user_messages']}")
    print(f"  AI消息：{summary['ai_messages']}")
    print(f"  记忆窗口：{summary['current_window']}轮")