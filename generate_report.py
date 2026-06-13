import os
import json
from datetime import datetime, timezone, timedelta
from tavily import TavilyClient
import google.generativeai as genai

JST = timezone(timedelta(hours=9))
def now_jst():
    return datetime.now(JST)

try:
    from weasyprint import HTML as WeasyprintHTML
    WEASYPRINT_AVAILABLE = True
except Exception:
    WEASYPRINT_AVAILABLE = False

# ============================================================
# HTML TEMPLATE
# ============================================================
REPORT_TEMPLATE = """<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{company_name} 商談前リサーチレポート</title>
<style>
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{ font-family:'Helvetica Neue',Arial,sans-serif; background:#0a0a0f; color:#e0e0e0; min-height:100vh; }}

  .header {{ background:linear-gradient(135deg,#1a1a2e 0%,#16213e 100%); padding:32px 40px; border-bottom:1px solid #2a2a4a; }}
  .header-top {{ display:flex; justify-content:space-between; align-items:flex-start; flex-wrap:wrap; gap:8px; }}
  .badge {{ background:#e94560; color:white; font-size:11px; font-weight:700; padding:4px 12px; border-radius:20px; letter-spacing:1px; }}
  .meta {{ color:#4a5568; font-size:12px; }}
  .company-name {{ font-size:32px; font-weight:800; color:#fff; margin:12px 0 4px; }}
  .person-info {{ color:#7f8c9a; font-size:15px; }}

  .container {{ max-width:1000px; margin:0 auto; padding:32px 24px; }}

  .back-link {{ display:inline-block; margin-bottom:24px; color:#e94560; text-decoration:none; font-size:14px; }}
  .back-link:hover {{ text-decoration:underline; }}

  /* Quick Stats */
  .quick-stats {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(150px,1fr)); gap:12px; margin-bottom:24px; }}
  .stat-box {{ background:#12121f; border:1px solid #2a2a4a; border-radius:10px; padding:16px; text-align:center; }}
  .stat-value {{ font-size:20px; font-weight:800; color:#e94560; }}
  .stat-label {{ font-size:11px; color:#7f8c9a; margin-top:4px; }}

  /* Sections */
  .section {{ background:#12121f; border:1px solid #2a2a4a; border-radius:12px; padding:28px; margin-bottom:16px; }}
  .section-title {{ font-size:16px; font-weight:700; margin-bottom:16px; display:flex; align-items:center; gap:10px; }}
  .section-body {{ color:#b0bec5; font-size:14px; line-height:1.9; }}
  .section-body p {{ margin-bottom:10px; }}
  .section-body ul {{ padding-left:20px; }}
  .section-body li {{ margin-bottom:6px; }}

  /* Highlight box */
  .highlight {{ background:#1e1e35; border-left:3px solid #e94560; padding:14px 18px; border-radius:0 8px 8px 0; margin:14px 0; }}
  .highlight p {{ color:#e0e0e0; margin:0; }}

  /* SNS voice */
  .voice-card {{ background:#1a1a2e; border:1px solid #2a2a4a; border-radius:8px; padding:14px 16px; margin:8px 0; }}
  .voice-card .voice-text {{ color:#d0d0d0; font-size:13px; line-height:1.7; font-style:italic; }}
  .voice-card .voice-meta {{ color:#4a5568; font-size:11px; margin-top:6px; }}

  /* Competitor table */
  .comp-table {{ width:100%; border-collapse:collapse; margin-top:12px; font-size:13px; }}
  .comp-table th {{ background:#1e1e35; color:#7f8c9a; padding:10px 12px; text-align:left; font-weight:600; border-bottom:1px solid #2a2a4a; }}
  .comp-table td {{ padding:10px 12px; border-bottom:1px solid #1a1a2e; color:#b0bec5; }}
  .comp-table tr:last-child td {{ border-bottom:none; }}
  .comp-table .target {{ color:#4fc3f7; font-weight:700; }}

  /* Checklist */
  .checklist li {{ list-style:none; padding-left:0; margin-bottom:8px; display:flex; align-items:flex-start; gap:8px; }}
  .checklist li::before {{ content:"☐"; color:#e94560; font-size:16px; flex-shrink:0; margin-top:-1px; }}

  /* QA */
  .qa-item {{ background:#1a1a2e; border-radius:8px; padding:14px 16px; margin:8px 0; }}
  .qa-q {{ color:#ffb74d; font-weight:700; font-size:13px; margin-bottom:6px; }}
  .qa-a {{ color:#b0bec5; font-size:13px; line-height:1.7; }}

  /* Icebreaker */
  .icebreaker-item {{ background:#1a1a2e; border-left:3px solid #81c784; border-radius:0 8px 8px 0; padding:12px 16px; margin:8px 0; font-size:13px; color:#d0d0d0; }}

  /* Tags */
  .tag {{ display:inline-block; background:#1e1e35; border:1px solid #3a3a5a; color:#9b9bbc; font-size:11px; padding:3px 10px; border-radius:20px; margin:3px; }}

  /* Confidence badges */
  .conf {{ display:inline-block; font-size:10px; font-weight:700; padding:2px 7px; border-radius:10px; margin-left:6px; vertical-align:middle; }}
  .conf-高 {{ background:#1b3a2a; color:#81c784; border:1px solid #2e6b45; }}
  .conf-中 {{ background:#3a2e10; color:#ffb74d; border:1px solid #7a5c10; }}
  .conf-低 {{ background:#3a1010; color:#e57373; border:1px solid #7a2020; }}
  .conf-低-wrap {{ background:#2b1010; border-left:3px solid #e57373; border-radius:0 6px 6px 0; padding:8px 12px; margin:4px 0; }}

  /* Source drawer */
  details.src {{ margin-top:14px; }}
  details.src summary {{ font-size:11px; color:#3a3a6a; cursor:pointer; user-select:none; list-style:none; display:inline-flex; align-items:center; gap:6px; padding:4px 10px; border:1px solid #2a2a4a; border-radius:20px; }}
  details.src summary::-webkit-details-marker {{ display:none; }}
  details.src summary::before {{ content:"📎"; }}
  details.src[open] summary {{ color:#7f8c9a; border-color:#3a3a6a; }}
  details.src .src-list {{ margin-top:10px; padding:10px 14px; background:#0a0a0f; border-radius:8px; border:1px solid #1a1a2e; }}
  details.src .src-list a {{ display:block; color:#4fc3f7; font-size:11px; text-decoration:none; padding:4px 0; border-bottom:1px solid #1a1a2e; word-break:break-all; }}
  details.src .src-list a:last-child {{ border-bottom:none; }}
  details.src .src-list a:hover {{ text-decoration:underline; }}
  details.src .src-title {{ font-size:10px; color:#4a5568; margin-bottom:2px; }}

  /* Key message */
  .key-message {{ background:linear-gradient(135deg,#1e0a15,#2a1020); border:1px solid #e94560; border-radius:10px; padding:20px 24px; margin-top:16px; }}
  .key-message-label {{ color:#e94560; font-size:11px; font-weight:700; letter-spacing:1px; margin-bottom:8px; }}
  .key-message-text {{ color:#fff; font-size:15px; font-weight:700; line-height:1.6; }}

  .footer {{ text-align:center; padding:24px; color:#3a3a5a; font-size:12px; border-top:1px solid #1a1a2e; margin-top:16px; }}

  @media print {{
    body {{ background:#fff; color:#000; }}
    .header {{ background:#1a1a2e !important; -webkit-print-color-adjust:exact; }}
    .section {{ border:1px solid #ddd; page-break-inside:avoid; }}
  }}
  /* Visual Summary */
  .vsummary {{ background:#12121f; border:1px solid #2a2a4a; border-radius:14px; padding:24px 28px; margin-bottom:20px; }}
  .vsummary-title {{ font-size:11px; font-weight:700; color:#4a5568; letter-spacing:1px; margin-bottom:16px; }}
  .key-facts {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(160px,1fr)); gap:8px; margin-bottom:16px; }}
  .key-fact {{ border-left:3px solid #2a2a4a; padding:10px 14px; }}
  .key-fact-label {{ font-size:10px; color:#4a5568; font-weight:600; margin-bottom:4px; }}
  .key-fact-value {{ font-size:14px; font-weight:700; color:#e0e0e0; line-height:1.4; }}

  @media(max-width:600px) {{
    .header {{ padding:24px; }}
    .quick-stats {{ grid-template-columns:1fr 1fr; }}
    .signal-row {{ grid-template-columns:1fr; }}
  }}
</style>
</head>
<body>
<div class="header">
  <div class="header-top">
    <span class="badge" style="background:{badge_color}">{service_name}</span>
    <span class="meta">生成日時: {created_at}　　🖨️ <a href="javascript:window.print()" style="color:#4a5568;text-decoration:none;">印刷</a></span>
  </div>
  <div class="company-name">{company_name}</div>
  <div class="person-info">👤 {person_display}</div>
</div>
<div class="container">
  <a href="../index.html" class="back-link">← レポート一覧に戻る</a>
  {visual_summary_html}
  {quick_stats_html}
  {sections_html}
  <div class="footer">DNPペルソナインサイト 商談前リサーチレポート｜自動生成　※情報は公開情報をもとにAIが分析したものです</div>
</div>
</body>
</html>"""


