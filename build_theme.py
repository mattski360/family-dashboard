"""Monthly colour themes for the wall pages (v3/ and landscape/).

The page picks the theme in the browser from the current month in America/Denver
(no rebuild needed; it re-checks every minute). `?theme=MM` (01-12) previews a month,
`?theme=off` shows the plain colours. Everything stays light and pastel; the kid colours
(Luke blue, Wyatt green, Tanner orange) never change. build.py calls apply() for
template_v3.html and template_landscape.html.

Variables per month:
  bg   page background (two light stops)     acc  dark accent text (motto, weekday) >= 4.5:1
  day  week-day cell background              tdy/ring  today cell background / outline
  dot  active nav dot                        c1/c2  Come-Follow-Me / Strength-of-Youth cards
  band thin stripe along the top             em   emoji after "Jensen Family" (+ faint header accents)
"""
THEMES = {
    "01": dict(name="New Year / winter", bg=("#F3F8FE", "#EEF2F8"), acc="#2F5F8F", day="#F1F5FA", tdy="#E5F0FC", ring="#9CC4EE",
               dot="#8DB8E6", c1="#EAF2FB", c2="#F1F2F6", band=("#CFE3F7", "#E4E8EE", "#BFD7EE"), em=("❄️", "✨", "⛄")),
    "02": dict(name="Valentine's", bg=("#FFF5F8", "#F7F1FD"), acc="#A33D64", day="#FBF3F7", tdy="#FDE6EF", ring="#F2A7C3",
               dot="#F2A7C3", c1="#FDEEF4", c2="#F3ECFD", band=("#F9C9D9", "#E4D4F7", "#F9C9D9"), em=("💗", "💌", "💕")),
    "03": dict(name="St. Patrick's / spring", bg=("#F1FAF4", "#FBF8EA"), acc="#2A6F46", day="#F1F8F3", tdy="#E3F5E9", ring="#8FD3A8",
               dot="#8FD3A8", c1="#EAF8EF", c2="#FBF5DC", band=("#BDE8CC", "#F3E2A3", "#BDE8CC"), em=("☘️", "🌈", "🪙")),
    "04": dict(name="Easter / spring", bg=("#FFF8F1", "#F1F6FF"), acc="#7A4AA8", day="#F7F5FB", tdy="#FFF4D6", ring="#F6D77A",
               dot="#C9B3F0", c1="#FFF0E8", c2="#EDF7EF", band=("#FFD6E5", "#FFF0B3", "#CDEBD8", "#CFE3FF", "#E3D4FA"), em=("🐣", "🌷", "🐰")),
    "05": dict(name="Spring flowers / Mother's Day", bg=("#FAF5FF", "#FFF5EE"), acc="#7F4A9C", day="#F8F4FB", tdy="#F3E8FC", ring="#CDA8EC",
               dot="#CDA8EC", c1="#FFF0E6", c2="#F4ECFC", band=("#E3CDF5", "#FFD9C2", "#E3CDF5"), em=("🌸", "💐", "🌼")),
    "06": dict(name="Early summer / Father's Day", bg=("#F0F7FF", "#FFFBEA"), acc="#25649B", day="#F2F7FC", tdy="#FFF6D1", ring="#F4D35E",
               dot="#F4D35E", c1="#EAF4FF", c2="#FFF8DC", band=("#BFDDF7", "#FFE89A", "#BFDDF7"), em=("☀️", "🌻", "🎣")),
    "07": dict(name="Independence Day / Pioneer Day", bg=("#F5F8FF", "#FFF6F6"), acc="#A8323F", day="#F5F7FB", tdy="#FDEDEF", ring="#F2A0A8",
               dot="#8FB2E6", c1="#FDEEF0", c2="#EDF3FF", band=("#F4A9B0", "#FFFFFF", "#A9C6F0"), em=("🎆", "⭐", "🇺🇸")),
    "08": dict(name="Summer / back to school", bg=("#EEFAF9", "#FFF6EF"), acc="#1A6F6A", day="#F0F8F8", tdy="#FFF5D6", ring="#F7D36B",
               dot="#6FD3CB", c1="#FFEEE8", c2="#E6F8F6", band=("#A8E6E0", "#FFC9B8", "#FFE59A"), em=("🌊", "🍉", "✏️")),
    "09": dict(name="Early fall", bg=("#FBF8EF", "#F2F7EF"), acc="#9E3F35", day="#F7F6F1", tdy="#FBF0D6", ring="#E8C26A",
               dot="#E8C26A", c1="#FCEDEA", c2="#EEF4EA", band=("#F2B8B0", "#F3D68E", "#C9DDBF"), em=("🍎", "🍯", "🌻")),
    "10": dict(name="Halloween", bg=("#FFF6EC", "#F6F0FD"), acc="#A4521A", day="#FAF6F2", tdy="#FFEBD6", ring="#F7B072",
               dot="#F7B072", c1="#FFF0E2", c2="#F3ECFD", band=("#FFC89A", "#D9C6F5", "#C8EED9", "#FFF3DC"), em=("🎃", "👻", "🦇")),
    "11": dict(name="Thanksgiving", bg=("#FFF8EE", "#F6F4EA"), acc="#9A4C1A", day="#FAF6F0", tdy="#FDEBD3", ring="#EDB177",
               dot="#EDB177", c1="#FDEFE2", c2="#F7EBEE", band=("#F5C49B", "#F1DFAE", "#E8B7BF", "#CFDDC4"), em=("🍂", "🦃", "🌾")),
    "12": dict(name="Christmas", bg=("#FFF7F7", "#F0F8F3"), acc="#A63434", day="#F7F8F6", tdy="#FDECEC", ring="#F0A5A5",
               dot="#8CC7A2", c1="#FDEFEF", c2="#EAF5EE", band=("#F2B0B0", "#F6E3A6", "#A9D8B8"), em=("🎄", "⭐", "❄️")),
}

