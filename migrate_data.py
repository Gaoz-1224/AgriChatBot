# migrate_data.py - 数据迁移脚本
# 将旧的记录迁移到新的数据结构

from web_app import app, db
from database import Crop, DataRecord

def migrate_old_data():
    """迁移旧数据到新结构"""
    
    with app.app_context():
        print("开始数据迁移...")
        
        # 1. 获取所有旧记录
        old_records = DataRecord.query.filter_by(crop_db_id=None).all()
        
        if not old_records:
            print("✅ 没有需要迁移的数据")
            return
        
        print(f"找到 {len(old_records)} 条旧记录")
        
        # 2. 按作物名称分组
        crop_groups = {}
        for record in old_records:
            crop_name = record.crop_name or "未知"
            if crop_name not in crop_groups:
                crop_groups[crop_name] = []
            crop_groups[crop_name].append(record)
        
        # 3. 为每个作物创建Crop记录
        for crop_name, records in crop_groups.items():
            # 检查是否已存在
            existing = Crop.query.filter_by(crop_type=crop_name, field_name="默认田块").first()
            
            if not existing:
                # 创建新的Crop
                crop_id = f"{crop_name}_{Crop.query.filter_by(crop_type=crop_name).count() + 1:03d}"
                
                new_crop = Crop(
                    crop_id=crop_id,
                    crop_type=crop_name,
                    field_name="默认田块",
                    notes="从旧数据迁移"
                )
                
                db.session.add(new_crop)
                db.session.flush()  # 获取ID
                
                print(f"✅ 创建作物：{crop_name}默认田块")
            else:
                new_crop = existing
            
            # 4. 更新记录的crop_db_id
            for record in records:
                record.crop_db_id = new_crop.id
            
            print(f"✅ 迁移 {len(records)} 条记录到 {crop_name}默认田块")
        
        # 5. 提交更改
        db.session.commit()
        print("\n✅ 数据迁移完成！")
        
        # 6. 显示统计
        total_crops = Crop.query.count()
        total_records = DataRecord.query.count()
        print(f"📊 现在有 {total_crops} 个作物，{total_records} 条记录")

if __name__ == "__main__":
    migrate_old_data()