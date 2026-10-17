#!/usr/bin/env python3
"""Rebuild the memorial site from the Kululu source folder. Incremental: only new media is processed.
Usage: python3 build.py   (then open index.html or serve the folder)"""
import json, os, subprocess, html, sys, datetime
from PIL.ExifTags import IFD
from concurrent.futures import ProcessPoolExecutor
from PIL import Image, ImageOps
ROOT = os.path.dirname(os.path.abspath(__file__))
CFG = json.load(open(os.path.join(ROOT, 'site.json')))
SRC = CFG['source_dir']
IMG_EXT = ('.jpg', '.jpeg', '.png', '.gif', '.webp', '.heic')
VID_EXT = ('.mov', '.mp4', '.m4v')
M = os.path.join(ROOT, 'media')

def do_photo(name):
    stem = os.path.splitext(name)[0]
    full, thumb = f'{M}/full/{stem}.webp', f'{M}/thumb/{stem}.webp'
    if os.path.exists(full) and os.path.exists(thumb): return stem
    try:
        im = Image.open(os.path.join(SRC, name)); im.seek(0)
        im = ImageOps.exif_transpose(im).convert('RGB')   # new image => no EXIF/GPS kept
        a = im.copy(); a.thumbnail((1600, 1600)); a.save(full, 'WEBP', quality=80, method=4)
        b = ImageOps.fit(im, (400, 400)); b.save(thumb, 'WEBP', quality=72, method=4)
        return stem
    except Exception as e:
        print('SKIP', name, e, file=sys.stderr); return None

def do_video(name):
    stem = os.path.splitext(name)[0]
    out, poster = f'{M}/video/{stem}.mp4', f'{M}/video/{stem}.jpg'
    if not os.path.exists(out):
        subprocess.run(['ffmpeg','-v','error','-y','-i',os.path.join(SRC,name),'-map_metadata','-1',
            '-vf',"scale='if(gt(iw,ih),-2,min(720,iw))':'if(gt(iw,ih),min(720,ih),-2)'",
            '-c:v','libx264','-preset','medium','-crf','27','-maxrate','2.5M','-bufsize','5M',
            '-pix_fmt','yuv420p','-c:a','aac','-b:a','96k','-movflags','+faststart',out+'.tmp.mp4'], check=True)
        os.replace(out+'.tmp.mp4', out)
    if not os.path.exists(poster):
        subprocess.run(['ffmpeg','-v','error','-y','-ss','1','-i',out,'-frames:v','1','-q:v','4',poster], check=True)
    return stem

def exif_info(name):
    """Offline only: returns (year or None, region id or None). Coordinates are never written anywhere."""
    try:
        ex = Image.open(os.path.join(SRC, name)).getexif()
        dt = ex.get_ifd(IFD.Exif).get(36867) or ex.get(306)
        year = int(dt[:4]) if dt and dt[:4].isdigit() and int(dt[:4]) > 1900 else None
        # Dates on/after the passing are almost always re-photographed prints/screenshots, so treat as undated
        if year and dt[:10].replace(':', '-') >= CFG.get('undated_after', '2026-09-26'): year = None
        g = ex.get_ifd(IFD.GPSInfo); region = None
        if g.get(2) and g.get(4):
            dms = lambda v: float(v[0]) + float(v[1]) / 60 + float(v[2]) / 3600
            lat = dms(g[2]) * (-1 if g.get(1) == 'S' else 1); lon = dms(g[4]) * (-1 if g.get(3) == 'W' else 1)
            for r in CFG.get('map_regions', []):
                a, b, c, d = r['box']
                if a <= lat <= c and b <= lon <= d: region = r['id']; break
        return year, region
    except Exception:
        return None, None

e = html.escape
def thumbs(stems, cls='grid'):
    return f'<div class="{cls}">' + ''.join(f'<a class="lb" href="media/full/{s}.webp"><img src="media/thumb/{s}.webp" loading="lazy" decoding="async" width="400" height="400" alt="Photo of Jim shared by family and friends"></a>' for s in stems) + '</div>'

