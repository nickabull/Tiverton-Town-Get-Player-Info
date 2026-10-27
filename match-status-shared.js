/* Shared pitch inspection presentation. No status changes automatically at inspection time. */
(function(root){'use strict';
 const endpoint='https://tivvy-match-status.lucy-bull-5102.chatgpt.site/api/status';
 const escape=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
 const key=f=>JSON.stringify([f.id,f.date,f.opposition,f.homeAway,f.competition,f.kickOff]);
 function noticeFor(f,notices){return notices.find(n=>n.fixtureId===f.id&&n.fixtureKey===key(f)&&['pending','passed','failed'].includes(n.status)&&!(String(f.result||'').match(/^\s*[WDL]\s+\d/)))||null;}
 function message(n,f){
  if(!n)return '';
  if(n.status==='passed')return '✅ Game on — passed pitch inspection';
  if(n.status==='failed')return '❌ Game off — failed pitch inspection';
  if(n.status==='pending'){
   const d=new Date(n.inspectionAt);if(!Number.isFinite(d.getTime()))return '';
   const day=d.toLocaleDateString('en-CA',{timeZone:'Europe/London'}),time=d.toLocaleTimeString('en-GB',{timeZone:'Europe/London',hour:'2-digit',minute:'2-digit'});
   const date=new Intl.DateTimeFormat('en-GB',{timeZone:'Europe/London',day:'numeric',month:'short'}).format(d);
   return '⚠️ Pending pitch inspection at '+time+(day===f.date?'':' on '+date);
  }return '';
 }
 function markup(n,f){const text=message(n,f);if(!text)return '';const d=new Date(n.updatedAt),updated=n.updatedAt&&Number.isFinite(d.getTime())?'Updated '+d.toLocaleString('en-GB',{timeZone:'Europe/London',day:'numeric',month:'short',hour:'2-digit',minute:'2-digit'})+' (UK time)':'';return '<div class="inspection-notice inspection-'+escape(n.status)+'" role="status"><strong>'+escape(text)+'</strong>'+(updated?'<small>'+escape(updated)+'</small>':'')+'</div>';}
 function selectNext(fixtures,notices,kickoff,now=Date.now()){
  return fixtures.filter(f=>{
   const n=noticeFor(f,notices),t=kickoff(f);
   if(n&&['pending','failed'].includes(n.status)&&t+86400000>now)return true;
   return !String(f.result||'').trim()&&t>now;
  }).sort((a,b)=>kickoff(a)-kickoff(b))[0];
 }
 const api={endpoint,key,noticeFor,message,markup,selectNext};
 if(typeof module==='object'&&module.exports)module.exports=api;else root.TivvyMatchStatus=api;
})(typeof globalThis==='object'?globalThis:this);
