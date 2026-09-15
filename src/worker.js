function json(data, status = 200) {
  return new Response(JSON.stringify(data), {
    status,
    headers: { "content-type": "application/json; charset=utf-8" },
  });
}

function validEmail(value) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value) && value.length <= 254;
}

function webhookHeaders(raw) {
  const headers = { "content-type": "application/json" };
  const value = String(raw || "").trim();
  if (!value) return headers;
  const cut = value.indexOf(":");
  if (cut > 0) {
    const name = value.slice(0, cut).trim();
    const rest = value.slice(cut + 1).trim();
    if (name && rest) headers[name] = rest;
  } else {
    headers.Authorization = value;
  }
  return headers;
}

async function notifySignup(env, email) {
  const hook = String(env.SIGNUP_WEBHOOK_URL || "").trim();
  if (!hook.startsWith("https://") && !hook.startsWith("http://")) return;
  try {
    await fetch(hook, {
      method: "POST",
      headers: webhookHeaders(env.SIGNUP_WEBHOOK_HEADER),
      body: JSON.stringify({ email }),
    });
  } catch {
    // KV stays the source of truth
  }
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    if (url.pathname === "/waitlist" && request.method === "POST") {
      let body;
      try {
        body = await request.json();
      } catch {
        return json({ error: "bad" }, 400);
      }
      const email = String(body.email || "").trim().toLowerCase();
      if (!validEmail(email)) return json({ error: "email" }, 400);
      const key = "email:" + email;
      const existing = await env.WAITLIST.get(key);
      if (!existing) {
        await env.WAITLIST.put(
          key,
          JSON.stringify({ email, at: new Date().toISOString() }),
        );
        await notifySignup(env, email);
      }
      return json({ ok: true });
    }
    if (url.pathname === "/waitlist") {
      return json({ error: "method" }, 405);
    }
    return env.ASSETS.fetch(request);
  },
};
