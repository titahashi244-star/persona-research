const GITHUB_OWNER = "titahashi244-star";
const GITHUB_REPO  = "persona-research";
const APP_PASSWORD = "dnp2025";

export default {
  async fetch(request, env, ctx) {
    if (request.method === "OPTIONS") {
      return corsResponse("");
    }

    const body = await request.json();
    const { password, action } = body;

    if (password !== APP_PASSWORD) {
      return corsResponse(JSON.stringify({ error: "パスワードが違います" }), 401);
    }

    // URLから会社名抽出
    if (action === "extract_company") {
      const { url } = body;
      try {
        const r = await fetch("https://api.tavily.com/extract", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ api_key: env.TAVILY_API_KEY, urls: [url] }),
        });
        const data = await r.json();
        const result = (data.results || [])[0];
        if (!result) return corsResponse(JSON.stringify({ error: "ページを取得できませんでした" }), 404);
        const title = result.title || "";
        // タイトルからパイプ・ダッシュ前の部分を会社名として抽出
        const companyName = title.split(/[|\-–—｜]/)[0].trim();
        return corsResponse(JSON.stringify({
          company_name: companyName,
          title,
          snippet: (result.raw_content || "").slice(0, 300),
        }));
      } catch (e) {
        return corsResponse(JSON.stringify({ error: e.message }), 500);
      }
    }

    // 会社確認検索
    if (action === "lookup") {
      const { company_name } = body;
      try {
        const r = await fetch("https://api.tavily.com/search", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            api_key: env.TAVILY_API_KEY,
            query: `${company_name} 会社概要 事業内容`,
            max_results: 4,
            search_depth: "basic",
          }),
        });
        const data = await r.json();
        const results = (data.results || []).map(x => ({
          title: x.title,
          url: x.url,
          snippet: x.content?.slice(0, 150) || "",
        }));
        return corsResponse(JSON.stringify({ results }));
      } catch (e) {
        return corsResponse(JSON.stringify({ error: e.message }), 500);
      }
    }

    // 削除
    if (action === "delete") {
      const { filename } = body;
      const res = await githubDispatch(env, "delete-report.yml", { filename });
      if (!res.ok) {
        return corsResponse(JSON.stringify({ error: await res.text() }), 500);
      }
      return corsResponse(JSON.stringify({ ok: true }));
    }

    // 生成（デフォルト）
    const { company_name, person_name, department, service_key } = body;
    const res = await githubDispatch(env, "generate-report.yml", {
      company_name,
      person_name:  person_name  || "",
      department:   department   || "",
      service_key:  service_key  || "persona_insight",
    });

    if (!res.ok) {
      return corsResponse(JSON.stringify({ error: await res.text() }), 500);
    }
    return corsResponse(JSON.stringify({ ok: true }));
  }
};

async function githubDispatch(env, workflow, inputs) {
  return fetch(
    `https://api.github.com/repos/${GITHUB_OWNER}/${GITHUB_REPO}/actions/workflows/${workflow}/dispatches`,
    {
      method: "POST",
      headers: {
        "Authorization": `token ${env.GITHUB_PAT}`,
        "Accept": "application/vnd.github.v3+json",
        "Content-Type": "application/json",
        "User-Agent": "persona-research-worker",
      },
      body: JSON.stringify({ ref: "main", inputs }),
    }
  );
}

function corsResponse(body, status = 200) {
  return new Response(body, {
    status,
    headers: {
      "Content-Type": "application/json",
      "Access-Control-Allow-Origin": "*",
      "Access-Control-Allow-Methods": "POST, OPTIONS",
      "Access-Control-Allow-Headers": "Content-Type",
    }
  });
}
