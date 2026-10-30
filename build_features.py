#!/usr/bin/env python3
"""Wall-page features for the live landscape page (and the landscape-mock/ preview):
  1. Weather in the page-1 and page-2 headers (under the date/clock): now + today hi/lo + next 4 days for Highland, UT,
     fetched client-side from Open-Meteo (keyless, one request renders both) every 30 min, cached in localStorage
     (wx-highland-v1), graceful fallback ("as of" time / "Weather unavailable").
  2. Trivia + Joke of the day (page-2 bottom row): tap-to-reveal, one of each per day from data/daily_fun.json.
  3. Gratitude board: third rotating page from GRAT_FROM to GRAT_TO (Oct 30 - Nov 30). Name picker + text box,
     notes in localStorage (grat-YYYY, this device only). Composing freezes rotation, the version-check reload and the
     30-min reload (replaces the meta refresh). ?grat=0 / ?grat=1 force it off / on.
build.py calls transform(html, fun, prod=True) on the rendered landscape page; build_nov_mockup.py makes the preview."""
import html, json, re, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
OUT = HERE / "landscape-mock"

GRAT_FROM, GRAT_TO = "10-30", "11-30"   # gratitude board season (MM-DD, America/Denver), every year

def F(n):  # authored size -> calc(var(--fs)*n) like build.py's rem rewrite
    return f"calc(var(--fs) * {n})"

