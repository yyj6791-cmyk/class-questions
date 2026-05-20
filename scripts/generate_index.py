#!/usr/bin/env python3
"""Scans all HTML files and generates a beautiful index.html."""

import re
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).parent.parent

SKIP = {"index.html", "design-system.html"}

FOLDER_LABELS = {
    "articles": "Articles",
    "specs":    "Specs",
    "reviews":  "Reviews",
    "reports":  "Reports",
    "explore":  "Explore",
    "tools":    "Tools",
}

FOLDER_GRADIENTS = {
    "articles": [("d95f2b","b84820"), ("bf4e20","9e3c16"), ("e07035","c85428"), ("b85020","9a3e16")],
    "specs":    [("2d5a8e","1e3d6b"), ("234e80","163460"), ("3666a0","244e82"), ("1e3d6b","122845")],
    "reviews":  [("3a6b4a","2a4f38"), ("2e5c3e","1e4029"), ("468060","325a46"), ("2a4f38","1a3526")],
    "reports":  [("8a6a00","6b5200"), ("7a5e00","5e4800"), ("9a7800","7a6000"), ("6b5200","503c00")],
    "explore":  [("6b48c8","4e34a0"), ("5c3cb8","422890"), ("7a58d4","5e44b0"), ("4e34a0","362280")],
    "tools":    [("2a7a7a","1d5555"), ("1e6868","144848"), ("348888","226666"), ("1d5555","103838")],
}
FOLDER_GRADIENT_DEFAULT = [("6b6a63","4a4a45")]


def get_title(path: Path) -> str:
    text = path.read_text(encoding="utf-8", errors="ignore")
    m = re.search(r"<title>(.*?)</title>", text, re.IGNORECASE | re.DOTALL)
    return m.group(1).strip() if m else path.stem.replace("-", " ").title()


def get_description(path: Path) -> str:
    text = path.read_text(encoding="utf-8", errors="ignore")
    m = re.search(r'<meta\s+name=["\']description["\']\s+content=["\'](.*?)["\']', text, re.IGNORECASE)
    return m.group(1).strip() if m else ""


def get_date(path: Path) -> str:
    m = re.match(r"(\d{4}-\d{2}-\d{2})", path.stem)
    return m.group(1) if m else ""


def get_og_image(path: Path) -> str:
    text = path.read_text(encoding="utf-8", errors="ignore")
    m = re.search(r'<meta\s+property=["\']og:image["\']\s+content=["\'](.*?)["\']', text, re.IGNORECASE)
    if not m:
        m = re.search(r'<meta\s+content=["\'](.*?)["\']\s+property=["\']og:image["\']', text, re.IGNORECASE)
    return m.group(1).strip() if m else ""


def collect_files():
    folders = {}
    for html in sorted(ROOT.rglob("*.html"), reverse=True):
        if html.name in SKIP:
            continue
        rel = html.relative_to(ROOT)
        parts = rel.parts
        folder = parts[0] if len(parts) > 1 else "."
        if folder.startswith("."):
            continue
        folders.setdefault(folder, []).append({
            "path": rel.as_posix(),
            "title": get_title(html),
            "description": get_description(html),
            "date": get_date(html),
            "og_image": get_og_image(html),
        })
    return folders


BACK_BUTTON_MARKER = 'id="back-to-index"'


def _back_button_snippet(depth: int) -> str:
    prefix = "../" * depth
    return (
        '\n<!-- Back to index -->\n'
        f'<a id="back-to-index" href="{prefix}index.html"'
        ' aria-label="목록으로 돌아가기" title="목록으로">'
        '<svg viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg"'
        ' width="18" height="18">'
        '<path d="M8.5 15L3 10l5.5-5" stroke="white" stroke-width="2"'
        ' stroke-linecap="round" stroke-linejoin="round"/>'
        '<path d="M3 10h14" stroke="white" stroke-width="2" stroke-linecap="round"/>'
        '</svg></a>\n'
        '<style>\n'
        '#back-to-index{position:fixed;bottom:1.5rem;left:1.5rem;width:44px;height:44px;'
        'background:#6b6a63;color:#fff;border-radius:9999px;display:flex;'
        'align-items:center;justify-content:center;text-decoration:none;'
        'box-shadow:0 4px 16px rgba(0,0,0,.18);transition:background .15s,transform .15s;z-index:800;}\n'
        '#back-to-index:hover{background:#d95f2b;transform:translateX(-2px);}\n'
        '@media(max-width:600px){#back-to-index{bottom:1rem;left:1rem;}}\n'
        '</style>\n'
    )


