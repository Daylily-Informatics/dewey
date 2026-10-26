const test = require('node:test');
const assert = require('node:assert/strict');
const {createEnvironment, flush, plain} = require('./dom_fixture.cjs');

function accountFixture(responder) {
  const env = createEnvironment({fetch: responder});
  env.node('editor-body').innerHTML = '<form id="token-form"><input name="name" value="fixture"><input name="lifetime_days" value="1"><button>Create</button></form>';
  env.load('recipient-account.js');
  return env;
}

test('recipient account renders text safely and offers revocation only for active own tokens', async () => {
  const rows = [{euid: 'token-fixture', name: '<b>literal</b>', expires_at: 'future', status: 'active'},
    {euid: 'retired-fixture', name: 'retired', expires_at: 'past', status: 'revoked'}];
  const env = accountFixture(() => rows);
  await flush();
  const table = env.node('tokens');
  assert.equal(table.children.length, 2);
  assert.equal(table.children[0].children[0].textContent, '<b>literal</b>');
  assert.equal(table.children[0].children[0].innerHTML, '');
  assert.equal(table.children[0].children[3].children.length, 1);
  assert.equal(table.children[1].children[3].children.length, 0);
  assert.equal(env.calls[0].options.credentials, 'same-origin');
});

test('recipient creation posts only name and finite lifetime, shows credential once as text and refreshes own list', async () => {
  const env = accountFixture((url, options) => options.method === 'POST'
    ? {token: '<credential-fixture>', expires_at: '2099-01-01'} : []);
  await flush();
  env.node('token-form').elements.lifetime_days.value = '30';
  await env.submit('token-form');
  const call = env.calls.find(value => value.options.method === 'POST');
  assert.equal(call.url, '/api/v2/recipient/tokens');
  assert.deepEqual(JSON.parse(call.options.body), {name: 'fixture', lifetime_days: 30});
  assert.equal(env.node('new-token').textContent, '<credential-fixture>');
  assert.equal(env.node('new-token').innerHTML, '');
  assert.equal(env.node('new-token').hidden, false);
  assert.equal(env.node('token-form').querySelector('button').disabled, false);
  assert.equal(env.calls.filter(value => !value.options.method).length, 2);
});

test('recipient creation failure clears previous one-use display and reenables submission', async () => {
  const env = accountFixture((url, options) => options.method === 'POST' ? {status: 409, body: {detail: 'Current identity changed'}} : []);
  await flush();
  env.node('new-token').textContent = 'previous-fixture';
  await env.submit('token-form');
  assert.equal(env.node('new-token').textContent, '');
  assert.equal(env.node('new-token').hidden, true);
  assert.equal(env.node('message').textContent, 'Current identity changed');
  assert.equal(env.node('token-form').querySelector('button').disabled, false);
});

for (const fail of [false, true]) test(`recipient revoke ${fail ? 'failure retains actionable button' : 'success refreshes list'}`, async () => {
  let revoked = false;
  const env = accountFixture((url, options) => {
    if (options.method === 'POST') {
      if (fail) return {status: 503, body: {}};
      revoked = true; return {status: 'revoked'};
    }
    return [{euid: 'token fixture', name: 'fixture', expires_at: 'future', status: revoked ? 'revoked' : 'active'}];
  });
  await flush();
  const button = env.node('tokens').children[0].children[3].children[0];
  await button.onclick();
  await flush();
  assert.equal(env.calls[1].url, '/api/v2/recipient/tokens/token%20fixture/revoke');
  if (fail) {
    assert.equal(button.disabled, false);
    assert.match(env.node('message').textContent, /Request failed \(503\)/);
  } else assert.equal(env.node('tokens').children[0].children[3].children.length, 0);
});

test('recipient initial list failure is visible without exposing a credential', async () => {
  const env = accountFixture(() => ({status: 401, body: {detail: 'Sign in again'}}));
  await flush();
  assert.equal(env.node('message').textContent, 'Sign in again');
  assert.equal(env.node('tokens').children.length, 0);
});