# Not live until Matt approves all 12 previews (build_theme_preview.py / shots_theme/theme_MM.png). Set True to ship.
LIVE = False

EMOJI_FONT = '"Noto Color Emoji","Apple Color Emoji","Segoe UI Emoji",sans-serif'


def css() -> str:
    r = []
    for mm, t in THEMES.items():
        band = ",".join(t["band"])
        r.append(f'html[data-theme="{mm}"]{{--th-bg1:{t["bg"][0]};--th-bg2:{t["bg"][1]};--th-acc:{t["acc"]};--th-day:{t["day"]};'
                 f'--th-tdy:{t["tdy"]};--th-ring:{t["ring"]};--th-dot:{t["dot"]};--th-c1:{t["c1"]};--th-c2:{t["c2"]};'
                 f'--th-band:linear-gradient(90deg,{band});--th-e1:"{t["em"][0]}";--th-e2:"{t["em"][1]}";--th-e3:"{t["em"][2]}"}}')
    T = "html[data-theme]"
    r.append(f"""{T},{T} body{{background:linear-gradient(160deg,var(--th-bg1) 0%,var(--th-bg2) 100%) fixed}}
{T} body::before{{content:"";position:fixed;left:0;right:0;top:0;height:6px;background:var(--th-band);z-index:5;pointer-events:none}}
{T} .motto,{T} .date b{{color:var(--th-acc)}}
{T} .day{{background:var(--th-day)}}
{T} .day.today{{background:var(--th-tdy);box-shadow:inset 0 0 0 3px var(--th-ring)}}
{T} #nav{{background:rgba(255,255,255,.88)}}
{T} #nav .dot.on{{background:var(--th-dot)}}
{T} .sc.cfm{{background:var(--th-c1)}} {T} .sc.fsy{{background:var(--th-c2)}}
{T} .fam::after{{content:var(--th-e1) " " var(--th-e2) " " var(--th-e3);font-family:{EMOJI_FONT};font-size:.62em;letter-spacing:-.05em;word-spacing:-.12em;margin-left:.4em;vertical-align:.12em;opacity:.9;white-space:nowrap}}
#thdeco{{display:none}}
{T} #thdeco{{display:block;position:fixed;inset:0;pointer-events:none;overflow:hidden;z-index:-1}}
#thdeco i{{position:absolute;font-style:normal;font-family:{EMOJI_FONT};opacity:.16;line-height:1}}
#thdeco i:nth-child(1)::before{{content:var(--th-e1)}} #thdeco i:nth-child(2)::before{{content:var(--th-e2)}} #thdeco i:nth-child(3)::before{{content:var(--th-e3)}}
#thdeco i:nth-child(1){{left:31%;top:1.2vh;font-size:4.2vh;transform:rotate(-12deg)}}
#thdeco i:nth-child(2){{left:38%;top:5.6vh;font-size:3vh;transform:rotate(10deg)}}
#thdeco i:nth-child(3){{left:44.5%;top:1.6vh;font-size:3.6vh;transform:rotate(-4deg)}}
@media (max-width:1500px),(orientation:portrait){{#thdeco i{{display:none}}}}""")
    return "<style id=\"mtheme\">\n" + "\n".join(r) + "\n</style>"


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
