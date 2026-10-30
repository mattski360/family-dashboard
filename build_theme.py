"""Monthly colour themes for the wall pages (v3/ and landscape/), all 3 landscape pages.

The browser picks the theme from the current month in America/Denver, so no rebuild is needed (it re-checks every minute).
`?theme=MM` (01-12) previews a month and `?theme=off` shows the plain colours.
Each month has 4 pastel hues: P primary, S secondary, T third, N neutral/surface. Every tone is derived from them:
  bg  very light fill, mid  border/chip, c  dots/buttons, dk  text, darkened until >= 4.8:1 on its bg.
The whole page is recoloured with these tones: background + pattern, header, study cards, kid cards (kid colours stay 3 distinct
hues), day cells, weather chips, trivia/joke cards, idea/meal/chores buttons, nav, gratitude board, composer.
Every border is an inset box-shadow, so no layout size changes. build.py applies it only when LIVE (or themes=True).
"""
import colorsys, urllib.parse

# Not live until Matt approves the previews (build_theme_preview.py + shot_themes.py -> shots_theme/). Set True to ship.
LIVE = False

#        name, P, S, T, N, kids (Luke, Wyatt, Tanner), emoji (header/cards), pattern
THEMES = {
 "01": ("New Year / winter", "#8EC5F0", "#B4BEDA", "#8FD6D6", "#C9D6E6", ("#7FB2F0", "#74CDBE", "#B7A6E8"), ("❄️", "✨", "⛄"), "snow"),
 "02": ("Valentine's", "#F4A3BE", "#C3A8EE", "#F59A9A", "#EBCFDC", ("#B49BEB", "#F29BBF", "#F7A58C"), ("💗", "💌", "💕"), "heart"),
 "03": ("St. Patrick's / spring", "#7FD6A4", "#EBCB6A", "#A8D98A", "#CDE5D4", ("#7FC4E0", "#6FCF8E", "#EFC05A"), ("☘️", "🌈", "🪙"), "clover"),
 "04": ("Easter / spring", "#C7AEF0", "#F5AFCB", "#F2D877", "#DCD6EC", ("#8FBCF2", "#84D9AE", "#F7BE7E"), ("🐣", "🌷", "🐰"), "egg"),
 "05": ("Spring flowers / Mother's Day", "#C9A3E6", "#F7B896", "#A6D69A", "#E3D3EC", ("#9DB4F0", "#8ED4A0", "#F6AE85"), ("🌸", "💐", "🌼"), "flower"),
 "06": ("Early summer / Father's Day", "#87C3F2", "#F5D35C", "#93D69A", "#CFE1F0", ("#7DB7F2", "#7FD08F", "#F7B95B"), ("☀️", "🌻", "🎣"), "sun"),
 "07": ("Independence Day / Pioneer Day", "#F29A9F", "#8DB1EC", "#EFD07A", "#D7DDEA", ("#86AEEE", "#F0959B", "#EDC46A"), ("🎆", "⭐", "🇺🇸"), "star"),
 "08": ("Summer / back to school", "#74D3CC", "#F7A48E", "#F5D15E", "#CDE7E5", ("#7CBCEB", "#6FD1B5", "#F6A07F"), ("🌊", "🍉", "✏️"), "wave"),
 "09": ("Fall harvest", "#EE9A8E", "#EDC06A", "#A9C79A", "#E3DCCB", ("#9DB1DD", "#9CC58C", "#EDB561"), ("🍎", "🍯", "🌾"), "apple"),
 "10": ("Halloween", "#F7AE6E", "#BFA2EC", "#A8DE8E", "#E6DCD0", ("#B59BEE", "#8FD98A", "#F7A65E"), ("🎃", "👻", "🦇"), "candycorn"),
 "11": ("Thanksgiving", "#F0A86A", "#E59AA8", "#A8C49A", "#E8D7AE", ("#E296A6", "#97C08A", "#EFA05E"), ("🍂", "🦃", "🌾"), "leaf"),
 "12": ("Christmas", "#EE9A9A", "#86C29A", "#EBCB72", "#DCE3DC", ("#8DB8EA", "#7FC096", "#EE9595"), ("🎄", "⭐", "❄️"), "snow"),
}

