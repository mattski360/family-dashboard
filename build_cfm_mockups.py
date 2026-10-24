#!/usr/bin/env python3
"""Come, Follow Me + Strength of Youth kid-friendly mockups (Cloudflare preview only).
Copies the built landscape/index.html and restyles ONLY the page-1 CFM and FSY cards:
  cfm-a/  emoji accents (📖 reading, 🙏 prayer, ✨ scripture bubble, keyword-picked FSY topic emoji)
  cfm-b/  inline-SVG line icons on soft colored badges + 'Scripture of the day' speech-bubble card
  cfm-c/  playful: SVG sunrise/tree header strip, big friendly section icons, 💬 'Talk about it' question
Run after build.py (same hidden-term check; exits 3 on a leak). deploy_cloudflare.sh uploads them."""
import html, re, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent

# FSY topic -> (emoji, icon key), first keyword match wins
TOPICS = [(("body", "health"), "💪", "heart"), (("sabbath", "temple", "worship"), "⛪", "home"),
          (("media", "music", "phone", "screen"), "📱", "phone"), (("friend", "relationship", "dating"), "🤝", "people"),
          (("language", "word", "speak"), "🗣️", "chat"), (("dress", "modest", "appearance"), "👕", "shirt"),
          (("honest", "integrity"), "✅", "check"), (("work", "self-reliance", "education"), "🛠️", "tool"),
          (("family",), "🏡", "home"), (("pray", "spirit", "jesus", "christ"), "🌟", "star"),
          (("repent", "agency", "choose", "choice"), "🧭", "compass")]

def topic_pick(t):
    t = t.lower()
    for keys, e, i in TOPICS:
        if any(k in t for k in keys):
            return e, i
    return "🌟", "star"

_P = {  # 24x24 line icons, stroke=currentColor
  "book": '<path d="M4 5.5C6.5 4 9.5 4 12 5.5v14c-2.5-1.5-5.5-1.5-8 0z"/><path d="M20 5.5C17.5 4 14.5 4 12 5.5v14c2.5-1.5 5.5-1.5 8 0z"/>',
  "pray": '<path d="M12 20s-7.5-4.6-7.5-10A4.3 4.3 0 0 1 12 7.4 4.3 4.3 0 0 1 19.5 10c0 5.4-7.5 10-7.5 10z"/>',
  "chat": '<path d="M4 6a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H10l-4 3.5V16H6a2 2 0 0 1-2-2z"/><path d="M8.5 9h7M8.5 12h4.5"/>',
  "spark": '<path d="M12 3v4M12 17v4M3 12h4M17 12h4M6 6l2.5 2.5M15.5 15.5 18 18M6 18l2.5-2.5M15.5 8.5 18 6"/>',
  "heart": '<path d="M12 20s-7.5-4.6-7.5-10A4.3 4.3 0 0 1 12 7.4 4.3 4.3 0 0 1 19.5 10c0 5.4-7.5 10-7.5 10z"/><path d="M8 12h2l1-2 2 4 1-2h2"/>',
  "home": '<path d="M4 11l8-6.5 8 6.5"/><path d="M6 10v9.5h12V10"/><path d="M10 19.5v-5h4v5"/>',
  "phone": '<rect x="7" y="3" width="10" height="18" rx="2.2"/><path d="M11 18h2"/>',
  "people": '<circle cx="9" cy="8" r="3"/><circle cx="16.5" cy="9" r="2.4"/><path d="M3.5 19.5c.6-3.4 2.8-5.2 5.5-5.2s4.9 1.8 5.5 5.2M14.5 14.6c2.7-.5 5.2.9 6 4.9"/>',
  "shirt": '<path d="M8.5 4 4 6.5l1.8 4 2.2-1v10.5h8V9.5l2.2 1 1.8-4L15.5 4c-.6 1.6-2 2.4-3.5 2.4S9.1 5.6 8.5 4z"/>',
  "check": '<circle cx="12" cy="12" r="8.5"/><path d="M8 12.3l2.7 2.7L16.2 9.5"/>',
  "tool": '<path d="M14.5 5.5a4 4 0 0 0 4.9 4.9l-9.3 9.3a2 2 0 0 1-2.8-2.8z"/>',
  "star": '<path d="M12 3.5l2.6 5.4 5.9.8-4.3 4.1 1 5.8-5.2-2.8-5.2 2.8 1-5.8-4.3-4.1 5.9-.8z"/>',
  "compass": '<circle cx="12" cy="12" r="8.5"/><path d="M15.5 8.5l-2 5-5 2 2-5z"/>',
  "sun": '<circle cx="12" cy="12" r="4"/><path d="M12 2.5v2.5M12 19v2.5M2.5 12H5M19 12h2.5M5.3 5.3l1.8 1.8M16.9 16.9l1.8 1.8M5.3 18.7l1.8-1.8M16.9 7.1l1.8-1.8"/>',
}
def svg(k, cls="li"):
    return (f'<svg class="{cls}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" '
            f'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{_P[k]}</svg>')

