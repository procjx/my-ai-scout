import os
import requests
import xml.etree.ElementTree as ET
from notion_client import Client
from datetime import datetime, timedelta

# --- 1. 配置 ---
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
DATABASE_ID = os.getenv("NOTION_DATABASE_ID")
# 如果没有 AI Key，可以先注释掉相关代码
LLM_API_KEY = os.getenv("LLM_API_KEY") 
LLM_BASE_URL = "https://api.deepseek.com" # 或 OpenAI 接口

notion = Client(auth=NOTION_TOKEN)

# --- 2. 获取 Arxiv 数据 ---
def fetch_arxiv_papers(query, max_results=3):
    url = f"http://export.arxiv.org/api/query?search_query=all:{query}&start=0&max_results={max_results}&sortBy=submittedDate&sortOrder=descending"
    response = requests.get(url)
    root = ET.fromstring(response.content)
    papers = []
    
    # 简单的 XML 解析
    ns = {'ns': 'http://www.w3.org/2005/Atom'}
    for entry in root.findall('ns:entry', ns):
        title = entry.find('ns:title', ns).text.replace('\n', ' ')
        link = entry.find('ns:id', ns).text
        summary = entry.find('ns:summary', ns).text.replace('\n', ' ')
        papers.append({"title": title, "url": link, "abstract": summary})
    return papers

# --- 3. AI 总结 (可选) ---
def summarize_with_ai(title, abstract):
    if not LLM_API_KEY:
        return "请手动查阅摘要"
    
    headers = {"Authorization": f"Bearer {LLM_API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": "deepseek-chat", # 或 gpt-3.5-turbo
        "messages": [
            {"role": "system", "content": "你是一个资深算法工程师，请用一句话中文总结这篇论文的核心创新点。"},
            {"role": "user", "content": f"标题: {title}\n摘要: {abstract}"}
        ]
    }
    try:
        res = requests.post(f"{LLM_BASE_URL}/chat/completions", json=payload, headers=headers)
        return res.json()['choices'][0]['message']['content']
    except:
        return "AI 总结失败，请查看链接"

# --- 4. 写入 Notion ---
def write_to_notion(title, url, summary, topic):
    notion.pages.create(
        parent={"database_id": DATABASE_ID},
        properties={
            "Name": {"title": [{"text": {"content": title}}]},
            "URL": {"url": url},
            "Summary": {"rich_text": [{"text": {"content": summary}}]},
            "Topic": {"select": {"name": topic}},
            "Source": {"select": {"name": "Arxiv"}},
            "Date": {"date": {"start": datetime.now().strftime("%Y-%m-%d")}}
        }
    )

if __name__ == "__main__":
    # 定义关注的关键词
    keywords = {
        "Recommendation System": "推荐系统",
        "Search Engine Retrieval": "搜索系统"
    }
    
    for query, topic_name in keywords.items():
        print(f"正在获取 {topic_name} 的最新内容...")
        papers = fetch_arxiv_papers(query)
        for paper in papers:
            # 简单的总结并存入
            brief = summarize_with_ai(paper['title'], paper['abstract'])
            write_to_notion(paper['title'], paper['url'], brief, topic_name)
