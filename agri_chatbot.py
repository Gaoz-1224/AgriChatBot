# agri_chatbot.py - 主程序
# 功能：整合所有模块，提供交互界面

import os  # <--- 1. 必须把它提到最最最前面
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com" # <--- 2. 马上设置镜像
import sys
from knowledge_base import KnowledgeBase
from rag_engine import RAGEngine
from chat_manager import ChatManager
from config import show_config

class AgriChatBot:
    """农业知识问答Bot主类"""
    
    def __init__(self):
        """初始化ChatBot"""
        print("="*60)
        print("🌾 农宝 AgriChatBot V1.0 初始化中...")
        print("="*60)
        
        # 1. 初始化知识库
        print("\n📦 初始化知识库...")
        self.kb = KnowledgeBase()
        
        # 2. 初始化RAG引擎
        print("\n🤖 初始化RAG引擎...")
        self.rag = RAGEngine(self.kb)
        
        # 3. 初始化对话管理
        print("\n💬 初始化对话管理...")
        self.chat = ChatManager()
        
        print("\n✅ 系统初始化完成！\n")
        
        # 如果知识库为空，自动加载示例数据
        if self.kb.collection.count() == 0:
            self._load_sample_data()
    
    def _load_sample_data(self):
        """加载示例数据"""
        print("📚 知识库为空，正在加载示例数据...")
        
        sample_docs = [
            {
                "content": "小麦的播种时间一般在10月下旬到11月上旬。北方地区可适当提前到10月中旬，南方地区可延迟到11月中旬。播种深度控制在3-5厘米。",
                "crop": "小麦",
                "topic": "播种",
                "source": "农业技术手册"
            },
            {
                "content": "小麦的施肥分为基肥和追肥。基肥在播种前施入，每亩施用有机肥2000-3000公斤，配合氮磷钾复合肥30-40公斤。追肥在返青期施用，每亩追施尿素10-15公斤。",
                "crop": "小麦",
                "topic": "施肥",
                "source": "农业技术手册"
            },
            {
                "content": "小麦赤霉病主要在抽穗扬花期发生，是小麦的主要病害之一。防治方法：在始花期和盛花期各喷药一次，可用50%多菌灵可湿性粉剂或25%戊唑醇乳油。注意用药安全，遵守安全间隔期。",
                "crop": "小麦",
                "topic": "病害",
                "source": "病虫害防治指南"
            },
            {
                "content": "水稻的种植分为三个阶段：育秧、插秧和田间管理。育秧期约30-35天，插秧时秧龄不宜超过40天。插秧深度2-3厘米，行株距30×15厘米。",
                "crop": "水稻",
                "topic": "种植",
                "source": "水稻栽培技术"
            },
            {
                "content": "水稻病虫害主要包括稻瘟病、纹枯病和稻飞虱。稻瘟病在分蘖期和孕穗期易发，可用三环唑或稻瘟灵防治。纹枯病可用井冈霉素防治。稻飞虱可用吡虫啉或噻嗪酮防治。",
                "crop": "水稻",
                "topic": "病害",
                "source": "病虫害防治指南"
            },
            {
                "content": "玉米的播种时间在4月下旬到5月上旬，需要土壤温度达到10℃以上。播种深度5-7厘米，行距60厘米，株距25-30厘米，每亩密度3500-4000株。",
                "crop": "玉米",
                "topic": "播种",
                "source": "玉米种植指南"
            },
            {
                "content": "玉米施肥要重视基肥和追肥的配合。基肥以有机肥为主，每亩2000公斤，配合复合肥40公斤。追肥分两次：拔节期追施尿素15公斤，大喇叭口期追施尿素10公斤。",
                "crop": "玉米",
                "topic": "施肥",
                "source": "科学施肥手册"
            },
            {
                "content": "大豆的播种适期在5月上旬到中旬，土壤温度稳定在8-10℃即可播种。播种深度3-5厘米，行距40-50厘米，株距15-20厘米，每亩保苗1.2-1.5万株。",
                "crop": "大豆",
                "topic": "播种",
                "source": "大豆种植技术"
            },
        ]
        
        self.kb.add_documents_batch(sample_docs)
        print(f"✅ 已加载 {len(sample_docs)} 个示例文档\n")
    
    def ask(self, question, show_sources=False):
        """
        向Bot提问
        
        参数:
            question: 用户问题
            show_sources: 是否显示来源文档
        
        返回:
            AI的回答
        """
        # 获取对话历史
        chat_history = self.chat.get_history()
        
        # 调用RAG引擎
        answer = self.rag.query(
            question=question,
            chat_history=chat_history,
            show_sources=show_sources
        )
        
        # 保存到对话历史
        self.chat.add_ai_message(question, answer)
        
        return answer
    
    def show_menu(self):
        """显示主菜单"""
        print("\n" + "="*60)
        print("📋 主菜单")
        print("="*60)
        print("1. 💬 开始对话")
        print("2. 📚 知识库管理")
        print("3. 📊 查看统计")
        print("4. 🔧 系统设置")
        print("5. ❌ 退出系统")
        print("="*60)
    
    def chat_mode(self):
        """对话模式"""
        print("\n" + "="*60)
        print("💬 对话模式（输入'返回'回到主菜单）")
        print("="*60)
        print("💡 提示：")
        print("  - 直接输入问题进行提问")
        print("  - 输入 '清空' 清空对话历史")
        print("  - 输入 '历史' 查看对话记录")
        print("  - 输入 '来源' 切换是否显示来源文档")
        print("="*60)
        
        show_sources = False
        
        while True:
            user_input = input("\n🧑 你：").strip()
            
            if not user_input:
                print("⚠️ 请输入内容")
                continue
            
            # 处理特殊命令
            if user_input in ["返回", "退出", "exit"]:
                break
            
            if user_input in ["清空", "clear"]:
                self.chat.clear_history()
                continue
            
            if user_input in ["历史", "history"]:
                self._show_chat_history()
                continue
            
            if user_input in ["来源", "source"]:
                show_sources = not show_sources
                status = "开启" if show_sources else "关闭"
                print(f"✅ 来源文档显示已{status}")
                continue
            
            # 正常提问
            print()
            answer = self.ask(user_input, show_sources=show_sources)
            
            print("="*60)
            print("🤖 农宝：")
            print("="*60)
            print(answer)
            print("="*60)
    
    def _show_chat_history(self):
        """显示对话历史"""
        history_list = self.chat.get_history_list()
        
        if not history_list:
            print("⚠️ 暂无对话历史")
            return
        
        print("\n" + "="*60)
        print("📜 对话历史")
        print("="*60)
        
        for i, msg in enumerate(history_list, 1):
            role = "你" if msg['role'] == 'user' else "农宝"
            content = msg['content']
            
            # 如果内容太长，截断显示
            if len(content) > 100:
                content = content[:100] + "..."
            
            print(f"\n{i}. {role}：{content}")
        
        summary = self.chat.get_summary()
        print(f"\n📊 共 {summary['total_messages']} 条消息（窗口：{summary['current_window']}轮）")
        print("="*60)
    
    def knowledge_base_menu(self):
        """知识库管理菜单"""
        while True:
            print("\n" + "="*60)
            print("📚 知识库管理")
            print("="*60)
            print("1. 📝 添加文档")
            print("2. 📋 查看文档列表")
            print("3. 🔍 搜索文档")
            print("4. 🗑️  删除文档")
            print("5. 🔙 返回主菜单")
            print("="*60)
            
            choice = input("\n请选择：").strip()
            
            if choice == "1":
                self._add_document_interactive()
            elif choice == "2":
                self._list_documents()
            elif choice == "3":
                self._search_documents()
            elif choice == "4":
                self._delete_document_interactive()
            elif choice == "5":
                break
            else:
                print("⚠️ 无效选择，请重新输入")
    
    def _add_document_interactive(self):
        """交互式添加文档"""
        print("\n" + "="*60)
        print("📝 添加文档")
        print("="*60)
        
        content = input("文档内容：").strip()
        if not content:
            print("⚠️ 内容不能为空")
            return
        
        crop = input("作物类型（如：小麦、水稻）：").strip() or "未分类"
        topic = input("主题（如：播种、施肥、病害）：").strip() or "未分类"
        source = input("来源（可选）：").strip() or "用户添加"
        
        doc_id = self.kb.add_document(content, crop, topic, source)
        print(f"✅ 文档添加成功（ID: {doc_id}）")
    
    def _list_documents(self):
        """列出文档"""
        print("\n" + "="*60)
        print("📋 文档列表")
        print("="*60)
        
        docs = self.kb.list_documents(limit=20)
        
        if not docs:
            print("⚠️ 知识库为空")
            return
        
        for i, doc in enumerate(docs, 1):
            meta = doc['metadata']
            crop = meta.get('crop', '未知')
            topic = meta.get('topic', '未知')
            content = doc['content']
            
            # 截断显示
            if len(content) > 80:
                content = content[:80] + "..."
            
            print(f"\n{i}. ID: {doc['id']}")
            print(f"   分类：{crop} - {topic}")
            print(f"   内容：{content}")
        
        print(f"\n共 {len(docs)} 个文档（最多显示20个）")
        print("="*60)
    
    def _search_documents(self):
        """搜索文档"""
        print("\n" + "="*60)
        print("🔍 搜索文档")
        print("="*60)
        
        query = input("搜索关键词：").strip()
        if not query:
            print("⚠️ 请输入关键词")
            return
        
        results = self.kb.search(query, n_results=5)
        
        if not results:
            print("⚠️ 没有找到相关文档")
            return
        
        print(f"\n找到 {len(results)} 个相关文档：\n")
        
        for i, result in enumerate(results, 1):
            meta = result['metadata']
            crop = meta.get('crop', '未知')
            topic = meta.get('topic', '未知')
            
            print(f"{i}. 相似度: {result['similarity']:.3f}")
            print(f"   分类：{crop} - {topic}")
            print(f"   内容：{result['content'][:80]}...")
            print()
        
        print("="*60)
    
    def _delete_document_interactive(self):
        """交互式删除文档"""
        print("\n" + "="*60)
        print("🗑️  删除文档")
        print("="*60)
        
        doc_id = input("请输入要删除的文档ID：").strip()
        
        if not doc_id:
            print("⚠️ 请输入文档ID")
            return
        
        # 先查询文档是否存在
        doc = self.kb.get_document(doc_id)
        
        if not doc:
            print(f"⚠️ 文档 {doc_id} 不存在")
            return
        
        # 显示文档信息
        print(f"\n即将删除：")
        print(f"  ID: {doc['id']}")
        print(f"  内容：{doc['content'][:80]}...")
        
        confirm = input("\n确认删除？(y/n)：").strip().lower()
        
        if confirm == 'y':
            self.kb.delete_document(doc_id)
        else:
            print("❌ 取消删除")
    
    def show_stats(self):
        """显示统计信息"""
        print("\n" + "="*60)
        print("📊 系统统计")
        print("="*60)
        
        # 知识库统计
        kb_stats = self.kb.get_stats()
        print(f"\n【知识库】")
        print(f"  文档总数：{kb_stats['total']}")
        
        if kb_stats['crops']:
            print(f"  作物分类：")
            for crop, count in kb_stats['crops'].items():
                print(f"    • {crop}: {count}篇")
        
        if kb_stats['topics']:
            print(f"  主题分类：")
            for topic, count in kb_stats['topics'].items():
                print(f"    • {topic}: {count}篇")
        
        # 对话统计
        chat_summary = self.chat.get_summary()
        print(f"\n【对话】")
        print(f"  消息总数：{chat_summary['total_messages']}")
        print(f"  用户消息：{chat_summary['user_messages']}")
        print(f"  AI消息：{chat_summary['ai_messages']}")
        print(f"  记忆窗口：{chat_summary['current_window']}轮")
        
        print("="*60)
    
    def settings_menu(self):
        """设置菜单"""
        print("\n" + "="*60)
        print("🔧 系统设置")
        print("="*60)
        print("1. 📋 查看配置")
        print("2. 🗑️  清空对话历史")
        print("3. ⚠️  清空知识库（危险）")
        print("4. 🔙 返回")
        print("="*60)
        
        choice = input("\n请选择：").strip()
        
        if choice == "1":
            show_config()
        elif choice == "2":
            confirm = input("确认清空对话历史？(y/n)：").strip().lower()
            if confirm == 'y':
                self.chat.clear_history()
        elif choice == "3":
            confirm = input("⚠️ 危险操作！确认清空知识库？(y/n)：").strip().lower()
            if confirm == 'y':
                self.kb.clear_all()
                print("⚠️ 知识库已清空")
        elif choice == "4":
            return
        else:
            print("⚠️ 无效选择")
    
    def run(self):
        """运行主程序"""
        print("\n" + "="*60)
        print("🎉 欢迎使用农宝 AgriChatBot V1.0")
        print("="*60)
        
        while True:
            self.show_menu()
            choice = input("\n请选择功能：").strip()
            
            if choice == "1":
                self.chat_mode()
            elif choice == "2":
                self.knowledge_base_menu()
            elif choice == "3":
                self.show_stats()
            elif choice == "4":
                self.settings_menu()
            elif choice == "5":
                print("\n👋 感谢使用农宝，再见！")
                break
            else:
                print("⚠️ 无效选择，请输入1-5")

# ===== 主程序入口 =====
if __name__ == "__main__":
    try:
        bot = AgriChatBot()
        bot.run()
    except KeyboardInterrupt:
        print("\n\n👋 程序被中断，再见！")
    except Exception as e:
        print(f"\n❌ 程序出错：{str(e)}")
        import traceback
        traceback.print_exc()