# ---------- colour maths ----------
def _rgb(h): h = h.lstrip("#"); return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
def _hex(r): return "#" + "".join(f"{max(0, min(255, round(x * 255))):02X}" for x in r)
def mix(a, b, t):  # t = share of b
    A, B = _rgb(a), _rgb(b); return _hex(tuple(x + (y - x) * t for x, y in zip(A, B)))
def lum(h):
    v = [x / 12.92 if x <= .03928 else ((x + .055) / 1.055) ** 2.4 for x in _rgb(h)]; return .2126 * v[0] + .7152 * v[1] + .0722 * v[2]
def contrast(a, b): x, y = lum(a), lum(b); return (max(x, y) + .05) / (min(x, y) + .05)
def dark(c, against, target=4.8, sat=None):
    r, g, b = _rgb(c); h, l, s = colorsys.rgb_to_hls(r, g, b); s = min(1, max(s, .5)) if sat is None else sat
    while l > 0:
        out = _hex(colorsys.hls_to_rgb(h, l, s))
        if all(contrast(out, x) >= target for x in against): return out
        l -= .01
    return "#202020"
def tones(c):
    bg, mid = mix(c, "#FFFFFF", .84), mix(c, "#FFFFFF", .62)
    return dict(c=c, bg=bg, mid=mid, lt=mix(c, "#FFFFFF", .90), dk=dark(c, [bg, mid, "#FFFFFF", mix(c, "#FFFFFF", .93)]))

# ---------- background patterns (SVG tiles, very faint) ----------
def _pattern(kind, a, b, corner=False):
    s = {
     "snow": f'<g stroke="{a}" stroke-width="3" stroke-linecap="round"><path d="M30 14v32M16 22l28 16M16 38l28-16"/></g><g stroke="{b}" stroke-width="2.4" stroke-linecap="round"><path d="M95 72v24M85 78l20 12M85 90l20-12"/></g>',
     "heart": f'<path fill="{a}" d="M30 46C10 32 14 16 24 16c4 0 6 3 6 3s2-3 6-3c10 0 14 16-6 30z"/><path fill="{b}" d="M94 100C80 90 83 79 90 79c3 0 4 2 4 2s1-2 4-2c7 0 10 11-4 21z"/>',
     "clover": f'<g fill="{a}"><circle cx="24" cy="22" r="7"/><circle cx="36" cy="22" r="7"/><circle cx="30" cy="32" r="7"/></g><path stroke="{a}" stroke-width="3" d="M30 36q2 8 6 12" fill="none"/><circle fill="{b}" cx="94" cy="88" r="5"/>',
     "egg": f'<ellipse fill="{a}" cx="30" cy="30" rx="11" ry="15"/><path stroke="#fff" stroke-width="3" d="M20 30h20" /><ellipse fill="{b}" cx="94" cy="88" rx="9" ry="12"/>',
     "flower": f'<g fill="{a}"><circle cx="30" cy="20" r="6"/><circle cx="40" cy="28" r="6"/><circle cx="36" cy="40" r="6"/><circle cx="24" cy="40" r="6"/><circle cx="20" cy="28" r="6"/></g><circle fill="{b}" cx="30" cy="30" r="5"/><circle fill="{b}" cx="94" cy="90" r="6"/>',
     "sun": f'<circle fill="{a}" cx="30" cy="30" r="9"/><g stroke="{a}" stroke-width="3" stroke-linecap="round"><path d="M30 12v4M30 44v4M12 30h4M44 30h4M17 17l3 3M40 40l3 3M43 17l-3 3M17 43l3-3"/></g><circle fill="{b}" cx="94" cy="90" r="5"/>',
     "star": f'<path fill="{a}" d="M30 14l4.7 9.6 10.6 1.5-7.6 7.5 1.8 10.5L30 38.2l-9.5 4.9 1.8-10.5-7.6-7.5 10.6-1.5z"/><path fill="{b}" d="M94 78l3.2 6.5 7.2 1-5.2 5.1 1.2 7.1L94 94.4l-6.4 3.3 1.2-7.1-5.2-5.1 7.2-1z"/>',
     "wave": f'<path fill="none" stroke="{a}" stroke-width="3" stroke-linecap="round" d="M10 30q10-10 20 0t20 0"/><circle fill="{b}" cx="94" cy="88" r="6"/>',
     "apple": f'<circle fill="{a}" cx="30" cy="32" r="11"/><path fill="{b}" d="M31 21q6-9 12-5-5 6-12 5z"/><circle fill="{b}" cx="94" cy="90" r="5"/>',
     "candycorn": f'<path fill="#FFE27A" d="M30 14l13 30H17z"/><path fill="{a}" d="M23.3 29.5h13.4L40.6 39H19.4z"/><path fill="#FFFFFF" d="M17 44h26l-2.4-5H19.4z"/><path fill="{b}" d="M84 86q10-10 20 0-5-2-10 4-5-6-10-4z"/>',
     "leaf": f'<path fill="{a}" d="M18 42Q18 18 44 16 44 42 18 42z"/><path stroke="#fff" stroke-width="2" d="M20 40L40 20"/><path fill="{b}" d="M86 98Q86 80 104 78 104 98 86 98z"/>',
    }[kind]
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="4 4 52 52" width="52" height="52" opacity=".42">{s}</svg>' if corner else
           f'<svg xmlns="http://www.w3.org/2000/svg" width="120" height="120" viewBox="0 0 120 120" opacity=".45">{s}</svg>')
    return "url(\"data:image/svg+xml," + urllib.parse.quote(svg, safe="=:/ ") + "\")"

