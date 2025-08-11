# config.py
import streamlit as st

# 从 Streamlit Secrets 加载配置
def load_config():
    try:
        secrets = st.secrets
        return {
            "DB_HOST": secrets["DB_HOST"],
            "DB_USER": secrets["DB_USER"],
            "DB_PASSWORD": secrets["DB_PASSWORD"],
            "DB_NAME": secrets["DB_NAME"],
            "DB_PORT": int(secrets["DB_PORT"]),
            "ADMIN_PASSWORD": secrets["ADMIN_PASSWORD"]
        }
    except KeyError as e:
        raise Exception(f"❌ 缺少必要的 Secrets 配置: {e}")
    except Exception as e:
        raise Exception(f"❌ 加载配置失败: {e}")

# 全局配置对象
config = load_config()