CSS = r"""
/* ===== weather (page-1 + page-2 headers) ===== */
#p1 header,#p2 header{display:grid;grid-template-columns:minmax(0,1fr) auto;column-gap:@1;row-gap:@.45;align-items:center}
#p1 header .hl,#p2 header .hl{grid-column:1;grid-row:1/3} #p1 header .clk,#p2 header .clk{grid-column:2;grid-row:1;justify-content:flex-end}
.wx{grid-column:2;grid-row:2;display:flex;gap:@.4;align-items:stretch;justify-content:flex-end}
.wx .wd{display:grid;grid-template-columns:auto auto;grid-template-rows:auto auto;column-gap:@.4;align-items:center;
  background:#F3F7FD;border-radius:@.85;padding:@.3 @.6 @.3 @.45;text-align:left;min-width:0}
.wx .wd .wi{grid-row:1/3;font-size:@1.9;line-height:1;font-family:"Noto Color Emoji","Apple Color Emoji","Segoe UI Emoji",sans-serif}
.wx .wd .w1{font-size:@1.02;font-weight:800;white-space:nowrap;line-height:1.15}
.wx .wd .w1 .wdn{color:var(--muted);font-weight:800;font-size:@.78;letter-spacing:.06em;text-transform:uppercase;margin-right:@.35}
.wx .wd .w1 .lo{color:var(--faint);font-weight:700}
.wx .wd .w2{font-size:@.8;font-weight:700;color:var(--muted);white-space:nowrap;line-height:1.2}
.wx .wd .w2 .pp{color:#2C62C0;margin-left:@.25}
.wx .wd.now{background:linear-gradient(135deg,#E3EFFF,#F2F7FF);grid-template-columns:auto auto auto;padding-right:@.8}
.wx .wd.now .wi{font-size:@2.2}
.wx .wd.now .wbig{grid-row:1/3;grid-column:2;font-size:@2.1;font-weight:800;letter-spacing:-.03em;line-height:1;padding-right:@.15}
.wx .wd.now .w1,.wx .wd.now .w2{grid-column:3}
.wx .wd.wet .w2 .pp{font-weight:800}
@media (max-width:1500px){#p1 header .hl,#p2 header .hl{grid-row:1} .wx{grid-column:1/3;justify-content:stretch} .wx .wd{flex:1 1 0} .wx .wd.now{flex:1.4 1 0}}
.wx .wfall{font-size:@.75;font-weight:700;color:var(--faint);background:#F5F6F9;border-radius:@.8;padding:@.45 @.8}
.wx .wage{grid-column:2;font-size:@.58;color:var(--faint);font-weight:700}

/* ===== trivia + joke of the day (page-2 bottom row) ===== */
#p2 .brow .ab{white-space:nowrap;flex:none}
#p2 .brow .fun{flex:1 1 0;min-width:0;display:flex;gap:@.7;margin-right:auto}
.fcard{flex:1 1 0;min-width:0;border-radius:@1.1;padding:@.5 @.9;display:flex;flex-direction:column;justify-content:center;gap:@.15;
  cursor:pointer;-webkit-tap-highlight-color:transparent;position:relative;overflow:hidden}
.fcard.tr{background:linear-gradient(135deg,#EAF2FF,#F4EEFF)} .fcard.jk{background:linear-gradient(135deg,#FFF4D6,#FFE9DC)}
.fcard .fk{font-size:@.62;font-weight:800;letter-spacing:.08em;text-transform:uppercase;display:flex;align-items:center;gap:@.35}
.fcard.tr .fk{color:#5B47B0} .fcard.jk .fk{color:#B4620C}
.fcard .fk .em{font-size:1.5em;font-family:"Noto Color Emoji","Apple Color Emoji","Segoe UI Emoji",sans-serif;letter-spacing:0}
.fcard .fq{font-size:@.8;font-weight:800;line-height:1.22;color:var(--text)}
.fcard .fa{font-size:@.76;font-weight:800;line-height:1.2;display:none}
.fcard.tr .fa{color:#2C62C0} .fcard.jk .fa{color:#B4620C}
.fcard .ftap{font-size:@.62;font-weight:800;align-self:flex-start;border-radius:99px;padding:@.12 @.6;background:#fff;color:var(--muted);box-shadow:0 1px 0 rgba(0,0,0,.05)}
.fcard.open .fa{display:block;animation:fpop .35s ease} .fcard.open .ftap{display:none}
@keyframes fpop{from{opacity:0;transform:translateY(4px)}to{opacity:1;transform:none}}

/* ===== gratitude board (page 3, November) ===== */
.p-matt{--c:#3FB3C6;--dk:#17707F;--bg:#E4F6F9;--mid:#C4ECF2}
.p-sabrina{--c:#EE8DB4;--dk:#B13A6D;--bg:#FDEBF3;--mid:#F9D0E2}
#p3{background:radial-gradient(ellipse at 15% 0%,#FFF3DF 0,rgba(255,243,223,0) 55%),linear-gradient(180deg,#FFF8EE 0%,#FDEBD6 100%);gap:@.9}
#p3 .gdeco{position:absolute;inset:0;pointer-events:none;overflow:hidden}
#p3 .gdeco i{position:absolute;font-style:normal;opacity:.22;font-family:"Noto Color Emoji","Apple Color Emoji",sans-serif}
#p3 header .gt{font-size:@1.9;font-weight:800;color:#8A4A12;letter-spacing:-.01em;line-height:1.1;display:flex;align-items:center;gap:@.5}
#p3 header .gt .em{font-family:"Noto Color Emoji","Apple Color Emoji",sans-serif}
#p3 header .gs{margin-top:@.3;font-size:@.95;font-weight:700;color:#B4752E}
#p3 header .gs b{color:#8A4A12}
#p3 .gwho{display:flex;gap:@.6;align-items:center;flex-wrap:wrap}
#p3 .gwho .gper{display:flex;align-items:center;gap:@.45;background:rgba(255,255,255,.7);border-radius:99px;padding:@.25 @.8 @.25 @.25;font-size:@1;font-weight:800;color:var(--dk)}
#p3 .gwho .gper .av{width:@1.9;height:@1.9;border-radius:99px;font-size:@.95;transform:none}
#p3 .gwho .gper b{background:var(--c);color:#fff;border-radius:99px;padding:0 @.45;font-size:@.75;min-width:@1.4;text-align:center}
#p3 .gwho .gtk{margin-left:auto;font-size:@1;font-weight:800;color:#8A4A12;background:#FFE3C2;border-radius:99px;padding:@.3 @.9}
#p3 .gboard{flex:1 1 auto;min-height:0;position:relative;column-count:4;column-gap:@1.1;overflow:hidden;padding:@.3 @.2}
#p3 .gnote{break-inside:avoid;display:block;margin:0 0 @1.1;background:var(--bg);border:2px solid var(--mid);border-radius:@1.3 @.35 @1.3 @.35;
  padding:@.9 @1.1 @.8;position:relative;transform:rotate(var(--r,0deg));box-shadow:0 3px 10px rgba(138,74,18,.08)}
#p3 .gnote .lf{position:absolute;right:@.55;top:@.4;font-size:@1.8;font-family:"Noto Color Emoji","Apple Color Emoji",sans-serif}
#p3 .gnote .gtx{font-size:@1.45;font-weight:700;line-height:1.28;color:var(--text);padding-right:@1.9}
#p3 .gnote .gby{margin-top:@.5;font-size:@.92;font-weight:800;color:var(--dk);display:flex;align-items:center;gap:@.35}
#p3 .gnote .gby .dot{width:@.6;height:@.6;border-radius:99px;background:var(--c)}
#p3 .gnote .gby .gd{color:var(--faint);font-weight:700}
#p3 .gnote .gdel{display:none;position:absolute;right:-@.5;top:-@.6;border:0;background:#CF4436;color:#fff;font:inherit;font-weight:800;font-size:@.7;border-radius:99px;padding:@.25 @.6}
#p3 .gnote.sel .gdel{display:block}
#p3 .gnote.new{animation:gnew .7s cubic-bezier(.2,1.4,.4,1)}
@keyframes gnew{from{opacity:0;transform:scale(.6) rotate(-8deg)}to{opacity:1;transform:rotate(var(--r,0deg))}}
#p3 .gempty{column-span:all;text-align:center;font-size:@1.2;font-weight:700;color:#B4752E;padding:@3 0}
#p3 .gfoot{display:flex;align-items:center;gap:@1}
#p3 .gadd{border:0;font:inherit;font-size:@1.15;font-weight:800;color:#fff;background:linear-gradient(135deg,#F08A3C,#D9602A);border-radius:99px;
  padding:@.7 @1.6;box-shadow:0 4px 14px rgba(217,96,42,.3);cursor:pointer;display:flex;align-items:center;gap:@.5;min-height:56px}
#p3 .gidea{font-size:@.9;font-weight:700;color:#8A4A12}
#p3 .gidea b{color:#D9602A}
#p3 .gmore{font-size:@.78;font-weight:700;color:#B4752E}
#p3 .gmock{margin-top:@.25;font-size:@.75;font-weight:700;color:#C9A27A}
/* composer overlay (outside #stage: its taps never flip pages) */
#gcomp{position:fixed;inset:0;z-index:60;background:rgba(80,40,10,.35);display:none;align-items:flex-start;justify-content:center;padding-top:3vh}
#gcomp.on{display:flex}
#gcomp .gcard{width:min(92vw,1100px);background:#FFFBF5;border-radius:28px;padding:22px 28px 22px;box-shadow:0 20px 60px rgba(80,40,10,.3);font-size:18px}
#gcomp .gch{display:flex;align-items:center;gap:12px;font-size:26px;font-weight:800;color:#8A4A12}
#gcomp .gch .gcx{margin-left:auto;border:0;background:#F3E6D6;color:#8A4A12;font-size:28px;line-height:1;width:52px;height:52px;border-radius:99px;cursor:pointer}
#gcomp .gl{margin:14px 0 8px;font-size:15px;font-weight:800;letter-spacing:.06em;text-transform:uppercase;color:#B4752E}
#gcomp .gnames{display:flex;gap:12px;flex-wrap:wrap}
#gcomp .gnames button{display:flex;align-items:center;gap:10px;border:3px solid transparent;background:var(--bg);color:var(--dk);font:inherit;font-size:22px;font-weight:800;
  border-radius:99px;padding:6px 22px 6px 6px;min-height:60px;cursor:pointer}
#gcomp .gnames button .av{width:46px;height:46px;border-radius:99px;font-size:22px;transform:none}
#gcomp .gnames button.on{border-color:var(--c);background:#fff;box-shadow:0 0 0 4px var(--mid)}
#gcomp .grw{display:flex;gap:12px;align-items:stretch}
#gcomp input{flex:1;min-width:0;font:inherit;font-size:26px;font-weight:700;color:var(--text);border:3px solid #F2C89A;border-radius:18px;padding:12px 18px;background:#fff;outline:none;
  -webkit-user-select:text;user-select:text}
#gcomp input:focus{border-color:#F08A3C;box-shadow:0 0 0 4px #FFE3C2}
#gcomp .gsave{border:0;font:inherit;font-size:22px;font-weight:800;color:#fff;background:linear-gradient(135deg,#F08A3C,#D9602A);border-radius:18px;padding:0 26px;cursor:pointer;min-height:60px}
#gcomp .gsave:disabled{opacity:.4}
#gcomp .ghelp{display:flex;align-items:center;gap:12px;margin-top:10px;font-size:15px;font-weight:700;color:#B4752E}
#gcomp .ghelp .cnt{margin-left:auto}
#gcomp .gstarts{display:flex;gap:8px;flex-wrap:wrap;margin-top:10px}
#gcomp .gstarts button{border:0;background:#FFEBD2;color:#8A4A12;font:inherit;font-size:17px;font-weight:700;border-radius:99px;padding:8px 16px;min-height:44px;cursor:pointer}
#gcomp .kbt{border:0;background:#F3E6D6;color:#8A4A12;font:inherit;font-size:15px;font-weight:800;border-radius:99px;padding:8px 14px;min-height:44px;cursor:pointer}
#gkeys{display:none;margin-top:12px;gap:8px;flex-direction:column}
#gkeys.on{display:flex}
#gkeys .kr{display:flex;gap:8px;justify-content:center}
#gkeys button{flex:1;max-width:84px;min-height:58px;border:0;border-radius:12px;background:#fff;box-shadow:0 2px 0 #E8D3BA;font:inherit;font-size:24px;font-weight:800;color:var(--text);cursor:pointer}
#gkeys button.w{max-width:none;flex:2.2;font-size:18px} #gkeys button.sp{max-width:none;flex:6}
#gkeys button:active{background:#FFE3C2}
#gtoast{position:fixed;left:50%;top:40%;transform:translate(-50%,-50%) scale(.8);background:#fff;border-radius:24px;padding:22px 34px;font-size:28px;font-weight:800;color:#8A4A12;
  box-shadow:0 16px 50px rgba(80,40,10,.25);opacity:0;pointer-events:none;transition:all .35s;z-index:70}
#gtoast.on{opacity:1;transform:translate(-50%,-50%) scale(1)}
#nav .dot[data-i="2"].on{background:#E8833A}
#nav .mockpill{margin-left:10px;font-size:12px;font-weight:800;letter-spacing:.06em;color:#fff;background:#E8833A;border-radius:99px;padding:3px 10px}
"""
CSS = re.sub(r"@(-?)(\d*\.?\d+)", lambda m: (f"calc(var(--fs) * -{m.group(2)})" if m.group(1) else F(m.group(2))), CSS)