# ============================================================
# SEARCH
# ============================================================
PRESS_RELEASE_DOMAINS = [
    "prtimes.jp", "atpress.ne.jp", "valuepress.co.jp",
    "prwire.jp", "digitalpr.jp", "release.nikkei.co.jp",
]

SNS_REVIEW_DOMAINS = [
    "kakaku.com", "cosme.net", "@cosme.net", "amazon.co.jp",
    "tabelog.com", "rakuten.co.jp", "twitter.com", "x.com",
    "togetter.com", "note.com",
]

def search_all(tavily: TavilyClient, company_name: str, person_name: str, department: str) -> dict:
    # 鮮度重視（直近30日）の検索設定
    FRESH = {"days": 30}

    queries = [
        # key, query, extra_kwargs
        ("financials",         f"{company_name} 決算 売上 営業利益 業績",                          {}),
        ("ir",                 f"{company_name} IR 中期経営計画 成長戦略",                         {}),
        ("news",               f"{company_name} 新発表 新戦略 リリース",                           {**FRESH, "include_domains": PRESS_RELEASE_DOMAINS}),
        ("news_general",       f"{company_name} ニュース 発表",                                   FRESH),
        ("products",           f"{company_name} 新商品 新サービス 発売",                           FRESH),
        ("products_ranking",   f"{company_name} 商品 売上ランキング カテゴリ シェア",               {}),
        ("industry",           f"{company_name} 業界 市場規模 市場動向 シェア",                    {}),
        ("competitors",        f"{company_name} 競合他社 比較 シェア",                             {}),
        ("competitor_products",f"{company_name} 競合 商品比較 差別化",                             {}),
        ("sns_consumer",       f"{company_name} 口コミ 評判 レビュー 本音",                        {**FRESH, "include_domains": SNS_REVIEW_DOMAINS}),
        ("sns_trend",          f"{company_name} 話題 キャンペーン トレンド バズ",                  FRESH),
        ("person",             f"{company_name} {person_name} {department}" if person_name else f"{company_name} {department} 責任者", {}),
        ("person_sns",         f"{person_name} {company_name} インタビュー 登壇 発言" if person_name else "", {}),
        ("initiatives",        f"{company_name} DX マーケティング 取り組み",                       FRESH),
        ("issues",             f"{company_name} 課題 リスク 懸念 弱点",                            {}),
    ]

    results = {}
    for key, query, kwargs in queries:
        if not query.strip():
            results[key] = []
            continue
        try:
            r = tavily.search(query, max_results=5, search_depth="advanced", **kwargs)
            results[key] = [
                {"title": x["title"], "content": x["content"][:600], "url": x["url"]}
                for x in r["results"]
            ]
            print(f"  ✓ {key}: {len(results[key])}件")
        except Exception as e:
            # include_domains で結果0件の場合はdomains指定なしで再試行
            if "include_domains" in kwargs:
                try:
                    fallback_kwargs = {k: v for k, v in kwargs.items() if k != "include_domains"}
                    r = tavily.search(query, max_results=5, search_depth="advanced", **fallback_kwargs)
                    results[key] = [
                        {"title": x["title"], "content": x["content"][:600], "url": x["url"]}
                        for x in r["results"]
                    ]
                    print(f"  ✓ {key} (fallback): {len(results[key])}件")
                except Exception as e2:
                    results[key] = []
                    print(f"  Search warn ({key}): {e2}")
            else:
                results[key] = []
                print(f"  Search warn ({key}): {e}")

    # news + news_general をマージしてnewsに統合
    seen = set()
    merged = []
    for item in results.get("news", []) + results.get("news_general", []):
        if item["url"] not in seen:
            seen.add(item["url"])
            merged.append(item)
    results["news"] = merged[:8]
    del results["news_general"]

    return results


