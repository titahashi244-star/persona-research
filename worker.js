const GITHUB_OWNER = "titahashi244-star";
const GITHUB_REPO  = "persona-research";
const APP_PASSWORD = "dnp2025";

export default {
  async fetch(request, env, ctx) {
    if (request.method === "OPTIONS") {
      return corsResponse("");
    }

    const { password, company_name, person_name, department, service_key } = await request.json();

    if (password !== APP_PASSWORD) {
      return corsResponse(JSON.stringify({ error: "パスワードが違います" }), 401);
    }

    const res = await fetch(
      `https://api.github.com/repos/${GITHUB_OWNER}/${GITHUB_REPO}/actions/workflows/generate-report.yml/dispatches`,
      {
        method: "POST",
        headers: {
          "Authorization": `token ${env.GITHUB_PAT}`,
          "Accept": "application/vnd.github.v3+json",
          "Content-Type": "application/json",
          "User-Agent": "persona-research-worker",
        },
        body: JSON.stringify({
          ref: "main",
          inputs: {
            company_name,
            person_name:  person_name  || "",
            department:   department   || "",
            service_key:  service_key  || "persona_insight",
          }
        })
      }
    );

    if (!res.ok) {
      const err = await res.text();
      return corsResponse(JSON.stringify({ error: err }), 500);
    }

    return corsResponse(JSON.stringify({ ok: true }));
  }
};

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
