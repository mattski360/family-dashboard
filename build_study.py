#!/usr/bin/env python3
"""Tap-to-open study popups for the Come, Follow Me and For the Strength of Youth cards (live landscape only).

Content comes from data/dashboard.json:
  spiritual.come_follow_me.deep_dive    (weekly; refreshed Saturday with the rest of come_follow_me)
  spiritual.strength_of_youth.deep_dive (monthly chapter)
See README.md "Study popups" for field docs. A popup is only wired up when its deep_dive exists
(and, for CFM, deep_dive.week_of matches come_follow_me.week_of). While open, page rotation is held
(window.dashRotHold); closes on X, tap outside, or 5 minutes without a touch.
"""
from __future__ import annotations
import html

def esc(s) -> str:
    return html.escape(str(s or ""), quote=True)

CSS = r"""
.sc.cfm.tap,.sc.fsy.tap{cursor:pointer;position:relative}
.sc.tap .tapme{position:absolute;right:.9rem;bottom:.7rem;font-size:max(20px,2vh);font-weight:800;background:rgba(255,255,255,.7);color:#4B3F72;border-radius:999px;padding:.22rem .7rem}
.stp{position:fixed;inset:0;z-index:26;display:none;background:rgba(40,48,68,.42);align-items:center;justify-content:center;padding:2vh 2vw}
.stp.on{display:flex}
.stp .mc{position:relative;width:100%;height:100%;max-width:1800px;background:#FBFCFE;border-radius:2.2vh;box-shadow:0 2vh 6vh rgba(0,0,0,.25);display:flex;flex-direction:column;overflow:hidden;color:#283044;font-family:inherit;font-size:clamp(16px,2vh,26px)}
.stp .x{position:absolute;top:1.2vh;right:1vw;width:max(64px,7vh);height:max(64px,7vh);border-radius:50%;border:0;background:#fff;color:#283044;font-size:max(32px,3.6vh);cursor:pointer;line-height:1;z-index:2;box-shadow:0 .3vh 1vh rgba(0,0,0,.12)}
.stp .hd{flex:none;padding:2vh 2vw 1.6vh;padding-right:max(90px,9vh)}
#cfmp .hd{background:#FFE4D1}#fsyp .hd{background:#FBDDE6}
.stp .hd .k{font-size:.8em;font-weight:900;letter-spacing:.08em;text-transform:uppercase;color:#69718a}
.stp .hd h2{font-size:2em;font-weight:900;line-height:1.15;margin:.15em 0}
.stp .hd .rd{font-weight:800;font-size:1.05em;color:#4B3F72}
.stp .bd{flex:1;overflow-y:auto;-webkit-overflow-scrolling:touch;overscroll-behavior:contain;padding:1.8vh 2vw 3vh;display:grid;grid-template-columns:minmax(0,1.35fr) minmax(0,1fr);gap:1.6vh 2vw;align-content:start}
.stp .col{display:flex;flex-direction:column;gap:1.6vh;min-width:0}
.stp h3{font-size:1.05em;font-weight:900;letter-spacing:.06em;text-transform:uppercase;color:#69718a;margin:.4em 0 0}
.stp .intro{font-size:1.08em;line-height:1.5;grid-column:1/-1;background:#F4F1FA;border-radius:1.6vh;padding:1.4vh 1.4vw}
.stp .pr{display:flex;gap:.8em;background:#fff;border:2px solid #E6E9F0;border-radius:1.6vh;padding:1.2vh 1.1vw;line-height:1.45}
.stp .pr .e{font-size:2em;line-height:1;flex:none}
.stp .pr b{display:block;font-size:1.08em;line-height:1.3}
.stp .pr .rf{display:block;margin:.15em 0 .25em;font-size:.82em;font-weight:800;color:#8A5A2B}
.stp .vs{background:#FFF7E6;border-left:.5em solid #F2B33D;border-radius:1.2vh;padding:1vh 1vw;line-height:1.45}
.stp .vs q{font-style:italic;quotes:"\201C" "\201D"}
.stp .vs .rf{display:block;font-weight:900;font-size:.85em;margin-top:.2em;color:#8A5A2B}
.stp ol{margin:0;padding-left:1.4em;line-height:1.5}.stp ol li{margin:.35em 0}
.stp .act{background:#E9F8F0;border-radius:1.6vh;padding:1.2vh 1.2vw;line-height:1.5}
.stp .act b{display:block;font-size:1.1em;color:#1F7A4D}
.stp .sb{display:flex;flex-wrap:wrap;gap:.5em}.stp .sb span{background:#EEF0F4;border-radius:999px;padding:.35em .9em;font-weight:700;font-size:.9em}
.stp .lk{display:block;background:#E4EEFF;color:#245A9E;border-radius:1.4vh;padding:1.1vh 1vw;font-weight:800;text-decoration:none;word-break:break-all;font-size:.85em}
.stp .lk b{display:block;font-size:1.15em;word-break:normal}
"""

