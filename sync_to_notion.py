import os
import requests
import sys
from datetime import datetime

# 从 GitHub Action 的 Secrets 中获取
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
DATABASE_ID = os.getenv("NOTION_DATABASE_ID")

def push_to_notion(file_path):
    # 提取文件名（例如 2025-12-30）
    file_name = os.path.basename(file_path).replace(".md", "")
    
    # 【已更新】链接现在指向 ai-daily-content 仓库
    file_url = f"https://github.com/Qiangs1023/ai-daily-content/blob/main/{file_path}"

    headers = {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }
    
    # 构造 Notion 基础数据
    data = {
        "parent": {"database_id": DATABASE_ID},
        "properties": {
            "Name": {"title": [{"text": {"content": f"AI日报 - {file_name}"}}]},
            "Date": {"date": {"start": datetime.now().strftime("%Y-%m-%d")}},
            "Link": {"url": file_url}
        }
    }
    
    response = requests.post("https://api.notion.com/v1/pages", headers=headers, json=data)
    if response.status_code == 200:
        print(f"✅ 成功同步到 Notion: {file_name}")
    else:
        print(f"❌ 同步失败: {response.status_code}, {response.text}")

if __name__ == "__main__":
    files = sys.argv[1:]
    for f in files:
        # 只处理 daily/ 目录下的 .md 文件
        if f.startswith("daily/") and f.endswith(".md"):
            push_to_notion(f)