# ============================================================
# SERVICE DEFINITIONS
# ============================================================
SERVICES = {
    "persona_insight": {
        "name": "DNPペルソナインサイト",
        "badge_color": "#e94560",
        "description": """日本の統計データとDNP独自データを学習したAIが、仮想生活者（ペルソナ）との対話形式で
「生活者が上手く言葉にできない本音・インサイト」を言語化するマーケティングリサーチプラットフォーム。
活用場面：新商品開発・パッケージ評価・ターゲット深層心理把握・デジタルマーケティング最適化""",
        "proposal_context": "消費者インサイトの言語化・ペルソナ対話による深層心理把握・新商品コンセプト開発・ターゲット理解の効率化",
    },
    "human_research": {
        "name": "DNPヒューマンリサーチ®",
        "badge_color": "#1565c0",
        "description": """生体反応（アイトラッカー・接触力センサー）×発話×ヒト特性から、消費者の無意識・無自覚な購買・使用行動を
科学的に計測・分析するパッケージ総合評価サービス。
活用場面：パッケージデザイン評価・POP効果検証・開封性・使用性改善・医薬品包材検証""",
        "proposal_context": "パッケージ・店頭での無意識行動分析・生体反応による客観的評価・開封性・視認性改善・ユーザビリティ検証",
    },
}