JS = r"""
function init(){
  var IDLE=5*60*1000,openEl=null,t=null;
  function hold(on){if(window.dashRotHold)window.dashRotHold(on);}
  function bump(){clearTimeout(t);t=setTimeout(close,IDLE);}
  function open(id){var p=document.getElementById(id);if(!p)return;if(openEl)close();openEl=p;p.classList.add('on');p.setAttribute('aria-hidden','false');p.querySelector('.bd').scrollTop=0;hold(true);bump();}
  function close(){if(!openEl)return;openEl.classList.remove('on');openEl.setAttribute('aria-hidden','true');openEl=null;clearTimeout(t);hold(false);}
  window.__study={open:open,close:close};
  [['.sc.cfm','cfmp'],['.sc.fsy','fsyp']].forEach(function(a){
    if(!document.getElementById(a[1]))return;
    document.querySelectorAll(a[0]).forEach(function(c){c.classList.add('tap');c.insertAdjacentHTML('beforeend','<span class="tapme">Tap to study \uD83D\uDC46</span>');
      ['pointerdown','touchstart'].forEach(function(e){c.addEventListener(e,function(ev){ev.stopPropagation()},{passive:true})});
      c.addEventListener('click',function(e){e.stopPropagation();e.preventDefault();open(a[1]);});});
    var p=document.getElementById(a[1]);
    ['pointerdown','touchstart','pointerup','touchend'].forEach(function(e){p.addEventListener(e,function(ev){ev.stopPropagation();bump();},{passive:true})});
    p.querySelector('.bd').addEventListener('scroll',bump,{passive:true});
    p.addEventListener('click',function(e){e.stopPropagation();if(e.target===p||e.target.closest('.x'))close();});
  });
  var m=/[?&]study=(cfm|fsy)/.exec(location.search);if(m)setTimeout(function(){open(m[1]+'p')},300);
}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init);else init();
"""

def _verse(v):
    return f'<div class="vs"><q>{esc(v.get("text"))}</q><span class="rf">{esc(v.get("ref"))}</span></div>'

def _pr(p):
    rf = f'<span class="rf">{esc(p["ref"])}</span>' if p.get("ref") else ""
    return f'<div class="pr"><span class="e">{esc(p.get("emoji") or "✨")}</span><div><b>{esc(p.get("title"))}</b>{rf}{esc(p.get("explain"))}</div></div>'

def _qs(qs):
    return "<ol>" + "".join(f"<li>{esc(q)}</li>" for q in qs) + "</ol>" if qs else ""

def _link(url, label):
    return f'<a class="lk" href="{esc(url)}" target="_blank" rel="noopener"><b>🔗 {esc(label)}</b>{esc(url)}</a>' if url else ""