function share(changes = {}) {
  return {euid: 'share-fixture', share_euid: 'share-fixture', target_euid: 'target-fixture', name: 'Synthetic report',
    purpose: '', targets: [{euid: 'target-fixture', name: 'Report', kind: 'prefix'}], expires_at: null,
    status: 'active', audience: 'recipients', content_mode: 'www', report_entrypoint: 'nested/report name.html', report_bundle_root: '',
    policy_revision: 3, include_patterns: ['**'], exclude_patterns: [], denied_emails: [], member_count: 1,
    live_prefix: true, can_manage: true, aliases: [],
    grants: [{grant_euid: 'grant-fixture', recipient_type: 'email', recipient: 'viewer@example.test', status: 'active',
      include_subdomains: false, include_patterns: ['**'], exclude_patterns: [], expires_at: null, target_euids: ['target-fixture']}], ...changes};
}

function sharingFixture({detail = share(), api} = {}) {
  const env = createEnvironment();
  env.apiCalls = []; env.renderCount = 0;
  env.load('sharing.js');
  env.sharing = env.context.DeweySharing;
  const defaultAPI = path => {
    if (path.includes('/contents?')) return {items: [{target_euid: 'target-fixture', name: 'report name.html', relative_key: 'nested/report name.html', size: 123}], incomplete: false, continuation_token: null};
    if (path.startsWith('/api/v1/registry/shares/')) return detail;
    return {euid: 'target-fixture', name: 'Report', kind: 'prefix'};
  };
  env.sharing.init({content: env.node('content'), setCurrent: value => { env.current = value; },
    modal: markup => { env.node('editor-body').innerHTML = markup; env.node('editor').showModal(); },
    render: async () => { env.renderCount++; },
    safe: async fn => { try { await fn(); } catch (error) { env.errors.push(error.message); } },
    api: async (path, method = 'GET', body) => { env.apiCalls.push({path, method, body: body === undefined ? undefined : plain(body)}); return (api || defaultAPI)(path, method, body); }});
  return env;
}

function policyForm(env, overrides = {}) {
  const form = env.node('managed-share-form');
  form.elements.share_indefinite.checked = true;
  for (const [name, value] of Object.entries(overrides)) form.elements[name].value = value;
  for (const row of form.querySelectorAll('[data-grant]')) {
    const prefix = 'g' + row.dataset.grant;
    form.elements[prefix + '_indefinite'].checked = true;
  }
  return form;
}

test('sharing editor creates registered-public WWW share with explicit indefinite lifetime and no anonymous grant', async () => {
  const env = sharingFixture({api: (path, method) => method === 'POST' ? {euid: 'new-share-fixture'} : {kind: 'prefix', name: '<script>report</script>'}});
  await env.sharing.editor('target-fixture');
  const form = policyForm(env, {audience: 'public_registered', content_mode: 'www', report_entrypoint: 'multiqc.html'});
  form.elements.g0_recipient.value = '';
  await env.submit('managed-share-form');
  const created = env.apiCalls.find(call => call.method === 'POST');
  assert.equal(created.body.expires_at, null);
  assert.deepEqual(created.body.grants, []);
  assert.deepEqual(created.body.allowed_users, []);
  assert.deepEqual(created.body.delivery_modes, ['gateway']);
  assert.equal(created.body.audience, 'public_registered');
  assert.equal(created.body.report_entrypoint, 'multiqc.html');
  assert.deepEqual(env.assigned, ['/shares/new-share-fixture']);
  assert.match(env.node('editor-body').innerHTML, /&lt;script&gt;report&lt;\/script&gt;/);
});

