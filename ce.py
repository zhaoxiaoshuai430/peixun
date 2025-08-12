import streamlit as st
import json
from datetime import datetime
import pandas as pd  # ⚠️ 注意：原代码使用了 pd，但未导入，这里补充

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
    page = st.sidebar.radio("导航", ["学习模块", "答题模块", "完成情况"])

    # ================== ✅ 答题模块 ==================
    if page == "答题模块":
        st.header("📝 答题模块")

        if 'user_info' not in st.session_state:
            with st.form("user_info_form"):
                st.subheader("请填写基本信息")
                name = st.text_input("姓名")
                hotel = st.selectbox(
                    "酒店",
                    ["中油花园酒店", "华智酒店", "华丰来旺达酒店",
                     "来旺达商旅酒店", "开封来旺达酒店", "新乡来旺达轻居酒店"]
                )
                # ✅ 修正：使用 selectbox 让用户选择部门
                department = st.selectbox(
                    "部门",
                    ["总经理办公室", "房务部", "餐饮部", "财务部",
                     "工保部", "行政人事部", "市场经营部", "人力资源部", "汉风物业"]
                )

                # ✅ 提交按钮必须在 form 内部
                submitted = st.form_submit_button("开始答题")

                if submitted:
                    if not name.strip() or not department:
                        st.error("请填写姓名和选择部门！")
                    else:
                        st.session_state.user_info = {
                            "name": name.strip(),
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
                st.markdown(f"**{i+1}. {q['question_text']}**")
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
    
        # ✅ 检查是否已通过管理员验证
        if 'admin_authenticated' not in st.session_state:
            st.session_state.admin_authenticated = False
    
        if not st.session_state.admin_authenticated:
            password = st.text_input("请输入管理员密码：", type="password")
            if st.button("验证"):
                if password == config["ADMIN_PASSWORD"]:
                    st.session_state.admin_authenticated = True  # ✅ 标记已验证
                    st.success("✅ 验证成功！")
                    st.rerun()  # 刷新页面以进入统计界面
                else:
                    if password:
                        st.error("❌ 密码错误！")
        else:
            # ✅ 已验证，显示统计内容
            try:
                df = quiz_system.get_completion_status()
    
                if df.empty:
                    st.info("📭 暂无用户提交记录")
                else:
                    df["submit_time"] = pd.to_datetime(df["submit_time"])
    
                    # 🔍 筛选控件
                    st.subheader("🔍 筛选条件")
                    col1, col2, col3 = st.columns(3)
    
                    with col1:
                        selected_hotel = st.selectbox(
                            "选择酒店",
                            options=["全部"] + sorted(df["hotel"].unique().tolist()),
                            key="selected_hotel"  # ✅ 添加 key 保持状态
                        )
                    with col2:
                        # 动态更新部门选项
                        if selected_hotel == "全部":
                            dept_options = df["department"].unique().tolist()
                        else:
                            dept_options = df[df["hotel"] == selected_hotel]["department"].unique().tolist()
                        selected_department = st.selectbox(
                            "选择部门",
                            options=["全部"] + sorted(dept_options),
                            key="selected_department"  # ✅ 添加 key 保持状态
                        )
                    with col3:
                        name_search = st.text_input(
                            "搜索姓名（支持模糊）",
                            value="",
                            key="name_search"  # ✅ 添加 key 保持状态
                        ).strip()
    
                    # 📅 时间范围筛选
                    st.markdown("📅 提交时间范围")
                    min_time = df["submit_time"].min().date()
                    max_time = df["submit_time"].max().date()
                    start_date, end_date = st.date_input(
                        "选择时间区间",
                        value=[min_time, max_time],
                        min_value=min_time,
                        max_value=max_time,
                        key="date_range"  # ✅ 添加 key 保持状态
                    )
    
                    # 🔎 应用筛选
                    filtered_df = df.copy()
    
                    if selected_hotel != "全部":
                        filtered_df = filtered_df[filtered_df["hotel"] == selected_hotel]
    
                    if selected_department != "全部":
                        filtered_df = filtered_df[filtered_df["department"] == selected_department]
    
                    if name_search:
                        filtered_df = filtered_df[
                            filtered_df["user_name"].str.contains(name_search, case=False, na=False)
                        ]
    
                    if start_date and end_date:
                        mask = (
                            (filtered_df["submit_time"].dt.date >= start_date) &
                            (filtered_df["submit_time"].dt.date <= end_date)
                        )
                        filtered_df = filtered_df[mask]
    
                    # 📊 显示结果
                    st.subheader(f"📋 查询结果（共 {len(filtered_df)} 人）")
    
                    if filtered_df.empty:
                        st.warning("⚠️ 当前筛选条件下无数据")
                    else:
                        # ✅ 显示数据表格
                        st.dataframe(
                            filtered_df,
                            column_config={
                                "submit_time": st.column_config.DatetimeColumn(
                                    "提交时间", format="YYYY-MM-DD HH:mm:ss"
                                )
                            },
                            hide_index=True,
                            use_container_width=True
                        )
    
                        # 📈 统计图表
                        st.subheader("📊 数据分析")
    
                        if selected_hotel == "全部":
                            hotel_stats = filtered_df["hotel"].value_counts()
                            st.bar_chart(hotel_stats, height=300)
                            st.caption("各酒店参与人数")
    
                        if selected_department == "全部":
                            dept_stats = filtered_df["department"].value_counts()
                            st.bar_chart(dept_stats, height=250)
                            st.caption("各部门参与人数")
    
                        # 📅 时间趋势图
                        filtered_df["date"] = filtered_df["submit_time"].dt.date
                        daily_stats = filtered_df.groupby("date").size()
                        st.line_chart(daily_stats)
                        st.caption("每日提交趋势")

                        st.write("🔍 原始数据预览：", filtered_df.head())
        
                        # 💾 导出功能
                        if not filtered_df.empty:
                            export_df = filtered_df.drop(columns=["date"], errors='ignore').copy()  # 使用 copy() 避免警告
    
                            for col in export_df.select_dtypes(include=['object']).columns:
                                export_df[col] = export_df[col].astype(str)
                        
                            csv = export_df.to_csv(index=False, encoding='utf-8-sig', lineterminator='\n')
    
                            # 💾 创建下载按钮
                            st.download_button(
                                label="📥 导出筛选结果为 CSV",
                                data=csv,
                                file_name=f"答题记录_筛选结果_{datetime.now().strftime('%Y%m%d')}.csv",
                                mime="text/csv",
                                key="download_csv"  # 避免重复键错误
                            )

            except Exception as e:
                st.error(f"❌ 获取统计信息失败：{str(e)}")
                st.exception(e)

            # ✅ 添加退出按钮（可选）
            if st.button("退出管理员模式"):
                del st.session_state.admin_authenticated
                st.rerun()


# 运行主程序
if __name__ == "__main__":
    main()




