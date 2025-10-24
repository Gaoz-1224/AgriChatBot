# rag_engine.py - RAG检索增强生成引擎
from langchain_community.chat_models import ChatTongyi
import os
import hashlib

class RAGEngine:
    """RAG检索增强生成引擎"""
    
    def __init__(self, knowledge_base):
        """初始化RAG引擎"""
        self.kb = knowledge_base
        self.llm = self._init_llm()
        
        # 缓存系统
        self.cache = {}
        self.cache_hits = 0
        self.cache_misses = 0
        
        print("✅ RAG引擎已初始化")
    
    def _init_llm(self):
        """初始化大语言模型"""
        # 🔑 在这里替换你的新API Key
        api_key = os.getenv('DASHSCOPE_API_KEY', "sk-20f85e700899477b82bcbb00713108d9")
        
        print(f"🔑 使用API Key: {api_key[:8]}...{api_key[-4:]}")
        
        try:
            llm = ChatTongyi(
                dashscope_api_key=api_key,
                model="qwen-plus",
                temperature=0.7,
                top_p=0.8,
                max_tokens=2000
            )
            print("✅ 通义千问模型已连接")
            return llm
        except Exception as e:
            print(f"❌ 模型初始化失败: {str(e)}")
            print("💡 请检查API Key是否有效：https://dashscope.console.aliyun.com/apiKey")
            raise Exception(f"模型初始化失败: {str(e)}")
    
    def _get_cache_key(self, query):
        """生成查询的缓存键"""
        return hashlib.md5(query.encode('utf-8')).hexdigest()
    
    def query(self, question, chat_history=None, show_sources=False):
        """RAG查询（带缓存和错误处理）"""
        try:
            # 检查缓存
            cache_key = self._get_cache_key(question)
            
            if cache_key in self.cache:
                self.cache_hits += 1
                total = self.cache_hits + self.cache_misses
                print(f"🚀 缓存命中！(命中率: {self.cache_hits}/{total} = {self.cache_hits/total*100:.1f}%)")
                return self.cache[cache_key]
            
            self.cache_misses += 1
            
            # 1. 检索相关文档
            relevant_docs = self.kb.search(question, n_results=5)
            
            if not relevant_docs:
                result = "抱歉，我的知识库中没有找到相关信息。你可以尝试换个方式提问，或者联系管理员添加相关知识。"
                return result
            
            # 2. 构建上下文
            context = "\n\n".join([
                f"【文档{i+1} - {doc['metadata'].get('crop', '未分类')}】\n{doc['content']}"
                for i, doc in enumerate(relevant_docs)
            ])
            
            # 3. 构建prompt
            if chat_history and len(chat_history) > 0:
                chat_context = "\n".join([
                    f"{'用户' if msg['role'] == 'user' else 'AI'}：{msg['content']}"
                    for msg in chat_history[-5:]
                ])
                
                prompt = f"""你是农宝🌾，一位专业、友好的农业AI助手。

【对话历史】
{chat_context}

【相关知识】
{context}

【用户问题】
{question}

【回答要求】
1. 基于上述知识库内容回答
2. 语言通俗易懂，避免过于专业的术语
3. 如果知识库信息不足，诚实说明并给出一般性建议
4. 适当使用emoji让回答更生动（如🌾💧🐛等）
5. 150-300字左右

请回答："""
            else:
                prompt = f"""你是农宝🌾，一位专业、友好的农业AI助手。

【相关知识】
{context}

【用户问题】
{question}

【回答要求】
1. 基于上述知识库内容回答
2. 语言通俗易懂，避免过于专业的术语
3. 如果知识库信息不足，诚实说明并给出一般性建议
4. 适当使用emoji让回答更生动（如🌾💧🐛等）
5. 150-300字左右

请回答："""
            
            # 4. 调用LLM
            response = self.llm.invoke(prompt)
            result = response.content.strip()
            
            # 存入缓存（最多100条）
            if len(self.cache) >= 100:
                oldest_key = next(iter(self.cache))
                del self.cache[oldest_key]
            
            self.cache[cache_key] = result
            return result
            
        except Exception as e:
            error_msg = str(e)
            
            # API Key错误
            if "InvalidApiKey" in error_msg or "401" in error_msg:
                return "❌ API Key无效或已过期！\n\n请管理员访问以下链接更新API Key：\nhttps://dashscope.console.aliyun.com/apiKey"
            
            # 其他错误
            return f"😔 抱歉，AI回答时出现错误：{error_msg}\n\n请稍后重试或联系管理员。"
    
    def get_cache_stats(self):
        """获取缓存统计"""
        total = self.cache_hits + self.cache_misses
        hit_rate = (self.cache_hits / total * 100) if total > 0 else 0
        return {
            'hits': self.cache_hits,
            'misses': self.cache_misses,
            'total_queries': total,
            'hit_rate': f'{hit_rate:.1f}%',
            'cache_size': len(self.cache)
        }
    
    def clear_cache(self):
        """清空缓存"""
        self.cache = {}
        self.cache_hits = 0
        self.cache_misses = 0
        print("🧹 缓存已清空")


# 测试代码
if __name__ == "__main__":
    print("🧪 测试RAG引擎...")
    
    from knowledge_base import KnowledgeBase
    
    kb = KnowledgeBase()
    rag = RAGEngine(kb)
    
    answer = rag.query("小麦什么时候播种？")
    print(f"\n回答：\n{answer}")