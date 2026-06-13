import re
from urllib.parse import quote, urljoin
from bs4 import BeautifulSoup
from flask import Flask, render_template_string, request
import requests

app = Flask(__name__)

LANDING_PAGE = "https://dudefilms.to/"
SESSION = requests.Session()
SESSION.headers.update(
    {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
)

BASE_HTML = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>NY Movies – Watch & Download Films</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Inter:wght@300;400;500;600&display=swap" rel="stylesheet">
  <style>
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

    :root {
      --gold: #E8B84B;
      --gold-dark: #C89A2A;
      --red: #C0392B;
      --bg: #0A0A0F;
      --surface: #12121A;
      --surface2: #1A1A26;
      --border: rgba(255,255,255,0.07);
      --text: #F0EDE8;
      --muted: #8A8899;
      --radius: 10px;
    }

    html { scroll-behavior: smooth; }

    body {
      font-family: 'Inter', sans-serif;
      background: var(--bg);
      color: var(--text);
      min-height: 100vh;
      font-size: 15px;
      line-height: 1.6;
    }

    /* ── HEADER ── */
    header {
      position: sticky;
      top: 0;
      z-index: 100;
      background: rgba(10,10,15,0.95);
      backdrop-filter: blur(12px);
      border-bottom: 1px solid var(--border);
    }

    .header-inner {
      max-width: 1100px;
      margin: 0 auto;
      padding: 0 1.5rem;
      height: 64px;
      display: flex;
      align-items: center;
      gap: 2rem;
    }

    .logo {
      font-family: 'Bebas Neue', sans-serif;
      font-size: 2rem;
      letter-spacing: 0.04em;
      color: var(--text);
      text-decoration: none;
      display: flex;
      align-items: center;
      gap: 0.4rem;
      flex-shrink: 0;
    }

    .logo span {
      color: var(--gold);
    }

    .logo-dot {
      width: 8px;
      height: 8px;
      background: var(--red);
      border-radius: 50%;
      display: inline-block;
      margin-left: 3px;
      vertical-align: middle;
    }

    .search-wrap {
      flex: 1;
      max-width: 480px;
      position: relative;
    }

    .search-wrap input {
      width: 100%;
      background: var(--surface2);
      border: 1px solid var(--border);
      border-radius: 50px;
      padding: 0.55rem 1.2rem 0.55rem 3rem;
      color: var(--text);
      font-family: 'Inter', sans-serif;
      font-size: 14px;
      outline: none;
      transition: border-color 0.2s;
    }

    .search-wrap input::placeholder { color: var(--muted); }
    .search-wrap input:focus { border-color: var(--gold); }

    .search-wrap .search-icon {
      position: absolute;
      left: 1rem;
      top: 50%;
      transform: translateY(-50%);
      color: var(--muted);
      font-size: 16px;
      pointer-events: none;
    }

    .search-wrap button {
      position: absolute;
      right: 6px;
      top: 50%;
      transform: translateY(-50%);
      background: var(--gold);
      color: #000;
      border: none;
      border-radius: 50px;
      padding: 0.3rem 1rem;
      font-size: 13px;
      font-weight: 600;
      cursor: pointer;
      font-family: 'Inter', sans-serif;
      transition: background 0.2s;
    }

    .search-wrap button:hover { background: var(--gold-dark); }

    nav {
      display: flex;
      gap: 1.5rem;
      margin-left: auto;
    }

    nav a {
      color: var(--muted);
      text-decoration: none;
      font-size: 13px;
      font-weight: 500;
      letter-spacing: 0.03em;
      transition: color 0.2s;
    }

    nav a:hover { color: var(--gold); }

    /* ── HERO ── */
    .hero {
      background:
        linear-gradient(to bottom, rgba(10,10,15,0.3) 0%, rgba(10,10,15,0.85) 70%, var(--bg) 100%),
        url('https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?w=1400&q=80') center/cover no-repeat;
      min-height: 420px;
      display: flex;
      align-items: flex-end;
      padding: 3rem 1.5rem;
    }

    .hero-inner {
      max-width: 1100px;
      margin: 0 auto;
      width: 100%;
    }

    .hero-eyebrow {
      font-size: 11px;
      letter-spacing: 0.18em;
      text-transform: uppercase;
      color: var(--gold);
      font-weight: 600;
      margin-bottom: 0.75rem;
    }

    .hero h1 {
      font-family: 'Bebas Neue', sans-serif;
      font-size: clamp(2.8rem, 6vw, 4.5rem);
      letter-spacing: 0.03em;
      line-height: 1;
      color: var(--text);
      margin-bottom: 0.75rem;
    }

    .hero p {
      color: var(--muted);
      max-width: 520px;
      font-size: 15px;
      margin-bottom: 1.5rem;
    }

    .hero-actions {
      display: flex;
      gap: 0.75rem;
      flex-wrap: wrap;
      align-items: center;
    }

    .btn {
      display: inline-flex;
      align-items: center;
      gap: 0.4rem;
      padding: 0.65rem 1.5rem;
      border-radius: 50px;
      font-family: 'Inter', sans-serif;
      font-size: 14px;
      font-weight: 600;
      cursor: pointer;
      text-decoration: none;
      transition: all 0.2s;
      border: none;
    }

    .btn-primary {
      background: var(--gold);
      color: #000;
    }

    .btn-primary:hover {
      background: var(--gold-dark);
      color: #000;
    }

    .btn-outline {
      background: transparent;
      color: var(--text);
      border: 1px solid rgba(255,255,255,0.25);
    }

    .btn-outline:hover {
      border-color: var(--gold);
      color: var(--gold);
    }

    /* ── MAIN CONTENT ── */
    .main {
      max-width: 1100px;
      margin: 0 auto;
      padding: 2.5rem 1.5rem 4rem;
    }

    .section-label {
      font-size: 11px;
      letter-spacing: 0.16em;
      text-transform: uppercase;
      color: var(--gold);
      font-weight: 600;
      margin-bottom: 0.5rem;
    }

    .section-title {
      font-family: 'Bebas Neue', sans-serif;
      font-size: 2rem;
      letter-spacing: 0.03em;
      color: var(--text);
      margin-bottom: 1.5rem;
    }

    /* ── MOVIE CARDS ── */
    .movies-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
      gap: 1.25rem;
      margin-bottom: 2rem;
    }

    .movie-card {
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: var(--radius);
      overflow: hidden;
      transition: transform 0.2s, border-color 0.2s;
      text-decoration: none;
    }

    .movie-card:hover {
      transform: translateY(-4px);
      border-color: var(--gold);
    }

    .movie-poster {
      aspect-ratio: 2/3;
      background: var(--surface2);
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 3rem;
      position: relative;
      overflow: hidden;
    }

    .movie-poster-icon {
      opacity: 0.15;
      font-size: 4rem;
    }

    .movie-badge {
      position: absolute;
      top: 8px;
      left: 8px;
      background: var(--gold);
      color: #000;
      font-size: 10px;
      font-weight: 700;
      letter-spacing: 0.08em;
      padding: 3px 8px;
      border-radius: 4px;
    }

    .movie-info {
      padding: 0.85rem 1rem;
    }

    .movie-title {
      font-weight: 600;
      font-size: 14px;
      color: var(--text);
      line-height: 1.4;
      margin-bottom: 0.3rem;
      display: -webkit-box;
      -webkit-line-clamp: 2;
      -webkit-box-orient: vertical;
      overflow: hidden;
    }

    .movie-meta {
      font-size: 12px;
      color: var(--muted);
    }

    .movie-card .watch-btn {
      display: block;
      margin: 0 1rem 0.85rem;
      text-align: center;
      background: var(--gold);
      color: #000;
      font-size: 12px;
      font-weight: 700;
      letter-spacing: 0.04em;
      padding: 0.45rem;
      border-radius: 6px;
      text-decoration: none;
      transition: background 0.2s;
    }

    .movie-card .watch-btn:hover { background: var(--gold-dark); }

    /* ── DOWNLOAD PAGE ── */
    .movie-page-header {
      display: flex;
      gap: 2rem;
      align-items: flex-start;
      margin-bottom: 2.5rem;
      flex-wrap: wrap;
    }

    .movie-page-poster {
      width: 160px;
      flex-shrink: 0;
      aspect-ratio: 2/3;
      background: var(--surface2);
      border-radius: var(--radius);
      border: 1px solid var(--border);
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 3.5rem;
    }

    .movie-page-info h2 {
      font-family: 'Bebas Neue', sans-serif;
      font-size: 2.5rem;
      letter-spacing: 0.02em;
      color: var(--text);
      line-height: 1.1;
      margin-bottom: 0.5rem;
    }

    .tag-row {
      display: flex;
      gap: 0.5rem;
      flex-wrap: wrap;
      margin-bottom: 1rem;
    }

    .tag {
      background: var(--surface2);
      border: 1px solid var(--border);
      border-radius: 4px;
      font-size: 12px;
      color: var(--muted);
      padding: 3px 10px;
    }

    .tag.gold {
      border-color: var(--gold);
      color: var(--gold);
      background: rgba(232,184,75,0.08);
    }

    /* ── DOWNLOAD SECTION ── */
    .download-section {
      margin-bottom: 2rem;
    }

    .quality-header {
      display: flex;
      align-items: center;
      gap: 0.75rem;
      margin-bottom: 1rem;
      padding-bottom: 0.75rem;
      border-bottom: 1px solid var(--border);
    }

    .quality-badge {
      background: var(--gold);
      color: #000;
      font-size: 12px;
      font-weight: 700;
      letter-spacing: 0.06em;
      padding: 4px 12px;
      border-radius: 4px;
    }

    .quality-label {
      color: var(--muted);
      font-size: 14px;
    }

    .dl-card {
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: var(--radius);
      padding: 1.25rem 1.5rem;
      margin-bottom: 0.85rem;
    }

    .dl-card-title {
      font-weight: 600;
      font-size: 15px;
      color: var(--text);
      margin-bottom: 0.35rem;
    }

    .dl-card-url {
      font-size: 12px;
      color: var(--muted);
      font-family: monospace;
      word-break: break-all;
      margin-bottom: 0.85rem;
      background: var(--surface2);
      padding: 6px 10px;
      border-radius: 6px;
    }

    .dl-actions {
      display: flex;
      gap: 0.6rem;
      flex-wrap: wrap;
    }

    .btn-dl {
      display: inline-flex;
      align-items: center;
      gap: 0.35rem;
      padding: 0.5rem 1.1rem;
      border-radius: 6px;
      font-size: 13px;
      font-weight: 600;
      text-decoration: none;
      transition: all 0.2s;
      cursor: pointer;
    }

    .btn-dl-primary {
      background: var(--gold);
      color: #000;
    }

    .btn-dl-primary:hover { background: var(--gold-dark); }

    .btn-dl-ghost {
      background: var(--surface2);
      color: var(--text);
      border: 1px solid var(--border);
    }

    .btn-dl-ghost:hover {
      border-color: var(--gold);
      color: var(--gold);
    }

    .mirror-list {
      margin-top: 0.85rem;
      padding-top: 0.85rem;
      border-top: 1px dashed var(--border);
    }

    .mirror-item {
      background: rgba(232,184,75,0.05);
      border: 1px solid rgba(232,184,75,0.15);
      border-radius: 8px;
      padding: 0.85rem 1rem;
      margin-bottom: 0.6rem;
      display: flex;
      align-items: center;
      gap: 1rem;
      flex-wrap: wrap;
    }

    .mirror-host {
      font-size: 13px;
      font-weight: 600;
      color: var(--gold);
      flex: 1;
      min-width: 120px;
    }

    .mirror-url {
      font-size: 11px;
      color: var(--muted);
      font-family: monospace;
      word-break: break-all;
      flex: 2;
    }

    /* ── UTILITY ── */
    .page-top {
      display: flex;
      align-items: center;
      gap: 0.75rem;
      margin-bottom: 2rem;
    }

    .back-link {
      display: inline-flex;
      align-items: center;
      gap: 0.35rem;
      color: var(--muted);
      text-decoration: none;
      font-size: 14px;
      transition: color 0.2s;
    }

    .back-link:hover { color: var(--gold); }

    .empty-state {
      text-align: center;
      padding: 5rem 1.5rem;
      color: var(--muted);
    }

    .empty-state .icon { font-size: 3rem; margin-bottom: 1rem; opacity: 0.4; }
    .empty-state h3 { font-size: 1.25rem; color: var(--text); margin-bottom: 0.5rem; }

    .alert-error {
      background: rgba(192,57,43,0.12);
      border: 1px solid rgba(192,57,43,0.35);
      border-radius: var(--radius);
      padding: 1rem 1.25rem;
      color: #f08080;
      font-size: 14px;
    }

    /* ── FOOTER ── */
    footer {
      border-top: 1px solid var(--border);
      padding: 2.5rem 1.5rem;
      text-align: center;
      color: var(--muted);
      font-size: 13px;
    }

    footer .footer-logo {
      font-family: 'Bebas Neue', sans-serif;
      font-size: 1.5rem;
      color: var(--text);
      letter-spacing: 0.04em;
      margin-bottom: 0.5rem;
    }

    footer .footer-logo span { color: var(--gold); }

    footer p { margin-bottom: 0.25rem; line-height: 1.8; }

    /* ── DIVIDER ── */
    .divider {
      display: flex;
      align-items: center;
      gap: 1rem;
      margin: 2rem 0;
      color: var(--border);
      font-size: 11px;
      letter-spacing: 0.12em;
      text-transform: uppercase;
      color: var(--muted);
    }

    .divider::before, .divider::after {
      content: '';
      flex: 1;
      height: 1px;
      background: var(--border);
    }

    @media (max-width: 640px) {
      .header-inner { flex-wrap: wrap; height: auto; padding: 0.75rem 1rem; gap: 0.75rem; }
      nav { display: none; }
      .hero { min-height: 300px; }
      .movies-grid { grid-template-columns: repeat(2, 1fr); }
      .movie-page-header { flex-direction: column; }
      .movie-page-poster { width: 120px; }
    }
  </style>
