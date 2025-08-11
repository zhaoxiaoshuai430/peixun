# config.py
import streamlit as st
import os

# 尝试从 Streamlit Secrets 获取配置
try:
    secrets = st.secrets
    DB_HOST = secrets["DB_HOST"]
    DB_USER = secrets["DB_USER"]
    DB_PASSWORD = secrets["DB_PASSWORD"]
    DB_NAME = secrets["DB_NAME"]
    DB_PORT = int(secrets["DB_PORT"])
except Exception as e:
    # 如果不在 Streamlit 环境中（如本地运行），尝试从 .env 文件加载
    from dotenv import load_dotenv
    load_dotenv()
    DB_HOST = os.getenv("DB_HOST")
    DB_USER = os.getenv("DB_USER")
    DB_PASSWORD = os.getenv("DB_PASSWORD")
    DB_NAME = os.getenv("DB_NAME")
    DB_PORT = int(os.getenv("DB_PORT", 3306))