WX_HTML = '<div class="wx" id="wx"><div class="wfall">🌤️ Loading Highland weather…</div></div>'

FUN_HTML = ('<div class="fun" id="fun">'
  '<div class="fcard tr" id="ftr" role="button"><div class="fk"><span class="em">🧠</span>Trivia of the day</div>'
  '<div class="fq"></div><div class="fa"></div><span class="ftap">👆 Tap to reveal the answer</span></div>'
  '<div class="fcard jk" id="fjk" role="button"><div class="fk"><span class="em">😂</span>Joke of the day</div>'
  '<div class="fq"></div><div class="fa"></div><span class="ftap">👆 Tap for the punchline</span></div></div>')

P3_HTML = """
<!-- ====================== PAGE 3: GRATITUDE BOARD (Oct 30 - Nov 30, data-grat-from/to) ====================== -->
<section class="page" id="p3" data-name="Gratitude">
  <div class="gdeco" id="gdeco"></div>
  <header>
    <div class="hl"><div class="gt"><span class="em">🍂</span>Our Gratitude Board</div>
      <div class="gs" id="gsub">Thanksgiving season &middot; <b id="gcount">0</b> things we&rsquo;re thankful for</div><div class="gmock" id="gmock"></div></div>
    <div class="clk"><div class="time js-time">&nbsp;</div><div class="date js-date">&nbsp;</div></div>
  </header>
  <div class="gwho" id="gwho"></div>
  <div class="gboard" id="gboard"></div>
  <div class="gfoot"><button class="gadd" id="gadd" type="button"><span>✏️</span>Add what I&rsquo;m grateful for</button>
    <div class="gidea">Today&rsquo;s idea: <b id="gidea"></b></div><div class="gmore" id="gmore"></div></div>
</section>
"""

