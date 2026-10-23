#!/usr/bin/env python3
"""Wrap src/orientation.html into an installable PWA in docs/ (served by GitHub Pages).

The source file is a bare page body (no <html>/<head>) so it can also be published
as a claude.ai Artifact unchanged. This script adds the document skeleton, the web
app manifest, home-screen icons and an offline service worker.
"""
import hashlib
import json
import pathlib

ROOT = pathlib.Path(__file__).parent
SRC = ROOT / "src" / "orientation.html"
OUT = ROOT / "docs"

HEAD = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="description" content="Diegetic SCP Foundation orientation: learn the lore, terms and reading habits of the SCP Wiki.">
<link rel="manifest" href="manifest.webmanifest">
<link rel="icon" href="icon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="icon-192.png">
<style>
:root { color-scheme: light; padding-top: env(safe-area-inset-top, 0px); padding-bottom: env(safe-area-inset-bottom, 0px); }
body { margin: 0; }
img { max-width: 100%; }
[hidden] { display: none !important; }
</style>
"""

TAIL = """
<script>
if ("serviceWorker" in navigator) {
  window.addEventListener("load", function () { navigator.serviceWorker.register("sw.js").catch(function () {}); });
}
</script>
</body>
</html>
"""

ICON_SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
<rect width="100" height="100" fill="#15191B"/>
<g transform="translate(50 50) scale(.72) translate(-50 -50)" color="#E2A84A">
<circle cx="50" cy="50" r="38" fill="none" stroke="currentColor" stroke-width="8"/>
<circle cx="50" cy="50" r="13" fill="none" stroke="currentColor" stroke-width="6"/>
<g><rect x="46.5" y="2" width="7" height="20" fill="currentColor"/><polygon points="38,20 62,20 50,34" fill="currentColor"/></g>
<g transform="rotate(120 50 50)"><rect x="46.5" y="2" width="7" height="20" fill="currentColor"/><polygon points="38,20 62,20 50,34" fill="currentColor"/></g>
<g transform="rotate(240 50 50)"><rect x="46.5" y="2" width="7" height="20" fill="currentColor"/><polygon points="38,20 62,20 50,34" fill="currentColor"/></g>
</g>
</svg>
"""


def main():
    body = SRC.read_text(encoding="utf-8")
    # The source starts with <title>/<meta>/<link>/<style> (head material) followed by markup.
    split = body.index("</style>") + len("</style>")
    html = HEAD + body[:split] + "\n</head>\n<body>\n" + body[split:] + TAIL
    OUT.mkdir(exist_ok=True)
    (OUT / "index.html").write_text(html, encoding="utf-8")
    (OUT / "icon.svg").write_text(ICON_SVG, encoding="utf-8")

    manifest = {
        "name": "SCP Agent Orientation",
        "short_name": "SCP Orientation",
        "description": "Diegetic SCP Foundation orientation terminal.",
        "start_url": "./",
        "scope": "./",
        "display": "standalone",
        "orientation": "portrait",
        "background_color": "#15191B",
        "theme_color": "#15191B",
        "icons": [
            {"src": "icon-192.png", "sizes": "192x192", "type": "image/png"},
            {"src": "icon-512.png", "sizes": "512x512", "type": "image/png"},
            {"src": "icon-maskable-512.png", "sizes": "512x512", "type": "image/png", "purpose": "maskable"},
            {"src": "icon.svg", "sizes": "any", "type": "image/svg+xml"},
        ],
    }
    (OUT / "manifest.webmanifest").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    # Cache name changes whenever the page changes, so installed copies pick up updates.
    version = hashlib.sha1(html.encode("utf-8")).hexdigest()[:10]
    sw = f"""const CACHE = "scp-orientation-{version}";
const ASSETS = ["./", "index.html", "manifest.webmanifest", "icon.svg", "icon-192.png", "icon-512.png"];
self.addEventListener("install", e => {{
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(ASSETS)).then(() => self.skipWaiting()));
}});
self.addEventListener("activate", e => {{
  e.waitUntil(caches.keys().then(keys => Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k)))).then(() => self.clients.claim()));
}});
self.addEventListener("fetch", e => {{
  if (e.request.method !== "GET") return;
  e.respondWith(caches.match(e.request).then(hit => hit || fetch(e.request).then(res => {{
    if (res.ok && (e.request.url.startsWith(self.location.origin) || e.request.url.includes("fonts.g"))) {{
      const copy = res.clone(); caches.open(CACHE).then(c => c.put(e.request, copy));
    }}
    return res;
  }}).catch(() => caches.match("index.html"))));
}});
"""
    (OUT / "sw.js").write_text(sw, encoding="utf-8")
    print("built docs/ (cache", version + ")")


if __name__ == "__main__":
    main()
