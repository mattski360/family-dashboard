"""Synthesize 20 original celebration sounds -> assets/celebrate/NN.mp3 (numpy + ffmpeg)."""
import numpy as np, subprocess, pathlib, wave
SR=44100; OUT=pathlib.Path(__file__).parent/"assets/celebrate"; OUT.mkdir(parents=True,exist_ok=True)
rng=np.random.default_rng(7)
def t(d): return np.arange(int(SR*d))/SR
def f(n): return 440*2**((n-69)/12)
def env(x,a=.01,r=.2):
    n=len(x); e=np.ones(n); A=max(1,int(a*SR)); R=min(n,max(1,int(r*SR)))
    e[:A]=np.linspace(0,1,A); e[-R:]*=np.linspace(1,0,R); return x*e
def tone(n,d,wav="sine",a=.01,r=None,vib=0):
    tt=t(d); fr=f(n)*(1+vib*np.sin(2*np.pi*5.5*tt)); ph=2*np.pi*np.cumsum(fr)/SR
    if wav=="sine": x=np.sin(ph)+.3*np.sin(2*ph)
    elif wav=="square": x=np.sign(np.sin(ph))*.5
    elif wav=="tri": x=2/np.pi*np.arcsin(np.sin(ph))
    elif wav=="brass": x=sum(np.sin(k*ph)/k for k in range(1,8))*.6
    elif wav=="bell": x=np.sin(ph)*np.exp(-3*tt)+.5*np.sin(2.76*ph)*np.exp(-5*tt)+.25*np.sin(5.4*ph)*np.exp(-8*tt)
    return env(x,a,r if r is not None else min(.15,d*.5))
def seq(notes,wav="sine",gap=0.0,**k):
    parts=[]; 
    for n,d in notes:
        parts.append(tone(n,d,wav,**k) if n else np.zeros(int(SR*d))); parts.append(np.zeros(int(SR*gap)))
    return np.concatenate(parts)
def chord(ns,d,wav="sine",**k): return sum(tone(n,d,wav,**k) for n in ns)/len(ns)
def mix(*xs):
    L=max(len(x) for x in xs); o=np.zeros(L)
    for x in xs: o[:len(x)]+=x
    return o
def at(x,s): return np.concatenate([np.zeros(int(SR*s)),x])
def noise(d,hp=True): 
    x=rng.standard_normal(int(SR*d))
    if hp: x=np.diff(x,prepend=0)
    return x
def claps(d,rate=18):
    o=np.zeros(int(SR*d))
    for _ in range(int(d*rate)):
        s=rng.integers(0,len(o)-2000); L=int(SR*.03); o[s:s+L]+=noise(.03)[:L]*np.exp(-np.arange(L)/300)*rng.uniform(.4,1)
    return env(o,.15,.5)
S={}
S["Brass fanfare"]=mix(seq([(60,.15),(64,.15),(67,.15)],"brass"),at(chord([60,64,67,72],1.0,"brass",r=.4),.45))
S["Tada!"]=mix(tone(67,.12,"brass"),at(chord([60,64,67,72,76],1.2,"brass",a=.005,r=.8),.14))
S["Rising chime arpeggio"]=mix(*[at(tone(n,1.2,"bell",r=.6),i*.1) for i,n in enumerate([72,76,79,84,88])])
S["8-bit victory"]=seq([(72,.1),(72,.1),(72,.1),(72,.3),(68,.3),(70,.3),(72,.15),(70,.08),(72,.6)],"square",gap=.01)
S["Level up"]=seq([(n,.07) for n in [60,64,67,72,64,67,72,76,67,72,76,79]]+[(84,.4)],"square")
S["Applause burst"]=claps(2.2)
S["Applause and cheer chord"]=mix(claps(2.0)*.8,chord([67,71,74,79],1.6,"tri",r=.8)*.6)
S["Sparkle shimmer"]=mix(*[at(tone(int(rng.integers(84,100)),.4,"bell",r=.3)*.6,i*.06) for i in range(22)])
S["Doorbell ding-dong-ding"]=seq([(76,.4),(72,.4),(79,1.0)],"bell")
S["Coin collect"]=mix(seq([(83,.08),(88,.5)],"square"),at(tone(100,.3,"bell")*.3,.08))
S["Major triad pop"]=mix(*[at(tone(n,.9,"tri",r=.6),i*.07) for i,n in enumerate([65,69,72,77])])
S["Trumpet call"]=seq([(67,.12),(67,.12),(67,.12),(72,.7)],"brass",gap=.03,vib=.004)
S["Xylophone run"]=seq([(n,.08) for n in [72,74,76,77,79,81,83,84]]+[(84,.6)],"bell")
S["Whistle slide up"]=env(np.sin(2*np.pi*np.cumsum(np.linspace(600,1800,int(SR*.6)))/SR),.02,.1)
S["Whistle slide up"]=np.concatenate([S["Whistle slide up"],chord([72,76,79],.8,"tri",r=.5)])
S["Game over win"]=seq([(67,.12),(72,.12),(76,.12),(79,.12),(84,.3),(79,.12),(84,.7)],"square",gap=.01)
S["Harp glissando"]=mix(*[at(tone(n,1.0,"bell",r=.7)*.7,i*.035) for i,n in enumerate([60,62,64,67,69,72,74,76,79,81,84,86,88])])
S["Celebration horns"]=mix(seq([(60,.2),(65,.2),(69,.2),(72,.8)],"brass"),seq([(57,.2),(60,.2),(65,.2),(69,.8)],"brass")*.7)
S["Confetti pop"]=mix(env(noise(.08),.001,.07)*1.5,at(mix(*[at(tone(int(rng.integers(79,96)),.35,"bell",r=.25)*.5,i*.05) for i in range(12)]),.05))
S["Robot yay"]=seq([(64,.15),(69,.15),(76,.6)],"square",gap=.04,vib=.03)
S["Grand finish chord"]=mix(tone(48,1.8,"brass",r=1.0)*.6,at(chord([60,64,67,72,76,79],1.7,"sine",a=.1,r=1.0),.05),at(claps(1.6)*.3,.2))
names=list(S)
assert len(names)==20
for i,nm in enumerate(names,1):
    x=S[nm]; x=x/np.max(np.abs(x))*0.5   # peak -6 dBFS
    x=np.concatenate([x,np.zeros(int(SR*.05))])
    w=f"/tmp/cel{i:02d}.wav"
    with wave.open(w,"wb") as wf:
        wf.setnchannels(1);wf.setsampwidth(2);wf.setframerate(SR);wf.writeframes((x*32767).astype("<i2").tobytes())
    subprocess.run(["ffmpeg","-y","-loglevel","error","-i",w,"-af","loudnorm=I=-20:TP=-3","-ar","44100","-ac","1","-b:a","64k",str(OUT/f"{i:02d}.mp3")],check=True)
with open(OUT/"README.md","w") as fh:
    fh.write("# Chore celebration sounds\n\nOriginal sounds synthesized by `make_celebrate_sounds.py` (numpy + ffmpeg), no third-party samples. Mono 64 kbps MP3, loudness-normalized to about -20 LUFS.\n\n")
    for i,nm in enumerate(names,1): fh.write(f"- `{i:02d}.mp3`: {nm} ({len(S[nm])/SR:.1f}s)\n")
print("\n".join(names))
