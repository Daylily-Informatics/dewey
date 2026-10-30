// Focused native UI policy capture, no browser/network/mail.
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const source=fs.readFileSync('dewey_service/static/sharing.js','utf8');
const context={window:{},document:{},Intl,Date,console};
const instrumented=source.replace('return {init:helpers=>{h=helpers;},editor,page,handle};','return {scopedLifetime,expiry,expiryMarkup,updateExpiry,localValue,offsetValue,init:helpers=>{h=helpers;},editor,page,handle};');
assert.notEqual(instrumented,source);vm.runInNewContext(instrumented,context);
const ui=context.window.DeweySharing,checks=[];
function check(name,value){assert(value,name);checks.push(name);}
const internal={email:'owner@lsmc.com',email_verified:true,service:false},outside={email:'x@example.net',email_verified:true,service:false};
const cases=[['exact internal email',internal,{audience:'recipients',grants:[{recipient_type:'email',recipient:'reader@lsmc.bio'}]},true],['exact internal domains',internal,{audience:'recipients',grants:[{recipient_type:'domain',recipient:'lsmc.com'},{recipient_type:'domain',recipient:'lsmc.bio'}]},true],['mixed',internal,{audience:'recipients',grants:[{recipient_type:'email',recipient:'reader@lsmc.bio'},{recipient_type:'email',recipient:'x@example.net'}]},false],['external creator',outside,{audience:'recipients',grants:[{recipient_type:'email',recipient:'reader@lsmc.bio'}]},false],['subdomain',internal,{audience:'recipients',grants:[{recipient_type:'domain',recipient:'lab.lsmc.com'}]},false],['include subdomains',internal,{audience:'recipients',grants:[{recipient_type:'domain',recipient:'lsmc.bio',include_subdomains:true}]},false],['public registration',internal,{audience:'public_registered',grants:[{recipient_type:'domain',recipient:'lsmc.bio'}]},false],['unverified creator',{...internal,email_verified:false},{audience:'recipients',grants:[{recipient_type:'domain',recipient:'lsmc.bio'}]},false],['service creator',{...internal,service:true},{audience:'recipients',grants:[{recipient_type:'domain',recipient:'lsmc.bio'}]},false]];
for(const[name,creator,data,expected]of cases){const result=ui.scopedLifetime(creator,data);check('native UI scope '+name,result.indefinite_allowed===expected&&result.default_lifetime_days===(expected?null:14)&&result.max_lifetime_days===(expected?null:365));}
function form({creator=internal,recipient='reader@lsmc.bio',existing=false,checked=false,days=14}={}){
 const d=new Date(Date.now()+days*86400000),outputs=[{dataset:{expiry:'share'},classList:{add(){},remove(){}}}],note={};
 const elements={audience:{value:'recipients'},share_indefinite:{checked},share_local:{value:ui.localValue(d)},share_offset:{value:ui.offsetValue(d)},g0_type:{value:'email'},g0_recipient:{value:recipient},g0_subdomains:{checked:false}};
 return {elements,_sharing:{creator,existing,expiryTouched:false},querySelectorAll:s=>s==='[data-grant]'?[{dataset:{grant:'0'}}]:outputs,querySelector:()=>note,outputs,note};
}
let f=form();ui.updateExpiry(f);check('new eligible internal share auto noexpiry',f.elements.share_indefinite.checked&&f._expiryScope.indefinite_allowed);
f.elements.g0_recipient.value='outside@example.net';ui.updateExpiry(f);check('switch to external forces finite14day and disables infinity',!f.elements.share_indefinite.checked&&f.elements.share_indefinite.disabled&&!f._expiryScope.indefinite_allowed&&Math.abs(new Date(ui.expiry(f,'share')).getTime()-Date.now()-14*86400000)<3000);
f=form({existing:true,checked:false,days:800});ui.updateExpiry(f);check('existing internal finite800days retained',!f.elements.share_indefinite.checked&&new Date(ui.expiry(f,'share'))>new Date(Date.now()+799*86400000));
f=form({creator:outside,checked:true});ui.updateExpiry(f);check('original external creator stays bounded in editor',!f.elements.share_indefinite.checked&&!f._expiryScope.indefinite_allowed);
f=form({creator:outside,days:366});ui.updateExpiry(f);let rejected=false;try{ui.expiry(f,'share');}catch(e){rejected=/365/.test(e.message);}check('UI rejects bounded expiry beyond365days',rejected);
f=form({creator:outside,checked:true});f._expiryScope={indefinite_allowed:false,max_lifetime_days:365};rejected=false;try{ui.expiry(f,'share');}catch(e){rejected=/original verified internal/.test(e.message);}check('UI rejects explicit null for bounded scope',rejected);
const admin=fs.readFileSync('dewey_service/static/registry.js','utf8'),template=fs.readFileSync('dewey_service/templates/admin.html','utf8');new vm.Script(admin);
check('native admin dialog has no mutable global lifetime field',!admin.includes('field("share_lifetime_days"'));
check('native admin JS describes both scopes',admin.includes('original verified creator')&&admin.includes('maximum 365'));
check('native server admin template describes both scopes',template.includes('original creator')&&template.includes('14 days by default, maximum 365 days'));
check('revive UI requires explicit recipient selections',source.includes('name="reauthorize"')&&source.includes('Explicitly reauthorize the public-with-registration audience')&&source.includes('Old aliases and delivery contexts remain invalid'));
check('existing policy exceptions visibly require explicit review',source.includes('Existing no-expiry policy does not meet the current creator/audience rules'));
const receipt={observed_at:new Date().toISOString(),status:'PASS',checks,check_count:checks.length,network_calls:0,mail_sends:0,source:'dewey_service/static/sharing.js',limits:['Native UI functions evaluated in captured DOM; deployed browser acceptance remains separate.']};fs.writeFileSync('docs/plans/evidence/20261027_scoped_share_expiry/ui_capture_receipt.json',JSON.stringify(receipt,null,2)+'\n');console.log(JSON.stringify(receipt,null,2));
