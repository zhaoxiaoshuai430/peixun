# config.py
import os
from dotenv import load_dotenv

# 加载本地 .env 文件（仅开发环境）
load_dotenv()

def DB_CONFIG():
    return {
        "host": os.getenv("DB_HOST"),
        "user": os.getenv("DB_USER"),
        "password": os.getenv("DB_PASSWORD"),
        "database": os.getenv("DB_NAME")
    }

def ADMIN_PASSWORD():
    return os.getenv("ADMIN_PASSWORD")
