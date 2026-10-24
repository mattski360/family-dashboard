#!/usr/bin/env python3
"""Meal planner v1 (live landscape): 'Tonight' card + full-screen week planner. Library: data/dashboard.json -> meals.library
[{name, emoji, tags}]. Plan lives in localStorage 'dash-meals:<weekStartSunday>' = {YYYY-MM-DD: mealName} (one object per
week, so it can move to a Cloudflare Worker + KV later with the same key/value shape)."""
import json

CSS = r"""
#mlcard{order:-1;flex:none;margin-right:auto;align-self:center;display:flex;align-items:center;gap:.7rem;border:0;cursor:pointer;font-family:inherit;
  background:#F4F1FA;color:#4B3F72;border-radius:1.2rem;padding:0 1.1rem;height:max(60px,7vh);max-width:34vw;text-align:left;touch-action:manipulation}
#mlcard .me{font-size:max(26px,3vh)}#mlcard .mt{display:flex;flex-direction:column;line-height:1.2;min-width:0}
#mlcard b{font-size:max(17px,1.9vh);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
#mlcard small{font-size:max(13px,1.35vh);font-weight:700;opacity:.7;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
#mlcard .tp{color:#8B7BC0;font-style:italic}
.day .dml{flex:none;display:flex;align-items:center;gap:.25rem;margin:.1rem 0 .3rem;background:#F4F1FA;color:#4B3F72;border-radius:.6rem;padding:.22rem .45rem;font-size:.72rem;font-weight:800;line-height:1.2;min-width:0;overflow:hidden;white-space:nowrap}
.day .dml span{min-width:0;overflow:hidden;text-overflow:ellipsis}
#mlp button{font-size:1em;height:auto;box-shadow:none}
#mlp{position:fixed;inset:0;z-index:25;display:none;background:rgba(40,48,68,.38);align-items:center;justify-content:center;padding:1.6vh 1.4vw}
#mlp.on{display:flex}
#mlp .mc{position:relative;width:100%;height:100%;background:#FBFCFE;border-radius:2.2vh;box-shadow:0 2vh 6vh rgba(0,0,0,.25);display:flex;flex-direction:column;
  overflow:hidden;font-size:clamp(15px,1.85vh,24px);color:#283044;font-family:inherit;padding:1.4vh 1.6vw;gap:1.4vh}
#mlp .x{position:absolute;top:1vh;right:1vw;width:max(60px,6.5vh);height:max(60px,6.5vh);border-radius:50%;border:0;background:#EEF0F4;color:#283044;font-size:max(30px,3.4vh);cursor:pointer;line-height:1;z-index:2}
#mlp .mh{display:flex;align-items:center;gap:1vw;padding-right:max(70px,7.5vh);flex:none;flex-wrap:wrap}
#mlp .mh h2{font-size:1.75em;font-weight:900}
#mlp .mh .wr{color:#69718a;font-weight:700}
#mlp .acts{margin-left:auto;display:flex;gap:.6vw;flex-wrap:wrap}
#mlp button.a{border:0;border-radius:999px;padding:.55em 1.1em;font-family:inherit;font-weight:800;font-size:.95em;background:#EEF0F4;color:#283044;cursor:pointer;min-height:48px}
#mlp button.a.wk{background:#E4EEFF;color:#245A9E}#mlp button.a.clr{background:#FFE3E0;color:#B23A2E}
#mlp .days7{flex:1;min-height:0;display:grid;grid-template-columns:repeat(7,minmax(0,1fr));gap:.8vw}
#mlp .dt{font-size:1.45em;border:2.5px solid #E6E9F0;background:#fff;border-radius:1.8vh;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:1vh;
  cursor:pointer;font-family:inherit;color:inherit;padding:1vh .5vw;text-align:center}
#mlp .dt.today{border-color:#F2B630;background:#FFF6DA}
#mlp .dt .dw{font-weight:900;font-size:1.1em;text-transform:uppercase;letter-spacing:.06em;color:#69718a}
#mlp .dt .dd{font-size:.9em;color:#69718a;font-weight:700}
#mlp .dt .de{font-size:3.4em;line-height:1}
#mlp .dt .dm{font-weight:800;font-size:1.15em}
#mlp .dt.empty .dm{color:#A9AFBF;font-style:italic;font-weight:700}
#mlk{position:absolute;inset:0;background:#FBFCFE;display:none;flex-direction:column;padding:1.4vh 1.6vw;gap:1.2vh;z-index:1}
#mlk.on{display:flex}
#mlk .kh{display:flex;align-items:center;gap:1vw;flex-wrap:wrap;padding-right:max(70px,7.5vh)}
#mlk .kh h3{font-size:1.6em;font-weight:900}
#mlk .chips{display:flex;gap:.5vw;flex-wrap:wrap}
#mlk .chip{border:2px solid #D9DEE8;background:#fff;border-radius:999px;padding:.45em 1em;font-family:inherit;font-weight:800;font-size:.95em;cursor:pointer;min-height:48px;color:#283044}
#mlk .chip.on{background:#283044;color:#fff;border-color:#283044}
#mlk .grid{flex:1;min-height:0;overflow-y:auto;display:grid;grid-template-columns:repeat(auto-fill,minmax(max(190px,15vw),1fr));grid-auto-rows:max(96px,11vh);gap:.8vw;align-content:start}
#mlk .mb{position:relative;border:2.5px solid #E6E9F0;background:#fff;border-radius:1.6vh;display:flex;align-items:center;gap:.7em;padding:0 1vw;font-family:inherit;font-weight:800;font-size:1.15em;
  ;color:inherit;cursor:pointer;text-align:left}
#mlk .mb .e{font-size:1.9em}#mlk .mb.bi{background:#F4F6FA}
#mlk .mb.sel{border-color:#3DB97B;background:#E9F8F0}
#mlk .mb.used{opacity:.55}
#mlk .mb .bd{position:absolute;top:.4em;right:.5em;font-size:.62em;font-weight:800;background:#EEF0F4;color:#69718a;border-radius:999px;padding:.15em .6em}
#mlk .sec{grid-column:1/-1;font-size:.8em;font-weight:900;letter-spacing:.07em;text-transform:uppercase;color:#69718a;align-self:end}
"""

