const test = require('node:test');
const assert = require('node:assert/strict');
const {createEnvironment, flush} = require('./dom_fixture.cjs');

const root = 's3://fixture/docs/';
const stamp = '2026-07-11T04:36:36+00:00';
const items = [
  {kind:'object',name:'z.tsv',uri:root+'z.tsv',size:100,etag:'multi-2',storage_class:'GLACIER',last_modified:stamp,euid:'Z-file'},
  {kind:'object',name:'a.tsv',uri:root+'a.tsv',size:9,etag:'single',storage_class:'STANDARD',last_modified:'2026-01-01T00:00:00Z'},
  {kind:'prefix',name:'known/',uri:root+'known/',marker_last_modified:stamp},
  {kind:'prefix',name:'unknown/',uri:root+'unknown/'},
];
function setup(rows=items, next=null) {
  const env=createEnvironment({section:'S3 Browser',fetch:url=>{
    if(url.includes('continuation_token=next'))return {root_uri:root,items:[{kind:'object',name:'b.tsv',uri:root+'b.tsv',size:15}],breadcrumbs:[],next_continuation_token:null};
    if(url.startsWith('/api/v1/storage/object'))return {uri:new URL(url,'https://fixture.test').searchParams.get('uri')};
    assert.ok(url.startsWith('/api/v1/storage/browse?'));
    return {root_uri:root,items:structuredClone(rows),breadcrumbs:[{label:'fixture',uri:root}],next_continuation_token:next};
  }});
  env.location.search='?uri='+encodeURIComponent(root);
  env.context.DeweySharing={init(){},handle:async()=>false};
  env.load('registry.js');return env;
}
const order=html=>[...html.matchAll(/data-storage-index="(\d+)"/g)].map(m=>Number(m[1]));
async function filter(env,value) {
  for(const handler of env.document.listeners.input||[])handler({target:{id:'storage-name-filter',value}});
  await flush();
}

test('metadata, marker meaning, local ascending/descending numeric sorting and exact URI copy',async()=>{
  const env=setup();await flush();
  const html=env.node('content').innerHTML;
  assert.match(html,/2026-07-11 04:36:36 UTC/);
  assert.match(html,/\(2026-07-11 04:36:36 UTC\)/);
  assert.match(html,/Unknown/);assert.match(html,/GLACIER/);assert.match(html,/multi-2/);
  assert.match(html,/ETag is not necessarily an MD5/);
  assert.match(html,/Copy S3 URI for z.tsv/);
  assert.doesNotMatch(html,/data-action="(?:delete|replace)/);
  await env.click('storage-sort','size');
  assert.deepEqual(order(env.node('storage-table').innerHTML),[1,0,2,3]);
  assert.match(env.node('storage-table').innerHTML,/aria-sort="ascending"/);
  await env.click('storage-sort','size');
  assert.deepEqual(order(env.node('storage-table').innerHTML),[0,1,2,3]);
  assert.match(env.node('storage-table').innerHTML,/aria-sort="descending"/);
  for(const key of ['kind','name','modified','storage_class','etag','euid','uri']) {
    await env.click('storage-sort',key);await env.click('storage-sort',key);
  }
  await env.click('storage-copy','0');
  assert.deepEqual(env.copied,[root+'z.tsv']);
  assert.equal(env.calls.length,1);
});

test('TSV exports the loaded filtered sorted view with safe tabs newlines and quotes, without fetching',async()=>{
  const name='a\t"quoted"\nfile.tsv';
  const env=setup([...items,{kind:'object',name,uri:root+name,size:12,etag:'"etag"'}],'next');
  await flush();await env.click('storage-sort','size');await filter(env,'.tsv');
  await env.click('storage-export');
  const tsv=await env.blobs[0].text();
  assert.ok(tsv.startsWith('Kind\tName\tSize (bytes)\tLast modified (UTC)'));
  assert.ok(tsv.includes('"a\t""quoted""\nfile.tsv"'));
  assert.ok(tsv.includes('"s3://fixture/docs/a\t""quoted""\nfile.tsv"'));
  assert.ok(tsv.indexOf('a.tsv')<tsv.indexOf('"a\t'));
  assert.ok(tsv.indexOf('"a\t')<tsv.indexOf('z.tsv'));
  assert.ok(!tsv.includes('unknown/'));
  assert.equal(env.calls.length,1);assert.equal(env.document.clicks.at(-1).download,'dewey-s3-view.tsv');
  assert.match(env.node('storage-table').innerHTML,/Showing 3 of 5 loaded rows. More pages available/);
});

test('loading another page preserves local sort/filter and original row actions',async()=>{
  const env=setup(items,'next');await flush();
  await filter(env,'.tsv');await env.click('storage-sort','size');
  await env.click('storage-next','next');
  assert.equal(env.calls.length,2);
  assert.match(env.node('storage-list').innerHTML,/value=".tsv"/);
  assert.deepEqual(order(env.node('storage-list').innerHTML),[1,4,0]);
  await env.click('storage-copy','4');assert.deepEqual(env.copied,[root+'b.tsv']);
  await env.click('storage-export');const tsv=await env.blobs[0].text();
  assert.ok(tsv.indexOf('a.tsv')<tsv.indexOf('b.tsv')&&tsv.indexOf('b.tsv')<tsv.indexOf('z.tsv'));
  assert.equal(env.calls.length,2);
  await env.click('object','0');
  assert.ok(env.calls.at(-1).url.endsWith(encodeURIComponent(root+'z.tsv')));
});

test('new-file upload UI has no replacement path',async()=>{
  const env=setup();await flush();await env.click('upload',root);
  const html=env.node('editor-body').innerHTML;
  assert.match(html,/Existing objects cannot be replaced or deleted, including by administrators/);
  assert.doesNotMatch(html,/Exact replacement|Admin replacement/);
});