def _shell(pid, kicker, title, sub, body):
    return (f'<div class="stp" id="{pid}" aria-hidden="true"><div class="mc" role="dialog" aria-label="{esc(kicker)}">'
            f'<button class="x" type="button" aria-label="Close">&times;</button>'
            f'<div class="hd"><div class="k">{kicker}</div><h2>{esc(title)}</h2><div class="rd">{sub}</div></div>'
            f'<div class="bd">{body}</div></div></div>')

def cfm_popup(c: dict) -> str:
    dd = c.get("deep_dive") or {}
    if not dd or c.get("status") == "pending" or (dd.get("week_of") and dd["week_of"] != c.get("week_of")):
        return ""
    left = "<h3>💡 Main principles</h3>" + "".join(_pr(p) for p in dd.get("principles", []))
    if dd.get("questions"):
        left += "<h3>🗣️ Family discussion</h3>" + _qs(dd["questions"])
    right = ""
    if dd.get("key_verses"):
        right += "<h3>📜 Key verses</h3>" + "".join(_verse(v) for v in dd["key_verses"])
    q = dd.get("quote") or {}
    if q.get("text"):
        right += "<h3>🎙️ Prophet's words</h3>" + _verse({"text": q["text"], "ref": q.get("by")})
    a = dd.get("activity") or {}
    if a:
        right += f'<h3>🎨 Try this together</h3><div class="act"><b>{esc(a.get("title"))}</b>{esc(a.get("steps"))}</div>'
    if dd.get("scripture_blocks"):
        right += '<h3>📚 This week\'s reading</h3><div class="sb">' + "".join(
            f'<span>{esc(b["ref"])} · {esc(b.get("about"))}</span>' for b in dd["scripture_blocks"]) + "</div>"
    right += _link(dd.get("source_url") or c.get("source_url"), "Official lesson (Gospel Library)")
    body = (f'<div class="intro">{esc(dd.get("intro"))}</div>' if dd.get("intro") else "") + \
           f'<div class="col">{left}</div><div class="col">{right}</div>'
    kick = f'📖 Come, Follow Me · Lesson {esc(c.get("lesson"))} · {esc(c.get("dates_label"))}'
    return _shell("cfmp", kick, (c.get("title") or "").strip(), "📚 " + esc(c.get("reading")), body)

def fsy_popup(f: dict) -> str:
    dd = f.get("deep_dive") or {}
    if not dd or f.get("status") == "pending" or (dd.get("month") and f.get("month") and dd["month"] != f["month"]):
        return ""
    left = "<h3>💡 Main teachings</h3>" + "".join(_pr(p) for p in dd.get("teachings", []))
    right = ""
    s = dd.get("scripture") or {}
    if s.get("text"):
        right += "<h3>📜 Chapter scripture</h3>" + _verse(s)
    if dd.get("quotes"):
        right += "<h3>⭐ Key quotes</h3>" + "".join(_verse({"text": q, "ref": "For the Strength of Youth"}) for q in dd["quotes"])
    if dd.get("blessings"):
        right += f'<h3>🎁 Promised blessing</h3><div class="act">{esc(dd["blessings"])}</div>'
    if dd.get("questions"):
        right += "<h3>🤔 Questions to ponder</h3>" + _qs(dd["questions"])
    right += _link(dd.get("source_url") or f.get("source_url"), "Read the chapter (Gospel Library)")
    body = (f'<div class="intro">{esc(dd.get("intro"))}</div>' if dd.get("intro") else "") + \
           f'<div class="col">{left}</div><div class="col">{right}</div>'
    kick = f'🛡️ For the Strength of Youth · {esc(f.get("label"))}'
    return _shell("fsyp", kick, dd.get("chapter_title") or f.get("topic"), esc(s.get("ref") or ""), body)

def block(data: dict) -> str:
    sp = data.get("spiritual") or {}
    pops = cfm_popup(sp.get("come_follow_me") or {}) + fsy_popup(sp.get("strength_of_youth") or {})
    if not pops:
        return ""
    return f"<style>{CSS}</style>\n{pops}\n<script>(function(){{{JS}}})();</script>\n"
