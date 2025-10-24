# init_db.py - 初始化数据库
# 删除旧表，创建新表

from web_app import app, db
from database import Crop, DataRecord

def init_database():
    """初始化数据库"""
    
    with app.app_context():
        print("⚠️ 警告：这将删除所有现有数据！")
        confirm = input("确定要继续吗？(yes/no): ")
        
        if confirm.lower() != 'yes':
            print("❌ 操作已取消")
            return
        
        # 删除所有表
        print("删除旧表...")
        db.drop_all()
        
        # 创建新表
        print("创建新表...")
        db.create_all()
        
        print("✅ 数据库初始化完成！")
        print("\n📝 提示：")
        print("1. 现在可以在 /crops 页面创建作物")
        print("2. 然后在 /records 页面添加记录")

if __name__ == "__main__":
    init_database()