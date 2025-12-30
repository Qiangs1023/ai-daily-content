import os
import requests
import sys
from datetime import datetime
import re

# 从 GitHub Action 的 Secrets 中获取
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
DATABASE_ID = os.getenv("NOTION_DATABASE_ID")

def markdown_to_notion_blocks(md_content):
    """
    将 Markdown 内容转换为 Notion 的 Block 格式
    支持：标题(##, ###)、无序列表(-, *, 1.)、普通段落
    """
    blocks = []
    # 过滤掉一些干扰字符，按行处理
    lines = md_content.split('\n')
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # 1. 处理三级标题 ###
        if line.startswith('###'):
            text = line.replace('###', '').strip()
            blocks.append({
                "object": "block",
                "type": "heading_3",
                "heading_3": {"rich_text": [{"type": "text", "text": {"content": text[:2000]}}]}
            })
        # 2. 处理二级标题 ##
        elif line.startswith('##'):
            text = line.replace('##', '').strip()
            blocks.append({
                "object": "block",
                "type": "heading_2",
                "heading_2": {"rich_text": [{"type": "text", "text": {"content": text[:2000]}}]}
            })
        # 3. 处理无序列表或有序列表 (- , * , 1. )
        elif re.match(r'^(\d+\.|-|\*)\s+', line):
            text = re.sub(r'^(\d+\.|-|\*)\s+', '', line)
            blocks.append({
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {"rich_text": [{"type": "text", "text": {"content": text[:2000]}}]}
            })
        # 4. 处理引用块 ( > )
        elif line.startswith('>'):
            text = line.replace('>', '').strip()
            blocks.append({
                "object": "block",
                "type": "quote",
                "quote": {"rich_text": [{"type": "text", "text": {"content": text[:2000]}}]}
            })
        # 5. 普通段落
        else:
            # 过滤掉代码块标识符 ```
            if line.startswith('```'):
                continue
            blocks.append({
                "object": "block",
                "type": "paragraph",
                "paragraph": {"rich_text": [{"type": "text", "text": {"content": line[:2000]}}]}
            })
            
    # Notion API 单次创建页面最多支持 100 个 blocks
    return blocks[:100]

def push_to_notion(file_path):
    print(f"正在处理文件: {file_path}")
    file_name = os.path.basename(file_path).replace(".md", "")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            full_content = f.read()
    except Exception as e:
        print(f"读取文件失败: {e}")
        return

    # 解析 Markdown 为 Notion 块
    notion_blocks = markdown_to_notion_blocks(full_content)
    
    # 构建你自己的仓库预览链接
    file_url = f"https://github.com/Qiangs1023/ai-daily-content/blob/main/{file_path}"

    headers = {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }
    
    data = {
        "parent": {"database_id": DATABASE_ID},
        "properties": {
            "Name": {"title": [{"text": {"content": f"KYinsight {file_name}"}}]},
            "Date": {"date": {"start": datetime.now().strftime("%Y-%m-%d")}},
            "Link": {"url": file_url}
        },
        "children": notion_blocks
    }
    
    # 修正后的 API 地址，确保没有 Markdown 污染
    api_url = "https://api.notion.com/v1/pages"
    
    response = requests.post(api_url, headers=headers, json=data)
    
    if response.status_code == 200:
        print(f"✅ 同步成功: {file_name}")
    else:
        print(f"❌ 同步失败: {response.status_code}")
        print(f"原因: {response.text}")
        sys.exit(1)

if __name__ == "__main__":
    added_files = sys.argv[1:]
    if not added_files:
        print("未检测到新增文件。")
    for f in added_files:
        if f.startswith("daily/") and f.endswith(".md"):
            push_to_notion(f)