def page(fname, title, nav, body, extra_head='', extra_js=''):
    open(os.path.join(ROOT, fname), 'w').write(f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(title)}</title><meta name="robots" content="noindex"><link rel="stylesheet" href="assets/style.css">{extra_head}</head><body>
{nav}
{body}
<footer>{e(CFG.get("footer",""))}<span class="credit">{e(CFG.get("footer_credit",""))}</span></footer>
<div id="lb"><button class="close" aria-label="Close">&times;</button><button class="prev" aria-label="Previous">&#8249;</button><img alt=""><button class="next" aria-label="Next">&#8250;</button><div class="count"></div></div>
<script src="assets/lightbox.js"></script>{extra_js}</body></html>""")

def main():
    for d in ('full','thumb','video'): os.makedirs(f'{M}/{d}', exist_ok=True)
    files = sorted(os.listdir(SRC))
    photos = [f for f in files if f.lower().endswith(IMG_EXT)]
    videos = [f for f in files if f.lower().endswith(VID_EXT)]
    with ProcessPoolExecutor() as ex:
        stems = [s for s in ex.map(do_photo, photos) if s]
        info = dict(zip([os.path.splitext(p)[0] for p in photos], ex.map(exif_info, photos)))
    vstems = [do_video(v) for v in videos]
    feat = os.path.splitext(CFG.get('featured') or stems[0])[0]
    today = datetime.date.today().isoformat()
    secs = CFG['sections']

    def navbar(prefix):
        main_l = [(s['id'], s['nav']) for s in secs if s.get('nav') and not s.get('more')]
        more_l = [(s['id'], s['nav']) for s in secs if s.get('nav') and s.get('more')]
        a = ''.join(f'<a href="{prefix}#{i}">{e(t)}</a>' for i, t in main_l)
        a += '<a href="timeline.html">Timeline</a><a href="map.html">Map</a>'
        a += '<details class="more"><summary>More</summary><div>' + ''.join(f'<a href="{prefix}#{i}">{e(t)}</a>' for i, t in more_l) + '</div></details>'
        return f'<nav><a class="home" href="{prefix or "#top"}">Home</a>{a}</nav>'

    def b_potd():
        return ('<div class="potd"><a id="potd-link" class="potd-img" href="#"><img id="potd-img" alt="Photo of the day"></a>'
                '<div><div class="eyebrow">Photo of the Day</div><p>A different photo of your dad every day. Tap to see it bigger.</p></div></div>')
    def b_photos(): return f'<p class="placeholder" style="font-style:normal">{e(CFG.get("photos_note","{n} photos").format(n=len(stems)))}</p>' + thumbs(stems)
    def b_videos(): return '<div class="videos">' + ''.join(f'<video controls preload="none" playsinline poster="media/video/{s}.jpg" src="media/video/{s}.mp4"></video>' for s in vstems) + '</div>'
    def b_memories():
        mem = json.load(open(os.path.join(ROOT, 'content/memories.json'))).get('memories', [])
        prompts = ["My favorite Jim story", "What I'd want James to know about her dad", "The funniest thing he ever did", "An adventure we shared"]
        h = '<p class="center">Did you know Jim? Share a memory for James using one of these prompts:</p><div class="prompts">' + ''.join(f'<span>{e(p)}</span>' for p in prompts) + '</div>'
        url = CFG.get('share_memory_url')
        h += '<p class="cta">' + (f'<a href="{e(url)}" target="_blank" rel="noopener">Share a memory</a>' if url else '<a class="disabled" aria-disabled="true">Share a memory <small>[form link coming soon]</small></a>')
        h += f' <a href="{e(CFG["kululu_upload_url"])}" target="_blank" rel="noopener">Add your photos</a></p>'
        if mem:
            h += '<div class="memcards">' + ''.join(f'<blockquote class="memcard"><div class="eyebrow">{e(m.get("prompt",""))}</div><p>{e(m["text"])}</p><cite>{e(m.get("name",""))}</cite></blockquote>' for m in mem) + '</div>'
        else:
            h += '<p class="placeholder">[Approved memories from family and friends will appear here]</p>'
        return h
    def b_letters():
        try: L = json.load(open(CFG['letters_file'])).get('letters', [])
        except FileNotFoundError: L = []
        h = '<p class="center prose">Family and friends are writing letters for you to open at special moments in your life. Each one stays sealed until its day comes.</p><div class="letters">'
        for l in sorted(L, key=lambda x: x['unlock']):
            frm = e(l['from']) if l.get('show_from', True) else 'Someone who loves you'
            if l['unlock'] <= today and not l.get('example'):
                h += f'<article class="letter open"><div class="eyebrow">{e(l.get("label",""))}</div><p>{e(l["text"]).replace(chr(10),"<br>")}</p><cite>From {frm}</cite></article>'
            else:  # sealed: letter text is NEVER written to the site
                d = datetime.date.fromisoformat(l['unlock']).strftime('%B %-d, %Y')
                h += f'<article class="letter sealed"><div class="seal">✉</div><div class="eyebrow">Sealed</div><h3>{e(l.get("label") or "Opens on " + d)}</h3><p>Opens {d}</p><cite>From {frm}</cite></article>'
        return h + '</div>' + ('' if L else '<p class="placeholder">[No letters yet]</p>')
    def b_playlist():
        u = CFG.get('playlist_embed_url')
        if u: return f'<div class="playlist"><iframe src="{e(u)}" loading="lazy" allow="autoplay; clipboard-write; encrypted-media; picture-in-picture" title="Dad&#39;s Playlist"></iframe></div>'
        return '<div class="soon">♪<p>Playlist coming soon</p><p class="placeholder">[Songs your dad loved, to be added by family]</p></div>'
    B = dict(potd=b_potd, photos=b_photos, videos=b_videos, memories=b_memories, letters=b_letters, playlist=b_playlist)
    def sec(s):
        inner = B[s['builtin']]() if s.get('builtin') else open(os.path.join(ROOT, s['file'])).read()
        h2 = '' if s.get('builtin') == 'potd' else f'<h2>{e(s["title"])}</h2>'
        return f'<section id="{s["id"]}">{h2}\n{inner}</section>\n'

    hero = (f'<header class="hero" id="top"><div id="special" class="special" hidden></div><img src="media/full/{feat}.webp" alt="{e(CFG["full_name"])}">'
            f'<div class="eyebrow">{e(CFG.get("eyebrow",""))}</div><h1>{e(CFG["title"])}</h1><div class="subname">{e(CFG["full_name"])}</div><div class="dates">{e(CFG["dates"])}</div>'
            f'<p class="dedication">{e(CFG["dedication"])}</p></header>')
    data = dict(photos=stems, birthday=CFG.get('birthday',''), birthday_note=CFG.get('birthday_note',''), birthday_photo=CFG.get('birthday_photo',''),
                remembrance=CFG.get('remembrance_date',''), remembrance_note=CFG.get('remembrance_note',''), remembrance_photo=CFG.get('remembrance_photo',''))
    js = f'<script>window.SITE={json.dumps(data)};</script><script src="assets/home.js"></script>'
    page('index.html', CFG.get('page_title', CFG['title']), navbar(''), hero + ''.join(sec(s) for s in secs), extra_js=js)

    T = json.load(open(os.path.join(ROOT, 'timeline.json')))
    groups = {}
    for s in stems:
        y = T.get('move', {}).get(s, info.get(s, (None,))[0])
        groups.setdefault(str(y) if y else 'undated', []).append(s)
    markers = {}
    for m in T.get('markers', []): markers.setdefault(str(m['year']), []).append(m['text'])
    years = sorted(set([k for k in groups if k != 'undated'] + list(markers)), key=int)
    tl = '<section class="timeline-intro"><h2>Full Throttle Timeline</h2><p class="center prose">Photos of your dad arranged by the year they were taken, when the photo file records a date. Milestones come from his obituary.</p></section><div class="timeline">'
    for k in years + (['undated'] if 'undated' in groups else []):
        label = 'Undated memories' if k == 'undated' else k
        era = T.get('eras', {}).get(k)
        tl += f'<div class="tl-item" id="y{k}"><div class="tl-dot"></div><h3>{e(label)}' + (f' <small>· {e(era)}</small>' if era else '') + '</h3>'
        tl += ''.join(f'<p class="milestone">★ {e(t)}</p>' for t in markers.get(k, []))
        if groups.get(k): tl += f'<p class="small">{len(groups[k])} photo{"s" if len(groups[k]) > 1 else ""}</p>' + thumbs(groups[k])
        tl += '</div>'
    tl += '</div>'
    page('timeline.html', 'Full Throttle Timeline · ' + CFG['title'], navbar('index.html'), tl)

    regs = CFG.get('map_regions', [])
    byreg = {r['id']: [s for s in stems if info.get(s, (None, None))[1] == r['id']] for r in regs}
    pins = [dict(id=r['id'], name=r['name'], caption=r['caption'], lat=r['lat'], lon=r['lon'], n=len(byreg[r['id']])) for r in regs]
    mp = '<section><h2>Dad&#39;s Adventure Map</h2><p class="center prose">Places named in your dad&#39;s story. Tap a pin to see more.</p><div id="map"></div></section>'
    for r in regs:
        ph = byreg[r['id']]
        mp += f'<section id="r-{r["id"]}"><h3 class="center">{e(r["name"])}</h3><p class="center">{e(r["caption"])}</p>'
        mp += (thumbs(ph[:24]) if ph else '<p class="placeholder">[Family can add photos from here]</p>') + '</section>'
    lh = '<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" crossorigin="">'
    lj = f'<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js" crossorigin=""></script><script>window.PINS={json.dumps(pins)};</script><script src="assets/map.js"></script>'
    page('map.html', "Dad's Adventure Map · " + CFG['title'], navbar('index.html'), mp, lh, lj)
    print(f'Built: {len(stems)} photos, {len(vstems)} videos; timeline years={len(years)} undated={len(groups.get("undated",[]))}; map=' + ', '.join(f'{k}:{len(v)}' for k, v in byreg.items()))

if __name__ == '__main__': main()
