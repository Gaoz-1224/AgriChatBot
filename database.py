# database.py - 新的数据模型（完整版）
# 农业智能管理系统 - 数据库模型
# 作者：高哲 (@Gaoz-1224)

# database.py - 数据库模型（完整修正版）
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

# ===== 作物/田块管理模型 =====
class Crop(db.Model):
    """作物/田块管理模型"""
    __tablename__ = 'crop'
    
    id = db.Column(db.Integer, primary_key=True)
    crop_id = db.Column(db.String(50), unique=True, nullable=False)
    crop_type = db.Column(db.String(50), nullable=False)
    field_name = db.Column(db.String(100), nullable=False)
    variety = db.Column(db.String(100), nullable=True)
    area = db.Column(db.Float, nullable=True)
    planting_date = db.Column(db.String(50), nullable=True)
    status = db.Column(db.String(20), default='生长中')
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    records = db.relationship('DataRecord', backref='crop', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        record_count = len(self.records)
        avg_temp = 0
        avg_humidity = 0
        
        if record_count > 0:
            temps = [r.temperature for r in self.records if r.temperature]
            humidities = [r.humidity for r in self.records if r.humidity]
            avg_temp = sum(temps) / len(temps) if temps else 0
            avg_humidity = sum(humidities) / len(humidities) if humidities else 0
        
        days_growing = 0
        if self.planting_date:
            try:
                planting = datetime.strptime(self.planting_date, '%Y-%m-%d')
                days_growing = (datetime.now() - planting).days
            except:
                pass
        
        return {
            'id': self.id,
            'crop_id': self.crop_id,
            'crop_type': self.crop_type,
            'field_name': self.field_name,
            'display_name': f"{self.crop_type}{self.field_name}",
            'variety': self.variety,
            'area': self.area,
            'planting_date': self.planting_date,
            'status': self.status,
            'notes': self.notes,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'record_count': record_count,
            'avg_temperature': round(avg_temp, 1),
            'avg_humidity': round(avg_humidity, 1),
            'days_growing': days_growing
        }

# ===== 数据记录模型 =====
class DataRecord(db.Model):
    """农业数据记录模型"""
    __tablename__ = 'data_record'
    
    id = db.Column(db.Integer, primary_key=True)
    crop_db_id = db.Column(db.Integer, db.ForeignKey('crop.id'), nullable=False)  # ⭐ 关键字段
    crop_name = db.Column(db.String(100), nullable=True)
    date = db.Column(db.String(50), nullable=False)
    record_type = db.Column(db.String(20), default='环境')
    temperature = db.Column(db.Float, nullable=True)
    humidity = db.Column(db.Float, nullable=True)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        crop_info = self.crop.to_dict() if self.crop else {}
        
        return {
            'id': self.id,
            'crop_db_id': self.crop_db_id,
            'crop_name': self.crop_name or crop_info.get('crop_type', '未知'),
            'field_name': crop_info.get('field_name', ''),
            'display_name': crop_info.get('display_name', self.crop_name),
            'date': self.date,
            'record_type': self.record_type,
            'temperature': self.temperature,
            'humidity': self.humidity,
            'notes': self.notes,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }
    
    def to_text(self):
        crop_info = self.crop.to_dict() if self.crop else {}
        text = f"""
【记录时间】{self.date}
【作物】{crop_info.get('display_name', self.crop_name)}
【温度】{self.temperature}°C
【湿度】{self.humidity}%
"""
        if self.notes:
            text += f"【备注】{self.notes}"
        return text.strip()