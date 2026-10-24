#!/usr/bin/env python3
"""Chores mockups (Cloudflare preview only): injects a 'Chores' button + panel into the built landscape page.
Writes chores-a/ (per-kid columns, today), chores-b/ (kid picker, big cards), chores-c/ (week grid).
Data: data/dashboard.json -> chores (tasks, weekly zone rotation). Checks persist in localStorage per MT date
(so they reset at midnight MT; reset_time can move that). Run after build.py; deploy_cloudflare.sh uploads them."""
import json, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent

CSS = r"""
#chbtn{position:fixed;right:calc(max(14px,env(safe-area-inset-right)) + max(60px,6.5vh));bottom:max(4px,env(safe-area-inset-bottom));z-index:8;
  height:max(52px,5.2vh);padding:0 max(18px,1.6vh);border:0;border-radius:999px;background:linear-gradient(135deg,#D3E4FF,#C9F0DC 55%,#FFE0BF);
  color:#283044;font:800 max(18px,1.9vh)/1 inherit;font-family:inherit;display:flex;align-items:center;gap:.45em;box-shadow:0 3px 12px rgba(40,48,68,.18);cursor:pointer}
#chbtn b{background:#fff;border-radius:999px;padding:.18em .55em;font-size:.85em;color:#1C8452}
#chp{position:fixed;inset:0;z-index:25;display:none;background:rgba(40,48,68,.38);align-items:center;justify-content:center;padding:1.6vh 1.4vw}
#chp.on{display:flex}
#chp .cc{position:relative;width:100%;height:100%;background:#FBFCFE;border-radius:2.2vh;box-shadow:0 2vh 6vh rgba(0,0,0,.25);display:flex;flex-direction:column;
  overflow:hidden;font-size:clamp(15px,1.85vh,24px);color:#283044;font-family:inherit}
#chp .chd{display:flex;align-items:center;gap:1.2vw;padding:1.4vh 1.6vw;border-bottom:1px solid #EEF0F4;flex:none;padding-right:calc(1.6vw + max(64px,7vh))}
#chp .chd h2{font-size:1.75em;font-weight:900;white-space:nowrap}
#chp .chd .dt{color:#69718a;font-weight:700;font-size:1.05em;white-space:nowrap}
#chp .wk{display:flex;gap:.6vw;margin-left:auto;flex-wrap:wrap;justify-content:flex-end;align-items:center}
#chp .wk>span{color:#69718a;font-weight:800;font-size:.8em;text-transform:uppercase;letter-spacing:.06em}
#chp .wkc{border-radius:999px;padding:.3em .8em;font-weight:800;font-size:.92em;background:var(--bg);color:var(--dk);border:2px solid var(--mid);white-space:nowrap}
#chp .x{position:absolute;top:1vh;right:1vw;width:max(60px,6.5vh);height:max(60px,6.5vh);border-radius:50%;border:0;background:#EEF0F4;color:#283044;font-size:max(30px,3.4vh);cursor:pointer;line-height:1}
#chp .cb{flex:1;min-height:0;padding:1.4vh 1.6vw;display:flex;gap:1.2vw}
#chp .zt{display:inline-block;border-radius:.5em;padding:.1em .5em;font-weight:900;font-size:.8em;color:#fff;margin-right:.35em}
#chp .zA{background:#4F8EEB}#chp .zB{background:#3DB97B}#chp .zC{background:#F29A3D}
.chk{display:flex;align-items:center;gap:.9em;width:100%;border:2.5px solid var(--mid);background:#fff;border-radius:1.4vh;padding:.7vh 1vw;text-align:left;
  font:inherit;color:inherit;cursor:pointer;min-height:56px;transition:background .15s}
.chk .bx{flex:none;width:max(44px,4.6vh);height:max(44px,4.6vh);border-radius:1vh;border:3px solid var(--c);background:#fff;display:flex;align-items:center;justify-content:center}
.chk .bx svg{width:70%;height:70%;opacity:0;transform:scale(.4);transition:all .18s}
.chk.on{background:var(--bg);border-color:var(--c)}
.chk.on .bx{background:var(--c)}
.chk.on .bx svg{opacity:1;transform:none}
.chk .tx{min-width:0;flex:1}
.chk .tx b{display:block;font-weight:800}
.chk .tx small{display:block;color:#69718a;font-size:.82em;line-height:1.3}
.chk.on .tx b{text-decoration:line-through;text-decoration-thickness:2px;color:var(--dk)}
.prog{height:1vh;min-height:8px;border-radius:99px;background:#EEF0F4;overflow:hidden}.prog i{display:block;height:100%;background:var(--c);transition:width .25s}
.chdone{color:var(--dk);font-weight:900}
"""

