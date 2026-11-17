// Playwright test: plays a whole narrated reel at N x speed and reports stalls. node test-reel-play.js <topic> <rate> [chapter-with-broken-audio]; needs test.html and webm copies of the narration in ../narr/webm
const { chromium } = require('playwright');const fs=require('fs');
const id=process.argv[2]||'vte',rate=+(process.argv[3]||8),breakCh=process.argv[4]||'';
(async()=>{const b=await chromium.launch({args:['--autoplay-policy=no-user-gesture-required']});const pg=await b.newPage({viewport:{width:1100,height:800}});const errs=[];pg.on('pageerror',e=>errs.push(e.message));
const pack=JSON.parse(fs.readFileSync('/home/user/afp-cme-quizzes/shlav-b/packs/'+id+'.json','utf8'));const W=process.cwd()+'/../narr/webm/';
pack.reel.chapters.forEach(c=>{if(c.narr)c.narr.src=c.id===breakCh?'file:///nope/missing.webm':'file://'+W+id+'-'+c.id+'.webm';});
const U='file://'+process.cwd()+'/test.html';await pg.goto(U+'#t-'+id);await pg.reload();await pg.waitForTimeout(200);
await pg.evaluate(p=>{PACKS[p.id]=p;render();},pack);await pg.click('.mode.reel');await pg.waitForTimeout(300);
await pg.evaluate(()=>{const r=document.getElementById('reelScrub');r.value=0;r.dispatchEvent(new Event('input'));});
await pg.click('.pbtn');await pg.evaluate(r=>{const a=REEL._aud;a.defaultPlaybackRate=r;a.playbackRate=r;a.addEventListener('loadedmetadata',()=>{a.playbackRate=r;});a.addEventListener('play',()=>{a.playbackRate=r;});},rate);
const N=pack.reel.chapters.length;let last=-1,lastChange=Date.now(),stalls=[],trans=[],t0=Date.now(),prevCh=0,samples=0,back=0;
while(true){await pg.waitForTimeout(200);samples++;
  const s=await pg.evaluate(()=>({v:+document.getElementById('reelScrub').value,playing:document.querySelector('.pbtn').getAttribute('aria-label')==='השהה'}));
  if(s.v<last-5)back++;
  if(s.v!==last){if(Date.now()-lastChange>1500&&last>=0)stalls.push({at:last,ms:Date.now()-lastChange});last=s.v;lastChange=Date.now();}
  const chN=Math.floor(s.v/1000);if(chN!==prevCh){trans.push({ch:chN,s:((Date.now()-t0)/1000).toFixed(1)});prevCh=chN;}
  if(!s.playing)break;if(Date.now()-t0>400000){console.log('timeout');break;}}
const expect=pack.reel.chapters.reduce((a,c)=>a+(c.narr?c.narr.dur:11),0)/rate;
console.log(JSON.stringify({id,end:last,N,secs:((Date.now()-t0)/1000).toFixed(1),expectSecs:expect.toFixed(1),transitions:trans.length,stalls,backwards:back,errs}));
await b.close();})();