WEB = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><g transform="translate(100 0) scale(-1 1)" fill="none" stroke="%23A98BD8" stroke-width="1.3" opacity=".6">'
       '<path d="M0 0L100 100M0 0L100 40M0 0L40 100M0 0L100 70M0 0L70 100"/>'
       '<path d="M30 12Q24 24 12 30M55 22Q42 42 22 55M82 32Q60 60 32 82M100 46Q76 76 46 100"/></g></svg>')

EMOJI_FONT = '"Noto Color Emoji","Apple Color Emoji","Segoe UI Emoji",sans-serif'

def palette(mm):
    name, P, S, T, N, kids, em, pat = THEMES[mm]
    p, s, t, n = tones(P), tones(S), tones(T), tones(N)
    k = [tones(x) for x in kids]
    return dict(name=name, P=p, S=s, T=t, N=n, K=k, em=em, pat=pat,
                bg1=mix(P, "#FFFFFF", .87), bg2=mix(S, "#FFFFFF", .87), surf=mix(N, "#FFFFFF", .80),
                muted=dark(N, sat=.18, against=[mix(N, "#FFFFFF", .80), mix(P, "#FFFFFF", .84), mix(S, "#FFFFFF", .84), mix(T, "#FFFFFF", .84)], target=5.6),
                faint=dark(N, sat=.16, against=[mix(N, "#FFFFFF", .80), mix(P, "#FFFFFF", .84), mix(S, "#FFFFFF", .84), mix(T, "#FFFFFF", .84)], target=4.6))