</head>
<body>

<header>
  <div class="header-inner">
    <a class="logo" href="/">NY<span>Movies</span><span class="logo-dot"></span></a>
    <div class="search-wrap">
      <form action="/search" method="get">
        <span class="search-icon">⌕</span>
        <input name="q" placeholder="Search movies, genres, actors…" value="{{ query|default('') }}" autocomplete="off">
        <button type="submit">Find</button>
      </form>
    </div>
    <nav>
      <a href="/">Home</a>
      <a href="/search?q=action">Action</a>
      <a href="/search?q=thriller">Thriller</a>
      <a href="/search?q=comedy">Comedy</a>
    </nav>
  </div>
</header>

{{ content|safe }}

<footer>
  <div style="max-width:900px;margin:0 auto;">
    <div class="footer-logo">NY<span>Movies</span></div>
    <p>Your destination for cinema — from blockbusters to hidden gems.</p>
    <p style="margin-top:1.25rem;font-size:12px;opacity:0.5;">
      © 2025 NYMovies. All content is provided for personal entertainment use only.
      NYMovies does not host any files. All links redirect to third-party hosting services.
    </p>
  </div>
</footer>

</body>
</html>
"""

HOME_CONTENT = """
<div class="hero">
  <div class="hero-inner">
    <div class="hero-eyebrow">Now Streaming</div>
    <h1>Cinema Without<br>Compromise</h1>
    <p>Thousands of films at your fingertips — search any title and get direct download links in seconds.</p>
    <div class="hero-actions">
      <a href="/search?q=action" class="btn btn-primary">▶ Browse Action</a>
      <a href="/search?q=new+2024" class="btn btn-outline">New Releases</a>
    </div>
  </div>