test('sharing editor preserves explicit domain/email scopes and null expiry when editing', async () => {
  const detail = share({grants: [share().grants[0], {...share().grants[0], grant_euid: 'domain-grant-fixture',
    recipient_type: 'domain', recipient: 'outside.example.test', include_subdomains: true}]});
  const env = sharingFixture();
  await env.sharing.editor('target-fixture', detail);
  const form = policyForm(env);
  form.elements.g0_targets.selectedOptions = [{value: 'target-fixture'}];
  await env.submit('managed-share-form');
  const updated = env.apiCalls.find(call => call.method === 'PATCH');
  assert.equal(updated.body.policy_revision, 3);
  assert.equal(updated.body.grants[0].grant_euid, 'grant-fixture');
  assert.deepEqual(updated.body.grants[0].target_euids, ['target-fixture']);
  assert.deepEqual(updated.body.allowed_domains, ['outside.example.test']);
  assert.equal(updated.body.grants[1].include_subdomains, true);
  assert.equal(env.renderCount, 1);
});

test('sharing editor resolves changed target IDs and submits typed target set at reviewed revision', async () => {
  const env = sharingFixture({api: (path, method) => method === 'GET' ? {kind: path.endsWith('new-fixture') ? 'object' : 'prefix'} : {euid: 'share-fixture'}});
  await env.sharing.editor('target-fixture', share());
  policyForm(env, {target_euids: 'target-fixture\nnew-fixture\nnew-fixture'});
  await env.submit('managed-share-form');
  const updated = env.apiCalls.find(call => call.method === 'PATCH');
  assert.deepEqual(updated.body.targets, [{target_kind: 'artifact_prefix', target_euid: 'target-fixture'}, {target_kind: 'artifact_object', target_euid: 'new-fixture'}]);
  assert.equal(updated.body.policy_revision, 3);
});

for (const [name, change, message] of [
  ['missing WWW entry', form => { form.elements.report_entrypoint.value = ''; }, /exact HTML entrypoint/],
  ['empty include policy', form => { form.elements.include_patterns.value = ''; }, /share-wide include/],
  ['blank named recipient', form => { form.elements.g0_recipient.value = ''; }, /Each grant needs/],
  ['email subdomain flag', form => { form.elements.g0_subdomains.checked = true; }, /only for domain grants/],
  ['zero targets', form => { form.elements.target_euids.value = ''; }, /at least one target/],
  ['removed scoped target', form => { form.elements.target_euids.value = 'other-fixture'; form.elements.g0_targets.selectedOptions = [{value: 'target-fixture'}]; }, /still selects a removed target/],
  ['invalid finite expiry', form => { form.elements.share_indefinite.checked = false; form.elements.share_offset.value = '+14:30'; }, /explicit UTC offset/],
  ['indefinite grant beyond finite share', form => { form.elements.share_indefinite.checked = false; }, /Grant expiry must not exceed/],
]) test(`sharing editor rejects ${name} without policy mutation`, async () => {
  const env = sharingFixture({api: () => ({kind: 'prefix'})});
  await env.sharing.editor('target-fixture', share({expires_at: new Date(Date.now() + 86400000).toISOString()}));
  const form = policyForm(env); change(form);
  await env.submit('managed-share-form');
  assert.ok(env.errors.some(value => message.test(value)), env.errors.join(';'));
  assert.equal(env.apiCalls.filter(call => call.method !== 'GET').length, 0);
  assert.equal(form.querySelector('button[type="submit"]').disabled, false);
});

test('sharing editor rejects missing target/revision and unsupported target kinds', async () => {
  const env = sharingFixture({api: () => ({kind: 'set'})});
  await assert.rejects(env.sharing.editor('target-fixture', share({targets: []})), /Persisted share targets/);
  await assert.rejects(env.sharing.editor('target-fixture', share({policy_revision: null})), /policy revision/);
  await env.sharing.editor('target-fixture', share());
  policyForm(env, {target_euids: 'set-fixture'});
  await env.submit('managed-share-form');
  assert.match(env.errors[0], /Object or Prefix EUIDs/);
});

test('duplicate share submission is suppressed and failed save reenables the form', async () => {
  const env = sharingFixture({api: async () => { throw Error('stale policy revision'); }});
  await env.sharing.editor('target-fixture', share());
  const form = policyForm(env);
  const event = {target: form, preventDefault() {}};
  form.onsubmit(event); form.onsubmit(event); await flush();
  assert.equal(env.apiCalls.length, 1);
  assert.equal(form._saving, false);
  assert.equal(form.querySelector('button[type="submit"]').disabled, false);
  assert.deepEqual(env.errors, ['stale policy revision']);
});

