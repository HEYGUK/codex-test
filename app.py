import base64
import io

import requests
import streamlit as st
from PIL import Image

# 1. 页面基本配置
st.set_page_config(page_title="BridgeAI | 留学生助手", page_icon="🎓", layout="wide")

# 2. 安全加载 API Key
# 部署后请在 Streamlit Cloud 的 Settings -> Secrets 中添加 GEMINI_API_KEY
if "GEMINI_API_KEY" in st.secrets:
    API_KEY = st.secrets["GEMINI_API_KEY"]
else:
    API_KEY = st.sidebar.text_input(
        "请输入 Gemini API Key",
        type="password",
        help="为了安全，建议在后台 Secrets 中配置",
    )

MODEL_NAME = "gemini-1.5-flash"

MODE_OPTIONS = [
    "学术论文 (润色/翻译)",
    "专业课讲义 (视觉拆解)",
    "生活社交 (地道表达)",
]

LANG_OPTIONS = [
    "英语",
    "日语",
    "韩语",
    "中文润色",
]

STYLE_OPTIONS = [
    "自然地道",
    "学术正式",
    "口语轻松",
]


# 3. 核心处理逻辑
def call_bridge_engine(text, img_b64=None, mode_label="学术论文 (润色/翻译)", target_lang="英语", style="自然地道"):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL_NAME}:generateContent?key={API_KEY}"

    mode_key = {
        "学术论文 (润色/翻译)": "学术",
        "专业课讲义 (视觉拆解)": "视觉拆解",
        "生活社交 (地道表达)": "生活社交",
    }.get(mode_label, "学术")

    lang_map = {
        "英语": "English",
        "日语": "Japanese",
        "韩语": "Korean",
        "中文润色": "Chinese",
    }
    target_lang_en = lang_map.get(target_lang, "English")

    # 结合 AI 与大气科学专业背景定制的系统指令
    system_prompt = (
        f"你是一位精通人工智能（AI）和大气科学的资深留学生导师，目前处于【{mode_key}】模式。\n"
        "任务要求：\n"
        "1. 学术模式：在保持学术准确性的前提下，优先使用母语者自然表达，必要时调整语序，避免逐字直译。\n"
        "2. 视觉拆解：逻辑清晰地解释图片中的图表或概念，分点说明关键变量与结论。\n"
        "3. 生活社交：输出地道表达，符合目标语言文化语感，避免生硬翻译。\n"
        "4. 专业术语要准确，必要时保留英文原词或给出对应术语。\n"
        f"输出语言：{target_lang_en}。表达风格：{style}。\n"
        "输出格式：只给出最终结果文本，不要附加分析过程。"
    )

    parts = [{"text": f"{system_prompt}\n\n待处理内容：\n{text}"}]
    if img_b64:
        parts.append({"inline_data": {"mime_type": "image/jpeg", "data": img_b64}})

    payload = {"contents": [{"parts": parts}]}

    try:
        response = requests.post(url, json=payload, timeout=60)
        response.raise_for_status()
        return response.json()["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e:
        return f"发生错误：{str(e)}\n(请检查 API Key 是否有效或网络是否通畅)"


# 4. 界面设计
st.title("BridgeAI 留学生助手")
st.markdown("---")

with st.sidebar:
    st.header("配置中心")
    mode = st.selectbox("选择场景", MODE_OPTIONS)
    target_lang = st.selectbox("目标语言", LANG_OPTIONS)
    style = st.selectbox("表达风格", STYLE_OPTIONS)
    st.write("---")
    st.info("提示：本版本已集成图片自动压缩技术，针对留学生校园网环境进行了优化。")

col_left, col_right = st.columns([1, 1])

with col_left:
    source_text = st.text_area(
        "在此输入需要处理的文字：",
        height=250,
        placeholder="粘贴论文段落、作业要求或想翻译的话...",
    )
    uploaded_file = st.file_uploader("上传图片/截图 (可选)：", type=["jpg", "jpeg", "png"])

if st.button("开始"):
    if not API_KEY:
        st.error("请在侧边栏输入 API Key 以启动 AI。")
    elif not source_text and not uploaded_file:
        st.error("请先输入文字或上传图片。")
    else:
        with st.spinner("AI 导师正在解析中..."):
            img_b64 = None
            if uploaded_file:
                # 自动压缩图片逻辑，减少上传带宽压力
                img = Image.open(uploaded_file).convert("RGB")
                img.thumbnail((1200, 1200))
                buf = io.BytesIO()
                img.save(buf, format="JPEG", quality=85)
                img_b64 = base64.b64encode(buf.getvalue()).decode()

            answer = call_bridge_engine(source_text, img_b64, mode, target_lang, style)

            with col_right:
                st.subheader("解析结果")
                st.success("处理完成")
                st.markdown(answer)
