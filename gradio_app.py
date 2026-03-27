import json
import os
import uuid

import gradio as gr
import httpx

API_BASE = "http://127.0.0.1:8000/api/v1"
TIMEOUT = 30.0
os.environ["NO_PROXY"] = "127.0.0.1,localhost"
os.environ["no_proxy"] = "127.0.0.1,localhost"
os.environ["GRADIO_ANALYTICS_ENABLED"] = "False"


def pretty(data):
    return json.dumps(data, ensure_ascii=False, indent=2)


def post_json(path, payload):
    url = API_BASE + path
    try:
        with httpx.Client(timeout=TIMEOUT, trust_env=False) as client:
            response = client.post(url, json=payload)
        body = response.json() if response.content else {}
        return pretty({"status_code": response.status_code, "data": body})
    except Exception as exc:
        return pretty({"status_code": 0, "error": str(exc), "url": url, "payload": payload})


def run_health():
    try:
        with httpx.Client(timeout=TIMEOUT, trust_env=False) as client:
            response = client.get("http://127.0.0.1:8000/health")
        body = response.json() if response.content else {}
        return pretty({"status_code": response.status_code, "data": body})
    except Exception as exc:
        return pretty({"status_code": 0, "error": str(exc)})


def do_chat(session_id, user_query):
    payload = {"session_id": session_id or uuid.uuid4().hex[:8], "user_query": user_query or ""}
    return post_json("/chat", payload)


def do_recommend(session_id, user_query):
    payload = {"session_id": session_id or uuid.uuid4().hex[:8], "user_query": user_query or ""}
    return post_json("/recommend", payload)


def parse_ids(raw):
    text = str(raw or "").replace(chr(10), ",")
    parts = [part.strip() for part in text.split(",")]
    return [int(part) for part in parts if part.isdigit()]


def do_compare(session_id, user_query, product_ids):
    payload = {
        "session_id": session_id or uuid.uuid4().hex[:8],
        "user_query": user_query or "",
        "product_ids": parse_ids(product_ids),
    }
    return post_json("/compare", payload)


with gr.Blocks(title="Smart Shopping Gradio") as demo:
    gr.Markdown("## 中文导购测试面板")
    gr.Markdown("这个页面直接调用本地 FastAPI 接口，用于聊天、推荐、对比联调。")
    with gr.Row():
        gr.Textbox(label="API Base", value=API_BASE, interactive=False)
        health_btn = gr.Button("检查后端健康")
    health_output = gr.Code(label="Health Response", language="json")
    health_btn.click(fn=run_health, outputs=health_output)

    with gr.Tab("聊天"):
        chat_session = gr.Textbox(label="Session ID", value="chat-demo")
        chat_query = gr.Textbox(label="用户问题", lines=4, value="我想买一台适合通勤和轻办公的轻薄本，预算5000左右")
        chat_btn = gr.Button("发起聊天")
        chat_output = gr.Code(label="Chat Response", language="json")
        chat_btn.click(fn=do_chat, inputs=[chat_session, chat_query], outputs=chat_output)

    with gr.Tab("推荐"):
        rec_session = gr.Textbox(label="Session ID", value="recommend-demo")
        rec_query = gr.Textbox(label="推荐需求", lines=4, value="推荐一款适合学生日常使用的手机，预算3000左右")
        rec_btn = gr.Button("获取推荐")
        rec_output = gr.Code(label="Recommend Response", language="json")
        rec_btn.click(fn=do_recommend, inputs=[rec_session, rec_query], outputs=rec_output)

    with gr.Tab("对比"):
        cmp_session = gr.Textbox(label="Session ID", value="compare-demo")
        cmp_query = gr.Textbox(label="对比问题", lines=3, value="帮我对比这两款商品")
        cmp_ids = gr.Textbox(label="Product IDs", value="1,2")
        cmp_btn = gr.Button("开始对比")
        cmp_output = gr.Code(label="Compare Response", language="json")
        cmp_btn.click(fn=do_compare, inputs=[cmp_session, cmp_query, cmp_ids], outputs=cmp_output)


if __name__ == "__main__":
    demo.launch(
        server_name="127.0.0.1",
        server_port=7860,
        show_error=True,
        debug=True,
        strict_cors=False,
    )