</div>

<div class="main">
  <div class="section-label">Explore by Genre</div>
  <h2 class="section-title">What Are You In The Mood For?</h2>
  <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(140px,1fr));gap:0.75rem;margin-bottom:3rem;">
    {% for genre, emoji in [('Action','💥'),('Comedy','😂'),('Horror','👻'),('Thriller','🔪'),('Drama','🎭'),('Sci-Fi','🚀'),('Romance','❤️'),('Animation','🎨')] %}
    <a href="/search?q={{ genre|lower }}" style="display:flex;align-items:center;gap:0.6rem;background:var(--surface);border:1px solid var(--border);border-radius:8px;padding:0.85rem 1rem;text-decoration:none;color:var(--text);font-size:14px;font-weight:500;transition:all 0.2s;" onmouseover="this.style.borderColor='var(--gold)';this.style.color='var(--gold)'" onmouseout="this.style.borderColor='var(--border)';this.style.color='var(--text)'">
      <span>{{ emoji }}</span> {{ genre }}
    </a>
    {% endfor %}
  </div>

  <div class="section-label">Quick Start</div>
  <h2 class="section-title">Search Any Movie Above</h2>
  <p style="color:var(--muted);max-width:560px;line-height:1.8;">
    Use the search bar at the top to find any film. NYMovies will locate available download options and present them neatly — no popups, no confusion.
  </p>