test('registered-public editor does not manufacture explicit email grants', async () => {
  const env = sharingFixture();
  await env.sharing.editor('target-fixture', share({audience: 'public_registered', grants: [{recipient_type: 'registered', status: 'active'}]}));
  policyForm(env);
  await env.submit('managed-share-form');
  assert.deepEqual(env.apiCalls[0].body.grants, []);
  await env.sharing.editor('target-fixture', share({grants: []}));
  policyForm(env);
  await env.submit('managed-share-form');
  assert.match(env.errors.at(-1), /at least one recipient grant/);
});

test('share pages render indefinite/public and expired policies without treating expiry null as expired', async () => {
  const detail = share({audience: 'public_registered', aliases: [{slug: 'friendly-fixture', status: 'active'}, {slug: 'retired-fixture', status: 'retired'}]});
  const env = sharingFixture({detail});
  await env.sharing.page('share-fixture');
  assert.match(env.node('content').innerHTML, /No expiry/);
  assert.match(env.node('content').innerHTML, /Public with registration/);
  assert.match(env.node('share-browser').innerHTML, /\/fetch\/share-fixture\/nested\/report%20name.html\?download=true/);
  assert.match(env.node('share-aliases').innerHTML, /friendly-fixture/);
  detail.status = 'revoked'; detail.can_manage = false;
  const before = env.apiCalls.length;
  await env.sharing.page('share-fixture');
  assert.equal(env.apiCalls.length, before + 1);
  assert.match(env.node('content').innerHTML, /no longer grants access/);
});

test('alias claim, copied report URL, permanent retirement and grant revoke carry reviewed revision', async () => {
  const env = sharingFixture(); await env.sharing.page('share-fixture');
  await env.sharing.handle('sharing-alias-add');
  env.node('alias-form').elements.slug.value = 'friendly-fixture'; await env.submit('alias-form');
  let mutation = env.apiCalls.find(call => call.path.endsWith('/aliases') && call.method === 'POST');
  assert.deepEqual(mutation.body, {slug: 'friendly-fixture', policy_revision: 3});
  await env.sharing.handle('sharing-alias-copy', 'friendly-fixture');
  assert.equal(env.copied[0], 'https://dewey.example.test/fetch/friendly-fixture/nested/report%20name.html');
  await env.sharing.handle('sharing-alias-retire', '<slug>');
  assert.match(env.node('editor-body').innerHTML, /&lt;slug&gt;/);
  await env.sharing.handle('sharing-alias-retire-confirmed', 'friendly-fixture');
  assert.deepEqual(env.apiCalls.at(-1).body, {policy_revision: 3});
  await env.sharing.handle('sharing-revoke-grant', 'grant fixture');
  env.node('grant-revoke-form').elements.reason.value = 'reviewed removal'; await env.submit('grant-revoke-form');
  assert.equal(env.apiCalls.at(-1).path, '/api/v1/registry/shares/share-fixture/grants/grant%20fixture/revoke');
  assert.deepEqual(env.apiCalls.at(-1).body, {reason: 'reviewed removal', policy_revision: 3});
  assert.equal(await env.sharing.handle('unrelated-action', ''), false);
});