CHECK_SVG = '<svg viewBox="0 0 24 24"><path fill="none" stroke="#fff" stroke-width="3.6" stroke-linecap="round" stroke-linejoin="round" d="M5 12.5l4.5 4.5L19 7.5"/></svg>'

CORE = r"""
var CH=__DATA__, NM=__NAMES__, CHECK='__CHECK__', TZ=CH.timezone||'America/Denver';
var DOWN=['Sunday','Monday','Tuesday','Wednesday','Thursday','Friday','Saturday'];
function mtParts(d){var f=new Intl.DateTimeFormat('en-CA',{timeZone:TZ,year:'numeric',month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit',hourCycle:'h23'}).formatToParts(d),o={};f.forEach(function(p){o[p.type]=p.value});return o;}
function choreDay(now){ // the chore "day" (MT); before reset_time it still counts as yesterday
  var p=mtParts(now||new Date()),rt=(CH.reset_time||'00:00').split(':'),d=new Date(Date.UTC(+p.year,+p.month-1,+p.day));
  if(+p.hour*60+ +p.minute < +rt[0]*60+ +rt[1]) d.setUTCDate(d.getUTCDate()-1); return d;}
function iso(d){return d.toISOString().slice(0,10);}
function addD(d,n){var x=new Date(d);x.setUTCDate(x.getUTCDate()+n);return x;}
function weekStart(d){return addD(d,-d.getUTCDay());}
function zonesFor(day){ // {kid: zone} for the week containing day
  var r=CH.rotation,a=new Date(r.anchor_sunday+'T00:00:00Z'),w=Math.round((weekStart(day)-a)/6048e5),o={};
  r.order.forEach(function(k,i){o[k]=r.zones[(((i+w+(r.offset||0))%3)+3)%3];});return o;}
function zone(id){for(var i=0;i<CH.zones.length;i++)if(CH.zones[i].id===id)return CH.zones[i];}
function key(day){return 'chores-'+iso(day);}
function load(day){try{return JSON.parse(localStorage.getItem(key(day))||'{}')}catch(e){return {}}}
function save(day,s){try{localStorage.setItem(key(day),JSON.stringify(s))}catch(e){}}
function prune(today){try{var keep=iso(weekStart(today));Object.keys(localStorage).forEach(function(k){if(/^chores-\d{4}-\d\d-\d\d$/.test(k)&&k.slice(7)<keep)localStorage.removeItem(k)})}catch(e){}}
function tasksFor(kid,day){ // [{id,title,sub}] for one kid on one day: 2 daily groups + 2 zone tasks
  var z=zone(zonesFor(day)[kid]),out=[];
  CH.daily.groups.forEach(function(g,i){out.push({id:kid+':'+g.id,title:i?g.items.join(' · '):'Bedroom & bathroom',sub:i?'':g.items.join(' · '),kind:'daily'})});
  out[1].title=CH.daily.groups[1].items.join(' & ');
  z.tasks.forEach(function(t){out.push({id:kid+':'+t.id,title:t.text,sub:'Zone '+z.id+' · '+z.name,kind:'zone',zone:z.id})});return out;}
function chkHTML(t,on,extra){return '<button class="chk'+(on?' on':'')+'" data-id="'+t.id+'"'+(extra||'')+'><span class="bx">'+CHECK+'</span><span class="tx"><b>'+t.title+'</b>'+(t.sub?'<small>'+t.sub+'</small>':'')+'</span></button>';}
function weekChips(day){var z=zonesFor(day);return '<div class="wk"><span>This week</span>'+CH.kids.map(function(k){var zz=zone(z[k]);return '<span class="wkc p-'+k+'">'+NM[k]+' → <i class="zt z'+zz.id+'">'+zz.id+'</i>'+zz.name+'</span>'}).join('')+'</div>';}
function dateLabel(d){return DOWN[d.getUTCDay()]+', '+d.toLocaleDateString('en-US',{month:'short',day:'numeric',timeZone:'UTC'});}
var chp,cday,timer;
function openP(){cday=choreDay();prune(cday);render();chp.classList.add('on');chp.setAttribute('aria-hidden','false');if(window.dashRotHold)window.dashRotHold(true);}
function closeP(){chp.classList.remove('on');chp.setAttribute('aria-hidden','true');if(window.dashRotHold)window.dashRotHold(false);updBtn();}
function updBtn(){var d=choreDay(),s=load(d),n=0,t=0;CH.kids.forEach(function(k){tasksFor(k,d).forEach(function(x){t++;if(s[x.id])n++})});
  document.getElementById('chbtnc').textContent=n+'/'+t;}
function init(){
  document.body.insertAdjacentHTML('beforeend','<button id="chbtn" type="button" aria-label="Chores">✅ Chores <b id="chbtnc"></b></button><div id="chp" aria-hidden="true"><div class="cc" role="dialog" aria-label="Chores"><button class="x" type="button" aria-label="Close">&times;</button><div class="chd"></div><div class="cb"></div></div></div>');
  chp=document.getElementById('chp');
  var b=document.getElementById('chbtn');['pointerdown','touchstart'].forEach(function(e){b.addEventListener(e,function(ev){ev.stopPropagation()},{passive:true})});
  b.addEventListener('click',function(e){e.stopPropagation();openP()});
  chp.addEventListener('click',function(e){e.stopPropagation();if(e.target===chp||e.target.closest('.x'))return closeP();
    var c=e.target.closest('.chk');if(c&&!c.disabled){var day=c.dataset.day?new Date(c.dataset.day+'T00:00:00Z'):cday,s=load(day);s[c.dataset.id]=!s[c.dataset.id];if(!s[c.dataset.id])delete s[c.dataset.id];save(day,s);render();}
    var k=e.target.closest('[data-kid]');if(k&&!c){window.__chkid=k.dataset.kid;render();}});
  ['pointerdown','touchstart'].forEach(function(e){chp.addEventListener(e,function(ev){ev.stopPropagation()},{passive:true})});
  updBtn();setInterval(function(){var d=choreDay();if(cday&&iso(d)!==iso(cday)){cday=d;prune(d);if(chp.classList.contains('on'))render();}updBtn();},30000);
}
"""