# ============================================================
# GEMINI ANALYSIS
# ============================================================
def analyze_with_gemini(company_name: str, person_name: str, department: str, research: dict, service_key: str = "persona_insight") -> dict:
    service = SERVICES.get(service_key, SERVICES["persona_insight"])
    genai.configure(api_key=os.environ["GEMINI_API_KEY"])
    model = genai.GenerativeModel("gemini-2.5-flash")

    prompt = f"""
あなたは大日本印刷（DNP）の凄腕B2B営業担当です。
「この会社のことを業界の誰よりも深く理解している」という印象を与えられるレベルの商談前レポートを作成してください。

【重要】深さより鮮度を優先してください。
- 直近1ヶ月以内の新商品・ニュースリリース・キャンペーン情報を必ず含める
- SNSの声は「最近話題になっていること」を具体的に記述する
- 古い情報より新しい情報を優先する

【今回提案するDNPサービス: {service["name"]}】
{service["description"]}
提案の核心: {service["proposal_context"]}

{service["name"]}の商談前レポートを作成してください。

訪問企業: {company_name}
面談相手: {person_name or "未定"}（{department or "未定"}）

【リサーチデータ】
{json.dumps(research, ensure_ascii=False, indent=2)[:15000]}

【信頼度ルール】
各事実・数値には confidence フィールドを付けてください:
- "高": 検索結果に明確な根拠あり（決算資料・公式IR・報道等で確認済み）
- "中": 複数ソースから推測できるが直接的な数値根拠なし
- "低": 推測・類推・情報が古い可能性あり → 要確認

以下のJSONスキーマで出力してください（マークダウンなし、JSONのみ、日本語で）:
{{
  "quick_stats": {{
    "industry": "業界・セクター（例: 食品メーカー）",
    "founded": "設立年（わかれば）",
    "employees": "従業員数（わかれば）",
    "revenue": "直近売上高（わかれば）",
    "market_position": "市場ポジション（例: 業界3位）",
    "confidence": "高/中/低"
  }},
  "company_summary": {{
    "description": "企業の事業内容・特徴・経営ビジョン（4〜5文。具体的な数字・ブランド名を含める）",
    "key_points": ["具体的なポイント1（数字含む）", "ポイント2", "ポイント3", "ポイント4"]
  }},
  "financials": {{
    "summary": "直近の業績・財務状況（4〜5文。具体的な数字を含める）",
    "highlights": [
      {{"text": "数字を含む注目点1", "confidence": "高/中/低"}},
      {{"text": "注目点2", "confidence": "高/中/低"}},
      {{"text": "注目点3", "confidence": "高/中/低"}},
      {{"text": "注目点4", "confidence": "高/中/低"}}
    ],
    "concerns": ["課題・懸念点1", "課題2"]
  }},
  "industry_trends": {{
    "summary": "業界トレンド・市場動向（4〜5文）",
    "trends": ["トレンド1（具体的に）", "トレンド2", "トレンド3", "トレンド4"],
    "market_size": "市場規模・成長率（わかれば）",
    "market_size_confidence": "高/中/低"
  }},
  "competitors": {{
    "summary": "競合状況の概要（3〜4文）",
    "table": [
      {{"company": "企業名または{company_name}（自社）", "is_target": true, "strength": "強み", "weakness": "弱み", "share": "シェア（わかれば）", "confidence": "高/中/低"}},
      {{"company": "競合A", "is_target": false, "strength": "強み", "weakness": "弱み", "share": "シェア（わかれば）", "confidence": "高/中/低"}},
      {{"company": "競合B", "is_target": false, "strength": "強み", "weakness": "弱み", "share": "シェア（わかれば）", "confidence": "高/中/低"}}
    ]
  }},
  "products": {{
    "summary": "主力製品・サービスと市場での位置づけ（3〜4文）",
    "categories": [
      {{"name": "カテゴリ名", "products": "代表製品名", "position": "市場での位置・ランキング", "confidence": "高/中/低"}},
      {{"name": "カテゴリ名2", "products": "代表製品名", "position": "市場での位置・ランキング", "confidence": "高/中/低"}}
    ]
  }},
  "latest_news": {{
    "summary": "最新ニュース・新商品・取り組みの概要（3〜4文）",
    "items": [
      {{"text": "ニュース1（具体的に）", "confidence": "高/中/低"}},
      {{"text": "ニュース2", "confidence": "高/中/低"}},
      {{"text": "ニュース3", "confidence": "高/中/低"}},
      {{"text": "ニュース4", "confidence": "高/中/低"}}
    ]
  }},
  "sns_voice": {{
    "summary": "消費者・市場からのSNS・口コミの全体感（3〜4文）",
    "positives": ["ポジティブな声1（具体的に）", "ポジティブ2", "ポジティブ3"],
    "negatives": ["ネガティブ・課題の声1（具体的に）", "ネガティブ2"],
    "opportunities": ["SNS動向から見えるビジネス機会1", "機会2"]
  }},
  "person_profile": {{
    "summary": "面談相手・部署の役割と特徴（3〜4文）",
    "likely_interests": ["関心事・KPIと思われる項目1", "関心事2", "関心事3"],
    "communication_tips": ["コミュニケーション上のポイント1", "ポイント2"]
  }},
  "icebreakers": [
    "アイスブレイクに使える話題1（最近のニュース・製品から具体的に）",
    "アイスブレイク話題2",
    "アイスブレイク話題3"
  ],
  "anticipated_qa": [
    {{"q": "想定される質問・懸念1", "a": "推奨回答・切り返し"}},
    {{"q": "想定される質問・懸念2", "a": "推奨回答・切り返し"}},
    {{"q": "想定される質問・懸念3", "a": "推奨回答・切り返し"}}
  ],
  "checklist": [
    "訪問前に確認すべきこと1",
    "確認事項2",
    "確認事項3",
    "持参すべき資料・準備物",
    "確認事項5"
  ]
}}
"""

    response = model.generate_content(prompt)
    text = response.text.strip()
    if "```" in text:
        parts = text.split("```")
        for part in parts:
            if part.startswith("json"):
                text = part[4:].strip()
                break
            elif "{" in part:
                text = part.strip()
                break
    return json.loads(text.strip())


