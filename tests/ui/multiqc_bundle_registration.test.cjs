const test = require('node:test');
const assert = require('node:assert/strict');
const {createEnvironment, flush} = require('./dom_fixture.cjs');

function registry(responder) {
  const env=createEnvironment({section:'Admin',fetch:responder});
  env.context.DeweySharing={init(){},handle:async()=>false};
  env.load('registry.js');
  return env;
}

test('full HTML inventory is reviewed before any bundle repair and blocked records are retained',async()=>{
  const env=registry((url,options)=>{
    if(url==='/api/v1/registry/admin')return {version:'fixture',bucket_registry:[]};
    if(url.startsWith('/api/v1/admin/'))return {items:[],page:1};
    if(url.includes('multiqc-candidates'))return {items:[{euid:'bundle'},{euid:'standalone'},{euid:'other'},{euid:'missing'}],has_more:false};
    if(options.method==='POST')return {registration_changed:true,shares:[{status:'repaired'}]};
    if(url.includes('/missing/'))return {status:400,body:{detail:'missing report asset'}};
    return {bundle:url.includes('/other/')?null:{mode:url.includes('/standalone/')?'standalone':'bundle'},bundle_digest:'d'.repeat(64),shares:[]};
  });
  await flush();await env.click('multiqc-bundles');
  assert.equal(env.node('multiqc-repair').disabled,true);
  await env.node('multiqc-review').onclick();await flush();
  assert.equal(env.calls.filter(c=>c.options.method==='POST').length,0);
  const plans=JSON.parse(env.node('multiqc-results').textContent);
  assert.deepEqual(plans.map(p=>p.status),['reviewed','standalone','other_html','blocked']);
  assert.equal(env.node('multiqc-repair').disabled,false);
  await env.node('multiqc-repair').onclick();await flush();
  const writes=env.calls.filter(c=>c.options.method==='POST');
  assert.equal(writes.length,2);
  assert.ok(writes.every(c=>JSON.parse(c.options.body).expected_bundle_digest==='d'.repeat(64)));
  assert.ok(writes.every(c=>JSON.parse(c.options.body).repair_shares===true));
  assert.equal(JSON.parse(env.node('multiqc-results').textContent)[3].error,'missing report asset');
});

test('new MultiQC share uses saved report path and bundle without recipient configuration',async()=>{
  const env=createEnvironment();let hooks;
  env.load('sharing.js');
  env.context.DeweySharing.init({api:async path=>path.includes('share-expiry-policy')?{creator:{email:'owner@lsmc.com',email_verified:true,service:false}}:{kind:'object',name:'Renamed report',report_bundle:{entrypoint:'actual.html',include_patterns:['actual.html','actual_files/**']}},
    modal:html=>{env.node('editor-body').innerHTML=html;},safe:async fn=>fn(),render:async()=>{},content:env.node('content'),setCurrent(){}});
  await env.context.DeweySharing.editor('report-euid');await flush();
  const form=env.node('managed-share-form');
  assert.equal(form.elements.content_mode.value,'www');
  assert.equal(form.elements.report_entrypoint.value,'actual.html');
  assert.match(env.node('editor-body').innerHTML,/supporting assets come from the saved MultiQC registration/);
});
