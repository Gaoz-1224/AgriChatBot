# web_app.py - Flask Web应用
# 功能：提供Web界面访问AgriChatBot
import os  # <--- 1. 必须在所有库之前
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com" # <--- 2. 设置镜像
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_cors import CORS
from knowledge_base import KnowledgeBase
from rag_engine import RAGEngine
from chat_manager import ChatManager
from database import db, DataRecord
import uuid
from database import Crop  # 添加到文件顶部的导入

app = Flask(__name__)
app.secret_key = os.urandom(24)
CORS(app)

# ===== 数据库配置 =====
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///agri_data.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 初始化数据库
db.init_app(app)

# ===== 初始化Bot =====
print("🚀 初始化AgriChatBot...")
kb = KnowledgeBase()
rag = RAGEngine(kb)
chat_managers = {}

def get_chat_manager():
    """获取当前用户的ChatManager"""
    if 'user_id' not in session:
        session['user_id'] = str(uuid.uuid4())
    
    user_id = session['user_id']
    
    if user_id not in chat_managers:
        chat_managers[user_id] = ChatManager()
    
    return chat_managers[user_id]

# ===== 页面路由 =====

@app.route('/')
def home():
    """首页 - 欢迎页"""
    return render_template('home.html')

@app.route('/chat')
def chat():
    """AI问答页面"""
    return render_template('chat.html')

@app.route('/crops')
def crops():
    """作物管理页面"""
    return render_template('crops.html')

@app.route('/records')
def records():
    """数据记录页面"""
    return render_template('records.html')

@app.route('/analysis')
def analysis():
    """智能分析页面"""
    return render_template('analysis.html')

@app.route('/knowledge')
def knowledge():
    """知识库管理页面"""
    return render_template('knowledge.html')

# ===== AI问答API =====