SCENE_C = ('<svg class="scene" viewBox="0 0 600 70" preserveAspectRatio="xMidYMax slice" aria-hidden="true">'
  '<defs><linearGradient id="skyc" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#FFE3B8"/><stop offset="1" stop-color="#FFF4E2"/></linearGradient></defs>'
  '<rect width="600" height="70" fill="url(#skyc)"/>'
  '<g fill="#FFC24B"><circle cx="300" cy="62" r="24"/></g>'
  '<g stroke="#FFC24B" stroke-width="4" stroke-linecap="round"><path d="M300 26v-12M262 40l-9-7M338 40l9-7M244 58h-12M356 58h12"/></g>'
  '<path d="M0 60 Q90 34 190 56 T400 54 T600 50 V70 H0z" fill="#9FD8A6"/>'
  '<path d="M0 66 Q140 50 300 64 T600 62 V70 H0z" fill="#6CC17A"/>'
  '<g><rect x="512" y="30" width="7" height="28" rx="2" fill="#A0703F"/><circle cx="515" cy="26" r="15" fill="#4FAE62"/><circle cx="503" cy="33" r="10" fill="#5BBE6E"/><circle cx="528" cy="33" r="10" fill="#5BBE6E"/></g>'
  '<g fill="#fff" opacity=".9"><ellipse cx="90" cy="20" rx="20" ry="7"/><ellipse cx="108" cy="16" rx="13" ry="7"/><ellipse cx="430" cy="16" rx="16" ry="6"/></g></svg>')
SCENE_C2 = ('<svg class="scene" viewBox="0 0 600 70" preserveAspectRatio="xMidYMax slice" aria-hidden="true">'
  '<defs><linearGradient id="skyf" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#CFE6FF"/><stop offset="1" stop-color="#FDEFF5"/></linearGradient></defs>'
  '<rect width="600" height="70" fill="url(#skyf)"/>'
  '<path d="M0 70 L120 22 L200 52 L300 12 L420 56 L500 30 L600 60 V70z" fill="#B9A6E8"/>'
  '<path d="M300 12 L330 30 L312 28 L300 36 L288 28 L270 30z" fill="#fff"/>'
  '<path d="M0 64 Q150 52 300 64 T600 60 V70 H0z" fill="#8FD39B"/>'
  '<g fill="#FFC24B"><path d="M80 18l3 6 6.5 1-4.7 4.5 1.1 6.5-5.9-3.1-5.9 3.1 1.1-6.5L70.5 25l6.5-1z"/></g>'
  '<g fill="#fff" opacity=".9"><ellipse cx="470" cy="18" rx="18" ry="6"/></g></svg>')