def _vars(mm):
    q = palette(mm); v = {}
    for key in "PSTN":
        for t, x in q[key].items(): v[f"--{key}{t}"] = x
    for kid, tt in zip(("luke", "wyatt", "tanner"), q["K"]):
        v[f"--{kid}"] = tt["c"]; v[f"--{kid}-dk"] = tt["dk"]; v[f"--{kid}-bg"] = tt["bg"]; v[f"--{kid}-mid"] = tt["mid"]
    v.update({"--th-bg1": q["bg1"], "--th-bg2": q["bg2"], "--surf": q["surf"], "--muted": q["muted"], "--faint": q["faint"],
              "--th-pat": _pattern(q["pat"], q["P"]["mid"], q["S"]["mid"]),
              "--th-corner": _pattern(q["pat"], q["P"]["c"], q["S"]["c"], corner=True),
              "--th-e1": f'"{q["em"][0]}"', "--th-e2": f'"{q["em"][1]}"', "--th-e3": f'"{q["em"][2]}"',
              "--th-band": f'linear-gradient(90deg,{q["P"]["c"]},{q["S"]["c"]},{q["T"]["c"]},{q["P"]["c"]})'})
    return f'html[data-theme="{mm}"]{{' + ";".join(f"{a}:{b}" for a, b in v.items()) + "}"