JS = r"""
var LIB=__LIB__,TZ='America/Denver',DOW=['Sun','Mon','Tue','Wed','Thu','Fri','Sat'];
var BUILTIN=[{name:'Leftovers',emoji:'\uD83E\uDD61',tags:['quick']},{name:'Eat Out / Pizza',emoji:'\uD83C\uDF55',tags:[]},{name:'Fend for Yourself',emoji:'\uD83E\uDD37',tags:['quick']}];
var FILTERS=[['all','All'],['quick','Quick'],['crockpot','Crockpot'],['grill','Grill'],['kids','Kids\u2019 pick']];
function todayISO(){var o={};new Intl.DateTimeFormat('en-US',{timeZone:TZ,year:'numeric',month:'2-digit',day:'2-digit'}).formatToParts(new Date()).forEach(function(p){o[p.type]=p.value});return o.year+'-'+o.month+'-'+o.day;}
function D(s){return new Date(s+'T00:00:00Z')}function I(d){return d.toISOString().slice(0,10)}function add(s,n){var d=D(s);d.setUTCDate(d.getUTCDate()+n);return I(d)}
function sun(s){return add(s,-D(s).getUTCDay())}
function KEY(w){return 'dash-meals:'+w}
function load(w){try{return JSON.parse(localStorage.getItem(KEY(w))||'{}')||{}}catch(e){return {}}}
function save(w,o){try{localStorage.setItem(KEY(w),JSON.stringify(o))}catch(e){}tiles();}
var tilesSig=null;function tiles(){var sig=[],els=document.querySelectorAll('.day[data-date]');for(var i=0;i<els.length;i++){var el=els[i],d=el.getAttribute('data-date'),m=meal(planned(d)),x=el.querySelector('.dml');
  if(!m){if(x)x.remove();continue}sig.push(d+m.name);var h='\uD83C\uDF7D\uFE0F '+m.emoji+' <span>'+esc(m.name)+'</span>';if(!x){x=document.createElement('div');x.className='dml';var aw=el.querySelector('.away');el.insertBefore(x,aw||null)}
  if(x.innerHTML!==h){x.innerHTML=h;x.title=m.name}}sig=sig.join('|');if(sig!==tilesSig){var first=tilesSig===null;tilesSig=sig;if(!first||sig)window.dispatchEvent(new Event('resize'))}}
window.dashMealTiles=tiles;window.addEventListener('storage',function(e){if(!e.key||e.key.indexOf('dash-meals:')===0){tiles();card()}});
function meal(n){var all=LIB.concat(BUILTIN);for(var i=0;i<all.length;i++)if(all[i].name===n)return all[i];return n?{name:n,emoji:'\uD83C\uDF7D\uFE0F',tags:[]}:null}
function planned(s){return load(sun(s))[s]||''}
function esc(t){return String(t).replace(/[&<>"]/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]})}
var mlp,mlk,wk,pday,filt='all';
function card(){tiles();var c=document.getElementById('mlcard');if(!c)return;var t=todayISO(),a=meal(planned(t)),b=meal(planned(add(t,1)));
  c.innerHTML='<span class="me">'+(a?a.emoji:'\uD83C\uDF7D\uFE0F')+'</span><span class="mt"><b>Tonight: '+(a?esc(a.name):'<span class="tp">Tap to plan</span>')+'</b>'+
    '<small>Tomorrow: '+(b?b.emoji+' '+esc(b.name):'Tap to plan')+'</small></span>';}
function used(name,except){var t=todayISO(),cw=sun(t),out=[];[add(cw,-7),cw].forEach(function(w,wi){var p=load(w);Object.keys(p).forEach(function(d){if(p[d]===name&&d!==except)out.push((wi?'':'last ')+DOW[D(d).getUTCDay()])})});return out}
function render(){var t=todayISO(),p=load(wk),h='';
  mlp.querySelector('.wr').textContent=new Date(wk+'T12:00:00Z').toLocaleDateString('en-US',{month:'short',day:'numeric',timeZone:'UTC'})+' \u2013 '+new Date(add(wk,6)+'T12:00:00Z').toLocaleDateString('en-US',{month:'short',day:'numeric',timeZone:'UTC'});
  mlp.querySelector('.nw').textContent=wk===sun(t)?'Next week \u25B8':'\u25C2 This week';
  for(var i=0;i<7;i++){var d=add(wk,i),m=meal(p[d]);h+='<button class="dt'+(d===t?' today':'')+(m?'':' empty')+'" data-d="'+d+'"><span class="dw">'+(d===t?'Today':DOW[i])+'</span><span class="dd">'+DOW[i]+' '+D(d).getUTCDate()+'</span><span class="de">'+(m?m.emoji:'\u2795')+'</span><span class="dm">'+(m?esc(m.name):'Tap to plan')+'</span></button>'}
  mlp.querySelector('.days7').innerHTML=h;}
function pool(){return LIB.concat(BUILTIN).filter(function(m){return filt==='all'||(m.tags||[]).indexOf(filt)>=0})}
function renderK(){var p=load(wk),cur=p[pday];
  mlk.querySelector('h3').textContent='Dinner \u00b7 '+DOW[D(pday).getUTCDay()]+' '+D(pday).getUTCDate();
  mlk.querySelector('.chips').innerHTML=FILTERS.map(function(f){return '<button class="chip'+(f[0]===filt?' on':'')+'" data-f="'+f[0]+'">'+f[1]+'</button>'}).join('');
  var mb=function(m,bi){var u=used(m.name,pday);return '<button class="mb'+(bi?' bi':'')+(m.name===cur?' sel':'')+(u.length&&!bi?' used':'')+'" data-m="'+esc(m.name)+'"><span class="e">'+m.emoji+'</span>'+esc(m.name)+(u.length&&!bi?'<span class="bd">had '+u[0]+'</span>':'')+'</button>'};
  var lib=LIB.filter(function(m){return filt==='all'||(m.tags||[]).indexOf(filt)>=0}),bi=BUILTIN.filter(function(m){return filt==='all'||(m.tags||[]).indexOf(filt)>=0});
  mlk.querySelector('.grid').innerHTML=lib.map(function(m){return mb(m,0)}).join('')+(bi.length?'<div class="sec">Easy nights</div>'+bi.map(function(m){return mb(m,1)}).join(''):'')+(cur?'<div class="sec"></div><button class="mb bi" data-m=""><span class="e">\u274C</span>Clear this day</button>':'');}
function setDay(d,n){var p=load(wk);if(n)p[d]=n;else delete p[d];save(wk,p);}
function rnd(exclude){var c=pool().filter(function(m){return BUILTIN.indexOf(m)<0}),fresh=c.filter(function(m){return !used(m.name).length&&exclude.indexOf(m.name)<0}),nx=c.filter(function(m){return exclude.indexOf(m.name)<0});var l=fresh.length?fresh:(nx.length?nx:c);return l.length?l[Math.floor(Math.random()*l.length)].name:''}
function openP(){wk=sun(todayISO());render();mlk.classList.remove('on');mlp.classList.add('on');mlp.setAttribute('aria-hidden','false');if(window.dashRotHold)window.dashRotHold(true);}
function closeP(){mlp.classList.remove('on');mlp.setAttribute('aria-hidden','true');if(window.dashRotHold)window.dashRotHold(false);card();}
function init(){var c=document.getElementById('mlcard');if(!c)return;
  document.body.insertAdjacentHTML('beforeend','<div id="mlp" aria-hidden="true"><div class="mc" role="dialog" aria-label="Meal planner"><button class="x" type="button" aria-label="Close">&times;</button>'+
   '<div class="mh"><h2>\uD83C\uDF7D\uFE0F Dinners</h2><span class="wr"></span><div class="acts"><button class="a wk nw"></button><button class="a" data-act="fill">\uD83C\uDFB2 Fill empty days</button><button class="a" data-act="copy">\u21BA Copy last week</button><button class="a clr" data-act="clear">Clear week</button></div></div>'+
   '<div class="days7"></div><div id="mlk"><div class="kh"><button class="a" data-act="back">\u25C2 Back</button><h3></h3><div class="chips"></div><button class="a wk" data-act="rnd">\uD83C\uDFB2 Random</button></div><div class="grid"></div></div></div></div>');
  mlp=document.getElementById('mlp');mlk=document.getElementById('mlk');
  [c,mlp].forEach(function(el){['pointerdown','touchstart'].forEach(function(e){el.addEventListener(e,function(ev){ev.stopPropagation()},{passive:true})})});
  c.addEventListener('click',function(e){e.stopPropagation();e.preventDefault();openP()});
  mlp.addEventListener('click',function(e){e.stopPropagation();var t=e.target;
    if(t===mlp||t.closest('.x'))return closeP();
    var b=t.closest('[data-act]'),a=b&&b.dataset.act;
    if(t.closest('.nw')){var tw=sun(todayISO());wk=wk===tw?add(tw,7):tw;return render();}
    if(a==='back'){mlk.classList.remove('on');return render();}
    if(a==='fill'){filt='all';var p=load(wk),taken=Object.keys(p).map(function(k){return p[k]});for(var i=0;i<7;i++){var d=add(wk,i);if(!p[d]){var n=rnd(taken);if(n){p[d]=n;taken.push(n)}}}save(wk,p);return render();}
    if(a==='copy'){var lw=load(add(wk,-7)),q={};Object.keys(lw).forEach(function(d){q[add(d,7)]=lw[d]});if(!Object.keys(q).length){alert('Nothing planned last week.');return}save(wk,q);return render();}
    if(a==='clear'){if(confirm('Clear all dinners for this week?')){save(wk,{});render();}return;}
    if(a==='rnd'){var n=rnd([]);if(n){setDay(pday,n);mlk.classList.remove('on');render();}return;}
    var ch=t.closest('.chip');if(ch){filt=ch.dataset.f;return renderK();}
    var m=t.closest('.mb');if(m){setDay(pday,m.dataset.m);mlk.classList.remove('on');return render();}
    var dt=t.closest('.dt');if(dt){pday=dt.dataset.d;filt='all';renderK();mlk.classList.add('on');}});
  card();setInterval(card,60000);
  if(/[?&]meals=1/.test(location.search))setTimeout(openP,300);}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init);else init();
"""


def block(data: dict) -> str:
    lib = [{"name": m["name"], "emoji": m.get("emoji", "🍽️"), "tags": m.get("tags", [])}
           for m in sorted((data.get("meals") or {}).get("library", []), key=lambda m: m["name"].lower())]
    js = JS.replace("__LIB__", json.dumps(lib, ensure_ascii=False).replace("</", "<\\/"))
    return f"<style>{CSS}</style>\n<script>(function(){{{js}}})();</script>\n"
