import streamlit as st
import mysql.connector
import pandas as pd
import json
from datetime import datetime
import os
from config import DB_CONFIG, ADMIN_PASSWORD

# 设置页面配置
st.set_page_config(
    page_title="在线答题系统",
    page_icon="📝",
    layout="wide"
)

class QuizSystem:
    def __init__(self):
        self.connection = None
    
    def get_db_connection(self):
        """获取数据库连接"""
        try:
            if self.connection is None or not self.connection.is_connected():
                self.connection = mysql.connector.connect(**DB_CONFIG())
            return self.connection
        except mysql.connector.Error as e:
            st.error(f"数据库连接失败: {e}")
            return None
    
    def create_tables(self):
        """创建必要的数据表"""
        conn = self.get_db_connection()
        if conn:
            cursor = conn.cursor()
            
            # 创建用户答题记录表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_responses (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_name VARCHAR(100) NOT NULL,
                    hotel VARCHAR(100) NOT NULL,
                    department VARCHAR(100) NOT NULL,
                    response_data JSON,
                    submit_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    ip_address VARCHAR(45)
                )
            """)
            
            # 创建题目表（如果不存在）
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS questions (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    question_text TEXT NOT NULL,
                    options JSON,
                    question_type ENUM('radio', 'checkbox', 'text') DEFAULT 'radio',
                    answer_text TEXT,  -- 新增字段：标准答案（用于学习模块）
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.commit()
            cursor.close()
    
    def fetch_questions(self):
        """从数据库获取题目"""
        conn = self.get_db_connection()
        if conn:
            try:
                query = "SELECT id, question_text, options, question_type, options FROM questions ORDER BY id"
                df = pd.read_sql(query, conn)
                return df.to_dict('records')
            except Exception as e:
                st.error(f"获取题目失败: {e}")
                return []
        return []
    
    def fetch_question(self):
        """从数据库获取题目"""
        conn = self.get_db_connection()
        if conn:
            try:
                query = "SELECT question_id, title,content FROM question ORDER BY question_id"
                df = pd.read_sql(query, conn)
                return df.to_dict('records')
            except Exception as e:
                st.error(f"获取题目失败: {e}")
                return []
        return []
    
    def save_response(self, user_name, hotel, department, answers):
        """保存用户答题记录"""
        conn = self.get_db_connection()
        if conn:
            try:
                cursor = conn.cursor()
                ip_address = "127.0.0.1"  # 实际应用中可从 request 获取
                answers_json = json.dumps(answers, ensure_ascii=False)
                query = """
                INSERT INTO user_responses (user_name, hotel, department, response_data, ip_address) 
                VALUES (%s, %s, %s, %s, %s)
                """
                cursor.execute(query, (user_name, hotel, department, answers_json, ip_address))
                conn.commit()
                cursor.close()
                return True
            except Exception as e:
                st.error(f"保存失败: {e}")
                return False
        return False
    
    def get_completion_status(self):
        """获取完成情况统计"""
        conn = self.get_db_connection()
        if conn:
            try:
                query = """
                SELECT user_name, hotel, department, submit_time 
                FROM user_responses 
                ORDER BY submit_time DESC
                """
                df = pd.read_sql(query, conn)
                return df
            except Exception as e:
                st.error(f"获取统计信息失败: {e}")
                return pd.DataFrame()
        return pd.DataFrame()

def main():
    st.title("📝 在线答题系统")
    
    # 初始化系统
    quiz_system = QuizSystem()
    quiz_system.create_tables()
    
    # 侧边栏导航
    st.sidebar.title("导航")
    # ✅ 新增：添加“学习模块”
    page = st.sidebar.radio("选择页面", ["学习模块", "开始答题", "完成情况"])
    
    # ================== 开始答题模块（保持不变）==================
    if page == "开始答题":
        st.header("欢迎参加答题")
        
        # 用户信息输入
        col1, col2, col3 = st.columns(3)
        with col1:
            hotel = st.selectbox(
                "请选择您的酒店:",
                ["请选择酒店", "中油花园酒店", "郑州华智酒店", "开封来旺达酒店", "华丰来旺达酒店", "新乡来旺达酒店","来旺达商旅酒店"]
            )
        
        with col2:
            name = st.text_input("请输入您的姓名:")
        
        with col3:
            department = st.selectbox(
                "请选择您的部门:",
                ["请选择部门", "人力资源部", "财务部", "市场部", "技术部", "客服部", "行政部"]
            )
        
        # 验证输入
        if st.button("开始答题"):
            if hotel == "请选择酒店":
                st.warning("请先选择酒店！")
            elif not name.strip():
                st.warning("请输入您的姓名！")
            elif department == "请选择部门":
                st.warning("请先选择部门！")
            else:
                st.session_state.user_info = {"name": name, "hotel": hotel, "department": department}
                st.success(f"欢迎 {name} 来自 {hotel} 的 {department}！")
        
        # 显示答题界面
        if 'user_info' in st.session_state:
            user_info = st.session_state.user_info
            st.markdown(f"**当前用户**: {user_info['name']} | **酒店**: {user_info['hotel']} | **部门**: {user_info['department']}")
            st.markdown("---")
            
            questions = quiz_system.fetch_questions()
            if not questions:
                st.info("暂无题目，请联系管理员添加题目。")
                return
            
            answers = {}
            for i, q in enumerate(questions):
                st.subheader(f"第 {i+1} 题")
                st.write(q['question_text'])
                
                key = f"q_{q['id']}"
                if q['question_type'] == 'radio':
                    options_str = q['options'].strip('"') if isinstance(q['options'], str) else q['options']
                    options = [opt.strip() for opt in options_str.split(',')] if isinstance(options_str, str) else options_str
                    answers[key] = st.radio("", options, key=key, label_visibility="collapsed")
                elif q['question_type'] == 'checkbox':
                    options_str = q['options'].strip('"') if isinstance(q['options'], str) else q['options']
                    options = [opt.strip() for opt in options_str.split(',')] if isinstance(options_str, str) else options_str
                    answers[key] = st.multiselect("", options, key=key, label_visibility="collapsed")
                else:
                    answers[key] = st.text_input("", key=key)
                st.markdown("---")
            
            if st.button("提交答案", type="primary"):
                with st.spinner("正在保存..."):
                    if quiz_system.save_response(user_info['name'], user_info['hotel'], user_info['department'], answers):
                        st.success("✅ 答题提交成功！感谢您的参与！")
                        del st.session_state.user_info
                    else:
                        st.error("❌ 提交失败，请重试。")

    # ================== ✅ 新增：学习模块 ==================
    elif page == "学习模块":
        st.header("📘 学习模块")
        st.markdown("点击问题即可查看答案，用于复习和学习。")

        question = quiz_system.fetch_question()
        if not question:
            st.info("暂无学习内容，请联系管理员添加题目和答案。")
        else:
            for i, q in enumerate(question):
                question = q['title']
                answer = q.get('content', '暂无标准答案') or '暂无标准答案'

                # ✅ 使用 expander 实现“点击显示答案”
                with st.expander(f"❓ {i+1}. {question}"):
                    st.markdown(f"✅ **答案**: {answer}")

    # ================== 完成情况模块（保持不变）==================
    elif page == "完成情况":
        st.header("答题完成情况统计")
        
        password = st.text_input("输入密码:", type="password")
        
        if password == ADMIN_PASSWORD():
            st.success("✅ 验证成功！")
            df = quiz_system.get_completion_status()
            
            if df.empty:
                st.info("📭 暂无用户提交记录")
            else:
                st.write(f"📊 总共有 {len(df)} 人完成了答题")
                st.subheader("完成用户列表")
                st.dataframe(
                    df,
                    column_config={
                        "submit_time": st.column_config.DatetimeColumn("提交时间", format="YYYY-MM-DD HH:mm:ss")
                    },
                    hide_index=True,
                    use_container_width=True
                )
                
                st.subheader("统计分析")
                hotel_stats = df['hotel'].value_counts()
                st.bar_chart(hotel_stats, height=300)
                st.caption("各酒店参与人数")
                
                st.subheader("各酒店各部门参与情况")
                hotels = df['hotel'].unique()
                for hotel in hotels:
                    st.markdown(f"### {hotel}")
                    hotel_df = df[df['hotel'] == hotel]
                    dept_stats = hotel_df['department'].value_counts()
                    st.bar_chart(dept_stats, height=250)
                    st.markdown(f"**{hotel} 总参与人数**: {len(hotel_df)}")
                    st.markdown(f"**涉及部门数量**: {len(dept_stats)}")
                    st.markdown("---")
            
            if not df.empty:
                csv = df.to_csv(index=False, encoding='utf-8-sig')
                st.download_button(
                    label="📥 导出数据为CSV",
                    data=csv,
                    file_name=f"答题记录_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv"
                )
        
        elif password:
            st.error("❌ 密码错误！")

# 运行主程序
if __name__ == "__main__":
    main()