test('audit UI freezes timestamp/digest across pages and exports only declared inventory completeness', async () => {
  const env = sharingFixture({api: path => path.includes('sharing-report') ? {metrics: {authorization_evaluations: 2}} :
    {page: Number(new URL(path, env.location.origin).searchParams.get('page')), items: [{share_euid: 'share-fixture'}], total: 2,
      observed_at: '2026-01-01T00:00:00Z', inventory_sha256: 'digest-fixture', has_more: !path.includes('page=2'), complete: false}});
  await assert.rejects(env.sharing.handle('sharing-audit-export'), /Load a report first/);
  await env.sharing.handle('sharing-audit');
  const form = env.node('sharing-audit-form');
  form.elements.never_accessed.checked = true; form.elements.audience.value = 'public_registered';
  form.elements.older_than_days.value = '7'; await env.submit('sharing-audit-form');
  await env.sharing.handle('sharing-audit-page', '2');
  const params = new URL(env.apiCalls.at(-1).path, env.location.origin).searchParams;
  assert.equal(params.get('observed_at'), '2026-01-01T00:00:00Z');
  assert.equal(params.get('expected_inventory_sha256'), 'digest-fixture');
  assert.equal(params.get('never_accessed'), 'true');
  assert.equal(params.get('page_size'), '100');
  await env.sharing.handle('sharing-audit-export');
  const exported = JSON.parse(await env.blobs.at(-1).text());
  assert.equal(exported.complete, false);
  assert.equal(exported.inventory_page.page, 2);
  assert.equal(form.querySelector('button').disabled, false);
});

test('audit request failure reenables submission instead of exporting a stale result', async () => {
  const env = sharingFixture({api: async () => { throw Error('inventory changed'); }});
  await env.sharing.handle('sharing-audit'); await env.submit('sharing-audit-form');
  assert.equal(env.node('sharing-audit-form').querySelector('button').disabled, false);
  assert.deepEqual(env.errors, ['inventory changed']);
  await assert.rejects(env.sharing.handle('sharing-audit-export'), /Load a report first/);
});

async function registryFixture(options = {}) {
  const env = createEnvironment(options);
  env.context.DeweySharing = {handle: async () => false, init: helpers => { env.helpers = helpers; }, editor: async () => {}};
  env.load('registry.js'); await flush();
  env.helpers.setCurrent({policy_revision: 7, report_entrypoint: 'nested/report name.html', location_revision: 2, capabilities: {share: true}});
  return env;
}

for (const entry of [null, 'nested/report name.html']) test(`manager copy-share retains canonical URL ${entry ? 'with deep path' : 'without report'}`, async () => {
  const env = await registryFixture(); env.helpers.setCurrent({report_entrypoint: entry});
  await env.click('copy-share', 'share fixture');
  assert.equal(env.copied[0], 'https://dewey.example.test/fetch/share%20fixture' + (entry ? '/nested/report%20name.html' : ''));
  assert.match(env.node('notice').textContent, /verified email/);
});

for (const result of [{status: 'accepted'}, {status: 'uncertain'}, {invitation_status: 'failed'}, {}])
test(`manager invitation surfaces actual delivery state ${JSON.stringify(result)}`, async () => {
  const env = await registryFixture({fetch: () => ({...result, operation_euid: 'invitation-fixture'})});
  await env.click('share-invite', 'share-fixture');
  env.node('invite-form').elements.email.value = 'viewer@example.test'; await env.submit('invite-form');
  assert.equal(env.calls[0].url, '/api/v1/registry/shares/share-fixture/invite');
  assert.match(env.node('notice').textContent, new RegExp(result.status || result.invitation_status || 'recorded'));
  assert.match(env.node('notice').textContent, /invitation-fixture/);
});

test('manager revoke carries current revision and opens report through selected managed share', async () => {
  const env = await registryFixture();
  await env.click('revoke', 'share-fixture');
  env.node('revoke-share-form').elements.reason.value = 'reviewed expiry'; await env.submit('revoke-share-form');
  assert.deepEqual(JSON.parse(env.calls[0].options.body), {reason: 'reviewed expiry', policy_revision: 7});
  await env.click('preview', 'artifact-fixture');
  assert.match(env.node('editor-body').innerHTML, /Create managed share/);
  await env.submit('select-report-share'); assert.deepEqual(env.assigned, []);
  env.node('select-report-share').elements.share_euid.value = 'share fixture'; await env.submit('select-report-share');
  assert.deepEqual(env.assigned, ['/shares/share%20fixture']);
  env.helpers.setCurrent({capabilities: {share: false}}); await env.click('preview', 'artifact-fixture');
  assert.doesNotMatch(env.node('editor-body').innerHTML, /Create managed share/);
});

