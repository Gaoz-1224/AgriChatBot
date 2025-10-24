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