"use strict";
const message = document.getElementById("message");
async function accountRequest(path, options = {}) {
  const response = await fetch(path, {credentials: "same-origin", ...options});
  const body = await response.json();
  if (!response.ok) throw new Error(body.detail || `Request failed (${response.status})`);
  return body;
}
async function loadTokens() {
  const rows = await accountRequest("/api/v2/recipient/tokens");
  const target = document.getElementById("tokens");
  target.replaceChildren();
  for (const item of rows) {
    const row = document.createElement("tr");
    for (const value of [item.name, item.expires_at, item.status]) {
      const cell = document.createElement("td"); cell.textContent = value; row.append(cell);
    }
    const cell = document.createElement("td");
    if (item.status === "active") {
      const button = document.createElement("button"); button.textContent = "Revoke";
      button.onclick = async () => {
        button.disabled = true;
        try { await accountRequest(`/api/v2/recipient/tokens/${encodeURIComponent(item.euid)}/revoke`, {method: "POST"}); await loadTokens(); }
        catch (error) { message.textContent = error.message; button.disabled = false; }
      };
      cell.append(button);
    }
    row.append(cell); target.append(row);
  }
}
document.getElementById("token-form").onsubmit = async (event) => {
  event.preventDefault();
  const form = event.currentTarget, button = form.querySelector("button"); button.disabled = true;
  const output = document.getElementById("new-token"); output.textContent = ""; output.hidden = true;
  try {
    const data = new FormData(form);
    const result = await accountRequest("/api/v2/recipient/tokens", {method: "POST", headers: {"Content-Type": "application/json"},
      body: JSON.stringify({name: data.get("name"), lifetime_days: Number(data.get("lifetime_days"))})});
    output.textContent = result.token; output.hidden = false;
    message.textContent = `Save this credential now. It expires ${result.expires_at}.`;
    await loadTokens();
  } catch (error) { message.textContent = error.message; }
  finally { button.disabled = false; }
};
loadTokens().catch(error => { message.textContent = error.message; });