for (const version of ['', 'version-fixture']) test(`manager rebind posts reviewed location revision and ${version ? 'explicit' : 'null'} version`, async () => {
  const env = await registryFixture(); await env.click('location-rebind', 'artifact fixture');
  const form = env.node('rebind-form');
  form.elements.storage_uri.value = 's3://fixture-bucket/equivalent'; form.elements.version_id.value = version;
  form.elements.reason.value = 'verified equivalent'; await env.submit('rebind-form');
  assert.deepEqual(JSON.parse(env.calls[0].options.body), {storage_uri: 's3://fixture-bucket/equivalent', version_id: version || null,
    reason: 'verified equivalent', expected_location_revision: 2});
  assert.equal(form.querySelector('button').disabled, false);
});

test('manager rebind refuses missing current revision or blank reason before sending mutation', async () => {
  const env = await registryFixture(); env.helpers.setCurrent({location_revision: null});
  await env.click('location-rebind', 'artifact-fixture'); assert.match(env.node('notice').textContent, /revision is unavailable/);
  env.helpers.setCurrent({location_revision: 3}); await env.click('location-rebind', 'artifact-fixture');
  await env.submit('rebind-form');
  assert.match(env.node('notice').textContent, /reason is required/);
  assert.equal(env.calls.length, 0);
  assert.equal(env.node('rebind-form').querySelector('button').disabled, false);
});

for (const lifetime of ['0', '31', '1.5', 'not-a-number']) test(`manager token lifetime ${lifetime} is rejected before issuance`, async () => {
  const env = await registryFixture(); await env.click('token-create');
  env.node('token-form').elements.lifetime_days.value = lifetime; await env.submit('token-form');
  assert.equal(env.calls.length, 0);
  assert.match(env.node('notice').textContent, /1–30 days/);
});

for (const lifetime of ['1', '30']) test(`manager token lifetime boundary ${lifetime} sends intended role and escapes one-use display`, async () => {
  const env = await registryFixture({fetch: () => ({token: '<credential-fixture>', expires_at: 'future'})});
  await env.click('token-create');
  env.node('token-form').elements.lifetime_days.value = lifetime; await env.submit('token-form');
  assert.equal(JSON.parse(env.calls[0].options.body).lifetime_days, Number(lifetime));
  assert.equal(JSON.parse(env.calls[0].options.body).role, 'READ_ONLY');
  assert.match(env.node('editor-body').innerHTML, /&lt;credential-fixture&gt;/);
});

test('sharing index displays no-expiry and expired rows and provides audit entry', async () => {
  const env = await registryFixture({section: 'Sharing', fetch: () => ({items: [
    {euid: 'indefinite-fixture', name: 'Indefinite', expires_at: null, status: 'active', audience: 'recipients', content_mode: 'www'},
    {euid: 'expired-fixture', name: 'Expired', expires_at: '2000-01-01', status: 'active', audience: 'public_registered'},
    {euid: 'revoked-fixture', name: 'Revoked', expires_at: '2099-01-01', status: 'revoked', audience: 'recipients'},
  ], page: 1, pages: 1, total: 3})});
  assert.match(env.node('content').innerHTML, /No expiry/);
  assert.match(env.node('content').innerHTML, /expired/);
  assert.match(env.node('content').innerHTML, /Sharing audit report/);
});

for (const canEdit of [false, true]) test(`record exposes storage rebind only when edit capability is ${canEdit}`, async () => {
  const env = await registryFixture({section: 'Record', fetch: () => ({kind: 'object', storage_backend: 's3',
    name: 'Synthetic', owner: 'owner-fixture', created_at: '2026-01-01', storage_uri: 's3://fixture-bucket/file',
    size: 1, content_type: 'text/plain', capabilities: {download: true, share: false, edit: canEdit, owner: false}})});
  assert.equal(env.document.toolbarActions.innerHTML.includes('Rebind location'), canEdit);
});