def inject_back_button(path: Path) -> bool:
    text = path.read_text(encoding="utf-8", errors="ignore")
    if BACK_BUTTON_MARKER in text:
        return False
    if "</body>" not in text:
        return False
    rel = path.relative_to(ROOT)
    depth = len(rel.parts) - 1
    snippet = _back_button_snippet(depth)
    path.write_text(text.replace("</body>", snippet + "</body>", 1), encoding="utf-8")
    return True


def render_tab_buttons(folders):
    all_btn = '<button class="tab-btn active" onclick="filterFolder(\'all\', this)">All</button>'
    folder_btns = ""
    for folder in folders:
        label = FOLDER_LABELS.get(folder, folder.title())
        folder_btns += f'<button class="tab-btn" onclick="filterFolder(\'{folder}\', this)">{label}</button>'
    return all_btn + folder_btns


def render_cards(folders):
    html = ""
    for folder, files in folders.items():
        label = FOLDER_LABELS.get(folder, folder.title())
        variants = FOLDER_GRADIENTS.get(folder, FOLDER_GRADIENT_DEFAULT)
        for idx, f in enumerate(files):
            date_str = f"<span class='card-date'>{f['date']}</span>" if f["date"] else ""
            desc_str = f"<p class='card-desc'>{f['description']}</p>" if f["description"] else ""
            c1, c2 = variants[idx % len(variants)]
            if f["og_image"]:
                thumb = f"<div class='card-thumb'><img src='{f['og_image']}' alt='' loading='lazy'></div>"
            else:
                safe_title = f["title"].replace("<", "&lt;").replace(">", "&gt;")
                thumb = (
                    f"<div class='card-thumb card-thumb-grad'"
                    f" style='background:linear-gradient(135deg,#{c1},#{c2})'>"
                    f"<span class='card-thumb-text'>{safe_title}</span></div>"
                )
            html += f"""
    <a class="card" href="{f['path']}" data-folder="{folder}">
      {thumb}
      <div class="card-body">
        <div class="card-header">
          <span class="card-folder">{label}</span>
          {date_str}
        </div>
        <h3 class="card-title">{f['title']}</h3>
        {desc_str}
      </div>
    </a>"""
    return html


def build(folders):
    tab_buttons = render_tab_buttons(folders)
    cards = render_cards(folders)
    total = sum(len(v) for v in folders.values())
    generated = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

    return f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>My HTML Library</title>
