// Focused native UI capture: no browser, network, or email.
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
let html='',days=null,calls=[];
const form={elements:{},addEventListener(){},querySelectorAll(){return [];}};
const context={window:{},document:{querySelector(){return form;}},Intl,Date,console};
vm.runInNewContext(fs.readFileSync('dewey_service/static/sharing.js','utf8'),context);
context.window.DeweySharing.init({api:async path=>{calls.push(path);return path.endsWith('/defaults')?{share_lifetime_days:days}:{kind:'object',name:'Captured object'};},modal:markup=>{html=markup;}});
(async()=>{
 await context.window.DeweySharing.editor('capture-object');
 assert.match(html,/name="share_indefinite" checked/);
 assert.match(html,/name="g0_indefinite" checked/);
 assert.match(html,/name="share_local"[^>]*value=""/);
 assert(calls.includes('/api/v1/registry/defaults'));
 days=5;await context.window.DeweySharing.editor('capture-object');
 assert.doesNotMatch(html,/name="share_indefinite" checked/);
 const finite=new Date(Date.now()+86400000).toISOString();calls=[];
 await context.window.DeweySharing.editor('capture-object',{expires_at:null,targets:[{euid:'capture-object',name:'Captured'}],policy_revision:1,grants:['lsmc.com','lsmc.bio','external.example'].map(recipient=>({status:'active',recipient_type:'domain',recipient,expires_at:finite}))});
 assert.match(html,/name="share_indefinite" checked/);
 for(let i=0;i<3;i++)assert.doesNotMatch(html,new RegExp(`name="g${i}_indefinite" checked`));
 assert(!calls.includes('/api/v1/registry/defaults'));
 await context.window.DeweySharing.editor('capture-object',{expires_at:finite,targets:[{euid:'capture-object',name:'Captured'}],policy_revision:1,grants:[]});
 assert.doesNotMatch(html,/name="share_indefinite" checked/);
 const source=fs.readFileSync('dewey_service/static/registry.js','utf8');new vm.Script(source);
 const conversion=source.match(/for\(const key of Object.keys\(data\)\)data\[key\]=[^;]+;/)[0];
 const capture={data:{share_lifetime_days:'',delivery_lifetime_seconds:'900',listing_cache_ttl_seconds:'30'}};
 vm.runInNewContext(conversion,capture);assert.equal(capture.data.share_lifetime_days,null);assert.equal(capture.data.delivery_lifetime_seconds,900);
 capture.data={share_lifetime_days:'14'};vm.runInNewContext(conversion,capture);assert.equal(capture.data.share_lifetime_days,14);
 console.log(JSON.stringify({status:'PASS',new_default_none:true,native_finite_default:true,existing_finite_editor_preserved:true,three_domain_finite_grant_editors:true,blank_default_serializes_null:true,numeric_default_serializes_integer:true,network_calls:0}));
})().catch(error=>{console.error(error);process.exitCode=1;});