VARIANTS = {
"a": ("Per-kid columns · today", r"""
#chp .col{flex:1;min-width:0;display:flex;flex-direction:column;gap:1.1vh;background:var(--bg);border-radius:1.8vh;padding:1.4vh 1vw;border:2px solid var(--mid)}
#chp .col h3{display:flex;align-items:center;gap:.5em;font-size:1.55em;font-weight:900;color:var(--dk)}
#chp .col h3 span{margin-left:auto;font-size:.62em}
#chp .col h4{font-size:.8em;font-weight:900;letter-spacing:.07em;text-transform:uppercase;color:var(--dk);margin-top:.5vh}
#chp .col .chk{flex:1;max-height:15vh}
""", r"""
function render(){var s=load(cday);
  chp.querySelector('.chd').innerHTML='<h2>✅ Chores</h2><span class="dt">'+dateLabel(cday)+'</span>'+weekChips(cday);
  chp.querySelector('.cb').innerHTML=CH.kids.map(function(k){var ts=tasksFor(k,cday),n=ts.filter(function(t){return s[t.id]}).length,z=zone(zonesFor(cday)[k]);
    return '<div class="col p-'+k+'"><h3>'+NM[k]+'<span class="'+(n===ts.length?'chdone':'')+'">'+(n===ts.length?'All done! 🎉':n+' of '+ts.length)+'</span></h3><div class="prog"><i style="width:'+(100*n/ts.length)+'%"></i></div>'+
      '<h4>Every day</h4>'+chkHTML(ts[0],s[ts[0].id])+chkHTML(ts[1],s[ts[1].id])+
      '<h4><i class="zt z'+z.id+'">Zone '+z.id+'</i>'+z.name+' · this week</h4>'+chkHTML(ts[2],s[ts[2].id])+chkHTML(ts[3],s[ts[3].id])+'</div>'}).join('');}
"""),
"b": ("Kid picker · big cards", r"""
#chp .cb{flex-direction:column}
#chp .chkids{display:flex;gap:1.2vw;flex:none}
#chp .chkid{flex:1;display:flex;align-items:center;gap:1vw;border:3px solid var(--mid);background:#fff;border-radius:2vh;padding:1.2vh 1.2vw;font:inherit;color:inherit;cursor:pointer;min-height:max(80px,10vh)}
#chp .chkid.sel{background:var(--bg);border-color:var(--c);box-shadow:0 .6vh 2vh rgba(40,48,68,.12)}
#chp .chkid .chav{width:max(56px,6.4vh);height:max(56px,6.4vh);border-radius:50%;background:var(--c);color:#fff;font-weight:900;font-size:1.6em;display:flex;align-items:center;justify-content:center;flex:none}
#chp .chkid .chkn{text-align:left;flex:1}#chp .chkid .chkn b{display:block;font-size:1.4em;font-weight:900}#chp .chkid .chkn small{color:#69718a;font-weight:700}
#chp .chkid .chring{font-weight:900;color:var(--dk);font-size:1.25em}
#chp .cards{flex:1;min-height:0;display:grid;grid-template-columns:1fr 1fr;grid-template-rows:auto 1fr auto 1fr;gap:1.2vh 1.2vw;margin-top:1.4vh}
#chp .cards h4{grid-column:span 2;font-size:.85em;font-weight:900;letter-spacing:.07em;text-transform:uppercase;color:var(--dk)}
#chp .cards .chk{height:100%;font-size:1.3em;border-radius:2vh;padding:1.2vh 1.4vw}
#chp .cards .chk .bx{width:max(60px,7vh);height:max(60px,7vh)}
""", r"""
function render(){var s=load(cday),z=zonesFor(cday),sel=window.__chkid||CH.kids[0];
  chp.querySelector('.chd').innerHTML='<h2>✅ Chores</h2><span class="dt">'+dateLabel(cday)+'</span>'+weekChips(cday);
  var kids='<div class="chkids">'+CH.kids.map(function(k){var ts=tasksFor(k,cday),n=ts.filter(function(t){return s[t.id]}).length,zz=zone(z[k]);
    return '<button class="chkid p-'+k+(k===sel?' sel':'')+'" data-kid="'+k+'"><span class="chav">'+NM[k][0]+'</span><span class="chkn"><b>'+NM[k]+'</b><small>Zone '+zz.id+' · '+zz.name+'</small></span><span class="chring">'+(n===ts.length?'🎉':n+'/'+ts.length)+'</span></button>'}).join('')+'</div>';
  var ts=tasksFor(sel,cday),zz=zone(z[sel]);
  chp.querySelector('.cb').innerHTML=kids+'<div class="cards p-'+sel+'"><h4>'+NM[sel]+' · every day</h4>'+chkHTML(ts[0],s[ts[0].id])+chkHTML(ts[1],s[ts[1].id])+
    '<h4><i class="zt z'+zz.id+'">Zone '+zz.id+'</i>'+zz.name+' · this week</h4>'+chkHTML(ts[2],s[ts[2].id])+chkHTML(ts[3],s[ts[3].id])+'</div>';}
"""),
"c": ("Week grid · today highlighted", r"""
#chp .cb{flex-direction:column;padding-top:1vh}
#chp table{width:100%;height:100%;border-collapse:separate;border-spacing:.35vw .45vh;table-layout:fixed}
#chp th{font-weight:900;color:#69718a;font-size:.85em;text-transform:uppercase;letter-spacing:.05em;padding:.3vh 0}
#chp th.td{color:#fff;background:#F2B33D;border-radius:1vh}
#chp th.tl{width:31%;text-align:left}
#chp td.lb{background:var(--bg);border-radius:1vh;padding:0 .8vw;font-weight:800;line-height:1.2;overflow:hidden}
#chp td.lb small{display:block;color:#69718a;font-weight:700;font-size:.78em;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
#chp td.lb .chnm{color:var(--dk);font-weight:900;margin-right:.3em}
#chp td.sec{font-size:.8em;font-weight:900;letter-spacing:.07em;text-transform:uppercase;color:#69718a;padding:.4vh 0 0}
#chp td.c{padding:0;text-align:center}
#chp td.c.td{background:#FFF7E0;border-radius:1vh}
#chp td.c .chk{width:100%;height:100%;min-height:40px;padding:0;justify-content:center;border-width:2px;border-radius:1vh}
#chp td.c .chk .bx{width:max(32px,3.6vh);height:max(32px,3.6vh);border-width:2.5px}
#chp td.c .chk[disabled]{opacity:.35;cursor:default}
""", r"""
function render(){var ws=weekStart(cday),days=[0,1,2,3,4,5,6].map(function(i){return addD(ws,i)}),z=zonesFor(cday),st=days.map(load),ti=cday.getUTCDay();
  chp.querySelector('.chd').innerHTML='<h2>✅ Chores · this week</h2><span class="dt">Today: '+dateLabel(cday)+'</span>'+weekChips(cday);
  var h='<table><thead><tr><th class="tl"></th>'+days.map(function(d,i){return '<th class="'+(i===ti?'td':'')+'">'+DOWN[i].slice(0,3)+' '+d.getUTCDate()+'</th>'}).join('')+'</tr></thead><tbody>';
  function row(k,t,label,sub){return '<tr class="p-'+k+'"><td class="lb"><span class="chnm">'+NM[k]+'</span>'+label+(sub?'<small>'+sub+'</small>':'')+'</td>'+days.map(function(d,i){
      return '<td class="c'+(i===ti?' td':'')+'">'+chkHTML({id:t.id,title:'',sub:''},st[i][t.id],' data-day="'+iso(d)+'"'+(i>ti?' disabled':'')).replace('<span class="tx"><b></b></span>','')+'</td>'}).join('')+'</tr>';}
  h+='<tr><td class="sec" colspan="8">Every day · all boys</td></tr>';
  CH.kids.forEach(function(k){var ts=tasksFor(k,cday);h+=row(k,ts[0],'🛌 Room, bed, items, bathroom','');});
  CH.kids.forEach(function(k){var ts=tasksFor(k,cday);h+=row(k,ts[1],'👖 Laundry & 🎹 piano','');});
  h+='<tr><td class="sec" colspan="8">Zones · this week</td></tr>';
  CH.kids.forEach(function(k){var zz=zone(z[k]);zz.tasks.forEach(function(t){h+=row(k,{id:k+':'+t.id},'<i class="zt z'+zz.id+'">'+zz.id+'</i>'+t.text,'');})});
  chp.querySelector('.cb').innerHTML=h+'</tbody></table>';}
"""),
}