CSS = {
"a": r"""
/* mockup A: emoji accents */
#p1 .spirit .sc .sk .bub{display:none}
.em{font-family:"Noto Color Emoji","Apple Color Emoji","Segoe UI Emoji",sans-serif;font-style:normal;line-height:1}
#p1 .spirit .sk .em{font-size:1.7em;margin-right:.45em;vertical-align:-.3em}
#p1 .spirit .sk{font-size:.82rem}
.srd .em,.prayer .em{font-size:1.15em;margin-right:.3em}
.srd{display:flex;align-items:center}
.cfd .tk{display:flex;align-items:center;gap:.35em}
.cfd .tk .em{font-size:1.5em}
.cfd.tbox{position:relative;background:#fff;border:2.5px dashed #F2B97A;border-radius:1.6rem}
.cfd.tbox:after{content:"";position:absolute;left:2.2rem;top:-.75rem;width:1.1rem;height:1.1rem;background:#fff;border-left:2.5px dashed #F2B97A;border-top:2.5px dashed #F2B97A;transform:rotate(45deg)}
.fsy .stt .em{font-size:1.25em;margin-right:.35em;vertical-align:-.12em}
.fsy .t-today .tk .em{font-size:1.4em;margin-right:.3em;vertical-align:-.25em}
.fsy .t-today{background:#fff;border:2.5px solid #F3B8D3}
.fsy .t-tmrw b .em{font-size:1.3em;margin-right:.25em}
""",
"b": r"""
/* mockup B: line icons on soft badges + 'Scripture of the day' speech bubble */
#p1 .spirit .sk .bub{display:none}
.li{width:1em;height:1em;flex:none}
.bdg{flex:none;display:inline-flex;align-items:center;justify-content:center;width:2.4rem;height:2.4rem;border-radius:.85rem;font-size:1.45rem}
.b-or{background:#FFE0C2;color:#C26A1D}.b-bl{background:#DCE8FF;color:#3C6FD1}.b-gr{background:#D6F2E1;color:#22865A}
.b-pk{background:#FFD8E8;color:#B2477A}.b-pu{background:#E6DEFF;color:#6A4FC7}.b-ye{background:#FFF0C4;color:#B5821D}
#p1 .spirit .sk{display:flex;align-items:center;gap:.6rem;font-size:.82rem}
.rowb{display:flex;align-items:center;gap:.65rem}
.rowb .bdg{width:2.2rem;height:2.2rem;border-radius:.75rem;font-size:1.4rem}
#p1 .spirit .sk .bdg{width:2.6rem;height:2.6rem;font-size:1.65rem}
.prayer{margin:.15em 0 0}
.sotd{position:relative;margin-top:.9rem !important;background:#fff !important;border-radius:1.3rem;box-shadow:0 3px 0 #F2C9A0}
.sotd:before{content:"";position:absolute;left:1.6rem;top:-.7rem;border:.7rem solid transparent;border-top:0;border-bottom-color:#fff}
.sotd .tk{display:flex;align-items:center;gap:.5rem}
.sotd .tk .bdg{width:1.8rem;height:1.8rem;border-radius:.6rem;font-size:1.3rem}
.sotd .tk span{margin-left:auto;background:#FFF1E2;border-radius:999px;padding:.15em .7em;font-weight:800;color:#B5651D}
.fsy .t-today .tk{display:flex;align-items:center;gap:.5rem}
.fsy .t-today .tk .bdg{width:1.8rem;height:1.8rem;border-radius:.6rem;font-size:1.3rem}
.fsy .t-today{background:#fff;box-shadow:0 3px 0 #F3B8D3}
.fsy .rowb .stt{margin-top:0}
""",
"c": r"""
/* mockup C: playful header strip, big friendly icons, Talk about it */
#p1 .spirit .sk .bub{display:none}
#p1 .spirit .sc{position:relative;overflow:hidden;padding-top:0 !important}
.scene{display:block;width:calc(100% + 2.8rem);height:2.9rem;margin:0 -1.4rem 0;flex:none}
.big{flex:none;display:flex;align-items:center;justify-content:center;width:3.6rem;height:3.6rem;border-radius:50%;background:#fff;
  border:3px solid var(--bc);color:var(--bc);font-size:2.05rem;box-shadow:0 4px 0 var(--bc);margin-top:-1.9rem;position:relative}
.big .li{width:1em;height:1em;stroke-width:2.1}
.cfm{--bc:#E58A2E}.fsy{--bc:#D0558F}
.hdc{display:flex;align-items:flex-end;gap:.8rem}
.hdc .sk{padding-bottom:.15rem;font-size:.9rem}
.cfm .stt,.fsy .stt{margin-top:.1rem}
.prayer .pr-l:before{content:"🙏 ";font-family:"Noto Color Emoji",sans-serif}
.cfd.tbox{border:3px solid #F6C892;background:#FFFBF5}
.talk{display:flex;gap:.5em;align-items:flex-start;background:#E9F3FF;border-radius:1rem;padding:.35em .7em;color:#24446E;font-weight:700;font-size:1.1rem;line-height:1.3}
.talk b{flex:none;font-size:.7rem;letter-spacing:.07em;text-transform:uppercase;color:#3C6FD1;padding-top:.35em}
.talk .em{font-family:"Noto Color Emoji",sans-serif;font-size:1.3em;line-height:1}
.fsy .t-today{border:3px solid #F3B8D3;background:#FFF9FC}
.fsy .t-today .tk:before{content:"🎯 ";font-family:"Noto Color Emoji",sans-serif;font-size:1.4em;vertical-align:-.2em}
""",
}

