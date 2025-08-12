# quiz_system.py
import mysql.connector
from mysql.connector import Error
import pandas as pd
import json
from datetime import datetime


class QuizSystem:
    def __init__(self, host, user, password, database, port=3306):
        """
        初始化数据库连接
        """
        self.connection = None
        print(f"Connecting to MySQL server at {host}:{port} with user {user}:{password}")
        try:
            self.connection = mysql.connector.connect(
                host=host,
                port=int(port),
                user=user,
                password=password,
                database=database,
                charset='utf8mb4',
                autocommit=True
            )
            if self.connection.is_connected():
                print("✅ 数据库连接成功")
        except Error as e:
            raise Exception(f"❌ 数据库连接失败: {e}")

    def __del__(self):
        """
        关闭数据库连接
        """
        if self.connection and self.connection.is_connected():
            self.connection.close()
            print("🔌 数据库连接已关闭")

    def fetch_questions_for_quiz(self):
        """
        获取用于答题的题目（只返回题目，不含答案）
        假设题目表名为: questions
        """
        try:
            cursor = self.connection.cursor(dictionary=True)
            query = "SELECT id, question_text FROM questions ORDER BY id"
            cursor.execute(query)
            result = cursor.fetchall()
            cursor.close()
            return result
        except Error as e:
            raise Exception(f"❌ 获取题目失败: {e}")

    def fetch_question(self):
        """
        获取题目和答案（用于学习模块）
        假设表字段: id, title, content（答案）
        """
        try:
            cursor = self.connection.cursor(dictionary=True)
            query = "SELECT question_id, title, content FROM question ORDER BY question_id"
            cursor.execute(query)
            result = cursor.fetchall()
            cursor.close()
            return result
        except Error as e:
            raise Exception(f"❌ 获取题目和答案失败: {e}")

from pymysql import Error  # 确保导入
    def save_response(self, name, hotel, department, answers):
        """
        保存用户答题答案（推荐：整份答卷存为一条 JSON 记录）
        answers: dict, {question_id: user_answer}
        """
        try:
            # 将整个答案字典转为 JSON 字符串
            answers_json = json.dumps(answers, ensure_ascii=False, indent=2)
    
            with self.connection.cursor() as cursor:
                insert_query = """
                INSERT INTO responses 
                (user_name, hotel, department, answers_json, submit_time) 
                VALUES (%s, %s, %s, %s, %s)
                """
                data = (name, hotel, department, answers_json, datetime.now())
                cursor.execute(insert_query, data)
    
            # ✅ 提交事务
            self.connection.commit()
            return True
    
        except Error as e:
            print(f"❌ 保存答案失败: {e}")
            self.connection.rollback()  # 回滚
            return False

    def get_completion_status(self):
        """
        获取答题完成情况统计
        返回 DataFrame: 姓名、酒店、部门、提交时间
        """
        try:
            query = """
            SELECT DISTINCT name, hotel, department, submit_time 
            FROM responses 
            ORDER BY submit_time DESC
            """
            df = pd.read_sql(query, self.connection)
            return df
        except Error as e:

            raise Exception(f"❌ 获取完成情况失败: {e}")