# ============================================================
# HTML RENDERING
# ============================================================
def render_sources_drawer(sources: list) -> str:
    if not sources:
        return ""
    links = "".join(
        f'<a href="{s["url"]}" target="_blank"><span class="src-title">{s.get("title","")}</span></a>'
        for s in sources if s.get("url")
    )
    return f'<details class="src"><summary>根拠を見る（{len(sources)}件）</summary><div class="src-list">{links}</div></details>'


def render_section(icon: str, title: str, color: str, body_html: str, sources: list = None) -> str:
    drawer = render_sources_drawer(sources) if sources else ""
    return f"""
<div class="section">
  <div class="section-title" style="color:{color}">
    <span style="font-size:20px">{icon}</span>{title}
  </div>
  <div class="section-body">{body_html}</div>
  {drawer}
</div>"""


def conf_badge(level: str) -> str:
    level = level or "中"
    return f'<span class="conf conf-{level}">{level}</span>'


def bullets(items: list) -> str:
    if not items:
        return ""
    parts = []
    for i in items:
        if isinstance(i, dict):
            text = i.get("text", "")
            conf = i.get("confidence", "")
            wrap_class = ' class="conf-低-wrap"' if conf == "低" else ""
            badge = conf_badge(conf) if conf else ""
            parts.append(f"<li{wrap_class}>{text}{badge}</li>")
        else:
            parts.append(f"<li>{i}</li>")
    return "<ul>" + "".join(parts) + "</ul>"


def build_visual_summary(data: dict) -> str:
    qs = data.get("quick_stats", {})
    fin = data.get("financials", {})

    # キーファクト（業界・売上・ポジション・従業員）
    highlights = fin.get("highlights", [])
    fin_highlight = ""
    if highlights:
        h = highlights[0]
        fin_highlight = h.get("text", "") if isinstance(h, dict) else str(h)

    facts = [
        ("業界", qs.get("industry", "")),
        ("売上高", qs.get("revenue", "")),
        ("市場ポジション", qs.get("market_position", "")),
        ("従業員数", qs.get("employees", "")),
        ("業績ハイライト", fin_highlight),
    ]
    facts_html = "".join(
        f'<div class="key-fact"><div class="key-fact-label">{l}</div><div class="key-fact-value">{v}</div></div>'
        for l, v in facts if v and v != "—"
    )

    return f"""
<div class="vsummary">
  <div class="vsummary-title">📋 概要サマリー</div>
  <div class="key-facts">{facts_html}</div>
</div>"""


def build_quick_stats(data: dict) -> str:
    qs = data.get("quick_stats", {})
    conf = qs.get("confidence", "")
    badge = conf_badge(conf) if conf else ""
    stats = [
        (qs.get("industry", "—"), "業界"),
        (qs.get("revenue", "—"), "売上高"),
        (qs.get("employees", "—"), "従業員数"),
        (qs.get("market_position", "—"), "市場ポジション"),
    ]
    boxes = "".join(f'<div class="stat-box"><div class="stat-value">{v}</div><div class="stat-label">{l}</div></div>' for v, l in stats)
    conf_note = f'<div style="text-align:right;margin-bottom:8px;font-size:11px;color:#4a5568">基本情報の信頼度: {badge}</div>' if badge else ""
    return f'{conf_note}<div class="quick-stats">{boxes}</div>'


def build_sources_html(research: dict) -> str:
    category_labels = {
        "financials": "財務・業績",
        "ir": "IR・中期経営計画",
        "news": "最新ニュース",
        "products": "製品・サービス",
        "industry": "業界・市場動向",
        "competitors": "競合分析",
        "competitor_products": "競合製品比較",
        "sns_consumer": "SNS・消費者の声",
        "sns_trend": "SNSトレンド",
        "person": "面談相手・部署",
        "person_sns": "面談相手SNS・発言",
        "initiatives": "DX・マーケティング取り組み",
        "issues": "課題・リスク",
    }
    seen_urls = set()
    items_html = ""
    for key, label in category_labels.items():
        results = research.get(key, [])
        links = []
        for r in results:
            url = r.get("url", "")
            title = r.get("title", url)
            if url and url not in seen_urls:
                seen_urls.add(url)
                links.append(f'<li><a href="{url}" target="_blank" style="color:#4fc3f7;font-size:12px;word-break:break-all">{title}</a></li>')
        if links:
            items_html += f'<div style="margin-bottom:14px"><p style="color:#7f8c9a;font-size:11px;font-weight:700;letter-spacing:0.5px;margin-bottom:6px">{label}</p><ul style="padding-left:16px">{"".join(links)}</ul></div>'
    if not items_html:
        return ""
    return f"""
<div class="section" style="margin-top:16px">
  <div class="section-title" style="color:#4a5568">
    <span style="font-size:20px">🔗</span>参考URL・エビデンス
  </div>
  <div class="section-body">{items_html}</div>
</div>"""


