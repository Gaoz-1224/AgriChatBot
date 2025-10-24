# models.py - 数据库模型（完整版 - 包含分析历史）
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta

db = SQLAlchemy()

# ===== 作物模型（核心）=====
class Crop(db.Model):
    """作物 - 一个作物就是一个完整的生命周期"""
    __tablename__ = 'crops'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # 基本信息
    name = db.Column(db.String(100), nullable=False)
    crop_type = db.Column(db.String(50), nullable=False)
    variety = db.Column(db.String(100))
    area = db.Column(db.Float)
    
    # 时间信息
    planting_date = db.Column(db.Date)
    expected_harvest_date = db.Column(db.Date)
    actual_harvest_date = db.Column(db.Date)
    
    # 状态
    status = db.Column(db.String(20), default='生长中')
    
    # 备注
    notes = db.Column(db.Text)
    
    # 创建时间
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 关联：每日记录
    daily_records = db.relationship('DailyRecord', backref='crop', lazy=True, cascade='all, delete-orphan')
    
    # 关联：关键事件
    events = db.relationship('CropEvent', backref='crop', lazy=True, cascade='all, delete-orphan')
    
    # 关联：分析历史
    analysis_histories = db.relationship('AnalysisHistory', backref='crop', lazy=True, cascade='all, delete-orphan')
    
    def get_growth_days(self):
        """计算生长天数"""
        if not self.planting_date:
            return 0
        
        end_date = self.actual_harvest_date or datetime.now().date()
        return (end_date - self.planting_date).days
    
    def get_latest_record(self):
        """获取最新记录"""
        if not self.daily_records:
            return None
        return sorted(self.daily_records, key=lambda x: x.date, reverse=True)[0]
    
    def get_avg_temperature(self, days=7):
        """获取最近N天平均温度"""
        records = sorted(self.daily_records, key=lambda x: x.date, reverse=True)[:days]
        if not records:
            return None
        temps = [r.temperature for r in records if r.temperature]
        return round(sum(temps) / len(temps), 1) if temps else None
    
    def get_avg_humidity(self, days=7):
        """获取最近N天平均湿度"""
        records = sorted(self.daily_records, key=lambda x: x.date, reverse=True)[:days]
        if not records:
            return None
        humidities = [r.humidity for r in records if r.humidity]
        return round(sum(humidities) / len(humidities), 1) if humidities else None
    
    def to_dict(self):
        """转换为字典"""
        latest = self.get_latest_record()
        
        return {
            'id': self.id,
            'name': self.name,
            'crop_type': self.crop_type,
            'variety': self.variety,
            'area': self.area,
            'planting_date': self.planting_date.strftime('%Y-%m-%d') if self.planting_date else None,
            'expected_harvest_date': self.expected_harvest_date.strftime('%Y-%m-%d') if self.expected_harvest_date else None,
            'actual_harvest_date': self.actual_harvest_date.strftime('%Y-%m-%d') if self.actual_harvest_date else None,
            'status': self.status,
            'notes': self.notes,
            'growth_days': self.get_growth_days(),
            'record_count': len(self.daily_records),
            'event_count': len(self.events),
            'avg_temperature_7d': self.get_avg_temperature(7),
            'avg_humidity_7d': self.get_avg_humidity(7),
            'latest_temperature': latest.temperature if latest else None,
            'latest_humidity': latest.humidity if latest else None,
            'latest_date': latest.date.strftime('%Y-%m-%d') if latest else None,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }
    
    def __repr__(self):
        return f'<Crop {self.name}>'

# ===== 每日记录模型 =====
class DailyRecord(db.Model):
    """每日记录 - 快速记录每天的数据"""
    __tablename__ = 'daily_records'
    
    id = db.Column(db.Integer, primary_key=True)
    crop_id = db.Column(db.Integer, db.ForeignKey('crops.id'), nullable=False)
    
    date = db.Column(db.Date, nullable=False)
    temperature = db.Column(db.Float)
    humidity = db.Column(db.Float)
    weather = db.Column(db.String(50))
    growth_status = db.Column(db.String(100))
    notes = db.Column(db.Text)
    
    photo_url = db.Column(db.String(500))
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'crop_id': self.crop_id,
            'date': self.date.strftime('%Y-%m-%d'),
            'temperature': self.temperature,
            'humidity': self.humidity,
            'weather': self.weather,
            'growth_status': self.growth_status,
            'notes': self.notes,
            'photo_url': self.photo_url,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }
    
    def __repr__(self):
        return f'<DailyRecord {self.date}>'

# ===== 关键事件模型 =====
class CropEvent(db.Model):
    """关键事件 - 记录重要操作（播种、施肥、打药等）"""
    __tablename__ = 'crop_events'
    
    id = db.Column(db.Integer, primary_key=True)
    crop_id = db.Column(db.Integer, db.ForeignKey('crops.id'), nullable=False)
    
    date = db.Column(db.Date, nullable=False)
    event_type = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text)
    cost = db.Column(db.Float)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'crop_id': self.crop_id,
            'date': self.date.strftime('%Y-%m-%d'),
            'event_type': self.event_type,
            'description': self.description,
            'cost': self.cost,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }
    
    def __repr__(self):
        return f'<CropEvent {self.event_type} - {self.date}>'

# ===== AI分析历史模型 =====
class AnalysisHistory(db.Model):
    """AI分析历史记录"""
    __tablename__ = 'analysis_history'
    
    id = db.Column(db.Integer, primary_key=True)
    crop_id = db.Column(db.Integer, db.ForeignKey('crops.id'), nullable=False)
    
    analysis_type = db.Column(db.String(50), default='快速分析')
    analysis_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 分析结果
    growth_evaluation = db.Column(db.Text)
    growth_score = db.Column(db.Integer)
    fertilizer_advice = db.Column(db.Text)
    pest_prediction = db.Column(db.Text)
    pest_risk = db.Column(db.String(20))
    
    # 完整分析内容（JSON）
    full_analysis = db.Column(db.Text)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'crop_id': self.crop_id,
            'analysis_type': self.analysis_type,
            'analysis_date': self.analysis_date.strftime('%Y-%m-%d %H:%M:%S'),
            'growth_evaluation': self.growth_evaluation,
            'growth_score': self.growth_score,
            'fertilizer_advice': self.fertilizer_advice,
            'pest_prediction': self.pest_prediction,
            'pest_risk': self.pest_risk,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }
    
    def __repr__(self):
        return f'<AnalysisHistory {self.id} - {self.analysis_date}>'