@app.route('/api/ask', methods=['POST'])
def api_ask():
    """问答API"""
    try:
        data = request.json
        question = data.get('question', '').strip()
        
        if not question:
            return jsonify({"error": "问题不能为空"}), 400
        
        chat = get_chat_manager()
        chat_history = chat.get_history()
        
        # 调用RAG
        answer = rag.query(
            question=question,
            chat_history=chat_history,
            show_sources=False
        )
        
        chat.add_ai_message(question, answer)
        
        return jsonify({
            "success": True,
            "question": question,
            "answer": answer
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/clear_history', methods=['POST'])
def api_clear_history():
    """清空对话历史"""
    try:
        chat = get_chat_manager()
        chat.clear_history()
        return jsonify({"success": True, "message": "对话历史已清空"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ===== 作物管理API =====

@app.route('/api/crops', methods=['GET'])
def api_get_crops():
    """获取所有作物"""
    try:
        crops_list = Crop.query.order_by(Crop.created_at.desc()).all()
        return jsonify({
            "success": True,
            "crops": [c.to_dict() for c in crops_list],
            "total": len(crops_list)
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/crops', methods=['POST'])
def api_add_crop():
    """添加作物"""
    try:
        data = request.json
        
        # 生成crop_id
        crop_type = data['crop_type']
        existing_count = Crop.query.filter_by(crop_type=crop_type).count()
        crop_id = f"{crop_type}_{existing_count + 1:03d}"
        
        new_crop = Crop(
            crop_id=crop_id,
            crop_type=data['crop_type'],
            field_name=data['field_name'],
            variety=data.get('variety', ''),
            area=float(data['area']) if data.get('area') else None,
            planting_date=data.get('planting_date', ''),
            status=data.get('status', '生长中'),
            notes=data.get('notes', '')
        )
        
        db.session.add(new_crop)
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": "作物添加成功",
            "crop": new_crop.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/crops/<int:crop_id>', methods=['GET'])
def api_get_crop(crop_id):
    """获取单个作物详情"""
    try:
        crop = Crop.query.get_or_404(crop_id)
        
        # 获取该作物的所有记录
        records = DataRecord.query.filter_by(crop_db_id=crop_id).order_by(DataRecord.date.desc()).all()
        
        return jsonify({
            "success": True,
            "crop": crop.to_dict(),
            "records": [r.to_dict() for r in records]
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/crops/<int:crop_id>', methods=['PUT'])
def api_update_crop(crop_id):
    """更新作物信息"""
    try:
        crop = Crop.query.get_or_404(crop_id)
        data = request.json
        
        crop.field_name = data.get('field_name', crop.field_name)
        crop.variety = data.get('variety', crop.variety)
        crop.area = float(data['area']) if data.get('area') else crop.area
        crop.planting_date = data.get('planting_date', crop.planting_date)
        crop.status = data.get('status', crop.status)
        crop.notes = data.get('notes', crop.notes)
        
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": "作物更新成功",
            "crop": crop.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/crops/<int:crop_id>', methods=['DELETE'])
def api_delete_crop(crop_id):
    """删除作物（及其所有记录）"""
    try:
        crop = Crop.query.get_or_404(crop_id)
        
        # 由于设置了cascade='all, delete-orphan'，删除作物会自动删除关联的记录
        db.session.delete(crop)
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": f"作物已删除"
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500

# ===== 数据记录API =====

@app.route('/api/records', methods=['GET'])
def api_get_records():
    """获取所有记录"""
    try:
        records = DataRecord.query.order_by(DataRecord.date.desc()).all()
        return jsonify({
            "success": True,
            "records": [r.to_dict() for r in records],
            "total": len(records)
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/records', methods=['POST'])
def api_add_record():
    """添加记录（新版 - 支持作物管理）"""
    try:
        data = request.json
        
        # 获取crop_db_id
        crop_db_id = data.get('crop_db_id')
        if not crop_db_id:
            return jsonify({
                "success": False,
                "error": "请选择作物"
            }), 400
        
        # 验证作物是否存在
        crop = Crop.query.get(crop_db_id)
        if not crop:
            return jsonify({
                "success": False,
                "error": "作物不存在"
            }), 404
        
        new_record = DataRecord(
            crop_db_id=crop_db_id,
            crop_name=crop.crop_type,  # 冗余字段
            date=data['date'],
            record_type=data.get('record_type', '环境'),
            temperature=float(data['temperature']) if data.get('temperature') else None,
            humidity=float(data['humidity']) if data.get('humidity') else None,
            notes=data.get('notes', '')
        )
        
        db.session.add(new_record)
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": "记录添加成功",
            "record": new_record.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/records/<int:record_id>', methods=['DELETE'])
def api_delete_record(record_id):
    """删除记录"""
    try:
        record = DataRecord.query.get_or_404(record_id)
        db.session.delete(record)
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": f"记录 {record_id} 已删除"
        })
    except Exception as e:    
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500

# ===== 智能分析API =====

@app.route('/api/analysis/summary', methods=['POST'])
def api_analysis_summary():
    """AI分析数据记录并给出建议"""
    try:
        data = request.json
        crop_name = data.get('crop_name', None)
        days = data.get('days', 7)
        
        # 获取记录
        query = DataRecord.query
        if crop_name:
            query = query.filter_by(crop_name=crop_name)
        
        records = query.order_by(DataRecord.date.desc()).limit(days).all()
        
        if not records:
            return jsonify({
                "success": False,
                "error": "没有找到相关记录"
            }), 404
        
        # 将记录转换为文本
        records_text = "\n\n".join([f"记录{i+1}:\n{r.to_text()}" for i, r in enumerate(records)])
        
        # 构建分析Prompt
        analysis_prompt = f"""
你是农宝🌾，一位专业的农业数据分析师。

以下是用户最近{days}天记录的{crop_name if crop_name else '作物'}数据：

{records_text}

请分析这些数据并提供：
1. **数据总结**：温度、湿度的变化趋势
2. **潜在问题**：根据数据发现可能的问题（如温度异常、湿度不适等）
3. **专业建议**：针对性的管理建议（施肥、灌溉、病虫害预防等）
4. **风险提示**：需要注意的风险点

要求：
- 语言通俗易懂
- 结构清晰，分点说明
- 300-500字
- 适当使用emoji

请开始分析：
"""
        
        # 调用AI生成分析
        chat = get_chat_manager()
        response = rag.llm.invoke(analysis_prompt)
        analysis_result = response.content
        
        return jsonify({
            "success": True,
            "crop_name": crop_name,
            "days": days,
            "records_count": len(records),
            "analysis": analysis_result
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/analysis/ask_about_records', methods=['POST'])
def api_ask_about_records():
    """基于记录数据回答问题"""
    try:
        data = request.json
        question = data.get('question', '').strip()
        crop_name = data.get('crop_name', None)
        
        if not question:
            return jsonify({"error": "问题不能为空"}), 400
        
        # 获取相关记录
        query = DataRecord.query
        if crop_name:
            query = query.filter_by(crop_name=crop_name)
        
        records = query.order_by(DataRecord.date.desc()).limit(10).all()
        
        if not records:
            # 如果没有记录，用普通RAG回答
            chat = get_chat_manager()
            answer = rag.query(question, chat_history=chat.get_history())
        else:
            # 有记录，基于记录回答
            records_text = "\n\n".join([f"记录{i+1}:\n{r.to_text()}" for i, r in enumerate(records)])
            
            prompt = f"""
你是农宝🌾，用户想基于他的记录数据问你问题。

【用户的记录数据】
{records_text}

【用户问题】
{question}

【回答要求】
1. 优先基于记录数据回答
2. 如果记录数据不够，可以补充你的专业知识，但要说明
3. 语言通俗易懂，200-300字

请回答：
"""
            
            response = rag.llm.invoke(prompt)
            answer = response.content
        
        return jsonify({
            "success": True,
            "question": question,
            "answer": answer,
            "records_used": len(records) if records else 0
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

# ===== 知识库管理API =====

@app.route('/api/documents', methods=['GET'])
def api_get_documents():
    """获取文档列表"""
    try:
        limit = request.args.get('limit', 50, type=int)
        docs = kb.list_documents(limit=limit)
        
        return jsonify({
            "success": True,
            "documents": docs,
            "total": kb.collection.count()
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/documents', methods=['POST'])
def api_add_document():
    """添加文档"""
    try:
        data = request.json
        content = data.get('content', '').strip()
        crop = data.get('crop', '未分类')
        topic = data.get('topic', '未分类')
        source = data.get('source', 'Web添加')
        
        if not content:
            return jsonify({
                "success": False,
                "error": "文档内容不能为空"
            }), 400
        
        doc_id = kb.add_document(content, crop, topic, source)
        
        return jsonify({
            "success": True,
            "message": "文档添加成功",
            "doc_id": doc_id
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/documents/<doc_id>', methods=['DELETE'])
def api_delete_document(doc_id):
    """删除文档"""
    try:
        kb.delete_document(doc_id)
        
        return jsonify({
            "success": True,
            "message": f"文档 {doc_id} 已删除"
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/documents/stats', methods=['GET'])
def api_documents_stats():
    """获取知识库统计信息"""
    try:
        stats = kb.get_stats()
        
        return jsonify({
            "success": True,
            "total": stats['total'],
            "crops": stats['crops'],
            "topics": stats['topics']
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/search', methods=['POST'])
def api_search():
    """搜索文档"""
    try:
        data = request.json
        query = data.get('query', '').strip()
        n_results = data.get('n_results', 20)
        
        if not query:
            return jsonify({
                "success": False,
                "error": "搜索关键词不能为空"
            }), 400
        
        results = kb.search(query, n_results=n_results)
        
        return jsonify({
            "success": True,
            "results": results
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

# ===== 综合统计API =====

@app.route('/api/stats', methods=['GET'])
def api_stats():
    """获取统计信息"""
    try:
        kb_stats = kb.get_stats()
        chat = get_chat_manager()
        chat_summary = chat.get_summary()
        
        # 记录系统统计
        total_records = DataRecord.query.count()
        crops_query = db.session.query(DataRecord.crop_name, db.func.count(DataRecord.id)).group_by(DataRecord.crop_name).all()
        
        return jsonify({
            "success": True,
            "knowledge_base": {
                "total": kb_stats['total'],
                "crops": kb_stats['crops'],
                "topics": kb_stats['topics']
            },
            "chat": chat_summary,
            "records": {
                "total": total_records,
                "by_crop": {crop: count for crop, count in crops_query}
            }
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ===== 主程序 =====
if __name__ == '__main__':
    # 创建数据库表
    with app.app_context():
        db.create_all()
        print("✅ 数据库表已创建")
    
    # 加载示例数据
    if kb.collection.count() == 0:
        print("📚 加载示例数据...")
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
                "content": "小麦赤霉病主要在抽穗扬花期发生，是小麦的主要病害之一。防治方法：在始花期和盛花期各喷药一次，可用50%多菌灵可湿性粉剂或25%戊唑醇乳油。注意用药安全。",
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
                "content": "水稻病虫害主要包括稻瘟病、纹枯病和稻飞虱。稻瘟病在分蘖期和孕穗期易发，可用三环唑或稻瘟灵防治。稻飞虱可用吡虫啉或噻嗪酮防治。",
                "crop": "水稻",
                "topic": "病害",
                "source": "病虫害防治指南"
            },
        ]
        kb.add_documents_batch(sample_docs)
        print(f"✅ 已加载 {len(sample_docs)} 个示例文档")
    
    print("\n" + "="*60)
    print("🌾 农业智能管理系统已启动")
    print("📍 访问地址：http://localhost:5000")
    print("="*60 + "\n")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