def build_html(company_name: str, person_name: str, department: str, data: dict, service_key: str = "persona_insight", research: dict = None) -> str:
    service = SERVICES.get(service_key, SERVICES["persona_insight"])
    sections = []
    r = research or {}

    def src(*keys):
        seen, out = set(), []
        for k in keys:
            for item in r.get(k, []):
                if item.get("url") and item["url"] not in seen:
                    seen.add(item["url"])
                    out.append(item)
        return out

    # 1. 企業概要
    c = data.get("company_summary", {})
    sections.append(render_section("🏢", "企業概要", "#4fc3f7",
        f"<p>{c.get('description','')}</p>{bullets(c.get('key_points',[]))}",
        src("financials", "ir")))

    # 2. 財務・業績
    f = data.get("financials", {})
    concerns_html = ""
    if f.get("concerns"):
        concerns_html = f'<div class="highlight"><p>⚠️ 課題・懸念点：</p>{bullets(f["concerns"])}</div>'
    sections.append(render_section("📈", "財務・業績", "#81c784",
        f"<p>{f.get('summary','')}</p>{bullets(f.get('highlights',[]))}{concerns_html}",
        src("financials", "ir")))

    # 3. 業界トレンド
    t = data.get("industry_trends", {})
    market_badge = conf_badge(t.get("market_size_confidence", "")) if t.get("market_size_confidence") else ""
    market_html = f'<div class="highlight"><p>市場規模：{t["market_size"]}{market_badge}</p></div>' if t.get("market_size") else ""
    sections.append(render_section("🌊", "業界トレンド・市場動向", "#ffb74d",
        f"<p>{t.get('summary','')}</p>{bullets(t.get('trends',[]))}{market_html}",
        src("industry")))

    # 4. 競合分析
    comp = data.get("competitors", {})
    table_rows = ""
    for row in comp.get("table", []):
        cls = ' class="target"' if row.get("is_target") else ""
        badge = conf_badge(row.get("confidence", "")) if row.get("confidence") else ""
        table_rows += f"<tr><td{cls}>{row.get('company','')}{badge}</td><td>{row.get('share','—')}</td><td style='color:#81c784'>{row.get('strength','')}</td><td style='color:#e57373'>{row.get('weakness','')}</td></tr>"
    table_html = ""
    if table_rows:
        table_html = f"""<table class="comp-table">
<tr><th>企業名</th><th>シェア</th><th>強み</th><th>弱み</th></tr>
{table_rows}</table>"""
    sections.append(render_section("⚔️", "競合分析", "#ce93d8",
        f"<p>{comp.get('summary','')}</p>{table_html}",
        src("competitors", "competitor_products")))

    # 5. 主力製品・カテゴリ
    prod = data.get("products", {})
    cat_html = ""
    for cat in prod.get("categories", []):
        badge = conf_badge(cat.get("confidence", "")) if cat.get("confidence") else ""
        cat_html += f'<div class="voice-card"><strong style="color:#4fc3f7">{cat.get("name","")}</strong>　{cat.get("products","")}　<span style="color:#7f8c9a;font-size:12px">{cat.get("position","")}</span>{badge}</div>'
    sections.append(render_section("📦", "主力製品・カテゴリ別ポジション", "#80cbc4",
        f"<p>{prod.get('summary','')}</p>{cat_html}",
        src("products")))

    # 6. 最新ニュース
    n = data.get("latest_news", {})
    sections.append(render_section("🆕", "最新ニュース・新商品・取り組み", "#ffcc02",
        f"<p>{n.get('summary','')}</p>{bullets(n.get('items',[]))}",
        src("news", "initiatives")))

    # 7. SNS・消費者の声
    sns = data.get("sns_voice", {})
    pos_html = "".join(f'<div class="voice-card"><div class="voice-text">「{v}」</div><div class="voice-meta">ポジティブな声</div></div>' for v in sns.get("positives", []))
    neg_html = "".join(f'<div class="voice-card"><div class="voice-text">「{v}」</div><div class="voice-meta" style="color:#e57373">課題・ネガティブな声</div></div>' for v in sns.get("negatives", []))
    opp_html = bullets(sns.get("opportunities", []))
    sections.append(render_section("📱", "SNS・消費者の声", "#f48fb1",
        f"<p>{sns.get('summary','')}</p>{pos_html}{neg_html}"
        f"<p style='margin-top:14px;color:#81c784;font-weight:700'>💡 ビジネス機会</p>{opp_html}",
        src("sns_consumer", "sns_trend")))

    # 8. 面談相手プロファイル
    p = data.get("person_profile", {})
    tips_html = "".join(f'<div class="icebreaker-item" style="border-left-color:#4fc3f7">{t}</div>' for t in p.get("communication_tips", []))
    sections.append(render_section("👤", "面談相手・部署プロファイル", "#f48fb1",
        f"<p>{p.get('summary','')}</p>"
        f"<p style='margin-top:12px;font-weight:700;color:#7f8c9a'>関心事・KPI</p>{bullets(p.get('likely_interests',[]))}"
        f"<p style='margin-top:12px;font-weight:700;color:#7f8c9a'>コミュニケーションのポイント</p>{tips_html}",
        src("person", "person_sns")))

    # 9. アイスブレイク話題
    ib_html = "".join(f'<div class="icebreaker-item">💬 {i}</div>' for i in data.get("icebreakers", []))
    sections.append(render_section("☕", "アイスブレイク話題", "#a5d6a7", ib_html,
        src("news", "sns_trend")))

    # 10. 想定Q&A
    qa_html = "".join(f'<div class="qa-item"><div class="qa-q">Q: {qa.get("q","")}</div><div class="qa-a">A: {qa.get("a","")}</div></div>' for qa in data.get("anticipated_qa", []))
    sections.append(render_section("❓", "想定Q&A・切り返し", "#ffb74d", qa_html,
        src("issues", "competitors")))

    # 11. 訪問前チェックリスト
    cl_items = data.get("checklist", [])
    cl_html = f'<ul class="checklist">{"".join(f"<li>{i}</li>" for i in cl_items)}</ul>'
    sections.append(render_section("✅", "訪問前チェックリスト", "#81c784", cl_html))

    person_display = f"{person_name}（{department}）" if person_name else department or "担当者未定"
    badge_color = service.get("badge_color", "#e94560")

    return REPORT_TEMPLATE.format(
        company_name=company_name,
        person_display=person_display,
        service_name=service["name"],
        badge_color=badge_color,
        created_at=now_jst().strftime("%Y年%m月%d日 %H:%M"),
        visual_summary_html=build_visual_summary(data),
        quick_stats_html=build_quick_stats(data),
        sections_html="\n".join(sections),
    )