LIVE_CSS = r"""
#chbtn{right:auto;bottom:auto;left:0;top:0;width:0;height:0;visibility:hidden;justify-content:center;border-radius:1.6rem;
  font-size:max(24px,2.9vh);gap:.6em;box-shadow:0 4px 14px rgba(40,48,68,.2);z-index:8}
#chbtn.ok{visibility:visible}
#chbtn b{font-size:.8em;padding:.2em .7em}
#chbtn:active{filter:brightness(.95)}
"""

# live: park the big button over the .chslot reserved at the bottom of each page (identical rect on p1 and p2)
LIVE_JS = r"""document.body.classList.add('has-ch');(function(){function place(){var b=document.getElementById('chbtn');if(!b)return;
var sl=[].slice.call(document.querySelectorAll('.chslot')).map(function(e){return e.getBoundingClientRect()}).filter(function(r){return r.width>0});
if(!sl.length)return;var r=sl[0];b.style.left=r.left+'px';b.style.top=r.top+'px';b.style.width=r.width+'px';b.style.height=r.height+'px';b.classList.add('ok');}
window.addEventListener('resize',place);window.addEventListener('load',place);setTimeout(place,0);setTimeout(place,600);setInterval(place,5000);})();"""


def block(data: dict, v: str, live: bool = False) -> str:
    """<style>+<script> for variant v. live=True: nav-sized button and rotation hold while open (window.dashRotHold)."""
    CH = data["chores"]
    NAMES = {k: (data["people"].get(k) or {}).get("label", k.title()) for k in CH["kids"]}
    title, css, js = VARIANTS[v]
    core = (CORE.replace("__DATA__", json.dumps(CH, ensure_ascii=False)).replace("__NAMES__", json.dumps(NAMES))
            .replace("__CHECK__", CHECK_SVG))
    return (f"<style>{CSS}{css}{LIVE_CSS if live else ''}</style>\n<script>(function(){{{core}{js}\nif(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init);else init();"
            f"{LIVE_JS if live else ''}if(/[?&]open=1/.test(location.search))setTimeout(openP,300);}})();</script>\n")


def main() -> int:
    data = json.loads((HERE / "data" / "dashboard.json").read_text())
    base = (HERE / "landscape" / "index.html").read_text()
    if 'id="chbtn"' in base:   # live page already has chores (option A); keep the existing preview folders
        print("[chores] landscape already includes chores; previews left as-is")
        return 0
    for v, (title, css, js) in VARIANTS.items():
        out = base.replace("<title>", f"<title>[Chores mockup {v.upper()}: {title}] ", 1).replace("</body>", block(data, v) + "</body>", 1)
        o = HERE / f"chores-{v}" / "index.html"; o.parent.mkdir(exist_ok=True); o.write_text(out)
        print("wrote", o)
    return 0


if __name__ == "__main__":
    sys.exit(main())
