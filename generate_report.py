import os
import json
from datetime import datetime
from tavily import TavilyClient
import google.generativeai as genai

REPORT_TEMPLATE = """<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{company_name} 商談前リサーチレポート</title>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{ font-family: 'Helvetica Neue', Arial, sans-serif; background: #0a0a0f; color: #e0e0e0; min-height: 100vh; }}
  .header {{ background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); padding: 32px 40px; border-bottom: 1px solid #2a2a4a; }}
  .header-top {{ display: flex; justify-content: space-between; align-items: flex-start; }}
  .badge {{ background: #e94560; color: white; font-size: 11px; font-weight: 700; padding: 4px 10px; border-radius: 20px; letter-spacing: 1px; }}
  .company-name {{ font-size: 32px; font-weight: 800; color: #ffffff; margin: 12px 0 4px; }}
  .person-info {{ color: #7f8c9a; font-size: 15px; }}
  .meta {{ color: #4a5568; font-size: 12px; margin-top: 8px; }}
  .container {{ max-width: 1000px; margin: 0 auto; padding: 32px 24px; }}
  .section {{ background: #12121f; border: 1px solid #2a2a4a; border-radius: 12px; padding: 28px; margin-bottom: 20px; }}
  .section-title {{ font-size: 16px; font-weight: 700; margin-bottom: 16px; display: flex; align-items: center; gap: 10px; }}
  .section-title .icon {{ font-size: 20px; }}
  .section-body {{ color: #b0bec5; font-size: 14px; line-height: 1.9; }}
  .section-body p {{ margin-bottom: 10px; }}
  .section-body ul {{ padding-left: 20px; }}
  .section-body li {{ margin-bottom: 6px; }}
  .highlight {{ background: #1e1e35; border-left: 3px solid #e94560; padding: 14px 18px; border-radius: 0 8px 8px 0; margin: 16px 0; }}
  .highlight p {{ color: #e0e0e0; margin: 0; }}
  .tag {{ display: inline-block; background: #1e1e35; border: 1px solid #3a3a5a; color: #9b9bbc; font-size: 11px; padding: 3px 10px; border-radius: 20px; margin: 3px; }}
  .grid-2 {{ display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }}
  .stat-box {{ background: #1a1a2e; border-radius: 8px; padding: 16px; text-align: center; }}
  .stat-value {{ font-size: 22px; font-weight: 800; color: #e94560; }}
  .stat-label {{ font-size: 11px; color: #7f8c9a; margin-top: 4px; }}
  .footer {{ text-align: center; padding: 24px; color: #3a3a5a; font-size: 12px; border-top: 1px solid #1a1a2e; margin-top: 16px; }}
  .back-link {{ display: inline-block; margin: 24px 0 0; color: #e94560; text-decoration: none; font-size: 14px; }}
  .back-link:hover {{ text-decoration: underline; }}
  @media (max-width: 600px) {{ .grid-2 {{ grid-template-columns: 1fr; }} .header {{ padding: 24px; }} }}
</style>
</head>
<body>
<div class="header">
  <div class="header-top">
    <span class="badge">DNP PERSONA INSIGHT</span>
    <span class="meta">生成日時: {created_at}</span>
  </div>
  <div class="company-name">{company_name}</div>
  <div class="person-info">👤 {person_name}（{department}）</div>
</div>
<div class="container">
  <a href="../index.html" class="back-link">← レポート一覧に戻る</a>
  {sections_html}
  <div class="footer">DNPペルソナインサイト 商談前リサーチレポート｜自動生成</div>
</div>
</body>
</html>"""


def search_all(tavily: TavilyClient, company_name: str, person_name: str, department: str) -> dict:
    queries = {
        "financials": f"{company_name} 決算 売上 業績 2024 2025",
        "news": f"{company_name} 最新ニュース プレスリリース 2025",
        "products": f"{company_name} 新商品 新サービス 事業展開",
        "industry": f"{company_name} 業界 市場動向 競合",
        "sns": f"{company_name} X Twitter 話題 SNS",
        "person": f"{company_name} {department} {person_name}" if person_name else f"{company_name} {department}",
    }
    results = {}
    for key, query in queries.items():
        try:
            r = tavily.search(query, max_results=4, search_depth="advanced")
            results[key] = [{"title": x["title"], "content": x["content"][:500], "url": x["url"]} for x in r["results"]]
        except Exception as e:
            results[key] = []
            print(f"Search error ({key}): {e}")
    return results