# ============================================================
# PDF GENERATION
# ============================================================
PDF_CSS = """
@page { margin: 15mm 12mm; size: A4; }
* { margin:0; padding:0; box-sizing:border-box; }
body { font-family: 'Helvetica Neue', Arial, sans-serif; background:#fff; color:#1a1a2e; font-size:11px; line-height:1.6; }
.header { background:#1a1a2e; color:#fff; padding:20px 24px; margin-bottom:16px; }
.header .badge { background:#e94560; color:#fff; font-size:9px; font-weight:700; padding:2px 8px; border-radius:10px; display:inline-block; margin-bottom:6px; }
.header .company-name { font-size:22px; font-weight:800; color:#fff; margin:6px 0 2px; }
.header .person-info { color:#aaa; font-size:10px; }
.container { padding:0 12px; }
.vsummary { background:#f8f9fa; border:1px solid #ddd; border-radius:8px; padding:16px; margin-bottom:14px; }
.vsummary-title { font-size:9px; font-weight:700; color:#666; letter-spacing:1px; margin-bottom:12px; }
.signal-row { display:flex; gap:10px; margin-bottom:12px; }
.signal-box { flex:1; background:#fff; border:1px solid #ddd; border-radius:6px; padding:10px; text-align:center; }
.signal-light { font-size:20px; display:block; margin-bottom:4px; }
.signal-label { font-size:9px; color:#444; font-weight:700; }
.signal-note { font-size:8px; color:#888; margin-top:2px; }
.key-facts { display:flex; flex-wrap:wrap; gap:8px; margin-bottom:12px; }
.key-fact { background:#fff; border:1px solid #ddd; border-radius:6px; padding:8px 12px; flex:1; min-width:120px; }
.key-fact-label { font-size:8px; color:#888; font-weight:700; margin-bottom:2px; }
.key-fact-value { font-size:12px; font-weight:800; color:#1a1a2e; }
.opening-box { background:#f3eeff; border:1px solid #c9a0e8; border-radius:6px; padding:10px 14px; }
.opening-label { font-size:8px; color:#7b4fa6; font-weight:700; margin-bottom:4px; }
.opening-text { font-size:11px; font-weight:600; color:#1a1a2e; }
.opening-caution { font-size:8px; color:#999; margin-top:4px; }
.quick-stats { display:flex; gap:8px; margin-bottom:14px; flex-wrap:wrap; }
.stat-box { background:#f8f9fa; border:1px solid #ddd; border-radius:6px; padding:10px; text-align:center; flex:1; min-width:100px; }
.stat-value { font-size:13px; font-weight:800; color:#e94560; }
.stat-label { font-size:8px; color:#666; margin-top:2px; }
.section { background:#fff; border:1px solid #e0e0e0; border-radius:8px; padding:14px 16px; margin-bottom:10px; page-break-inside:avoid; }
.section-title { font-size:12px; font-weight:700; margin-bottom:10px; display:flex; align-items:center; gap:6px; }
.section-body { color:#333; font-size:10px; line-height:1.7; }
.section-body p { margin-bottom:6px; }
.section-body ul { padding-left:16px; }
.section-body li { margin-bottom:4px; }
.highlight { background:#f8f9fa; border-left:3px solid #e94560; padding:8px 12px; border-radius:0 4px 4px 0; margin:8px 0; }
.voice-card { background:#f8f9fa; border:1px solid #e0e0e0; border-radius:6px; padding:8px 12px; margin:5px 0; font-size:10px; }
.voice-card .voice-text { color:#333; font-style:italic; }
.voice-card .voice-meta { color:#888; font-size:9px; margin-top:3px; }
.comp-table { width:100%; border-collapse:collapse; font-size:9px; margin-top:8px; }
.comp-table th { background:#f0f0f0; padding:6px 8px; text-align:left; font-weight:700; border-bottom:1px solid #ddd; }
.comp-table td { padding:6px 8px; border-bottom:1px solid #f0f0f0; }
.comp-table .target { color:#1565c0; font-weight:700; }
.qa-item { background:#f8f9fa; border-radius:6px; padding:8px 12px; margin:5px 0; }
.qa-q { color:#e65100; font-weight:700; font-size:10px; margin-bottom:3px; }
.qa-a { color:#333; font-size:10px; }
.icebreaker-item { background:#f8f9fa; border-left:3px solid #81c784; padding:6px 12px; margin:4px 0; font-size:10px; }
.checklist li { list-style:none; display:flex; gap:6px; align-items:flex-start; margin-bottom:5px; }
.checklist li::before { content:"☐"; color:#e94560; flex-shrink:0; }
.key-message { background:#fff3e0; border:1px solid #ffb74d; border-radius:6px; padding:10px 14px; margin-top:10px; }
.key-message-label { font-size:8px; color:#e65100; font-weight:700; margin-bottom:4px; }
.key-message-text { font-size:12px; font-weight:800; color:#1a1a2e; }
.conf { display:inline-block; font-size:8px; font-weight:700; padding:1px 5px; border-radius:8px; margin-left:4px; }
.conf-高 { background:#e8f5e9; color:#388e3c; border:1px solid #a5d6a7; }
.conf-中 { background:#fff8e1; color:#f57c00; border:1px solid #ffe082; }
.conf-低 { background:#ffebee; color:#c62828; border:1px solid #ef9a9a; }
.conf-低-wrap { background:#fff5f5; border-left:3px solid #e57373; padding:4px 8px; margin:2px 0; }
.sources-section { background:#f8f9fa; border:1px solid #e0e0e0; border-radius:8px; padding:14px 16px; margin-top:10px; }
.sources-section a { color:#1565c0; font-size:9px; word-break:break-all; }
.footer { text-align:center; padding:16px; color:#aaa; font-size:9px; margin-top:10px; border-top:1px solid #eee; }
.back-link { display:none; }
"""