<style>
:root {{
  --color-bg:#f5f2ed; --color-bg-alt:#eceae4; --color-bg-card:#ffffff;
  --color-text:#1a1a18; --color-text-muted:#6b6a63; --color-text-faint:#a09f97;
  --color-border:#dedad2; --color-accent:#d95f2b; --color-accent-hover:#c2521f;
  --color-accent-soft:#faeee7;
  --font-sans:-apple-system,BlinkMacSystemFont,"Segoe UI",Helvetica,Arial,sans-serif;
  --text-sm:0.875rem; --text-base:1rem; --text-lg:1.125rem; --text-2xl:1.5rem; --text-3xl:1.875rem;
  --weight-medium:500; --weight-semibold:600; --weight-bold:700;
  --space-2:0.5rem; --space-3:0.75rem; --space-4:1rem; --space-6:1.5rem;
  --space-8:2rem; --space-12:3rem;
  --radius-md:8px; --radius-lg:12px;
  --shadow-sm:0 1px 3px rgba(0,0,0,0.07); --shadow-md:0 4px 12px rgba(0,0,0,0.08);
}}
*,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:var(--font-sans);background:var(--color-bg);color:var(--color-text);min-height:100vh}}
header{{background:var(--color-bg-card);border-bottom:1px solid var(--color-border);padding:var(--space-6) var(--space-8);display:flex;align-items:baseline;gap:var(--space-4);}}
header h1{{font-size:var(--text-2xl);font-weight:var(--weight-bold);}}
header .meta{{font-size:var(--text-sm);color:var(--color-text-faint);margin-left:auto}}
.container{{max-width:1100px;margin:0 auto;padding:var(--space-8)}}
.toolbar{{display:flex;align-items:center;gap:var(--space-2);flex-wrap:wrap;margin-bottom:var(--space-6)}}
.tab-btn{{padding:var(--space-2) var(--space-4);border:1px solid var(--color-border);background:var(--color-bg-card);color:var(--color-text-muted);border-radius:var(--radius-md);font-size:var(--text-sm);font-weight:var(--weight-medium);cursor:pointer;transition:all 120ms ease;}}
.tab-btn:hover{{border-color:var(--color-accent);color:var(--color-accent)}}
.tab-btn.active{{background:var(--color-accent);border-color:var(--color-accent);color:#fff}}
.search{{margin-left:auto}}
.search input{{padding:var(--space-2) var(--space-4);border:1px solid var(--color-border);border-radius:var(--radius-md);font-size:var(--text-sm);background:var(--color-bg-card);color:var(--color-text);outline:none;width:200px;}}
.search input:focus{{border-color:var(--color-accent)}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:var(--space-4)}}
.card{{background:var(--color-bg-card);border:1px solid var(--color-border);border-radius:var(--radius-lg);text-decoration:none;color:inherit;display:flex;flex-direction:column;overflow:hidden;box-shadow:var(--shadow-sm);transition:all 180ms ease;}}
.card:hover{{box-shadow:var(--shadow-md);border-color:var(--color-accent);transform:translateY(-2px)}}
.card-thumb{{width:100%;height:140px;overflow:hidden;flex-shrink:0;}}
.card-thumb img{{width:100%;height:100%;object-fit:cover;display:block;}}
.card-thumb-grad{{display:flex;align-items:flex-end;padding:var(--space-4);}}
.card-thumb-text{{font-size:var(--text-sm);font-weight:var(--weight-semibold);color:rgba(255,255,255,0.95);line-height:1.45;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;text-shadow:0 1px 6px rgba(0,0,0,0.35);}}
.card-body{{padding:var(--space-6);flex:1;display:flex;flex-direction:column;gap:var(--space-3);}}
.card-header{{display:flex;align-items:center;justify-content:space-between;}}
.card-folder{{font-size:var(--text-sm);font-weight:var(--weight-medium);color:var(--color-accent);background:var(--color-accent-soft);padding:3px var(--space-3);border-radius:var(--radius-md);}}
.card-date{{font-size:var(--text-sm);color:var(--color-text-faint)}}
.card-title{{font-size:var(--text-lg);font-weight:var(--weight-semibold);line-height:1.5;letter-spacing:-0.01em;margin-top:var(--space-1);}}
.card-desc{{font-size:var(--text-sm);color:var(--color-text-muted);line-height:1.7;}}
.empty{{text-align:center;color:var(--color-text-faint);padding:var(--space-12);font-size:var(--text-lg)}}
footer{{text-align:center;padding:var(--space-8);color:var(--color-text-faint);font-size:var(--text-sm);border-top:1px solid var(--color-border);margin-top:var(--space-12)}}
@media(max-width:600px){{header{{padding:var(--space-4)}}.container{{padding:var(--space-4)}}.search input{{width:100%}}.toolbar{{flex-direction:column;align-items:stretch}}.search{{margin-left:0}}}}
</style>
</head>
<body>
<header>
  <h1>My HTML Library</h1>
  <span class="meta">{total} files · Updated {generated}</span>
</header>
<div class="container">
  <div class="toolbar">
    {tab_buttons}
    <div class="search"><input type="text" placeholder="Search..." oninput="filterSearch(this.value)"></div>
  </div>
  <div class="grid" id="grid">{cards}</div>
  <div class="empty" id="empty" style="display:none">No files found.</div>
</div>
<footer>Generated by GitHub Actions · <a href="design-system.html" style="color:var(--color-accent)">Design System</a></footer>
<script>
let currentFolder = 'all', currentSearch = '';
function update() {{
  const cards = document.querySelectorAll('.card');
  let visible = 0;
  cards.forEach(c => {{
    const show = (currentFolder === 'all' || c.dataset.folder === currentFolder)
              && (!currentSearch || c.textContent.toLowerCase().includes(currentSearch));
    c.style.display = show ? '' : 'none';
    if (show) visible++;
  }});
  document.getElementById('empty').style.display = visible === 0 ? '' : 'none';
}}
function filterFolder(folder, btn) {{
  currentFolder = folder;
  document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  update();
}}
function filterSearch(val) {{ currentSearch = val.toLowerCase(); update(); }}
</script>
</body>
</html>
"""


if __name__ == "__main__":
    injected = 0
    for html in sorted(ROOT.rglob("*.html")):
        if html.name in SKIP:
            continue
        rel = html.relative_to(ROOT)
        if rel.parts[0].startswith("."):
            continue
        if inject_back_button(html):
            injected += 1
    if injected:
        print(f"Injected back-to-index button into {injected} file(s)")

    folders = collect_files()
    html_out = build(folders)
    out = ROOT / "index.html"
    out.write_text(html_out, encoding="utf-8")
    total = sum(len(v) for v in folders.values())
    print(f"Generated index.html — {total} files across {len(folders)} folders")
