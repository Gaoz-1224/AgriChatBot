# app_v2.py - 农业智能管理系统 V2（完整修复版）
# 作者：高哲 (@Gaoz-1224)
# 日期：2025-01-23

# app_v2.py - 农业智能管理系统主程序
# app_v2.py - 农业智能管理系统主程序
import os
import sys

# 设置环境变量（在导入任何其他模块之前）
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"

# 尝试加载 .env 文件
try:
    from dotenv import load_dotenv
    load_dotenv(encoding='utf-8')  # 明确指定UTF-8编码
    print("✅ 环境变量已加载")
except Exception as e:
    print(f"⚠️ .env文件加载失败: {e}")
    print("⚠️ 将使用默认配置")

# 如果环境变量中没有API Key，使用硬编码（开发环境）
if not os.getenv('DASHSCOPE_API_KEY'):
    os.environ['DASHSCOPE_API_KEY'] = 'sk-eacfe18e38104e7e873f2da5e8cb0aa0'
    print("⚠️ 使用硬编码API Key")

from flask import Flask, render_template, request, jsonify, session, redirect
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta

# 导入数据模型
from models import db, Crop, DailyRecord, AnalysisHistory

from knowledge_base import KnowledgeBase
from rag_engine import RAGEngine


app = Flask(__name__)
app.secret_key = os.urandom(24)


# ===== 数据库配置 =====
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///agri_v2.db'
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
    """首页"""
    return render_template('home.html')

@app.route('/chat')
def chat():
    """AI问答页面"""
    return render_template('chat.html')

@app.route('/my-crops')
def my_crops():
    """我的作物列表"""
    return render_template('my_crops.html')

@app.route('/crop/<int:crop_id>')
def crop_detail(crop_id):
    """作物详情页面"""
    return render_template('crop_detail.html', crop_id=crop_id)

@app.route('/crop/<int:crop_id>/quick-record')
def quick_record(crop_id):
    """快速记录页面"""
    return render_template('quick_record.html', crop_id=crop_id)

@app.route('/knowledge')
def knowledge():
    """知识库管理页面"""
    return render_template('knowledge.html')

# 注释掉智能分析路由
# @app.route('/analysis')
# def analysis():
#     """智能分析页面"""
#     return render_template('analysis.html')

# ===== AI问答API =====