def build_pdf_html(html: str) -> str:
    """HTMLのダークテーマCSSをPDF用ライトテーマに置き換える"""
    # <style>...</style>ブロックをPDF用CSSに差し替え
    import re
    pdf_html = re.sub(r"<style>.*?</style>", f"<style>{PDF_CSS}</style>", html, flags=re.DOTALL)
    return pdf_html


def generate_pdf(html: str, pdf_path: str) -> bool:
    if not WEASYPRINT_AVAILABLE:
        print("  weasyprint not available, skipping PDF")
        return False
    try:
        pdf_html = build_pdf_html(html)
        WeasyprintHTML(string=pdf_html).write_pdf(pdf_path)
        print(f"✓ PDF保存: {pdf_path}")
        return True
    except Exception as e:
        print(f"  PDF生成エラー: {e}")
        return False


# ============================================================
# INDEX
# ============================================================
def update_index(company_name: str, person_name: str, department: str, filename: str, pdf_filename: str = ""):
    index_path = "reports/index.json"
    index = []
    if os.path.exists(index_path):
        with open(index_path, encoding="utf-8") as f:
            index = json.load(f)
    entry = {
        "company": company_name,
        "person": person_name,
        "department": department,
        "file": filename,
        "created_at": now_jst().isoformat(),
    }
    if pdf_filename:
        entry["pdf"] = pdf_filename
    index.insert(0, entry)
    with open(index_path, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)


# ============================================================
# MAIN
# ============================================================
if __name__ == "__main__":
    company_name = os.environ["COMPANY_NAME"]
    person_name  = os.environ.get("PERSON_NAME", "")
    department   = os.environ.get("DEPARTMENT", "")
    service_key  = os.environ.get("SERVICE_KEY", "persona_insight")

    print(f"▶ リサーチ開始: {company_name} / {person_name} / {department} / {service_key}")

    tavily = TavilyClient(api_key=os.environ["TAVILY_API_KEY"])
    research = search_all(tavily, company_name, person_name, department)
    print(f"✓ Web検索完了 ({len([v for v in research.values() if v])}カテゴリ)")

    data = analyze_with_gemini(company_name, person_name, department, research, service_key)
    print("✓ Gemini分析完了")

    html = build_html(company_name, person_name, department, data, service_key, research)

    os.makedirs("reports", exist_ok=True)
    timestamp = now_jst().strftime("%Y%m%d_%H%M%S")
    slug = company_name.replace(" ", "_").replace("　", "_").replace("/", "-")
    service_label = "HR" if service_key == "human_research" else "PI"
    filename = f"{slug}_{service_label}_{timestamp}.html"
    filepath = f"reports/{filename}"

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"✓ レポート保存: {filepath}")

    pdf_filename = filename.replace(".html", ".pdf")
    pdf_filepath = f"reports/{pdf_filename}"
    pdf_ok = generate_pdf(html, pdf_filepath)

    update_index(company_name, person_name, department, filename, pdf_filename if pdf_ok else "")
    print("✓ 完了")