def analyze_with_gemini(company_name: str, person_name: str, department: str, research: dict) -> dict:
    genai.configure(api_key=os.environ["GEMINI_API_KEY"])
    model = genai.GenerativeModel("gemini-2.0-flash")

    prompt = f"""
あなたはB2B営業コンサルタントです。以下のリサーチデータを分析して、DNPペルソナインサイトの商談前レポートをJSON形式で生成してください。

訪問企業: {company_name}
面談相手: {person_name}（{department}）

リサーチデータ:
{json.dumps(research, ensure_ascii=False, indent=2)}

以下のJSONスキーマで出力してください（マークダウンなし、JSONのみ）:
{{
  "company_summary": {{
    "description": "企業の事業内容・特徴（3〜4文）",
    "key_points": ["ポイント1", "ポイント2", "ポイント3"]
  }},
  "financials": {{
    "summary": "直近の業績・財務状況（3〜4文）",
    "highlights": ["注目点1", "注目点2", "注目点3"]
  }},
  "industry_trends": {{
    "summary": "業界トレンド・市場動向（3〜4文）",
    "trends": ["トレンド1", "トレンド2", "トレンド3"]
  }},
  "latest_news": {{
    "summary": "最新ニュース・新商品・SNS動向（3〜4文）",
    "items": ["ニュース1", "ニュース2", "ニュース3"]
  }},
  "person_profile": {{
    "summary": "面談相手・部署の役割と特徴（3〜4文）",
    "points": ["ポイント1", "ポイント2"]
  }},
  "proposal_angles": {{
    "summary": "DNPペルソナインサイトの提案切り口（3〜4文）",
    "angles": ["切り口1", "切り口2", "切り口3"],
    "key_message": "商談での一言キーメッセージ"
  }}
}}
"""
    response = model.generate_content(prompt)
    text = response.text.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    return json.loads(text.strip())


def render_section(icon: str, title: str, color: str, body_html: str) -> str:
    return f"""
<div class="section">
  <div class="section-title" style="color:{color}">
    <span class="icon">{icon}</span>{title}
  </div>
  <div class="section-body">{body_html}</div>
</div>"""


def build_html(company_name: str, person_name: str, department: str, data: dict) -> str:
    def bullets(items):
        return "<ul>" + "".join(f"<li>{i}</li>" for i in items) + "</ul>"

    sections = []

    c = data["company_summary"]
    sections.append(render_section("🏢", "企業概要", "#4fc3f7",
        f"<p>{c['description']}</p>{bullets(c['key_points'])}"))

    f = data["financials"]
    sections.append(render_section("📈", "財務・業績", "#81c784",
        f"<p>{f['summary']}</p>{bullets(f['highlights'])}"))

    t = data["industry_trends"]
    sections.append(render_section("🌊", "業界トレンド・競合動向", "#ffb74d",
        f"<p>{t['summary']}</p>{bullets(t['trends'])}"))

    n = data["latest_news"]
    sections.append(render_section("🆕", "最新ニュース・SNS動向", "#ce93d8",
        f"<p>{n['summary']}</p>{bullets(n['items'])}"))

    p = data["person_profile"]
    sections.append(render_section("👤", "面談相手・部署プロファイル", "#f48fb1",
        f"<p>{p['summary']}</p>{bullets(p['points'])}"))

    a = data["proposal_angles"]
    key_msg = a["key_message"]
    sections.append(render_section("💡", "DNPペルソナインサイト 提案切り口", "#e94560",
        f"<p>{a['summary']}</p>{bullets(a['angles'])}"
        f'<div class="highlight"><p>💬 キーメッセージ：<strong>{key_msg}</strong></p></div>'))

    return REPORT_TEMPLATE.format(
        company_name=company_name,
        person_name=person_name,
        department=department,
        created_at=datetime.now().strftime("%Y年%m月%d日 %H:%M"),
        sections_html="\n".join(sections),
    )


def update_index(company_name: str, person_name: str, department: str, filename: str):
    index_path = "reports/index.json"
    index = []
    if os.path.exists(index_path):
        with open(index_path, encoding="utf-8") as f:
            index = json.load(f)
    index.insert(0, {
        "company": company_name,
        "person": person_name,
        "department": department,
        "file": filename,
        "created_at": datetime.now().isoformat(),
    })
    with open(index_path, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    company_name = os.environ["COMPANY_NAME"]
    person_name = os.environ.get("PERSON_NAME", "")
    department = os.environ.get("DEPARTMENT", "")

    print(f"▶ リサーチ開始: {company_name} / {person_name} / {department}")

    tavily = TavilyClient(api_key=os.environ["TAVILY_API_KEY"])
    research = search_all(tavily, company_name, person_name, department)
    print("✓ Web検索完了")

    data = analyze_with_gemini(company_name, person_name, department, research)
    print("✓ Gemini分析完了")

    html = build_html(company_name, person_name, department, data)

    os.makedirs("reports", exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    slug = company_name.replace(" ", "_").replace("　", "_").replace("/", "-")
    filename = f"{slug}_{timestamp}.html"
    filepath = f"reports/{filename}"

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"✓ レポート保存: {filepath}")

    update_index(company_name, person_name, department, filename)
    print("✓ インデックス更新完了")