@app.route('/api/ask', methods=['POST'])
def api_ask():
    """AI问答接口（增强版错误处理）"""
    try:
        # 1. 获取请求数据
        data = request.get_json()
        
        if not data:
            return jsonify({
                "success": False,
                "error": "请求数据为空"
            }), 400
        
        question = data.get('question', '').strip()
        
        if not question:
            return jsonify({
                "success": False,
                "error": "问题不能为空"
            }), 400
        
        if len(question) > 500:
            return jsonify({
                "success": False,
                "error": "问题过长（最多500字）"
            }), 400
        
        print(f"\n{'='*60}")
        print(f"🔍 用户问题：{question}")
        print(f"{'='*60}")
        
        # 2. 获取对话历史
        chat_history = session.get('chat_history', [])
        
        try:
            # 3. 调用RAG引擎
            answer = rag.query(question, chat_history=chat_history)
            
            # 4. 检查回答是否包含错误
            if answer.startswith("❌"):
                return jsonify({
                    "success": False,
                    "error": answer
                }), 500
            
            # 5. 保存到历史
            chat_history.append({"role": "user", "content": question})
            chat_history.append({"role": "ai", "content": answer})
            session['chat_history'] = chat_history[-20:]  # 只保留最近10轮
            
            print(f"✅ AI回答：{answer[:100]}...")
            
            return jsonify({
                "success": True,
                "answer": answer
            })
            
        except Exception as rag_error:
            error_msg = str(rag_error)
            print(f"❌ RAG引擎错误：{error_msg}")
            
            # 特殊处理API Key错误
            if "InvalidApiKey" in error_msg or "401" in error_msg:
                return jsonify({
                    "success": False,
                    "error": "API Key无效或已过期，请联系管理员更新\n\n访问：https://dashscope.console.aliyun.com/apiKey"
                }), 401
            
            # 网络错误
            if "timeout" in error_msg.lower() or "connection" in error_msg.lower():
                return jsonify({
                    "success": False,
                    "error": "网络连接超时，请稍后重试"
                }), 503
            
            # 其他错误
            return jsonify({
                "success": False,
                "error": f"AI处理失败：{error_msg}"
            }), 500
            
    except Exception as e:
        error_msg = str(e)
        print(f"❌ 服务器错误：{error_msg}")
        
        return jsonify({
            "success": False,
            "error": f"服务器错误：{error_msg}"
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

# ===== V2 作物管理API =====

@app.route('/api/v2/crops', methods=['GET'])
def api_v2_get_crops():
    """获取所有作物"""
    try:
        crops = Crop.query.order_by(Crop.created_at.desc()).all()
        
        return jsonify({
            "success": True,
            "crops": [c.to_dict() for c in crops],
            "total": len(crops)
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/v2/crops', methods=['POST'])
def api_v2_add_crop():
    """添加作物"""
    try:
        data = request.json
        
        new_crop = Crop(
            name=data['name'],
            crop_type=data['crop_type'],
            variety=data.get('variety', ''),
            area=float(data['area']) if data.get('area') else None,
            planting_date=datetime.strptime(data['planting_date'], '%Y-%m-%d').date() if data.get('planting_date') else None,
            expected_harvest_date=datetime.strptime(data['expected_harvest_date'], '%Y-%m-%d').date() if data.get('expected_harvest_date') else None,
            notes=data.get('notes', '')
        )
        
        db.session.add(new_crop)
        db.session.commit()
        
        if new_crop.planting_date:
            planting_event = CropEvent(
                crop_id=new_crop.id,
                date=new_crop.planting_date,
                event_type='播种',
                description=f'开始种植{new_crop.name}'
            )
            db.session.add(planting_event)
            db.session.commit()
        
        return jsonify({
            "success": True,
            "message": "作物创建成功",
            "crop": new_crop.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/v2/crops/<int:crop_id>', methods=['GET'])
def api_v2_get_crop(crop_id):
    """获取单个作物详情"""
    try:
        crop = Crop.query.get_or_404(crop_id)
        
        records = DailyRecord.query.filter_by(crop_id=crop_id)\
            .order_by(DailyRecord.date.desc()).all()
        
        events = CropEvent.query.filter_by(crop_id=crop_id)\
            .order_by(CropEvent.date.desc()).all()
        
        return jsonify({
            "success": True,
            "crop": crop.to_dict(),
            "records": [r.to_dict() for r in records],
            "events": [e.to_dict() for e in events]
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/v2/crops/<int:crop_id>', methods=['PUT'])
def api_v2_update_crop(crop_id):
    """更新作物信息"""
    try:
        crop = Crop.query.get_or_404(crop_id)
        data = request.json
        
        if 'name' in data:
            crop.name = data['name']
        if 'variety' in data:
            crop.variety = data['variety']
        if 'area' in data:
            crop.area = float(data['area']) if data['area'] else None
        if 'status' in data:
            crop.status = data['status']
        if 'notes' in data:
            crop.notes = data['notes']
        
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": "作物更新成功",
            "crop": crop.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/v2/crops/<int:crop_id>', methods=['DELETE'])
def api_v2_delete_crop(crop_id):
    """删除作物（及其所有记录和事件）"""
    try:
        crop = Crop.query.get_or_404(crop_id)
        
        db.session.delete(crop)
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": "作物已删除"
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500

# ===== V2 每日记录API =====

@app.route('/api/v2/daily-records', methods=['POST'])
def api_v2_add_daily_record():
    """添加每日记录"""
    try:
        data = request.json
        
        crop_id = data['crop_id']
        today = datetime.strptime(data['date'], '%Y-%m-%d').date()
        
        existing = DailyRecord.query.filter_by(
            crop_id=crop_id,
            date=today
        ).first()
        
        if existing:
            existing.temperature = float(data['temperature']) if data.get('temperature') else None
            existing.humidity = float(data['humidity']) if data.get('humidity') else None
            existing.weather = data.get('weather', '')
            existing.growth_status = data.get('growth_status', '')
            existing.notes = data.get('notes', '')
            
            db.session.commit()
            
            return jsonify({
                "success": True,
                "message": "今日记录已更新",
                "record": existing.to_dict()
            })
        else:
            new_record = DailyRecord(
                crop_id=crop_id,
                date=today,
                temperature=float(data['temperature']) if data.get('temperature') else None,
                humidity=float(data['humidity']) if data.get('humidity') else None,
                weather=data.get('weather', ''),
                growth_status=data.get('growth_status', ''),
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

@app.route('/api/v2/daily-records/<int:record_id>', methods=['DELETE'])
def api_v2_delete_daily_record(record_id):
    """删除每日记录"""
    try:
        record = DailyRecord.query.get_or_404(record_id)
        
        db.session.delete(record)
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": "记录已删除"
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500

# ===== V2 关键事件API =====

@app.route('/api/v2/crop-events', methods=['POST'])
def api_v2_add_crop_event():
    """添加关键事件"""
    try:
        data = request.json
        
        new_event = CropEvent(
            crop_id=data['crop_id'],
            date=datetime.strptime(data['date'], '%Y-%m-%d').date(),
            event_type=data['event_type'],
            description=data.get('description', ''),
            cost=float(data['cost']) if data.get('cost') else None
        )
        
        db.session.add(new_event)
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": "事件添加成功",
            "event": new_event.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500

# ===== AI快速分析API（修改版 - 保存历史）=====

@app.route('/api/v2/analysis/quick/<int:crop_id>', methods=['POST'])
def api_v2_quick_analysis(crop_id):
    """快速AI分析（保存历史记录）"""
    try:
        crop = Crop.query.get_or_404(crop_id)
        data = request.json
        days = data.get('days', 7)
        
        records = DailyRecord.query.filter_by(crop_id=crop_id)\
            .order_by(DailyRecord.date.desc())\
            .limit(days).all()
        
        if not records:
            return jsonify({
                "success": False,
                "error": "数据不足，至少需要3天的记录"
            }), 404
        
        temps = [r.temperature for r in records if r.temperature]
        humidities = [r.humidity for r in records if r.humidity]
        
        avg_temp = sum(temps) / len(temps) if temps else 0
        avg_humidity = sum(humidities) / len(humidities) if humidities else 0
        
        records_text = "\n".join([
            f"{r.date.strftime('%Y-%m-%d')}: 温度{r.temperature}°C, 湿度{r.humidity}%, " +
            f"天气{r.weather or '未知'}, 状态{r.growth_status or '未记录'}"
            for r in reversed(records)
        ])
        
        analysis_prompt = f"""
你是农宝🌾，一位专业的农业AI助手。请对以下作物进行快速分析：

【作物信息】
名称：{crop.name}
类型：{crop.crop_type}
品种：{crop.variety or '未知'}
生长天数：{crop.get_growth_days()}天

【最近{days}天数据】
{records_text}

平均温度：{avg_temp:.1f}°C
平均湿度：{avg_humidity:.1f}%

请从以下3个维度分析，并以JSON格式返回：

{{
    "growth_evaluation": "生长评估文字（50-80字）",
    "growth_score": 85,
    "fertilizer_advice": "施肥建议文字（50-80字）",
    "fertilizer_suggestions": ["具体建议1", "具体建议2"],
    "pest_prediction": "病虫害预测文字（50-80字）",
    "pest_risk": "低"
}}

要求：
1. 评估要客观，基于数据
2. 建议要具体可行
3. 语言要通俗易懂
4. 不要使用markdown格式

请直接返回JSON，不要其他内容。
"""
        
        response = rag.llm.invoke(analysis_prompt)
        result_text = response.content.strip()
        
        json_match = re.search(r'\{[\s\S]*\}', result_text)
        if json_match:
            analysis_json = json.loads(json_match.group())
        else:
            analysis_json = {
                "growth_evaluation": result_text[:100],
                "growth_score": 75,
                "fertilizer_advice": "建议根据作物生长阶段适时施肥",
                "fertilizer_suggestions": ["观察作物长势", "适时追肥"],
                "pest_prediction": "当前风险较低，注意观察",
                "pest_risk": "低"
            }
        
        # 保存分析历史
        analysis_history = AnalysisHistory(
            crop_id=crop_id,
            analysis_type='快速分析',
            growth_evaluation=analysis_json.get('growth_evaluation', ''),
            growth_score=analysis_json.get('growth_score', 0),
            fertilizer_advice=analysis_json.get('fertilizer_advice', ''),
            pest_prediction=analysis_json.get('pest_prediction', ''),
            pest_risk=analysis_json.get('pest_risk', '低'),
            full_analysis=json.dumps(analysis_json, ensure_ascii=False)
        )
        
        db.session.add(analysis_history)
        db.session.commit()
        
        return jsonify({
            "success": True,
            "crop_name": crop.name,
            "days": days,
            "records_count": len(records),
            "analysis": analysis_json,
            "history_id": analysis_history.id
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

# ===== AI分析历史API =====

@app.route('/api/v2/analysis/history/<int:crop_id>', methods=['GET'])
def api_v2_get_analysis_history(crop_id):
    """获取作物的分析历史"""
    try:
        crop = Crop.query.get_or_404(crop_id)
        
        histories = AnalysisHistory.query.filter_by(crop_id=crop_id)\
            .order_by(AnalysisHistory.analysis_date.desc()).all()
        
        return jsonify({
            "success": True,
            "crop_name": crop.name,
            "histories": [h.to_dict() for h in histories],
            "total": len(histories)
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/v2/analysis/history/detail/<int:history_id>', methods=['GET'])
def api_v2_get_analysis_detail(history_id):
    """获取单个分析详情"""
    try:
        history = AnalysisHistory.query.get_or_404(history_id)
        
        full_analysis = json.loads(history.full_analysis) if history.full_analysis else {}
        
        return jsonify({
            "success": True,
            "history": history.to_dict(),
            "full_analysis": full_analysis
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

# ===== AI对话助手API =====

@app.route('/api/v2/analysis/chat/<int:crop_id>', methods=['POST'])
def api_v2_chat_analysis(crop_id):
    """AI对话助手"""
    try:
        crop = Crop.query.get_or_404(crop_id)
        data = request.json
        
        question = data.get('question', '').strip()
        history = data.get('history', [])
        
        if not question:
            return jsonify({
                "success": False,
                "error": "问题不能为空"
            }), 400
        
        records = DailyRecord.query.filter_by(crop_id=crop_id)\
            .order_by(DailyRecord.date.desc())\
            .limit(7).all()
        
        events = CropEvent.query.filter_by(crop_id=crop_id)\
            .order_by(CropEvent.date.desc())\
            .limit(5).all()
        
        records_text = "\n".join([
            f"{r.date.strftime('%Y-%m-%d')}: 温度{r.temperature}°C, 湿度{r.humidity}%, "
            f"天气{r.weather or '未知'}, 状态{r.growth_status or '未记录'}"
            for r in reversed(records)
        ]) if records else "暂无记录"
        
        events_text = "\n".join([
            f"{e.date.strftime('%Y-%m-%d')}: {e.event_type} - {e.description or ''}"
            for e in reversed(events)
        ]) if events else "暂无事件"
        
        conversation_history = "\n".join([
            f"{'用户' if msg['role'] == 'user' else 'AI'}：{msg['content']}"
            for msg in history[-5:]
        ])
        
        chat_prompt = f"""
你是农宝🌾，一位专业、友好的农业AI助手。

【作物信息】
名称：{crop.name}
类型：{crop.crop_type}
品种：{crop.variety or '未知'}
生长天数：{crop.get_growth_days()}天
状态：{crop.status}

【最近7天记录】
{records_text}

【关键事件】
{events_text}

【对话历史】
{conversation_history if conversation_history else '（首次对话）'}

【用户问题】
{question}

【回答要求】
1. 基于作物的实际数据回答
2. 语言通俗易懂、亲切友好
3. 给出具体可行的建议
4. 150-300字左右
5. 适当使用emoji
6. 如果数据不足，诚实说明并给出一般性建议

请回答用户的问题：
"""
        
        response = rag.llm.invoke(chat_prompt)
        answer = response.content.strip()
        
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

# ===== 知识库管理API（保留原有）=====

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
        return jsonify({"success": False, "error": str(e)}), 500

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
            return jsonify({"success": False, "error": "文档内容不能为空"}), 400
        
        doc_id = kb.add_document(content, crop, topic, source)
        
        return jsonify({
            "success": True,
            "message": "文档添加成功",
            "doc_id": doc_id
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/documents/<doc_id>', methods=['DELETE'])
def api_delete_document(doc_id):
    """删除文档"""
    try:
        kb.delete_document(doc_id)
        return jsonify({"success": True, "message": f"文档 {doc_id} 已删除"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

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
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/search', methods=['POST'])
def api_search():
    """搜索文档"""
    try:
        data = request.json
        query = data.get('query', '').strip()
        n_results = data.get('n_results', 20)
        
        if not query:
            return jsonify({"success": False, "error": "搜索关键词不能为空"}), 400
        
        results = kb.search(query, n_results=n_results)
        
        return jsonify({
            "success": True,
            "results": results
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ===== 综合统计API =====

@app.route('/api/stats', methods=['GET'])
def api_stats():
    """获取统计信息"""
    try:
        kb_stats = kb.get_stats()
        chat = get_chat_manager()
        chat_summary = chat.get_summary()
        
        total_crops = Crop.query.count()
        total_records = DailyRecord.query.count()
        
        return jsonify({
            "success": True,
            "knowledge_base": {
                "total": kb_stats['total'],
                "crops": kb_stats['crops'],
                "topics": kb_stats['topics']
            },
            "chat": chat_summary,
            "crops_v2": {
                "total": total_crops,
                "records": total_records
            }
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# 在文件开头添加导入
from werkzeug.utils import secure_filename
import os

# 配置上传文件夹
UPLOAD_FOLDER = 'uploads/documents'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'docx'}

# 确保上传文件夹存在
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    """检查文件扩展名"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def read_document(filepath):
    """读取文档内容"""
    ext = filepath.rsplit('.', 1)[1].lower()
    
    if ext == 'txt':
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    
    elif ext == 'pdf':
        try:
            import PyPDF2
            with open(filepath, 'rb') as f:
                pdf_reader = PyPDF2.PdfReader(f)
                text = ''
                for page in pdf_reader.pages:
                    text += page.extract_text()
                return text
        except:
            return "PDF读取失败（需要安装 PyPDF2: pip install PyPDF2）"
    
    elif ext == 'docx':
        try:
            import docx
            doc = docx.Document(filepath)
            return '\n'.join([para.text for para in doc.paragraphs])
        except:
            return "DOCX读取失败（需要安装 python-docx: pip install python-docx）"
    
    return "不支持的文件格式"

# 添加上传API
@app.route('/api/documents/upload', methods=['POST'])
def upload_document():
    """上传文档并向量化"""
    try:
        # 检查文件
        if 'file' not in request.files:
            return jsonify({"success": False, "error": "没有文件"}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({"success": False, "error": "文件名为空"}), 400
        
        if not allowed_file(file.filename):
            return jsonify({"success": False, "error": "不支持的文件类型"}), 400
        
        # 保存文件
        filename = secure_filename(file.filename)
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)
        
        # 读取内容
        content = read_document(filepath)
        
        if not content or len(content.strip()) < 10:
            os.remove(filepath)
            return jsonify({"success": False, "error": "文件内容为空或过短"}), 400
        
        # 向量化并添加到知识库
        crop = request.form.get('crop', '未分类')
        topic = request.form.get('topic', '未分类')
        
        doc_id = kb.add_document(
            content=content,
            crop=crop,
            topic=topic,
            source=filename
        )
        
        return jsonify({
            "success": True,
            "message": "文档上传并向量化成功",
            "doc_id": doc_id,
            "content_length": len(content)
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

# ========== 缓存管理API ==========

@app.route('/api/cache/stats', methods=['GET'])
def api_cache_stats():
    """获取缓存统计"""
    try:
        stats = rag.get_cache_stats()
        return jsonify({
            "success": True,
            "stats": stats
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/cache/clear', methods=['POST'])
def api_cache_clear():
    """清空缓存"""
    try:
        rag.clear_cache()
        return jsonify({
            "success": True,
            "message": "缓存已清空"
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500




# ===== 主程序 =====
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        print("✅ 数据库表已创建")
    
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
                "content": "水稻的种植分为三个阶段：育秧、插秧和田间管理。育秧期约30-35天，插秧时秧龄不宜超过40天。插秧深度2-3厘米，行株距30×15厘米。",
                "crop": "水稻",
                "topic": "种植",
                "source": "水稻栽培技术"
            }
        ]
        kb.add_documents_batch(sample_docs)
        print(f"✅ 已加载 {len(sample_docs)} 个示例文档")
    
    print("\n" + "="*60)
    print("🌾 农业智能管理系统 V2 已启动")
    print("📍 访问地址：http://localhost:5000")
    print("="*60 + "\n")
    
    app.run(debug=True, host='0.0.0.0', port=5000)