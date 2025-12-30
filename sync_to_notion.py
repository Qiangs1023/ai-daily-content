import os
import requests
import sys
from datetime import datetime

NOTION_TOKEN = os.getenv("NOTION_TOKEN")
DATABASE_ID = os.getenv("NOTION_DATABASE_ID")

def extract_summary(file_path):
    """
    读取 Markdown 文件并提取摘要。
    逻辑：寻找包含'摘要'关键字的行，并抓取其后的段落。
    """
    summary = ""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            # 兼容多种格式：## 摘要、**摘要**、摘要：
            if "摘要" in content:
                # 按照“摘要”分割，取后面那部分
                parts = content.split("摘要", 1)
                # 取分割后的第一段（按双换行符判断）
                summary = parts[1].strip(": \n").split("\n\n")[0]
            else:
                # 如果没找到“摘要”字样，取文件开头前 200 字
                summary = content.strip()[:200] + "..."
    except Exception as e:
        print(f"读取文件失败: {e}")
    return summary

def push_to_notion(file_path):
    file_name = os.path.basename(file_path).replace(".md", "")
    # 获取摘要内容
    summary_text = extract_summary(file_path)
    
    file_url = f"https://github.com/Qiangs1023/ai-daily-content/blob/main/{file_path}"

    headers = {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }
    
    # 构造数据
    data = {
        "parent": {"database_id": DATABASE_ID},
        "properties": {
            "Name": {"title": [{"text": {"content": f"DailyNews - {file_name}"}}]},
            "Date": {"date": {"start": datetime.now().strftime("%Y-%m-%d")}},
            "Link": {"url": file_url}
        },
        # 【新增逻辑】将摘要写入 Notion 页面正文
        "children": [
            {
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [{"type": "text", "text": {"content": "🤖 AI 内容摘要"}}]
                }
            },
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [
                        {
                            "type": "text", 
                            "text": {"content": summary_text[:2000]} # Notion 限制单个块长度为 2000 字符
                        }
                    ]
                }
            }
        ]
    }
    
    response = requests.post("https://api.notion.com/v1/pages", headers=headers, json=data)
    if response.status_code == 200:
        print(f"✅ 成功同步并抓取摘要: {file_name}")
    else:
        print(f"❌ 同步失败: {response.status_code}, {response.text}")

if __name__ == "__main__":
    files = sys.argv[1:]
    for f in files:
        if f.startswith("daily/") and f.endswith(".md"):
            push_to_notion(f)
