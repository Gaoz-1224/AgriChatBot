# rebuild_db.py - 强制重建数据库
import os
from web_app import app, db

def rebuild():
    db_path = 'agri_data.db'
    
    # 删除旧数据库
    if os.path.exists(db_path):
        os.remove(db_path)
        print("✅ 已删除旧数据库")
    
    # 创建新数据库
    with app.app_context():
        db.create_all()
        print("✅ 已创建新数据库")
        
        # 检查表结构
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        
        print("\n📊 数据库表结构：")
        for table_name in inspector.get_table_names():
            print(f"\n表名：{table_name}")
            columns = inspector.get_columns(table_name)
            for col in columns:
                print(f"  - {col['name']}: {col['type']}")

if __name__ == "__main__":
    rebuild()