COMMON = "#p1 .spirit .cq{font-size:1.4rem;line-height:1.2}#p1 .spirit .tbox{padding:.75rem 1rem .8rem;margin-top:.4rem;gap:.3rem}#p1 .spirit .sc{gap:.32rem;padding-bottom:.95rem}@media (max-height:860px){#p1 .spirit .rowb .bdg{width:1.85rem;height:1.85rem;font-size:1.2rem}#p1 .spirit .sk .bdg{width:2.2rem;height:2.2rem;font-size:1.4rem}#p1 .spirit .tbox{margin-top:.25rem}#p1 .spirit .sc{padding-bottom:.7rem !important}#p1 .spirit .big{width:2.8rem;height:2.8rem;font-size:1.6rem;margin-top:-1.4rem}#p1 .spirit .scene{height:2rem !important}#p1 .spirit .talk{padding:.2em .6em}#p1 .spirit{grid-template-columns:minmax(0,1.32fr) minmax(0,1fr)}#p1 .spirit .ct{line-height:1.25}#p1 .spirit .ft{font-size:1.25rem}#p1 .spirit .sc.cfm{flex-direction:row;flex-wrap:wrap;align-content:flex-start;align-items:center;column-gap:1.2rem}#p1 .spirit .cfm>*{flex:1 0 100%}#p1 .spirit .cfm>.srd,#p1 .spirit .cfm>.prayer,#p1 .spirit .cfm>.rowb{flex:0 1 auto}#p1 .spirit .cq{font-size:1.06rem}#p1 .spirit .prayer{margin:0;font-size:1rem}#p1 .spirit .scene{height:2.4rem}#p1 .spirit .sc{gap:.22rem}#p1 .spirit .ct,#p1 .spirit .talk{font-size:1.02rem}#p1 .spirit .stt{font-size:1.3rem}#p1 .spirit .tbox{padding:.6rem .9rem .65rem}}"

def E(s):
    return f'<i class="em">{s}</i>'