COMP_HTML = """
<div id="gcomp" aria-hidden="true"><div class="gcard" role="dialog" aria-label="Add to the gratitude board">
  <div class="gch"><span>🍁</span>What are you grateful for?<button class="gcx" id="gcx" type="button" aria-label="Close">&times;</button></div>
  <div class="gl">Who&rsquo;s writing?</div><div class="gnames" id="gnames"></div>
  <div class="gl">I&rsquo;m grateful for&hellip;</div>
  <div class="grw"><input id="gin" type="text" maxlength="120" autocomplete="off" autocapitalize="sentences" enterkeyhint="done" placeholder="e.g. Mom&rsquo;s pancakes on Saturday">
    <button class="gsave" id="gsave" type="button" disabled>Add 🍂</button></div>
  <div class="gstarts" id="gstarts"></div>
  <div class="ghelp"><button class="kbt" id="gkbt" type="button">⌨️ On-screen keys</button><span>Pages stop turning while you type.</span><span class="cnt" id="gcnt">0/120</span></div>
  <div id="gkeys"></div>
</div></div>
<div id="gtoast">🍂 Added to the board!</div>
"""

JS = r"""
<script>
(function(){
  var B=document.body, TZ=B.getAttribute('data-tz')||'America/Denver';
  function parts(d){var o={};try{new Intl.DateTimeFormat('en-US',{timeZone:TZ,year:'numeric',month:'2-digit',day:'2-digit',weekday:'short',hour:'numeric',minute:'2-digit',hour12:true}).formatToParts(d).forEach(function(p){o[p.type]=p.value});}catch(e){}return o;}
  function ymd(d){var p=parts(d);return p.year+'-'+p.month+'-'+p.day;}
  function dayNum(s){var a=s.split('-');return Math.floor(Date.UTC(+a[0],+a[1]-1,+a[2])/864e5);}
  function store(k,v){try{if(v===undefined)return JSON.parse(localStorage.getItem(k)||'null');localStorage.setItem(k,JSON.stringify(v));}catch(e){return null;}}
  function esc(s){return String(s).replace(/[&<>"]/g,function(c){return{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c];});}
  function refit(){if(window.__fit)window.__fit();}

  /* ---------- 1. weather: Open-Meteo (keyless), Highland UT, client-side, cached ---------- */
  var WX_URL='https://api.open-meteo.com/v1/forecast?latitude=40.43&longitude=-111.79&current=temperature_2m,weather_code,is_day'+
    '&daily=weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max&temperature_unit=fahrenheit&timezone=America%2FDenver&forecast_days=6';
  var WK='wx-highland-v1', wxEls=[].slice.call(document.querySelectorAll('.wx'));
  function wxSet(h){wxEls.forEach(function(e){e.innerHTML=h;});}
  function wmo(c,day){c=+c;
    if(c===0)return day===0?['🌙','Clear']:['☀️','Sunny'];
    if(c===1)return day===0?['🌙','Mostly clear']:['🌤️','Mostly sunny'];
    if(c===2)return['⛅','Partly cloudy']; if(c===3)return['☁️','Cloudy'];
    if(c===45||c===48)return['🌫️','Fog'];
    if(c>=51&&c<=55)return['🌦️','Drizzle']; if(c===56||c===57)return['🌧️','Icy drizzle'];
    if(c===61)return['🌧️','Light rain']; if(c===63)return['🌧️','Rain']; if(c===65)return['🌧️','Heavy rain'];
    if(c===66||c===67)return['🧊','Freezing rain'];
    if(c===71)return['🌨️','Light snow']; if(c===73)return['🌨️','Snow']; if(c===75)return['❄️','Heavy snow']; if(c===77)return['🌨️','Snow'];
    if(c>=80&&c<=82)return['🌦️','Showers']; if(c===85||c===86)return['🌨️','Snow showers'];
    if(c===95)return['⛈️','T-storms']; if(c===96||c===99)return['⛈️','Storms + hail'];
    return['🌡️','—'];}
  function dname(s){var a=s.split('-');return ['Sun','Mon','Tue','Wed','Thu','Fri','Sat'][new Date(Date.UTC(+a[0],+a[1]-1,+a[2],12)).getUTCDay()];}
  function wxRender(c){
    if(!wxEls.length)return;
    var d=c&&c.data&&c.data.daily, today=ymd(new Date());
    if(!d||!d.time){wxSet('<div class="wfall">🌤️ Weather unavailable right now &middot; retrying</div>');refit();return;}
    var i0=d.time.indexOf(today); if(i0<0){wxSet('<div class="wfall">🌤️ Weather unavailable right now &middot; retrying</div>');refit();return;}
    var cur=c.data.current||{}, h='', fresh=Date.now()-c.ts<3*3600e3, i;
    var w0=wmo(fresh&&cur.weather_code!=null?cur.weather_code:d.weather_code[i0], fresh?cur.is_day:1);
    var pp0=d.precipitation_probability_max[i0];
    h+='<div class="wd now'+(pp0>=50?' wet':'')+'"><span class="wi">'+w0[0]+'</span>'+
       (fresh&&cur.temperature_2m!=null?'<span class="wbig">'+Math.round(cur.temperature_2m)+'°</span>':'')+
       '<div class="w1"><span class="wdn">Today</span>'+Math.round(d.temperature_2m_max[i0])+'° <span class="lo">/ '+Math.round(d.temperature_2m_min[i0])+'°</span></div>'+
       '<div class="w2">'+w0[1]+(pp0!=null?'<span class="pp">💧'+pp0+'%</span>':'')+
       (fresh?'':' &middot; as of '+new Date(c.ts).toLocaleTimeString('en-US',{timeZone:TZ,hour:'numeric',minute:'2-digit'}))+'</div></div>';
    for(i=i0+1;i<Math.min(d.time.length,i0+5);i++){var w=wmo(d.weather_code[i],1),pp=d.precipitation_probability_max[i];
      h+='<div class="wd'+(pp>=50?' wet':'')+'"><span class="wi">'+w[0]+'</span><div class="w1"><span class="wdn">'+(i===i0+1?'Tmrw':dname(d.time[i]))+'</span>'+
         Math.round(d.temperature_2m_max[i])+'° <span class="lo">/ '+Math.round(d.temperature_2m_min[i])+'°</span></div>'+
         '<div class="w2"><span class="wc">'+w[1]+'</span>'+(pp!=null?'<span class="pp">💧'+pp+'%</span>':'')+'</div></div>';}
    wxSet(h); refit();
  }
  function wxLoad(){
    var c=store(WK); if(c)wxRender(c);
    if(!window.fetch){if(!c)wxRender(null);return;}
    var ctl=window.AbortController?new AbortController():null, to=setTimeout(function(){if(ctl)ctl.abort();},12000);
    fetch(WX_URL,{cache:'no-store',signal:ctl?ctl.signal:undefined}).then(function(r){if(!r.ok)throw 0;return r.json();}).then(function(j){
      clearTimeout(to); if(!j||!j.daily)throw 0; var nc={ts:Date.now(),data:j}; store(WK,nc); wxRender(nc);
    }).catch(function(){clearTimeout(to);wxRender(store(WK));});
  }
  wxLoad(); setInterval(wxLoad,30*60*1000);
  var wxDay=ymd(new Date()); setInterval(function(){var t=ymd(new Date());if(t!==wxDay){wxDay=t;wxLoad();}},60000);

  /* ---------- 2. trivia + joke of the day ---------- */
  var FUN=JSON.parse(document.getElementById('fundata').textContent);
  function funDay(){
    var n=dayNum(ymd(new Date()));
    [['ftr',FUN.trivia,0],['fjk',FUN.jokes,17]].forEach(function(x){var el=document.getElementById(x[0]);if(!el||!x[1].length)return;
      var it=x[1][((n+x[2])%x[1].length+x[1].length)%x[1].length];
      el.querySelector('.fq').textContent=it.q; el.querySelector('.fa').textContent=(x[0]==='ftr'?'\u2705 ':'')+it.a; el.classList.remove('open');});
    refit();
  }
  funDay(); var funD=ymd(new Date()); setInterval(function(){var t=ymd(new Date());if(t!==funD){funD=t;funDay();}},60000);
  ['ftr','fjk'].forEach(function(id){var el=document.getElementById(id),t=0;
    el.addEventListener('click',function(ev){ev.stopPropagation();
      if(el.classList.contains('open')){el.classList.remove('open');return;}
      el.classList.add('open');
      // keep this page up a little longer so everyone can read the answer (rotation frozen 15 s, then resumes)
      if(window.dashRotHold){window.dashRotHold(true);clearTimeout(t);t=setTimeout(function(){window.dashRotHold(false);},15000);}
      setTimeout(function(){el.classList.remove('open');},90000);});});

  /* ---------- 3. November gratitude board ---------- */
  var P3=document.getElementById('p3');
  var PEOPLE=[['Matt','matt'],['Sabrina','sabrina'],['Luke','luke'],['Wyatt','wyatt'],['Tanner','tanner']];
  var IDEAS=['someone who helped you this week','something in nature you love','a favorite family tradition','a blessing you noticed today',
    'a teacher or leader','something that made you laugh','a scripture or hymn you love','a friend','a food you are thankful for',
    'something about our home','a talent or ability you have','something about Jesus Christ','a fun memory from this year','your favorite season',
    'someone in our ward','a hard thing that helped you grow','something your brother did for you','a book, song or game','a place in Utah you love',
    'the temple','your body and good health','something Mom or Dad does','a pet or animal','a sport or hobby','modern conveniences (like hot water!)',
    'a family member far away','a prayer that was answered','freedom and our country','a recent kindness','Thanksgiving dinner'];
  var STARTS=['My family','Our home','Jesus Christ','My friends','Good food','The temple','Our ward','Sunny days'];
  var LEAVES=['🍁','🍂','🍁','🌻','🍂','🥧','🍁','🌾'];
  var SAMPLES=B.getAttribute('data-grat-force')!=='1'?[]:[['Luke','Getting to pass the sacrament with my quorum'],['Tanner','Pancakes on Saturday mornings!'],['Sabrina','Five boys (counting Matt) who make me laugh every day'],
    ['Wyatt','BYU football wins 🏈'],['Matt','A warm house, a full pantry and a family who prays together'],['Tanner','My brothers playing catch with me'],
    ['Luke','Snow days and sledding'],['Wyatt','My friends at school'],['Sabrina','The temple being so close to home'],['Matt','Fall colors up American Fork Canyon']];
  var now0=new Date(), pn=parts(now0), YEAR=pn.year, GK='grat-'+YEAR, qs=location.search;
  var active=window.__gratOn?window.__gratOn():false;
  if(!active){P3.parentNode.removeChild(P3);var dd=document.querySelector('#nav .dot[data-i="2"]');if(dd)dd.parentNode.removeChild(dd);return;}
  if(B.getAttribute('data-grat-force')==='1')document.getElementById('gmock').textContent='Mockup preview \u00b7 on the wall this board shows '+(B.getAttribute('data-grat-from')||'11-01')+' to '+(B.getAttribute('data-grat-to')||'11-30');
  function notes(){var a=store(GK);return Array.isArray(a)?a:[];}
  function sizeP3(){var vv=window.visualViewport,W=vv?vv.width:innerWidth,H=Math.min(innerHeight,vv?vv.height:1e9);
    P3.style.setProperty('--fs',(Math.min(W/1920,H/1080)*20).toFixed(2)+'px');}
  function thanksgiving(){var y=+YEAR,d=new Date(Date.UTC(y,10,1,12)),first=(4-d.getUTCDay()+7)%7+1;return y+'-11-'+('0'+(first+21)).slice(-2);}
  function pc(name){for(var i=0;i<PEOPLE.length;i++)if(PEOPLE[i][0]===name)return PEOPLE[i][1];return 'family';}
  var selIdx=-1;
  function renderBoard(newTs){
    sizeP3();
    var arr=notes(), sample=!arr.length&&SAMPLES.length>0, list=sample?SAMPLES.map(function(s,i){return{n:s[0],t:s[1],ts:Date.now()-i*36e5*7,s:1};}):arr.slice();
    list.sort(function(a,b){return b.ts-a.ts;});
    document.getElementById('gcount').textContent=sample?0:arr.length;
    var cnt={};arr.forEach(function(x){cnt[x.n]=(cnt[x.n]||0)+1;});
    var tg=thanksgiving(), dn=dayNum(tg)-dayNum(ymd(new Date()));
    document.getElementById('gwho').innerHTML=PEOPLE.map(function(p){return '<span class="gper p-'+p[1]+'"><span class="av">'+p[0][0]+'</span>'+p[0]+'<b>'+(cnt[p[0]]||0)+'</b></span>';}).join('')+
      '<span class="gtk">🦃 '+(dn>1?'Thanksgiving in '+dn+' days':dn===1?'Thanksgiving is tomorrow!':dn===0?'Happy Thanksgiving!':'Thank you for a grateful November')+'</span>';
    var bd=document.getElementById('gboard'), h='';
    list.forEach(function(x,i){var r=((x.ts/1000|0)%7)-3, lf=LEAVES[(x.ts/1000|0)%LEAVES.length];
      var dd=new Intl.DateTimeFormat('en-US',{timeZone:TZ,month:'short',day:'numeric'}).format(new Date(x.ts));
      h+='<div class="gnote p-'+pc(x.n)+(x.ts===newTs?' new':'')+'" data-ts="'+x.ts+'"'+(x.s?' data-sample="1"':'')+' style="--r:'+(r*.6).toFixed(1)+'deg"><span class="lf">'+lf+'</span>'+
         '<div class="gtx">'+esc(x.t)+'</div><div class="gby"><span class="dot"></span>'+esc(x.n)+(x.s?'':' <span class="gd">&middot; '+dd+'</span>')+'</div>'+
         (x.s?'':'<button class="gdel" type="button">Remove</button>')+'</div>';});
    bd.innerHTML=h||'<div class="gempty">Be the first to add something you\u2019re grateful for! 🍁</div>';
    // keep the newest notes that fit; older ones stay saved (count shown bottom-right)
    var hid=0, els=[].slice.call(bd.querySelectorAll('.gnote'));
    while(els.length>1&&(bd.scrollWidth>bd.clientWidth+2||bd.scrollHeight>bd.clientHeight+2)){els.pop().remove();hid++;}
    document.getElementById('gmore').textContent=sample?'Sample notes (mockup) \u00b7 they disappear when you add your own':hid?'+'+hid+' more saved on the board':'';
    document.getElementById('gidea').textContent=IDEAS[dayNum(ymd(new Date()))%IDEAS.length];
  }
  // decorative falling-leaf emoji (static, very faint)
  var dh='';[['🍁',1,30,6],['🍂',95,30,5],['🍁',96,70,7],['🍂',2,78,5],['🌾',46,90,4],['🍁',58,1,3]].forEach(function(l){dh+='<i style="left:'+l[1]+'%;top:'+l[2]+'%;font-size:'+l[3]+'rem">'+l[0]+'</i>';});
  document.getElementById('gdeco').innerHTML=dh;

  var board=document.getElementById('gboard');
  board.addEventListener('click',function(ev){var n=ev.target.closest('.gnote');if(!n||n.hasAttribute('data-sample'))return;ev.stopPropagation();
    if(ev.target.classList.contains('gdel')){var ts=+n.getAttribute('data-ts');store(GK,notes().filter(function(x){return x.ts!==ts;}));renderBoard();return;}
    [].forEach.call(board.querySelectorAll('.gnote.sel'),function(o){if(o!==n)o.classList.remove('sel');});n.classList.toggle('sel');
    if(n.classList.contains('sel'))setTimeout(function(){n.classList.remove('sel');},6000);});

  // composer: rotation and page reloads are frozen while it is open; it closes itself after 2 min without typing
  var comp=document.getElementById('gcomp'), gin=document.getElementById('gin'), gsave=document.getElementById('gsave'), who='', idle=0, kbd=false;
  document.getElementById('gnames').innerHTML=PEOPLE.map(function(p){return '<button type="button" class="p-'+p[1]+'" data-n="'+p[0]+'"><span class="av">'+p[0][0]+'</span>'+p[0]+'</button>';}).join('');
  document.getElementById('gstarts').innerHTML=STARTS.map(function(s){return '<button type="button">'+s+'</button>';}).join('');
  function upd(){gsave.disabled=!(who&&gin.value.trim());document.getElementById('gcnt').textContent=gin.value.length+'/120';
    clearTimeout(idle);idle=setTimeout(close,120000);}
  function open(ev){if(ev){ev.stopPropagation();ev.preventDefault();}
    window.__composing=true; if(window.dashRotHold)window.dashRotHold(true);
    comp.classList.add('on');comp.setAttribute('aria-hidden','false');upd();
    if(!kbd)setTimeout(function(){gin.focus();},60);}
  function close(){clearTimeout(idle);comp.classList.remove('on');comp.setAttribute('aria-hidden','true');gin.blur();
    window.__composing=false; if(window.dashRotHold)window.dashRotHold(false);}
  function save(){var t=gin.value.trim().replace(/\s+/g,' ');if(!who||!t)return;
    var ts=Date.now(),a=notes();a.push({n:who,t:t.slice(0,120),ts:ts});store(GK,a);
    gin.value='';close();renderBoard(ts);var to=document.getElementById('gtoast');to.textContent='🍂 Thanks, '+who+'! Added to the board.';
    to.classList.add('on');setTimeout(function(){to.classList.remove('on');},1800);}
  document.getElementById('gadd').addEventListener('click',open);
  document.getElementById('gcx').addEventListener('click',function(ev){ev.stopPropagation();close();});
  comp.addEventListener('click',function(ev){ev.stopPropagation();if(ev.target===comp)close();});
  document.getElementById('gnames').addEventListener('click',function(ev){var b=ev.target.closest('button');if(!b)return;who=b.getAttribute('data-n');
    [].forEach.call(this.querySelectorAll('button'),function(o){o.classList.toggle('on',o===b);});upd();if(!kbd)gin.focus();});
  document.getElementById('gstarts').addEventListener('click',function(ev){var b=ev.target.closest('button');if(!b)return;gin.value=b.textContent+(gin.value?' '+gin.value:'');upd();if(!kbd)gin.focus();});
  gin.addEventListener('input',upd);
  gin.addEventListener('keydown',function(ev){if(ev.key==='Enter'){ev.preventDefault();save();}});
  gsave.addEventListener('click',save);
  // built-in keys for kiosk browsers that suppress the Android keyboard (inputmode=none hides the system one)
  var ROWS=['qwertyuiop','asdfghjkl','zxcvbnm'], kh='';
  ROWS.forEach(function(r,i){kh+='<div class="kr">'+(i===2?'<button class="w" data-k="shift">⇧</button>':'')+r.split('').map(function(c){return '<button data-k="'+c+'">'+c+'</button>';}).join('')+(i===2?'<button class="w" data-k="bs">⌫</button>':'')+'</div>';});
  kh+='<div class="kr"><button class="w" data-k="!">!</button><button class="w" data-k=",">,</button><button class="sp" data-k=" ">space</button><button class="w" data-k=".">.</button><button class="w" data-k="ok">Add 🍂</button></div>';
  var keys=document.getElementById('gkeys'), shift=true; keys.innerHTML=kh;
  function caps(){[].forEach.call(keys.querySelectorAll('button[data-k]'),function(b){var k=b.getAttribute('data-k');if(k.length===1&&/[a-z]/.test(k))b.textContent=shift?k.toUpperCase():k;});}
  keys.addEventListener('click',function(ev){var b=ev.target.closest('button');if(!b)return;var k=b.getAttribute('data-k');
    if(k==='shift'){shift=!shift;caps();return;} if(k==='bs'){gin.value=gin.value.slice(0,-1);} else if(k==='ok'){save();return;}
    else if(gin.value.length<120){gin.value+=(shift&&/[a-z]/.test(k))?k.toUpperCase():k;if(shift&&/[a-z]/.test(k)){shift=false;caps();}}
    if(/[.!]/.test(k)){shift=true;caps();} upd();});
  document.getElementById('gkbt').addEventListener('click',function(){kbd=!kbd;keys.classList.toggle('on',kbd);
    gin.setAttribute('inputmode',kbd?'none':'text');if(kbd){gin.blur();shift=!gin.value;caps();}else gin.focus();});
  window.__grat={open:open,close:close,render:renderBoard};
  renderBoard();
  window.addEventListener('resize',function(){clearTimeout(window.__g);window.__g=setTimeout(function(){if(!comp.classList.contains('on'))renderBoard();},200);});
  // re-render when page 3 comes on (keeps the fit current)
  new MutationObserver(function(){if(P3.classList.contains('on'))renderBoard();}).observe(P3,{attributes:true,attributeFilter:['class']});
  var gDay=ymd(new Date());setInterval(function(){var t=ymd(new Date());if(t!==gDay){gDay=t;renderBoard();}},60000);
})();
</script>
"""

