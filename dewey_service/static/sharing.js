/* Managed sharing always retains its share context and current viewer. */
"use strict";
window.DeweySharing = (() => {
  const enc = encodeURIComponent;
  let h, share, rows = [], activity = [], activityCursor = null, activityLoaded = false, activityLoading = false, browseGeneration = 0, reportCleanup = null, auditState = null;
  const $ = (s, root = document) => root.querySelector(s);
  const esc = v => String(v ?? "").replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
  const lines = v => String(v).split(/\r?\n/).map(x => x.trim()).filter(Boolean);
  const field = (name, label, value = "", type = "text", required = false) => `<label class="field">${esc(label)}<input name="${esc(name)}" type="${type}" value="${esc(value)}" ${required ? "required" : ""}></label>`;
  const area = (name, label, value) => `<label class="field">${esc(label)}<textarea name="${esc(name)}">${esc(value)}</textarea></label>`;
  const button = (text, action, value = "", cls = "") => `<button type="button" data-action="${action}" data-value="${esc(value)}" class="${cls}">${esc(text)}</button>`;
  const stamp = value => value ? `${new Date(value).toLocaleString()} · ${new Date(value).toISOString()}` : "No expiry";
  const pad = n => String(n).padStart(2, "0");
  const localValue = date => `${date.getFullYear()}-${pad(date.getMonth()+1)}-${pad(date.getDate())}T${pad(date.getHours())}:${pad(date.getMinutes())}:${pad(date.getSeconds())}`;
  const offsetValue = date => { const n = -date.getTimezoneOffset(); return `${n < 0 ? "-" : "+"}${pad(Math.floor(Math.abs(n)/60))}:${pad(Math.abs(n)%60)}`; };
  function expiryMarkup(prefix, value) {
    const d = new Date(value || Date.now()+30*86400000), zone = Intl.DateTimeFormat().resolvedOptions().timeZone;
    return `<label><input type="checkbox" name="${prefix}_indefinite" ${value===null?"checked":""}> No expiry · verified registered users only</label><div class="expiry-grid">${field(prefix+"_local", "Expiry in "+zone, localValue(d), "datetime-local", true)}${field(prefix+"_offset", "UTC offset (±HH:MM)", offsetValue(d), "text", true)}</div><output class="expiry-resolved" data-expiry="${prefix}"></output>`;
  }
  function expiry(form, prefix) {
    if(form.elements[prefix+"_indefinite"].checked) return null;
    const local = form.elements[prefix+"_local"].value, offset = form.elements[prefix+"_offset"].value;
    if (!/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(?::\d{2})?$/.test(local) || !/^[+-](?:0\d|1[0-4]):[0-5]\d$/.test(offset) || /^[-+]14:(?!00)/.test(offset)) throw Error("Specify an expiration date and explicit UTC offset.");
    const [year, month, day, hour, minute, second=0] = local.split(/[-T:]/).map(Number);
    const wall = new Date(year, month-1, day, hour, minute, second);
    if (wall.getFullYear()!==year || wall.getMonth()!==month-1 || wall.getDate()!==day || wall.getHours()!==hour || wall.getMinutes()!==minute || wall.getSeconds()!==second) throw Error("This local time does not exist in your timezone (including a daylight-saving gap).");
    const d = new Date(local+offset);
    if (!Number.isFinite(d.getTime()) || localValue(d)!==localValue(wall)) throw Error("UTC offset does not match this local time in your timezone. For repeated daylight-saving times, specify either valid offset.");
    if (d <= new Date()) throw Error("Expiration must be in the future.");
    return local+offset;
  }
  function updateExpiry(form) {
    form.querySelectorAll("[data-expiry]").forEach(out => {
      const prefix=out.dataset.expiry, indefinite=form.elements[prefix+"_indefinite"].checked;
      form.elements[prefix+"_local"].disabled=indefinite;form.elements[prefix+"_offset"].disabled=indefinite;
      try { const value=expiry(form,prefix);out.textContent = value===null?"No expiry. Access still requires a current verified identity and grant.":"Resolved UTC: "+new Date(value).toISOString(); out.classList.remove("error"); }
      catch(e) {out.textContent=e.message;out.classList.add("error");}
    });
  }
  function grantMarkup(grant, index, targets, deadline) {
    const scoped=(grant.target_euids||[]).length===targets.length?[]:(grant.target_euids||[]);
    return `<fieldset class="share-grant" data-grant="${index}" data-grant-euid="${esc(grant.grant_euid||'')}"><legend>Recipient grant ${index+1}</legend><div class="grid-equal"><label class="field">Recipient type<select name="g${index}_type"><option value="email" ${grant.recipient_type==="email"?"selected":""}>Email</option><option value="domain" ${grant.recipient_type==="domain"?"selected":""}>Exact domain</option></select></label>${field(`g${index}_recipient`,"Recipient",grant.recipient,"text",false)}</div><label><input type="checkbox" name="g${index}_subdomains" ${grant.include_subdomains?"checked":""}> Include subdomains for this domain grant</label>${area(`g${index}_include`,"Include patterns · one per line",(grant.include_patterns||["**"]).join("\n"))}${area(`g${index}_exclude`,"Exclude patterns · one per line",(grant.exclude_patterns||[]).join("\n"))}${expiryMarkup(`g${index}`,Object.hasOwn(grant,"expires_at")?grant.expires_at:deadline)}<label class="field">Limit to persisted targets (optional)<select name="g${index}_targets" multiple>${targets.map(t=>`<option value="${esc(t.euid)}" ${scoped.includes(t.euid)?"selected":""}>${esc(t.name||t.euid)} · ${esc(t.euid)}</option>`).join("")}</select><small>No selected targets means all reviewed share targets.</small></label>${button("Remove grant","sharing-remove-grant",index)}</fieldset>`;
  }
  async function editor(target, existing = null) {
    let record = null;
    if (!existing) record = await h.api(`/api/v1/records/${enc(target)}`);
    const deadline = existing ? existing.expires_at : new Date(Date.now()+30*86400000).toISOString();
    const targets = existing ? existing.targets : (record.kind==="set" ? record.members.map(m=>({euid:m.artifact_euid,name:m.original_filename,kind:m.storage_kind})) : [{euid:target,name:record.name}]);
    if (!Array.isArray(targets)||!targets.length||targets.some(t=>typeof t.euid!=="string"||!t.euid)) throw Error("Persisted share targets are required to edit grants.");
    const grants = existing ? existing.grants.filter(g=>g.status==="active"&&g.recipient_type!=="registered") : [{recipient_type:"email",recipient:"",include_patterns:["**"]}];
    if (existing && !Number.isInteger(existing.policy_revision)) throw Error("Current policy revision is required to edit this share.");
    h.modal(`<h2>${existing?"Edit share":"Create managed share"}</h2><p class="hint">Share with verified email addresses inside or outside LSMC. Recipients can register after you add them. Every file request checks current access.</p><form id="managed-share-form">${field("name","Share name",existing?.name||record?.name||"","text",true)}${area("purpose","Purpose",existing?.purpose||"")}<label class="field">Audience<select name="audience"><option value="recipients">Named recipients</option><option value="public_registered" ${existing?.audience==="public_registered"?"selected":""}>Public with registration</option></select></label><p class="muted">Public with registration permits anyone after email verification. Anonymous access is never allowed.</p>${expiryMarkup("share",deadline)}<label class="field">Share type<select name="content_mode"><option value="download">File downloads</option><option value="www" ${existing?.content_mode==="www"?"selected":""}>WWW report</option></select></label>${field("report_entrypoint","WWW entrypoint relative to the share",existing?.report_entrypoint||"","text")}${field("report_bundle_root","WWW bundle root relative to its target (empty or directory ending in /)",existing?.report_bundle_root||"")}<p class="muted">For multiple targets, the entrypoint begins with the target's persisted EUID. Share the containing prefix to include report sidecars.</p>${existing?area("target_euids","Shared Object or Prefix EUIDs · one per line",targets.map(t=>t.euid).join("\n")):""}<p class="hint">Prefix shares include future matching descendants. Patterns are case-sensitive and relative to each prefix target; objects use their stable filename. * stays within a segment; ** crosses segments; exclusions win.</p>${area("include_patterns","Share-wide include patterns",(existing?.include_patterns||["**"]).join("\n"))}${area("exclude_patterns","Share-wide exclusions",(existing?.exclude_patterns||[]).join("\n"))}${area("denied_emails","Excluded emails · one per line",(existing?.denied_emails||[]).join("\n"))}<div id="share-grants">${grants.map((g,i)=>grantMarkup(g,i,targets,deadline)).join("")}</div>${button("Add recipient grant","sharing-add-grant")}<div class="actions">${!existing?button("Preview matching selection","sharing-selection-preview",target):""}<button class="primary" type="submit">${existing?"Save policy":"Create share"}</button></div><div id="selection-preview" aria-live="polite"></div></form>`);
    const form=$("#managed-share-form");
    form._sharing={target,existing,targets,deadline,next:grants.length};
    form.addEventListener("input",()=>updateExpiry(form));
    form.querySelectorAll('input[type="datetime-local"]').forEach(input=>input.step=1);
    updateExpiry(form);
    form.onsubmit=event=>{event.preventDefault();if(form._saving)return;h.safe(async()=>{
      const data=policyData(form);form._saving=true;form.querySelector('button[type="submit"]').disabled=true;
      try {
      if(existing){const ids=[...new Set(lines(form.elements.target_euids.value))];if(!ids.length)throw Error("Retain at least one target, or revoke the share.");if(ids.join("\n")!==targets.map(t=>t.euid).join("\n")){data.targets=[];for(const id of ids){const row=await h.api(`/api/v1/records/${enc(id)}`);if(!["object","prefix"].includes(row.kind))throw Error("Share target edits require Object or Prefix EUIDs.");data.targets.push({target_kind:"artifact_"+row.kind,target_euid:id});}for(const grant of data.grants)if(grant.target_euids?.some(id=>!ids.includes(id)))throw Error("A recipient grant still selects a removed target. Clear or revise its target selection.");}}
      const result=existing?await h.api(`/api/v1/registry/shares/${enc(existing.euid)}`,"PATCH",data):await h.api(`/api/v1/records/${enc(target)}/shares`,"POST",data);
      $("#editor").close(); if(existing) await h.render(); else location.assign(`/shares/${enc(result.euid)}`);
      } finally {form._saving=false;form.querySelector('button[type="submit"]').disabled=false;}
    });};
  }
  function policyData(form) {
    const data={name:form.elements.name.value,purpose:form.elements.purpose.value,audience:form.elements.audience.value,content_mode:form.elements.content_mode.value,report_entrypoint:form.elements.report_entrypoint.value||null,report_bundle_root:form.elements.report_bundle_root.value,expires_at:expiry(form,"share"),include_patterns:lines(form.elements.include_patterns.value),exclude_patterns:lines(form.elements.exclude_patterns.value),denied_emails:lines(form.elements.denied_emails.value),delivery_modes:["gateway"],grants:[]};
    if(data.content_mode==="www"&&!data.report_entrypoint)throw Error("WWW shares require an exact HTML entrypoint.");
    if (!data.include_patterns.length) throw Error("At least one share-wide include pattern is required; use ** for all.");
    form.querySelectorAll("[data-grant]").forEach(row=>{
      const n=row.dataset.grant, val=k=>form.elements[`g${n}_${k}`];
      if(!val("recipient").value.trim()&&data.audience==="public_registered")return;
      const grant={recipient_type:val("type").value,recipient:val("recipient").value.trim(),include_subdomains:val("subdomains").checked,include_patterns:lines(val("include").value),exclude_patterns:lines(val("exclude").value),expires_at:expiry(form,"g"+n)};
      if(!grant.recipient||!grant.include_patterns.length) throw Error("Each grant needs a recipient and at least one include pattern.");
      if(grant.recipient_type==="email"&&grant.include_subdomains) throw Error("Include subdomains is available only for domain grants.");
      if(data.expires_at!==null&&(grant.expires_at===null||new Date(grant.expires_at)>new Date(data.expires_at))) throw Error("Grant expiry must not exceed the share expiry.");
      const ids=Array.from(val("targets").selectedOptions,o=>o.value); if(ids.length) grant.target_euids=ids;
      if(row.dataset.grantEuid) grant.grant_euid=row.dataset.grantEuid;
      data.grants.push(grant);
    });
    if(!data.grants.length&&data.audience!=="public_registered") throw Error("Add at least one recipient grant.");
    data.allowed_users=data.grants.filter(g=>g.recipient_type==="email").map(g=>g.recipient);
    data.allowed_domains=data.grants.filter(g=>g.recipient_type==="domain").map(g=>g.recipient);
    if(form._sharing.existing) data.policy_revision=form._sharing.existing.policy_revision;
    return data;
  }
  async function page(id) {
    share=await h.api(`/api/v1/registry/shares/${enc(id)}`); h.setCurrent(share); $("#title").textContent=share.name;
    const active=share.status==="active"&&(share.expires_at===null||new Date(share.expires_at)>new Date());
    h.content.innerHTML=`<div class="toolbar"><span>${esc(active?"Active":share.status)} · <code>${esc(id)}</code></span>${button("Copy share link","copy-share",id)}</div><p class="hint">Internal and external recipients sign in with their verified email. Current grants authorize each request.</p><div class="grid"><section class="panel"><h2>Shared files</h2><p>${esc(share.purpose||"")}</p><p class="muted">${share.live_prefix?"Live prefix: future matching descendants are included.":"Explicit targets: members are fixed; prefix members include future matching descendants."}</p><p><a class="button" href="/fetch/${enc(id)}">Open recipient URL</a> <a class="button" href="/fetch/${enc(id)}?format=manifest">Manifest</a> <a class="button" href="/fetch/${enc(id)}?format=tar">Download all as TAR</a></p>${active?'<div id="share-browser"></div>':"<p>This share no longer grants access.</p>"}</section><aside class="panel"><h2>Share policy</h2><p>${esc(stamp(share.expires_at))}</p><p>Audience: ${esc(share.audience==="public_registered"?"Public with registration":"Named recipients")}</p><p>Type: ${esc(share.content_mode)}</p>${share.report_entrypoint?`<p>Report: <code>${esc(share.report_entrypoint)}</code></p>`:""}<p>Policy revision: ${esc(share.policy_revision)}</p><p class="muted">Revocation stops subsequent requests and the next archive member. An admitted file may finish. Downloaded files cannot be recalled.</p>${share.can_manage?button("Edit share and targets","share-edit",id)+button("Send login invitation","share-invite",id)+button("Revoke share","revoke",id,"danger"):""}</aside></div>${share.can_manage?'<section class="panel"><h2>Readable URLs</h2><div id="share-aliases"></div>'+button("Claim a URL slug","sharing-alias-add")+'</section><section class="panel"><h2>Recipient grants</h2><div id="share-recipient-grants"></div></section><section class="panel"><h2>Activity</h2><p class="muted">Server response completion and bytes sent do not establish that a recipient saved the file.</p><div id="share-activity"></div><div class="actions">'+button("Load activity","sharing-activity")+button("Export loaded activity JSON","sharing-activity-export")+'</div></section>':""}`;
    if(share.can_manage) $("#share-aliases").innerHTML=(share.aliases||[]).map(alias=>`<p><a href="/fetch/${enc(alias.slug)}${share.report_entrypoint?"/"+share.report_entrypoint.split("/").map(enc).join("/"):""}">${esc(alias.slug)}</a> · ${esc(alias.status)} ${alias.status==="active"?button("Copy URL","sharing-alias-copy",alias.slug)+button("Retire slug","sharing-alias-retire",alias.slug):""}</p>`).join("")||"<p>No human-readable URL claimed.</p>";
    if(share.can_manage) $("#share-recipient-grants").innerHTML=share.grants.map(g=>`<div class="grant-summary"><strong>${esc(g.recipient_type)}: ${esc(g.recipient)}</strong> ${esc(g.include_subdomains?"including subdomains":"exact match")}<p>${esc(g.status)} · expires ${esc(stamp(g.expires_at))}</p><p>Include: <code>${esc(g.include_patterns.join(", "))}</code> · Exclude: <code>${esc(g.exclude_patterns.join(", "))}</code></p>${g.status==="active"&&g.recipient_type!=="registered"?button("Revoke recipient grant","sharing-revoke-grant",g.grant_euid,"danger"):""}</div>`).join("");
    activity=[];activityCursor=null;activityLoaded=false;
    if(active) await browse();
  }
  async function browse(target="",prefix="",token="",append=false) {
    const requestedGeneration=++browseGeneration;
    const query=new URLSearchParams({target_euid:target,prefix,limit:"100",continuation_token:token});
    const result=await h.api(`/api/v1/registry/shares/${enc(share.euid)}/contents?${query}`);
    if(requestedGeneration!==browseGeneration)return;
    rows=append?rows.concat(result.items):result.items;
    const root=$("#share-browser");
    root.dataset.target=target;root.dataset.prefix=prefix;root.dataset.token=result.continuation_token||"";
    root.innerHTML=`<div class="toolbar"><span class="mono">${esc(prefix||"Share root")}</span>${target||prefix?button("Share root","sharing-root"):""}</div><p class="muted">${rows.length} authorized entries loaded${result.incomplete?" · More pages remain.":" · Final page loaded."}</p><div class="table-panel"><table><thead><tr><th>Name</th><th>Size</th><th>Action</th></tr></thead><tbody>${rows.map((item,i)=>{const path=(share.member_count>1?item.target_euid+"/":"")+(item.relative_key||item.name);return `<tr><td class="mono">${esc(item.name)}</td><td>${item.size==null?"—":esc(item.size)+" B"}</td><td><a class="button primary" href="/fetch/${enc(share.euid)}/${path.split("/").map(enc).join("/")}?download=true">Download</a> ${/\.html?$/i.test(item.name)?button("View report","sharing-report",i):""}</td></tr>`;}).join("")||'<tr><td colspan="3">No permitted entries on this page.</td></tr>'}</tbody></table></div>${result.continuation_token?button("Load next page","sharing-next"):""}`;
  }
  async function report(item,bundleRoot) {
    const result=await h.api(`/api/v1/registry/shares/${enc(share.euid)}/preview`,"POST",{target_euid:item.target_euid,relative_key:item.relative_key,bundle_root:bundleRoot});
    const origin=new URL(result.preview_origin),challenge=new URL(result.challenge_url),endpoint=new URL(result.handoff_endpoint,location.origin);
    if(origin.protocol!=="https:"||origin.origin===location.origin||origin.href!==origin.origin+"/"||challenge.origin!==origin.origin||challenge.pathname!=="/__dewey_preview/challenge"||endpoint.origin!==location.origin) throw Error("Invalid isolated report handoff configuration.");
    if(reportCleanup) reportCleanup();
    h.modal(`<h2>Report preview</h2><p class="muted">Current viewer · expires ${esc(stamp(result.expires_at))}. Each linked asset is authorized within the selected report root.</p><iframe id="share-report-frame" name="dewey-report-${esc(crypto.randomUUID())}" title="Isolated shared report" sandbox="allow-scripts allow-same-origin allow-forms allow-downloads" referrerpolicy="no-referrer" class="share-report-frame"></iframe>`);
    const iframe=$("#share-report-frame"); let used=false;
    const listener=event=>{if(used||event.origin!==origin.origin||event.source!==iframe.contentWindow||event.data?.type!=="dewey-preview-challenge"||event.data.context_euid!==result.context_euid||typeof event.data.challenge!=="string") return;used=true;h.safe(async()=>{
      const handoff=await h.api(endpoint.pathname+endpoint.search,"POST",{challenge:event.data.challenge});
      if(typeof handoff.token!=="string"||!handoff.token) throw Error("Report handoff token missing.");
      const form=document.createElement("form");form.method="POST";form.action=origin.origin+"/__dewey_preview/handoff";form.target=iframe.name;form.hidden=true;
      const input=document.createElement("input");input.name="token";input.value=handoff.token;form.append(input);document.body.append(form);form.submit();form.remove();
    });};
    const close=()=>{window.removeEventListener("message",listener);$("#editor").removeEventListener("close",close);reportCleanup=null;};
    reportCleanup=close;window.addEventListener("message",listener);$("#editor").addEventListener("close",close,{once:true});iframe.src=challenge.href;
  }
  async function auditPage(page) {
    if(!auditState||auditState.loading)return;
    auditState.loading=true;
    try {
      const query=new URLSearchParams(auditState.query);query.set("page",String(page));query.set("page_size","100");
      if(auditState.inventory){query.set("observed_at",auditState.inventory.observed_at);query.set("expected_inventory_sha256",auditState.inventory.inventory_sha256);}
      const inventory=await h.api(`/api/v1/registry/sharing-inventory?${query}`);
      auditState.inventory=inventory;
      $("#sharing-audit-results").innerHTML=`<p>Coverage and server-observed metrics are included below. Completed responses do not prove that a client saved a file.</p><h3>Aggregate report</h3><pre>${esc(JSON.stringify(auditState.report,null,2))}</pre><h3>Lifecycle inventory</h3><p>Page ${inventory.page} · ${inventory.items.length} of ${inventory.total} shares · observed ${esc(inventory.observed_at)}</p><pre>${esc(JSON.stringify(inventory.items,null,2))}</pre><div class="actions">${inventory.page>1?button("Previous inventory page","sharing-audit-page",inventory.page-1):""}${inventory.has_more?button("Next inventory page","sharing-audit-page",inventory.page+1):""}${button("Export report and this inventory page","sharing-audit-export")}</div><p class="muted">Pagination freezes the observation time and verifies the inventory digest. A changed inventory requires a fresh report. For one complete inventory file, use dewey shares audit-report --inventory --output FILE.</p>`;
    } finally {auditState.loading=false;}
  }
  async function auditDialog() {
    const options=(name,label,values)=>`<label class="field">${label}<select name="${name}"><option value="">All</option>${values.map(value=>`<option>${value}</option>`).join("")}</select></label>`;
    h.modal(`<h2>Sharing audit report</h2><form id="sharing-audit-form">${field("starts_at","Observation start (ISO timestamp)",new Date(Date.now()-30*86400000).toISOString(),"text",true)}${field("ends_at","Observation end (ISO timestamp)",new Date().toISOString(),"text",true)}${options("status","Status",["active","expired","revoked"])}${options("audience","Audience",["recipients","public_registered"])}${options("content_mode","Type",["download","www"])}${field("owner_subject","Owner canonical user ID (optional)")}${field("created_from","Created from (ISO timestamp, optional)")}${field("created_before","Created before (ISO timestamp, optional)")}${field("older_than_days","Only shares older than days","","number")}<label><input type="checkbox" name="never_accessed"> Never accessed in observed history</label><button class="primary">Load report</button></form><div id="sharing-audit-results"></div>`);
    $("#sharing-audit-form").onsubmit=e=>{e.preventDefault();h.safe(async()=>{
      const form=e.target,query=new URLSearchParams({never_accessed:String(form.elements.never_accessed.checked)});
      for(const name of ["starts_at","ends_at","status","audience","content_mode","owner_subject","created_from","created_before","older_than_days"])
        if(form.elements[name].value)query.set(name,form.elements[name].value);
      form.querySelector("button").disabled=true;
      try {auditState={query,inventory:null,report:await h.api(`/api/v1/registry/sharing-report?${query}`)};await auditPage(1);}
      finally {form.querySelector("button").disabled=false;}
    });};
  }
  async function handle(name,value) {
    if(!name.startsWith("sharing-")) return false;
    if(name==="sharing-add-grant") {const form=$("#managed-share-form"),state=form._sharing;$("#share-grants").insertAdjacentHTML("beforeend",grantMarkup({recipient_type:"email",recipient:""},state.next++,state.targets,state.deadline));form.querySelectorAll('input[type="datetime-local"]').forEach(i=>i.step=1);updateExpiry(form);}
    else if(name==="sharing-remove-grant") $(`[data-grant="${Number(value)}"]`).remove();
    else if(name==="sharing-selection-preview") {const form=$("#managed-share-form"), result=await h.api(`/api/v1/records/${enc(value)}/shares/preview`,"POST",policyData(form));$("#selection-preview").innerHTML=`<h3>Bounded selection preview</h3><p class="hint">${result.incomplete?"Incomplete: this is a bounded preview and is not a complete inventory.":"Bounded metadata selection preview."}</p><pre>${esc(JSON.stringify(result,null,2))}</pre>`;}
    else if(name==="sharing-root") await browse();
    else if(name==="sharing-open") {const item=rows[Number(value)];await browse(item.target_euid,item.relative_key);}
    else if(name==="sharing-next") {const root=$("#share-browser");await browse(root.dataset.target,root.dataset.prefix,root.dataset.token,true);}
    else if(name==="sharing-report") {const item=rows[Number(value)];h.modal(`<h2>View report</h2><p>Choose the exact report bundle directory relative to this target. Linked assets are restricted to this directory and current grants.</p><form id="report-root-form">${field("bundle_root","Report bundle root (directory ending in /; empty for target root)",item.relative_key.slice(0,item.relative_key.lastIndexOf("/")+1))}<button class="primary">View report</button></form>`);$("#report-root-form").onsubmit=e=>{e.preventDefault();h.safe(()=>report(item,e.target.elements.bundle_root.value));};}
    else if(name==="sharing-alias-add") {h.modal(`<h2>Claim readable URL</h2><p>Use 3–63 lowercase letters, digits and hyphens, starting with a letter. A claimed or retired slug cannot be reassigned.</p><form id="alias-form">${field("slug","URL slug","","text",true)}<button class="primary">Claim slug</button></form>`);$("#alias-form").onsubmit=e=>{e.preventDefault();h.safe(async()=>{await h.api(`/api/v1/registry/shares/${enc(share.euid)}/aliases`,"POST",{slug:e.target.elements.slug.value,policy_revision:share.policy_revision});$("#editor").close();await h.render();});};}
    else if(name==="sharing-alias-copy") await navigator.clipboard.writeText(`${location.origin}/fetch/${enc(value)}${share.report_entrypoint?"/"+share.report_entrypoint.split("/").map(enc).join("/"):""}`);
    else if(name==="sharing-alias-retire") {h.modal(`<h2>Retire URL slug</h2><p>${esc(value)} will stop resolving and can never be claimed again. The share EUID URL remains available.</p>${button("Retire this slug","sharing-alias-retire-confirmed",value,"danger")}`);}
    else if(name==="sharing-alias-retire-confirmed") {await h.api(`/api/v1/registry/shares/${enc(share.euid)}/aliases/${enc(value)}/revoke`,"POST",{policy_revision:share.policy_revision});$("#editor").close();await h.render();}
    else if(name==="sharing-audit") await auditDialog();
    else if(name==="sharing-audit-page") await auditPage(Number(value));
    else if(name==="sharing-audit-export") {if(!auditState?.inventory)throw Error("Load a report first.");const blob=new Blob([JSON.stringify({report:auditState.report,inventory_page:auditState.inventory,complete:auditState.inventory.complete},null,2)],{type:"application/json"}),url=URL.createObjectURL(blob),link=document.createElement("a");link.href=url;link.download="dewey-sharing-report.json";link.click();URL.revokeObjectURL(url);}
    else if(name==="sharing-revoke-grant") {h.modal(`<h2>Revoke recipient grant</h2><p>Subsequent requests under this grant will be denied. Other independent grants remain effective.</p><form id="grant-revoke-form">${field("reason","Reason","","text",true)}<button class="danger">Revoke grant</button></form>`);$("#grant-revoke-form").onsubmit=e=>{e.preventDefault();h.safe(async()=>{await h.api(`/api/v1/registry/shares/${enc(share.euid)}/grants/${enc(value)}/revoke`,"POST",{reason:e.target.elements.reason.value,policy_revision:share.policy_revision});$("#editor").close();await h.render();});};}
    else if(name==="sharing-activity") {if(activityLoading)return true;activityLoading=true;try {const result=await h.api(`/api/v1/registry/shares/${enc(share.euid)}/activity?`+new URLSearchParams({limit:"100",continuation_token:activityCursor||""}));activity.push(...result.items);activityCursor=result.continuation_token;activityLoaded=true;$("#share-activity").innerHTML=`<p>${activity.length} events loaded${activityCursor?" · more available":""}</p><pre>${esc(JSON.stringify(activity,null,2))}</pre>`;const b=$('[data-action="sharing-activity"]');b.disabled=!activityCursor;b.textContent=activityCursor?"Load next activity page":"Activity loaded";}finally{activityLoading=false;}}
    else if(name==="sharing-activity-export") {if(!activityLoaded)throw Error("Load activity before exporting.");const blob=new Blob([JSON.stringify({share_euid:share.euid,exported_at:new Date().toISOString(),incomplete:Boolean(activityCursor),items:activity},null,2)],{type:"application/json"});const url=URL.createObjectURL(blob),a=document.createElement("a");a.href=url;a.download="dewey-share-activity.json";a.click();URL.revokeObjectURL(url);}
    return true;
  }
  return {init:helpers=>{h=helpers;},editor,page,handle};
})();