def transform(v, h):
    i = h.index('<div class="spirit">'); j = h.index('<div class="sc fsy', i)
    k = h.index('</div></div>', h.index('<div class="tbox t-today', j)) if '<div class="tbox t-today' in h[j:] else j
    cfm, rest = h[i:j], h[j:]
    m = re.search(r'<div class="stt">(.*?)</div>', rest); topic = html.unescape(m.group(1)) if m else ""
    emo, ico = topic_pick(topic)
    bub = re.compile(r'<span class="bub">.*?</span></span>|<span class="bub"><svg.*?</svg></span>')
    if v == "a":
        cfm = bub.sub(E("📖"), cfm, count=1)
        cfm = cfm.replace('<div class="srd">', f'<div class="srd">{E("📚")}', 1)
        cfm = cfm.replace('<span class="pr-l">Prayer:</span>', f'<span class="pr-l">{E("🙏")}Prayer:</span>', 1)
        cfm = cfm.replace('<div class="tk">Today', f'<div class="tk">{E("✨")}Scripture of the day')
        cfm = re.sub(r'(<div class="cfd-none"><div class="sq">)', r'\1' + E("💬") + " ", cfm)
        rest = bub.sub(E("🛡️"), rest, count=1)
        rest = rest.replace('<div class="stt">', f'<div class="stt">{E(emo)}', 1)
        rest = rest.replace('<div class="tk">Try today</div>', f'<div class="tk">{E("🎯")}Try today</div>', 1)
        rest = rest.replace('<b>Tomorrow</b>', f'<b>{E("🔜")}Tomorrow</b>', 1)
    elif v == "b":
        cfm = bub.sub(f'<span class="bdg b-or">{svg("book")}</span>', cfm, count=1)
        cfm = cfm.replace('<div class="srd">', f'<div class="rowb"><span class="bdg b-ye">{svg("book")}</span><div class="srd">', 1)
        cfm = re.sub(r'(<div class="srd">.*?</div>)', r'\1</div>', cfm, count=1)
        cfm = cfm.replace('<div class="prayer"', f'<div class="rowb"><span class="bdg b-pu">{svg("pray")}</span><div class="prayer"', 1)
        cfm = re.sub(r'(<div class="prayer".*?</div>)', r'\1</div>', cfm, count=1)
        cfm = cfm.replace('<div class="tbox cfd"', '<div class="tbox cfd sotd"')
        cfm = cfm.replace('<div class="tk">Today', f'<div class="tk"><span class="bdg b-bl" style="margin:0">{svg("chat")}</span>Scripture of the day')
        cfm = cfm.replace('<span class="bdg b-bl" style="margin:0">', '<i class="bdg b-bl">').replace(f'{svg("chat")}</span>Scripture', f'{svg("chat")}</i>Scripture')
        rest = bub.sub(f'<span class="bdg b-pk">{svg("star")}</span>', rest, count=1)
        rest = rest.replace('<div class="stt">', f'<div class="rowb"><span class="bdg b-gr">{svg(ico)}</span><div class="stt">', 1)
        rest = re.sub(r'(<div class="stt">.*?</div>)', r'\1</div>', rest, count=1)
        rest = rest.replace('<div class="tk">Try today</div>', f'<div class="tk"><i class="bdg b-ye">{svg("check")}</i>Try today</div>', 1)
    else:
        cfm = re.sub(r'(<div class="sc cfm[^"]*">)<div class="sk">(?:<span class="bub">.*?</svg></span>)(.*?)</div>',
                     lambda mm: mm.group(1) + SCENE_C + f'<div class="hdc"><span class="big">{svg("book")}</span><div class="sk">{mm.group(2)}</div></div>', cfm, count=1)
        def talk(mm):
            t = mm.group(1); q = re.search(r'([^.!?]*\?)\s*$', html.unescape(t))
            if not q: return mm.group(0)
            pre = html.unescape(t)[:q.start(1)].strip()
            return ((f'<div class="ct">{html.escape(pre, False)}</div>' if pre else "") +
                    f'<div class="talk">{E("💬")}<b>Talk about it</b><span>{html.escape(q.group(1).strip(), False)}</span></div>')
        cfm = re.sub(r'<div class="ct">(.*?)</div>', talk, cfm)
        cfm = cfm.replace('<div class="tk">Today', '<div class="tk">📜 Scripture of the day')
        rest = re.sub(r'(<div class="sc fsy[^"]*">)<div class="sk">(?:<span class="bub">.*?</svg></span>)(.*?)</div>',
                      lambda mm: mm.group(1) + SCENE_C2 + f'<div class="hdc"><span class="big">{svg(ico)}</span><div class="sk">{mm.group(2)}</div></div>', rest, count=1)
    h = h[:i] + cfm + rest
    h = h.replace("</head>", f"<style>{COMMON}{CSS[v]}</style></head>", 1)
    return h.replace("<title>", f"<title>CFM mockup {v.upper()} · ", 1)

def leaks(h):
    p = HERE / "data" / "private_hide.txt"
    if not p.exists(): return []
    terms = [l.strip().lower() for l in p.read_text().splitlines() if l.strip() and not l.startswith("#")]
    t = h.lower(); t += "\n" + html.unescape(t)
    return [x for x in terms if x in t]

def main():
    src = (HERE / "landscape" / "index.html").read_text()
    for v in "abc":
        out = transform(v, src)
        if leaks(out):
            print(f"[cfm] ERROR: cfm-{v} mentions a hidden term; not writing", file=sys.stderr); sys.exit(3)
        d = HERE / f"cfm-{v}"; d.mkdir(exist_ok=True); (d / "index.html").write_text(out)
        print(f"[cfm] wrote {d / 'index.html'}")

if __name__ == "__main__":
    main()