def sub1(h, old, new, count=1):
    n = h.count(old)
    if n < 1:
        sys.exit(f"[nov] anchor not found: {old[:60]!r}")
    return h.replace(old, new, count if count else n)

def transform(h, fun, prod=False):
    if not prod:
        h = sub1(h, "<title>", "<title>MOCKUP Nov features · ")
    # 30-min meta reload -> JS reload that waits while someone is typing on the gratitude board
    h = re.sub(r'<meta http-equiv="refresh" content="1800">\n?', "", h, count=1)
    h = sub1(h, "</head>", f"<style>{CSS}</style></head>")
    h = sub1(h, "<body ", f'<body data-grat-from="{GRAT_FROM}" data-grat-to="{GRAT_TO}" ' + ('' if prod else 'data-grat-force="1" '))
    # 1. weather in the page-1 header, under the date/clock
    for pid, wid in (("p1", "wx"), ("p2", "wx2")):  # same widget on both pages; one fetch renders both
        i = h.index(f'id="{pid}"'); j = h.index('</header>', i)
        h = h[:j] + WX_HTML.replace('id="wx"', f'id="{wid}"') + h[j:]
    # 2. trivia + joke on the page-2 bottom row
    i = h.index('id="p2"'); j = h.index('<div class="brow">', i) + len('<div class="brow">')
    h = h[:j] + FUN_HTML + h[j:]
    # 3. gratitude page after page 2, inside #stage; composer outside #stage
    i = h.index('<nav id="nav"'); j = h.rindex('</div>', 0, i)
    h = h[:j] + P3_HTML + h[j:]
    h = sub1(h, '<span class="nl" id="navl">', '<button class="dot" data-i="2" aria-label="Gratitude"></button><span class="nl" id="navl">')
    if not prod:
        h = sub1(h, '<button id="yegg"', '<span class="mockpill">MOCKUP</span><button id="yegg"')
    h = sub1(h, '<div id="prog"></div>', COMP_HTML + '<div id="prog"></div>')
    # rotation over 2 or 3 pages (fit() still sizes p1/p2 only; p3 sizes itself)
    h = sub1(h, "var pages=[document.getElementById('p1'),document.getElementById('p2')];",
             "var pages=[document.getElementById('p1'),document.getElementById('p2')];"
             "var RP=pages.slice(),P3x=document.getElementById('p3');"
             "window.__gratOn=function(){var q=location.search;if(/[?&]grat=0/.test(q))return false;"
             "if(/[?&]grat=1/.test(q)||B.getAttribute('data-grat-force')==='1')return true;"
             "var md=new Intl.DateTimeFormat('en-CA',{timeZone:TZ,month:'2-digit',day:'2-digit'}).format(new Date()).replace(/\\D/g,'-'),"
             "f=B.getAttribute('data-grat-from')||'11-01',t=B.getAttribute('data-grat-to')||'11-30';return md>=f&&md<=t;};"
             "if(P3x&&window.__gratOn())RP.push(P3x);"
             "window.__fit=function(){fit();};")
    h = sub1(h, "pages.forEach(function(pg,k){pg.classList.toggle('on',k===i);", "RP.forEach(function(pg,k){pg.classList.toggle('on',k===i);")
    h = sub1(h, "navl.textContent=pages[i].getAttribute", "navl.textContent=RP[i].getAttribute")
    h = sub1(h, "(st.i===0||st.i===1)", "(st.i>=0&&st.i<RP.length)")
    h = sub1(h, "(cur+1)%2", "(cur+1)%RP.length", 0)
    if not prod:  # the mockup keeps its own rotation state (same origin as the live page)
        h = sub1(h, "KEY='dash-land-rot'", "KEY='dash-mock-rot'")
    # version-check reload also waits while composing; plus the 30-min reload (was the meta refresh)
    h = sub1(h, "aEl.classList.contains('on'))return;", "aEl.classList.contains('on')||window.__composing)return;")
    h = sub1(h, "window.addEventListener('resize',function(){clearTimeout(window.__f);",
             "var bootAt=Date.now();setInterval(function(){if(!window.__composing&&Date.now()-bootAt>1800e3)location.reload();},30000);\n"
             "  window.addEventListener('resize',function(){clearTimeout(window.__f);")
    fun_json = json.dumps({"trivia": fun["trivia"], "jokes": fun["jokes"]}, ensure_ascii=False).replace("</", "<\\/")
    h = sub1(h, "</body>", f'<script type="application/json" id="fundata">{fun_json}</script>{JS}</body>')
    return h

