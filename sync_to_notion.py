import os
import requests
import sys
from datetime import datetime
import re

NOTION_TOKEN = os.getenv("NOTION_TOKEN")
DATABASE_ID = os.getenv("NOTION_DATABASE_ID")

def markdown_to_notion_blocks(md_content):
    """
    极简转换器：将 Markdown 行转换为 Notion 块对象
    """
    blocks = []
    lines = md_content.split('\n')
    
    for line in lines:
        line = line.strip()
        if not line: continue
        
        # 1. 处理标题 (###)
        if line.startswith('###'):
            blocks.append({
                "object": "block", "type": "heading_3",
                "heading_3": {"rich_text": [{"type": "text", "text": {"content": line.replace('###', '').strip()}}]}
            })
        elif line.startswith('##'):
            blocks.append({
                "object": "block", "type": "heading_2",
                "heading_2": {"rich_text": [{"type": "text", "text": {"content": line.replace('##', '').strip()}}]}
            })
        # 2. 处理代码块 (以 ``` 开头或包含在内)
        elif line.startswith('```'):
            continue # 简单处理，跳过代码块标记行
        # 3. 处理列表 (1. 或 - 或 *)
        elif re.match(r'^(\d+\.|-|\*)\s+', line):
            content = re.sub(r'^(\d+\.|-|\*)\s+', '', line)
            blocks.append({
                "object": "block", "type": "bulleted_list_item",
                "bulleted_list_item": {"rich_text": [{"type": "text", "text": {"content": content}}]}
            })
        # 4. 普通段落
        else:
            # 简单处理：保留加粗符号，Notion 有时能识别基础 Markdown 文本，
            # 或者你可以进一步用正则把 **text** 换成 Notion 的 annotations
            blocks.append({
                "object": "block", "type": "paragraph",
                "paragraph": {"rich_text": [{"type": "text", "text": {"content": line}}]}
            })
            
    return blocks[:100] # Notion 单次 API 调用最多支持 100 个块

def push_to_notion(file_path):
    file_name = os.path.basename(file_path).replace(".md", "")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        full_content = f.read()

    # 获取转换后的块
    notion_blocks = markdown_to_notion_blocks(full_content)
    
    file_url = f"[https://github.com/Qiangs1023/ai-daily-content/blob/main/](https://github.com/Qiangs1023/ai-daily-content/blob/main/){file_path}"
    headers = {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }
    
    data = {
        "parent": {"database_id": DATABASE_ID},
        "properties": {
            "Name": {"title": [{"text": {"content": f"{file_name} 数字旷野日报"}}]},
            "Date": {"date": {"start": datetime.now().strftime("%Y-%m-%d")}},
            "Link": {"url": file_url}
        },
        "children": notion_blocks # 直接把解析出来的所有块塞进去
    }
    
   response = requests.post("https://api.notion.com/v1/pages", headers=headers, json=data)
    if response.status_code == 200:
        print(f"✅ 全格式同步成功: {file_name}")
    else:
        print(f"❌ 失败: {response.text}")

if __name__ == "__main__":
    files = sys.argv[1:]
    for f in files:
        if f.startswith("daily/") and f.endswith(".md"):
            push_to_notion(f)
