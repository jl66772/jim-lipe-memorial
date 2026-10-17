# Jim Lipe Jr. memorial site (DRAFT, not published)

A static site: `index.html`, `assets/`, `media/`. There's no build tooling beyond Python with Pillow and ffmpeg.

## Update with new photos
1. `python3 /workspace/kululu/sync.py`  (pulls new Kululu uploads into the source folder)
2. `python3 build.py`  (processes only new media and regenerates index.html)

## Edit content
- `site.json`: title, name, dates, dedication, featured photo (a file stem from the source folder), and the section list and order.
- `content/*.html`: the HTML for each section. To add a section, create a file and add `{"id","title","file"}` to `sections`. The first section appears before Photos and the rest come after Videos.

## Media processing
Photos become 1600px WebP (lightbox) and 400px square WebP thumbs. Images are re-encoded, so EXIF and GPS data are stripped. GIFs use their first frame.
Videos become H.264 MP4 at 720p, CRF 27, with metadata stripped and a JPG poster frame.

## Preview
`python3 -m http.server 8765` and open http://localhost:8765. Screenshots are in `preview/` (script: /tmp/shot.py, venv /workspace/.pwvenv).

## Publish later (GitHub Pages)
(Done. See "Published" below.)

## Published
- Repo: https://github.com/jl66772/jim-lipe-memorial
- Live: https://jl66772.github.io/jim-lipe-memorial/
- Update: `./publish.sh` rebuilds, commits any changes with a dated message, and pushes. After the push, Pages redeploys in about a minute. For the daily job, run `python3 /workspace/kululu/sync.py && /workspace/jim-memorial-site/publish.sh`.
- Search engines: `index.html` has `<meta name="robots" content="noindex">`, so the site can be shared by link but isn't listed in search results. To allow indexing, remove that line from the template in `build.py`, then publish.
