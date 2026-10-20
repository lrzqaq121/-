import sys
from pathlib import Path

# 解决模块导入路径问题
CURRENT_DIR = Path(__file__).parent.resolve()
if str(CURRENT_DIR) not in sys.path:
    sys.path.append(str(CURRENT_DIR))

import streamlit as st
from its_agent import run_agent

# 页面配置
st.set_page_config(page_title="城市智能交通系统方案设计智能体", layout="wide")

st.title("🚦 城市智能交通系统方案设计智能体")
st.info("知识库：国标+工程案例 | 请先在左侧配置项目参数，生成效果更佳 | 禁止编造标准")

# ==========================================
# 侧边栏：参数配置与模板上传
# ==========================================
with st.sidebar:
    st.header("⚙️ 方案设计参数")

    project_name = st.text_input("项目名称", "某高校周边路网ITS改造")
    intersection_count = st.number_input("核心交叉口数量", min_value=1, max_value=10, value=3)
    road_length = st.number_input("涉及干道长度(km)", min_value=0.5, max_value=20.0, value=4.5)
    budget_level = st.selectbox("投资规模倾向", ["中等经济型", "高配旗舰型", "基础实用型"])

    st.markdown("---")
    st.subheader("📂 补充参考资料")
    uploaded_files = st.file_uploader("上传需求文档或特定国标 (.txt/.md)", accept_multiple_files=True,
                                      type=["txt", "md"])

    st.markdown("---")
    st.markdown(
        "💡 **使用提示**：\n1. 配置左侧参数\n2. 在下方对话框输入具体要求（如：重点设计信号控制和VMS）\n3. 等待Agent生成方案。")

# ==========================================
# 对话窗口与逻辑
# ==========================================
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# 渲染历史对话
for msg in st.session_state.chat_history:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# 输入框
user_input = st.chat_input("请输入需求，例如：以这3个交叉口为核心，帮我设计一个重点解决拥堵的ITS方案，列出预算")

if user_input:
    # 1. 显示用户提问
    st.session_state.chat_history.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # 2. 组装传给 Agent 的完整 Prompt
    context_prefix = (
        f"【项目背景信息】\n"
        f"- 项目名称：{project_name}\n"
        f"- 核心交叉口数量：{intersection_count} 个\n"
        f"- 涉及干道长度：{road_length} km\n"
        f"- 投资倾向：{budget_level}\n"
    )

    uploaded_text = ""
    if uploaded_files:
        uploaded_text += "\n【用户上传的参考资料】\n"
        for f in uploaded_files:
            try:
                content = f.read().decode("utf-8")
                uploaded_text += f"--- 文件名《{f.name}》---\n{content}\n"
            except Exception:
                st.error(f"无法读取文件 {f.name}")

    full_query = context_prefix + uploaded_text + "\n【用户具体需求】\n" + user_input

    # 3. 调用后端并显示结果
    with st.chat_message("assistant"):
        with st.spinner("正在解析参数、检索知识库并生成方案..."):
            answer = run_agent(full_query)
            st.markdown(answer)

    st.session_state.chat_history.append({"role": "assistant", "content": answer})