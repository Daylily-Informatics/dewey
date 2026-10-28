"use strict";
(() => {
  const target = document.getElementById("recipient-shares");
  const toggle = document.getElementById("show-expired");
  const more = document.getElementById("more");
  const message = document.getElementById("message");
  let page = 0;
  let count = 0;
  function dateCell(value, indefinite = false) {
    const cell = document.createElement("td");
    if (value === null && indefinite) { cell.textContent = "No expiration"; return cell; }
    const time = document.createElement("time");
    time.dateTime = value; time.title = value;
    time.textContent = new Date(value).toLocaleString(); cell.append(time);
    return cell;
  }
  async function load(reset) {
    toggle.disabled = true; more.disabled = true;
    if (reset) { page = 0; count = 0; target.replaceChildren(); more.hidden = true; }
    message.textContent = "Loading your shares…";
    try {
      const query = new URLSearchParams({page: String(page + 1), page_size: "50", include_expired: String(toggle.checked)});
      const response = await fetch(`/api/v2/recipient/shares?${query}`, {credentials: "same-origin", headers: {Accept: "application/json"}});
      const body = await response.json();
      if (!response.ok) throw new Error(typeof body.detail === "string" ? body.detail : `Unable to list shares (${response.status}).`);
      for (const item of body.items) {
        const row = document.createElement("tr");
        if (item.status === "expired") row.className = "expired";
        const id = document.createElement("td"), code = document.createElement("code");
        code.textContent = item.euid; id.append(code); row.append(id);
        const name = document.createElement("td");
        if (item.status === "active") {
          const link = document.createElement("a"); link.href = item.web_path; link.textContent = item.name; name.append(link);
        } else { name.textContent = item.name; name.title = "Ask the share owner to renew access."; }
        row.append(name, dateCell(item.shared_at), dateCell(item.expires_at, true));
        const status = document.createElement("td"); status.textContent = item.status === "active" ? "Active" : "Expired"; row.append(status);
        target.append(row); count += 1;
      }
      page = body.page; more.hidden = !body.has_more;
      message.textContent = count ? `${count} share${count === 1 ? "" : "s"} shown${body.has_more ? " · more available" : ""}.` : toggle.checked ? "No shares match your verified identity." : "No active shares. Use Show expired shares to include earlier access.";
    } catch (error) {
      message.textContent = `${error.message} You can log out above and sign in with a different account.`;
    } finally { toggle.disabled = false; more.disabled = false; }
  }
  toggle.addEventListener("change", () => load(true));
  more.addEventListener("click", () => load(false));
  load(true);
})();
