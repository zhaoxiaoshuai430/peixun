import streamlit as st
from datetime import datetime
# 假设你有一个 QuizSystem 类，这里只展示调用方式
# 请确保你已实现 QuizSystem 并能通过 config 连接数据库
from quiz_system import QuizSystem  # 请根据你的实际模块名调整
from config import config  # 导入配置

def main():
    st.set_page_config(
        page_title="在线答题系统",
        page_icon="📝",
        layout="wide"
    )

    st.title("📘 酒店知识在线答题系统")

    # 初始化 quiz_system
    try:
        quiz_system = QuizSystem(
            host=config["DB_HOST"],
            user=config["DB_USER"],
            password=config["DB_PASSWORD"],
            database=config["DB_NAME"],
            port=config["DB_PORT"]
        )
    except Exception as e:
        st.error("⚠️ 数据库连接失败，请检查配置或联系管理员。")
        st.exception(e)
        return

    # 页面选择
    page = st.sidebar.radio("导航", ["答题模块", "学习模块", "完成情况"])

    # ================== ✅ 答题模块 ==================
    if page == "答题模块":
        st.header("📝 答题模块")

        if 'user_info' not in st.session_state:
            with st.form("user_info_form"):
                st.subheader("请填写基本信息")
                name = st.text_input("姓名")
                hotel = st.selectbox("酒店", ["中油花园酒店", "华智酒店", "华丰来旺达酒店", "来旺达商旅酒店","开封来旺达酒店","新乡来旺达轻居酒店"])  # 示例
                department = st.text_input("总经理办公室","房务部","餐饮部","财务部","工保部","行政人事部","市场经营部","人力资源部","汉风物业")

                submitted = st.form_submit_button("开始答题")
                if submitted:
                    if not name or not department:
                        st.error("请填写姓名和部门！")
                    else:
                        st.session_state.user_info = {
                            "name": name,
                            "hotel": hotel,
                            "department": department
                        }
                        st.rerun()

        else:
            user_info = st.session_state.user_info
            st.success(f"欢迎 {user_info['name']}，来自 {user_info['hotel']} {user_info['department']}！")

            questions = quiz_system.fetch_questions_for_quiz()  # 假设这个方法存在
            if not questions:
                st.warning("暂无题目，请联系管理员。")
                return

            answers = {}
            for i, q in enumerate(questions):
                st.markdown(f"**{i+1}. {q['title']}**")
                user_answer = st.text_area(f"你的答案", key=f"answer_{i}")
                answers[q['id']] = user_answer

            if st.button("提交答案", type="primary"):
                with st.spinner("正在保存..."):
                    try:
                        if quiz_system.save_response(
                            user_info['name'],
                            user_info['hotel'],
                            user_info['department'],
                            answers
                        ):
                            st.success("✅ 答题提交成功！感谢您的参与！")
                            del st.session_state.user_info
                        else:
                            st.error("❌ 提交失败，请重试。")
                    except Exception as e:
                        st.error(f"❌ 保存失败：{str(e)}")

    # ================== ✅ 学习模块 ==================
    elif page == "学习模块":
        st.header("📘 学习模块")
        st.markdown("点击问题即可查看答案，用于复习和学习。")

        try:
            questions = quiz_system.fetch_question()  # 获取所有题目和答案
            if not questions:
                st.info("暂无学习内容，请联系管理员添加题目和答案。")
            else:
                for i, q in enumerate(questions):
                    title = q['title']
                    answer = q.get('content', '暂无标准答案') or '暂无标准答案'

                    with st.expander(f"❓ {i+1}. {title}"):
                        st.markdown(f"✅ **答案**: {answer}")
        except Exception as e:
            st.error(f"❌ 加载学习内容失败：{str(e)}")

    # ================== ✅ 完成情况模块 ==================
    elif page == "完成情况":
        st.header("📊 答题完成情况统计")

        password = st.text_input("请输入管理员密码：", type="password")

        if st.button("验证"):
            if password == config["ADMIN_PASSWORD"]:
                st.success("✅ 验证成功！")
                try:
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
                except Exception as e:
                    st.error(f"❌ 获取统计信息失败：{str(e)}")
            elif password:
                st.error("❌ 密码错误！")

# 运行主程序
if __name__ == "__main__":
    main()