T = "html[data-theme]"
RULES = f"""
{T},{T} body{{background:var(--th-pat) 0 0/170px 170px,linear-gradient(160deg,var(--th-bg1) 0%,var(--th-bg2) 100%);background-attachment:fixed}}
{T} body::before{{content:"";position:fixed;left:0;right:0;top:0;height:9px;background:var(--th-band);z-index:5;pointer-events:none}}
/* header */
{T} .motto,{T} .date b{{color:var(--Pdk)}}
{T} .fam{{color:var(--Pdk)}}
{T} .fam::after{{content:var(--th-e1) var(--th-e2) var(--th-e3);font-family:{EMOJI_FONT};font-size:.6em;letter-spacing:.12em;margin-left:.4em;vertical-align:.14em;white-space:nowrap}}
{T} .time small{{color:var(--muted)}}
{T} .bg{{background:var(--Nbg);color:var(--Ndk);box-shadow:inset 0 0 0 1.5px var(--Nmid)}}
/* weather */
{T} .wx .wd{{background:var(--Nbg);box-shadow:inset 0 0 0 1.5px var(--Nmid)}}
{T} .wx .wd.now{{background:linear-gradient(135deg,var(--Pbg),var(--Sbg));box-shadow:inset 0 0 0 1.5px var(--Pmid)}}
{T} .wx .wd .w2 .pp{{color:var(--Sdk)}}
{T} .wx .wfall{{background:var(--Nbg);color:var(--muted)}}
/* page 1: study cards */
{T} .sc.cfm{{background:var(--Pbg);box-shadow:inset 0 0 0 2px var(--Pmid)}}
{T} .sc.fsy{{background:var(--Sbg);box-shadow:inset 0 0 0 2px var(--Smid)}}
{T} .cfm .sk,{T} .srd,{T} .tk,{T} .prayer{{color:var(--Pdk)}}
{T} .fsy .sk,{T} .fsy .srd,{T} .fsy .tk,{T} .sq b{{color:var(--Sdk)}}
{T} .sk::after{{content:var(--th-e1);font-family:{EMOJI_FONT};font-size:1.25em;letter-spacing:0;margin-left:.2em}}
{T} .fsy .sk::after{{content:var(--th-e2)}}
{T} .cfd.tbox{{border-color:var(--Pc)}} {T} .cfd.tbox::after,{T} .cfd.tbox::before{{border-color:var(--Pc)}}
{T} .fsy .t-today{{border-color:var(--Sc)}}
{T} .sc.tap .tapme{{background:#fff;color:var(--Pdk);box-shadow:inset 0 0 0 1.5px var(--Pmid)}}
{T} .fsy.tap .tapme{{color:var(--Sdk);box-shadow:inset 0 0 0 1.5px var(--Smid)}}
/* page 1: kid cards (colours via --luke/--wyatt/--tanner) */
{T} .kid{{box-shadow:inset 0 0 0 2px var(--mid)}}
{T} .tmrw{{background:rgba(255,255,255,.82)}}
{T} .pstrip{{background:var(--Sbg);box-shadow:inset 0 0 0 1.5px var(--Smid)}} {T} .pstrip .lab{{color:var(--Sdk)}}
/* page 2: week */
{T} .h{{color:var(--Pdk)}}
{T} .h::after{{content:var(--th-e1) var(--th-e2);font-family:{EMOJI_FONT};font-size:.8em;letter-spacing:.15em}}
{T} .day{{background-color:var(--Plt);box-shadow:inset 0 0 0 1.5px var(--Pmid)}}
{T} .day:nth-child(3n+2){{background-color:var(--Slt);box-shadow:inset 0 0 0 1.5px var(--Smid)}}
{T} .day:nth-child(3n){{background-color:var(--Tlt);box-shadow:inset 0 0 0 1.5px var(--Tmid)}}
{T} .day.today{{background-color:var(--Tbg);box-shadow:inset 0 0 0 3px var(--Tc)}}
{T} .today .dw{{color:var(--Tdk)}}
{T} .day.brk{{background:var(--Tbg)}}
{T} .wkend .dn{{color:var(--Ndk)}}
/* page 2: bottom row */
{T} .fcard.tr{{background:linear-gradient(135deg,var(--Sbg),var(--Tbg));box-shadow:inset 0 0 0 2px var(--Smid)}}
{T} .fcard.jk{{background:linear-gradient(135deg,var(--Pbg),var(--Tbg));box-shadow:inset 0 0 0 2px var(--Pmid)}}
{T} .fcard.tr .fk,{T} .fcard.tr .fa{{color:var(--Sdk)}} {T} .fcard.jk .fk,{T} .fcard.jk .fa{{color:var(--Pdk)}}
{T} .ab.weekend{{background:var(--Sbg);color:var(--Sdk);box-shadow:inset 0 0 0 1.5px var(--Smid)}}
{T} .ab.evening{{background:var(--Pbg);color:var(--Pdk);box-shadow:inset 0 0 0 1.5px var(--Pmid)}}
{T} #mlcard{{background:var(--Tbg);color:var(--Tdk);box-shadow:inset 0 0 0 1.5px var(--Tmid)}} {T} #mlcard .tp{{color:var(--Tdk)}}
{T} #chbtn{{background:linear-gradient(135deg,var(--Pmid),var(--Smid) 55%,var(--Tmid));color:#283044}}
{T} #chbtn b{{color:var(--Pdk)}}
/* nav + footer */
{T} #nav{{background:var(--Nbg);border-top:1px solid var(--Nmid)}}
{T} #nav .dot{{background:var(--Nc)}} {T} #nav .dot.on{{background:var(--Pc)}} {T} #nav .nl{{color:var(--muted)}}
{T} #prog{{background:var(--Pc)}}
{T} .upd{{color:var(--muted)}}
/* page 3: gratitude board (keeps its notes and leaves; colours follow the month) */
{T} #p3{{background:var(--th-pat) 0 0/170px 170px,linear-gradient(180deg,var(--th-bg1) 0%,var(--Pbg) 100%)}}
{T} #p3 header .gt,{T} #p3 header .gs b,{T} #p3 .gidea,{T} #p3 .gempty{{color:var(--Pdk)}}
{T} #p3 header .gs,{T} #p3 .gmore,{T} #p3 .gidea b{{color:var(--Sdk)}}
{T} #p3 .gwho .gtk{{background:var(--Tbg);color:var(--Tdk);box-shadow:inset 0 0 0 1.5px var(--Tmid)}}
{T} #p3 .gwho .gper{{background:#fff;box-shadow:inset 0 0 0 1.5px var(--mid)}}
{T} #p3 .gwho .gper b{{background:var(--bg);color:var(--dk);box-shadow:inset 0 0 0 1.5px var(--c)}}
{T} #p3 .gadd{{background:var(--Pdk);box-shadow:0 4px 14px rgba(40,48,68,.18)}}
{T} #gcomp .gcard{{background:var(--surf)}} {T} #gcomp .gch,{T} #gcomp .gch .gcx{{color:var(--Pdk)}} {T} #gcomp .gch .gcx{{background:var(--Pbg)}}
{T} #gcomp .gl,{T} #gcomp .ghelp{{color:var(--Pdk)}} {T} #gcomp .gsave{{background:var(--Pdk)}}
{T} #gcomp input{{border-color:var(--Pmid)}} {T} #gcomp input:focus{{border-color:var(--Pc);box-shadow:0 0 0 4px var(--Pbg)}}
{T} #gcomp .gstarts button{{background:var(--Pbg);color:var(--Pdk)}} {T} #gkeys button{{box-shadow:0 2px 0 var(--Nmid)}}
/* decorations: faint emoji in the empty header space (wide screens), web corners in October */
#thdeco{{display:none}}
{T} #thdeco{{display:block;position:fixed;inset:0;pointer-events:none;overflow:hidden;z-index:-1}}
#thdeco i{{position:absolute;font-style:normal;font-family:{EMOJI_FONT};opacity:.2;line-height:1}}
#thdeco i:nth-child(1)::before{{content:var(--th-e1)}} #thdeco i:nth-child(2)::before{{content:var(--th-e2)}} #thdeco i:nth-child(3)::before{{content:var(--th-e3)}}
#thdeco i:nth-child(1){{left:31%;top:1.2vh;font-size:4.2vh;transform:rotate(-12deg)}}
#thdeco i:nth-child(2){{left:38%;top:5.6vh;font-size:3vh;transform:rotate(10deg)}}
#thdeco i:nth-child(3){{left:44.5%;top:1.6vh;font-size:3.6vh;transform:rotate(-4deg)}}
{T} .kid,{T} .day.on{{background-image:var(--th-corner);background-repeat:no-repeat;background-position:right .8em top .7em;background-size:2.6em}}
html[data-theme="10"] .kid,html[data-theme="10"] .day.on{{background-size:auto 46%;background-position:right top;background-image:url('data:image/svg+xml,{WEB}');background-repeat:no-repeat;background-position:right top;background-size:auto 46%}}
html[data-theme="10"] .day.on{{background-size:auto 34%}}
@media (max-width:1500px),(orientation:portrait){{#thdeco i{{display:none}}}}
html[data-theme="10"] #p3 .gdeco{{opacity:.9}}
"""

