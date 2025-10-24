# 知识库管理模块
# 功能： 文档的增删改、知识检索等

# knowledge_base.py - 知识库管理
# 功能：文档的增删改查

import chromadb
from chromadb.utils import embedding_functions
from config import CHROMA_DB_PATH, COLLECTION_NAME, EMBEDDING_MODEL
import os

class KnowledgeBase:
    """知识库管理类"""
    
    def __init__(self):
        """初始化知识库"""
        # 确保数据目录存在
        os.makedirs(CHROMA_DB_PATH, exist_ok=True)
        
        # 创建ChromaDB客户端
        self.client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
        
        # 设置embedding函数
        self.embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=EMBEDDING_MODEL
        )
        
        # 创建或获取集合
        self.collection = self.client.get_or_create_collection(
            name=COLLECTION_NAME,
            embedding_function=self.embedding_function
        )
        
        print(f"✅ 知识库已连接，当前文档数：{self.collection.count()}")
    
    def add_document(self, content, crop, topic, source="用户添加"):
        """
        添加单个文档
        
        参数:
            content: 文档内容
            crop: 作物类型
            topic: 主题
            source: 来源
        
        返回:
            文档ID
        """
        doc_id = f"doc_{self.collection.count() + 1}"
        
        self.collection.add(
            documents=[content],
            ids=[doc_id],
            metadatas=[{
                "crop": crop,
                "topic": topic,
                "source": source
            }]
        )
        
        print(f"✅ 文档已添加（ID: {doc_id}）")
        return doc_id
    
    def add_documents_batch(self, documents_list):
        """
        批量添加文档
        
        参数:
            documents_list: 文档列表，每个元素是字典
                [{"content": "...", "crop": "...", "topic": "...", "source": "..."}]
        
        返回:
            添加的文档ID列表
        """
        start_count = self.collection.count()
        
        contents = [doc["content"] for doc in documents_list]
        ids = [f"doc_{start_count + i + 1}" for i in range(len(documents_list))]
        metadatas = [
            {
                "crop": doc.get("crop", "未分类"),
                "topic": doc.get("topic", "未分类"),
                "source": doc.get("source", "未知")
            }
            for doc in documents_list
        ]
        
        self.collection.add(
            documents=contents,
            ids=ids,
            metadatas=metadatas
        )
        
        print(f"✅ 批量添加成功：{len(documents_list)} 个文档")
        return ids
    
    def get_document(self, doc_id):
        """
        获取单个文档
        
        参数:
            doc_id: 文档ID
        
        返回:
            文档信息（字典）
        """
        result = self.collection.get(ids=[doc_id])
        
        if result['documents']:
            return {
                "id": doc_id,
                "content": result['documents'][0],
                "metadata": result['metadatas'][0] if result['metadatas'] else {}
            }
        else:
            return None
    
    def delete_document(self, doc_id):
        """
        删除文档
        
        参数:
            doc_id: 文档ID
        """
        self.collection.delete(ids=[doc_id])
        print(f"✅ 文档已删除（ID: {doc_id}）")
    
    def list_documents(self, limit=10):
        """
        列出所有文档
        
        参数:
            limit: 最多显示数量
        
        返回:
            文档列表
        """
        count = self.collection.count()
        
        if count == 0:
            print("⚠️ 知识库为空")
            return []
        
        # 获取所有文档
        result = self.collection.get(limit=min(limit, count))
        
        documents = []
        for i in range(len(result['ids'])):
            documents.append({
                "id": result['ids'][i],
                "content": result['documents'][i],
                "metadata": result['metadatas'][i] if result['metadatas'] else {}
            })
        
        return documents
    
    def search(self, query, n_results=5):
        """
        搜索相关文档
        
        参数:
            query: 查询文本
            n_results: 返回结果数量
        
        返回:
            搜索结果列表
        """
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results
        )
        
        search_results = []
        for i in range(len(results['ids'][0])):
            search_results.append({
                "id": results['ids'][0][i],
                "content": results['documents'][0][i],
                "distance": results['distances'][0][i],
                "similarity": 1 - results['distances'][0][i],
                "metadata": results['metadatas'][0][i] if results['metadatas'] else {}
            })
        
        return search_results
    
    def get_stats(self):
        """
        获取知识库统计信息
        
        返回:
            统计信息字典
        """
        count = self.collection.count()
        
        if count == 0:
            return {
                "total": 0,
                "crops": {},
                "topics": {}
            }
        
        # 获取所有文档元数据
        all_docs = self.collection.get()
        metadatas = all_docs['metadatas']
        
        # 统计作物和主题分布
        crops = {}
        topics = {}
        
        for meta in metadatas:
            crop = meta.get('crop', '未分类')
            topic = meta.get('topic', '未分类')
            
            crops[crop] = crops.get(crop, 0) + 1
            topics[topic] = topics.get(topic, 0) + 1
        
        return {
            "total": count,
            "crops": crops,
            "topics": topics
        }
    
    def clear_all(self):
        """清空知识库（危险操作）"""
        # 删除集合
        self.client.delete_collection(name=COLLECTION_NAME)
        
        # 重新创建
        self.collection = self.client.get_or_create_collection(
            name=COLLECTION_NAME,
            embedding_function=self.embedding_function
        )
        
        print("⚠️ 知识库已清空")

# ===== 测试代码 =====
if __name__ == "__main__":
    # 测试知识库管理
    kb = KnowledgeBase()
    
    # 添加测试文档
    if kb.collection.count() == 0:
        print("\n添加测试文档...")
        test_docs = [
            {
                "content": "小麦的播种时间一般在10月下旬到11月上旬。",
                "crop": "小麦",
                "topic": "播种",
                "source": "测试数据"
            },
            {
                "content": "水稻的种植分为育秧、插秧和田间管理三个阶段。",
                "crop": "水稻",
                "topic": "种植",
                "source": "测试数据"
            }
        ]
        kb.add_documents_batch(test_docs)
    
    # 显示统计
    print("\n" + "="*60)
    stats = kb.get_stats()
    print(f"📊 知识库统计：")
    print(f"  总文档数：{stats['total']}")
    print(f"  作物分类：{stats['crops']}")
    print(f"  主题分类：{stats['topics']}")
    print("="*60)
    
    # 测试搜索
    print("\n测试搜索：")
    results = kb.search("小麦什么时候播种", n_results=2)
    for i, result in enumerate(results, 1):
        print(f"\n结果{i}（相似度: {result['similarity']:.3f}）:")
        print(f"  {result['content'][:50]}...")