</div>
"""

JINJA_HOME_EXTRAS = """
{% set genres = [['Action','💥'],['Comedy','😂'],['Horror','👻'],['Thriller','🔪'],['Drama','🎭'],['Sci-Fi','🚀'],['Romance','❤️'],['Animation','🎨']] %}
"""


def get_current_site():
    try:
        response = SESSION.get(LANDING_PAGE, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        for a in soup.find_all("a", href=True):
            if "visit" in a.get_text(" ", strip=True).lower():
                return a["href"].rstrip("/")
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if "dudefilms" in href and href.startswith("http"):
                return href.rstrip("/")
    except Exception:
        pass
    return "https://dudefilms.irish"


def build_absolute_url(base_url, url):
    if not url:
        return None
    return urljoin(base_url, url)


def parse_quality_size_from_heading(text):
    quality = None
    size = None
    if not text:
        return quality, size
    q_match = re.search(r"\b(\d{3,4}p)\b", text, re.I)
    s_match = re.search(r"\[?\s*([\d.]+\s*(?:mb|gb))\s*\]?", text, re.I)
    if q_match:
        quality = q_match.group(1).upper()
    if s_match:
        size = s_match.group(1).upper()
    return quality, size


def extract_block_download_links(soup, base_url):
    links = []
    for a in soup.select("a.maxbutton-download-link, a.maxbutton-download"):
        href = build_absolute_url(base_url, a.get("href"))
        if not href:
            continue
        heading = a.find_previous(["h1", "h2", "h3", "h4", "h5", "h6"])
        heading_text = heading.get_text(" ", strip=True) if heading else ""
        quality, size = parse_quality_size_from_heading(heading_text)
        label_parts = []
        if quality:
            label_parts.append(quality)
        if size:
            label_parts.append(size)
        label = " | ".join(label_parts)
        if not label:
            label = heading_text or a.get_text(" ", strip=True) or href
        links.append({"title": label, "url": href, "quality": quality, "size": size, "heading": heading_text})

    seen = set()
    unique_links = []
    for item in links:
        if item["url"] not in seen:
            seen.add(item["url"])
            unique_links.append(item)
    return unique_links


def find_search_results(soup):
    results = []
    selectors = [
        "article h2 a", "article h3 a", "div.post-title a", "h2 a", "h3 a",
    ]
    for selector in selectors:
        for a in soup.select(selector):
            href = a.get("href")
            title = a.get_text(" ", strip=True)
            if href and title:
                results.append({"title": title, "url": href})
        if results:
            break

    seen = set()
    unique_results = []
    for item in results:
        if item["url"] not in seen:
            seen.add(item["url"])
            unique_results.append(item)
    return unique_results


DOWNLOAD_HOSTS = [
    "filepress.online", "filepress.today", "howblogs.xyz", "gofile.io",
    "googleusercontent.com", "drive.google.com", "pixeldrain.dev", "dtflix.ink",
    "neolinks.icu", "krakenfiles.com", "hubcloud", "filebee", "r2.dev",
    "gdrive", "g-drive", "filepress",
]

DOWNLOAD_TEXT = [
    "download", "download link", "direct download", "g-drive", "g drive",
    "download [", "fast server", "download file", "download now",
]

EXCLUDE_TEXT = [
    "category", "home", "contact", "privacy", "disclaimer", "request",
    "dmca", "terms", "policy",
]


def extract_download_links(soup, base_url):
    block_links = extract_block_download_links(soup, base_url)
    if block_links:
        return block_links

    links = []
    for a in soup.find_all("a", href=True):
        href = build_absolute_url(base_url, a["href"])
        if not href:
            continue
        text = a.get_text(" ", strip=True)
        low_text = text.lower()
        low_href = href.lower()

        if any(exclude in low_text for exclude in EXCLUDE_TEXT):
            continue
        if any(host in low_href for host in DOWNLOAD_HOSTS):
            links.append({"title": text or href, "url": href})
            continue
        if any(token in low_text for token in DOWNLOAD_TEXT):
            links.append({"title": text or href, "url": href})

    seen = set()
    unique_links = []
    for item in links:
        if item["url"] not in seen:
            seen.add(item["url"])
            unique_links.append(item)
    return unique_links


def find_download_links(soup, base_url):
    return extract_download_links(soup, base_url)


def fetch_mirror_targets(link_url):
    response = SESSION.get(link_url, timeout=20)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    return extract_download_links(soup, response.url)


def clean_movie_title(raw_title):
    """Extract a clean movie name from a messy blog-post title."""
    title = re.sub(r'\(?\d{4}\)?\s*(hindi|english|dual audio|bluray|web-dl|webrip|hdcam|hd|4k|1080p|720p|480p).*', '', raw_title, flags=re.I)
    title = re.sub(r'download\s*', '', title, flags=re.I)
    return title.strip(" –|-") or raw_title


def guess_year(raw_title):
    m = re.search(r'\b(19\d{2}|20\d{2})\b', raw_title)
    return m.group(1) if m else ""


def guess_quality(raw_title):
    m = re.search(r'\b(4K|2160p|1080p|720p|480p|HDCam|BluRay|WEB-DL|WEBRip)\b', raw_title, re.I)
    return m.group(1).upper() if m else ""


@app.route("/")
def home():
    return render_template_string(BASE_HTML, query="", content=HOME_CONTENT)


@app.route("/search")
def search():
    query = request.args.get("q", "").strip()
    if not query:
        return render_template_string(
            BASE_HTML, query="", content=HOME_CONTENT
        )

    try:
        site = get_current_site()
        search_url = f"{site}/?s={quote(query)}"
        response = SESSION.get(search_url, timeout=20)
        results = find_search_results(BeautifulSoup(response.text, "html.parser"))
    except Exception as exc:
        content = f"""
        <div class="main">
          <div class="alert-error">
            <strong>Connection error:</strong> {exc}<br>
            <small>Please try again in a moment.</small>
          </div>
        </div>"""
        return render_template_string(BASE_HTML, query=query, content=content)

    if not results:
        content = f"""
        <div class="main">
          <div class="empty-state">
            <div class="icon">🔍</div>
            <h3>No results for "{query}"</h3>
            <p>Try a different spelling or a shorter title.</p>
          </div>
        </div>"""
    else:
        cards = []
        for item in results:
            safe_url = quote(item["url"], safe=":/?=&")
            clean = clean_movie_title(item["title"])
            year = guess_year(item["title"])
            quality = guess_quality(item["title"])
            quality_badge = f'<span class="movie-badge">{quality}</span>' if quality else ''
            year_meta = f'<span class="movie-meta">{year}</span>' if year else ''
            cards.append(f"""
            <div class="movie-card" style="display:flex;flex-direction:column;">
              <div class="movie-poster">
                <span class="movie-poster-icon">🎬</span>
                {quality_badge}
              </div>
              <div class="movie-info" style="flex:1;">
                <div class="movie-title">{clean}</div>
                {year_meta}
              </div>
              <a class="watch-btn" href="/movie?url={safe_url}">Get Download Links</a>
            </div>""")

        content = f"""
        <div class="main">
          <div class="page-top">
            <span class="section-label">Search results</span>
            <span style="color:var(--muted);font-size:13px;margin-left:auto;">{len(results)} titles found</span>
          </div>
          <h2 class="section-title">Results for "{query}"</h2>
          <div class="movies-grid">{''.join(cards)}</div>
        </div>"""

    return render_template_string(BASE_HTML, query=query, content=content)


@app.route("/movie")
def movie():
    movie_url = request.args.get("url", "").strip()
    back_query = request.args.get("back", "")
    if not movie_url:
        return render_template_string(
            BASE_HTML, content='<div class="main"><div class="alert-error">Missing movie URL.</div></div>'
        )

    try:
        response = SESSION.get(movie_url, timeout=20)
        soup = BeautifulSoup(response.text, "html.parser")

        # Try to extract title from page
        page_title = ""
        og_title = soup.find("meta", property="og:title")
        if og_title and og_title.get("content"):
            page_title = og_title["content"]
        elif soup.find("h1"):
            page_title = soup.find("h1").get_text(" ", strip=True)

        clean_title = clean_movie_title(page_title) if page_title else "Movie"
        year = guess_year(page_title)

        downloads = find_download_links(soup, response.url)
    except Exception as exc:
        content = f'<div class="main"><div class="alert-error"><strong>Error loading page:</strong> {exc}</div></div>'
        return render_template_string(BASE_HTML, content=content)

    if not downloads:
        content = f"""
        <div class="main">
          <a class="back-link" href="/search?q={quote(back_query)}">← Back to results</a>
          <div class="empty-state">
            <div class="icon">📭</div>
            <h3>No download links found</h3>
            <p>This page may not have any active links at this time.</p>
          </div>
        </div>"""
    else:
        rows = []

        # Movie header
        year_tag = f'<span class="tag">{year}</span>' if year else ''
        rows.append(f"""
        <div class="movie-page-header">
          <div class="movie-page-poster">🎬</div>
          <div class="movie-page-info">
            <p class="section-label">Now Downloading</p>
            <h2>{clean_title}</h2>
            <div class="tag-row">
              {year_tag}
              <span class="tag">{len(downloads)} source{"s" if len(downloads)!=1 else ""} available</span>
              <span class="tag gold">Free</span>
            </div>
            <p style="color:var(--muted);font-size:14px;max-width:500px;">
              Select your preferred quality and server below. All links open on third-party hosting services.
            </p>
          </div>
        </div>
        <div class="divider">Available Download Options</div>
        """)

        for idx, item in enumerate(downloads, 1):
            label = item.get("title") or item.get("heading") or f"Option {idx}"
            quality = item.get("quality") or guess_quality(label)
            size = item.get("size", "")
            quality_html = f'<span class="quality-badge">{quality}</span>' if quality else f'<span class="quality-badge">HD</span>'
            size_html = f'<span class="quality-label">{size}</span>' if size else ''

            rows.append(f"""
            <div class="download-section">
              <div class="quality-header">
                {quality_html}
                <span class="quality-label">{label}</span>
                {size_html}
              </div>
              <div class="dl-card">
                <div class="dl-card-title">Primary Source</div>
                <div class="dl-card-url">{item['url']}</div>
                <div class="dl-actions">
                  <a class="btn-dl btn-dl-primary" href="{item['url']}" target="_blank" rel="noopener">▼ Download Now</a>
                  <a class="btn-dl btn-dl-ghost" href="{item['url']}" target="_blank" rel="noopener">Open in New Tab ↗</a>
                </div>
            """)

            # Mirrors
            try:
                targets = fetch_mirror_targets(item["url"])
                if targets:
                    rows.append('<div class="mirror-list"><p style="font-size:12px;color:var(--muted);letter-spacing:0.08em;text-transform:uppercase;margin-bottom:0.75rem;">Mirror Servers</p>')
                    for t in targets:
                        turl = t.get("url", "")
                        ttitle = t.get("title") or turl
                        if turl and "hubcloud" in turl.lower():
                            ttitle = "HubCloud — Fast Server"
                        rows.append(f"""
                        <div class="mirror-item">
                          <span class="mirror-host">⚡ {ttitle}</span>
                          <span class="mirror-url">{turl}</span>
                          <a class="btn-dl btn-dl-primary" href="{turl}" target="_blank" rel="noopener" style="flex-shrink:0;">▼ Download</a>
                        </div>""")
                    rows.append('</div>')
            except Exception:
                pass

            rows.append("</div></div>")  # close dl-card + download-section

        safe_back = quote(back_query)
        content = f"""
        <div class="main">
          <a class="back-link" href="/search?q={safe_back}">← Back to results</a>
          {''.join(rows)}
        </div>"""

    return render_template_string(BASE_HTML, content=content)


if __name__ == "__main__":
    app.run(debug=True, port=5000)
