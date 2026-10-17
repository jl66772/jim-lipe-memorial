#!/usr/bin/env python3
"""Rebuild the memorial site from the Kululu source folder. Incremental: only new media is processed.
Usage: python3 build.py   (then open index.html or serve the folder)"""
import json, os, subprocess, html, sys
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

def main():
    for d in ('full','thumb','video'): os.makedirs(f'{M}/{d}', exist_ok=True)
    files = sorted(os.listdir(SRC))  # names start with UTC timestamp => chronological
    photos = [f for f in files if f.lower().endswith(IMG_EXT)]
    videos = [f for f in files if f.lower().endswith(VID_EXT)]
    with ProcessPoolExecutor() as ex: stems = [s for s in ex.map(do_photo, photos) if s]
    vstems = [do_video(v) for v in videos]
    feat = CFG.get('featured') or stems[0]
    feat = os.path.splitext(feat)[0]
    e = html.escape
    secs = CFG['sections']
    before = [s for s in secs if s.get('position','after') == 'before']
    after = [s for s in secs if s.get('position','after') != 'before']
    navl = [(s['id'], s.get('nav', s['title'])) for s in before] + [('photos', CFG.get('photos_nav','Photos'))]
    if vstems: navl.append(('videos', CFG.get('videos_nav','Videos')))
    navl += [(s['id'], s.get('nav', s['title'])) for s in after]
    nav = ''.join(f'<a href="#{i}">{e(t)}</a>' for i, t in navl)
    def sec(s): return f'<section id="{s["id"]}"><h2>{e(s["title"])}</h2>\n{open(os.path.join(ROOT,s["file"])).read()}</section>\n'
    grid = '\n'.join(f'<a href="media/full/{s}.webp"><img src="media/thumb/{s}.webp" loading="lazy" decoding="async" width="400" height="400" alt="Photo of Jim shared by family and friends"></a>' for s in stems)
    vids = '\n'.join(f'<video controls preload="none" playsinline poster="media/video/{s}.jpg" src="media/video/{s}.mp4"></video>' for s in vstems)
    note = CFG.get('photos_note','{n} photos').format(n=len(stems))
    page = f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(CFG.get("page_title", CFG["title"]))}</title><meta name="robots" content="noindex"><link rel="stylesheet" href="assets/style.css"></head><body>
<nav>{nav}</nav>
<header class="hero"><img src="media/full/{feat}.webp" alt="{e(CFG["full_name"])}">
<div class="eyebrow">{e(CFG.get("eyebrow","In Loving Memory"))}</div><h1>{e(CFG["title"])}</h1><div class="subname">{e(CFG["full_name"])}</div><div class="dates">{e(CFG["dates"])}</div>
<p class="dedication">{e(CFG["dedication"])}</p></header>
{''.join(sec(s) for s in before)}
<section id="photos"><h2>{e(CFG.get("photos_title","Photos"))}</h2><p class="placeholder" style="font-style:normal">{e(note)}</p><div class="grid">
{grid}
</div></section>
{f'<section id="videos"><h2>{e(CFG.get("videos_title","Videos"))}</h2><div class="videos">{vids}</div></section>' if vstems else ''}
{''.join(sec(s) for s in after)}
<footer>{e(CFG.get("footer",""))}<span class="credit">{e(CFG.get("footer_credit",""))}</span></footer>
<div id="lb"><button class="close" aria-label="Close">&times;</button><button class="prev" aria-label="Previous">&#8249;</button><img alt=""><button class="next" aria-label="Next">&#8250;</button><div class="count"></div></div>
<script src="assets/lightbox.js"></script></body></html>'''
    open(os.path.join(ROOT,'index.html'),'w').write(page)
    print(f'Built: {len(stems)} photos, {len(vstems)} videos, featured={feat}')
if __name__ == '__main__': main()