def css() -> str:
    return '<style id="mtheme">\n' + "\n".join(_vars(m) for m in THEMES) + RULES + "</style>"

JS = """<script>/* monthly theme: America/Denver month, ?theme=MM preview, ?theme=off plain */
(function(){var D=document.documentElement,q=location.search.match(/[?&]theme=([^&]+)/),o=q?decodeURIComponent(q[1]):'';
function mon(){try{return new Intl.DateTimeFormat('en-US',{timeZone:'America/Denver',month:'2-digit'}).format(new Date())}catch(e){return ('0'+(new Date().getMonth()+1)).slice(-2)}}
function set(){if(o==='off'){D.removeAttribute('data-theme');return}var n=parseInt(o,10),v=(n>=1&&n<=12)?('0'+n).slice(-2):mon();if(D.getAttribute('data-theme')!==v)D.setAttribute('data-theme',v)}
set();setInterval(set,60000);})();</script>"""

def apply(h: str) -> str:
    assert "</head>" in h and "<body" in h
    h = h.replace("</head>", css() + "\n" + JS + "\n</head>", 1)
    i = h.index(">", h.index("<body")) + 1
    return h[:i] + '<div id="thdeco" aria-hidden="true"><i></i><i></i><i></i></div>' + h[i:]

if __name__ == "__main__":   # print each month's tones and text contrast
    for m in THEMES:
        q = palette(m)
        print(m, q["name"][:16].ljust(16), " ".join(f'{k}:{q[k]["dk"]}({contrast(q[k]["dk"], q[k]["bg"]):.1f})' for k in "PSTN"),
              "muted", round(min(contrast(q["muted"], q[k]["bg"]) for k in "PSTN"), 2), "faint", round(min(contrast(q["faint"], x) for x in [q["surf"], q["P"]["bg"]]), 2))
