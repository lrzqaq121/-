# -*- coding: utf-8 -*-
import argparse, os, json, urllib.request, datetime, math

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SYS_PROMPT_PATH = os.path.join(ROOT, "prompts", "system_prompt.md")
KB_DIR = os.path.join(ROOT, "knowledge_base")
KEY_PATH = os.path.join(ROOT, "deepseek_key.txt")

# ---------- 知识库加载 ----------
def load_knowledge(max_chars=20000):
    if not os.path.isdir(KB_DIR):
        return "（知识库为空）"
    docs = []
    for base, _, fs in os.walk(KB_DIR):
        for f in sorted(fs):
            if f.lower().endswith((".md", ".txt")):
                p = os.path.join(base, f)
                try:
                    content = open(p, encoding="utf-8").read()
                    docs.append(f"=====《{f}》=====\n" + content)
                except Exception:
                    pass
    blob = "\n\n".join(docs)
    # 简单截断，防止超出DeepSeek的上下文限制
    return blob[:max_chars] + ("\n...[知识库过长已截断，请优先依据核心内容回答]" if len(blob) > max_chars else "")

# ---------- DeepSeek API 客户端 ----------
class DeepSeekClient:
    def __init__(self, api_key, model="deepseek-chat"):
        self.api_key, self.model = api_key, model

    def chat(self, messages, temperature=0.3):
        data = json.dumps({
            "model": self.model, "messages": messages,
            "temperature": temperature, "stream": False
        }).encode("utf-8")
        req = urllib.request.Request(
            "https://api.deepseek.com/chat/completions", data=data,
            headers={"Content-Type": "application/json",
                     "Authorization": "Bearer " + self.api_key})
        with urllib.request.urlopen(req, timeout=180) as r:
            resp = json.loads(r.read().decode("utf-8"))
        return resp["choices"][0]["message"]["content"]

def read_key():
    # 优先从环境变量读（部署到云端用这个）
    key = os.environ.get("DEEPSEEK_API_KEY", "").strip()
    if key:
        return key
    # 本地从文件读
    if os.path.exists(KEY_PATH):
        key = open(KEY_PATH, encoding="utf-8").read().strip()
        if key and not key.startswith("在此"):
            return key
    return None

# ---------- 离线 Mock 模式 (保底用，防止答辩断网) ----------
def mock_run():
    return """
# 高校周边示范路网 ITS方案(Mock演示)
## 一、 项目概况
交叉口3个，干道4.5km。
## 二、 子系统
包含 S1交通信息采集、S2智能信号控制、S3交通诱导...
## 三、 预算
总投资约 1200 万元。
"""

# ==========================================
# 核心区：给前端调用的 run_agent
# ==========================================
def run_agent(user_query):
    key = read_key()
    if not key:
        return "【系统提示】未找到 DeepSeek API Key。请检查 deepseek_key.txt 或环境变量。"

    # 1. 加载系统提示词和知识库
    try:
        with open(SYS_PROMPT_PATH, encoding="utf-8") as f:
            system_prompt = f.read()
    except FileNotFoundError:
        system_prompt = "你是一个资深的智能交通系统方案设计专家。请按模块输出方案。"

    knowledge = load_knowledge()

    # 2. 组装消息体
    # 这里的 user_query 是前端拼好的完整上下文（包含参数、上传文件、用户输入）
    messages = [
        {"role": "system", "content": system_prompt + "\n\n# 可用知识库参考资料：\n" + knowledge},
        {"role": "user", "content": user_query}
    ]

    # 3. 请求大模型
    client = DeepSeekClient(key)
    try:
        ans = client.chat(messages)
        return ans
    except Exception as e:
        return f"【请求失败】错误信息：{e}\n请检查 Key 是否有效、网络是否通畅。"


if __name__ == "__main__":
    # 保留控制台测试入口
    print("=== 智能交通方案设计 Agent (控制台测试) ===")
    while True:
        q = input("你> ")
        if q == "/exit": break
        print(run_agent(q))