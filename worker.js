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
