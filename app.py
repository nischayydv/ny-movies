import re
import concurrent.futures
from urllib.parse import quote, urljoin, urlparse
from bs4 import BeautifulSoup
from flask import Flask, render_template_string, request
import requests

app = Flask(__name__)

# ── CONFIG ──────────────────────────────────────────────────────────────────
LANDING_PAGE   = "https://dudefilms.to/"
HUBCLOUD_DOMAIN = "hubcloud.foo"   # rewrite all hubcloud.* domains to this

SESSION = requests.Session()
SESSION.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/124.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Referer": "https://www.google.com/",
})

# ── HTML TEMPLATE ────────────────────────────────────────────────────────────
BASE_HTML = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{% if page_title %}{{ page_title }} – {% endif %}NY Movies</title>
  <meta name="description" content="NY Movies — Download any film in HD, 4K, 1080p and more. Fast mirrors, clean links.">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
  <style>
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
    :root {
      --gold: #E8B84B;
      --gold-dark: #C89A2A;
      --gold-faint: rgba(232,184,75,0.08);
      --gold-border: rgba(232,184,75,0.22);
      --red: #C0392B;
      --green: #27AE60;
      --bg: #080810;
      --surface: #0F0F1A;
      --surface2: #161625;
      --surface3: #1E1E30;
      --border: rgba(255,255,255,0.065);
      --border2: rgba(255,255,255,0.12);
      --text: #EDEAD5;
      --muted: #7A7890;
      --muted2: #5A5870;
      --radius: 10px;
      --radius-sm: 6px;
    }
    html { scroll-behavior: smooth; }
    body {
      font-family: 'Inter', sans-serif;
      background: var(--bg);
      color: var(--text);
      min-height: 100vh;
      font-size: 15px;
      line-height: 1.65;
    }

    /* ── HEADER ── */
    header {
      position: sticky; top: 0; z-index: 200;
      background: rgba(8,8,16,0.97);
      backdrop-filter: blur(16px);
      border-bottom: 1px solid var(--border);
    }
    .header-inner {
      max-width: 1180px; margin: 0 auto;
      padding: 0 1.5rem; height: 66px;
      display: flex; align-items: center; gap: 1.75rem;
    }
    .logo {
      font-family: 'Bebas Neue', sans-serif;
      font-size: 2.1rem; letter-spacing: 0.05em;
      color: var(--text); text-decoration: none;
      display: flex; align-items: center; gap: 0; flex-shrink: 0;
    }
    .logo-ny { color: var(--text); }
    .logo-m  { color: var(--gold); }
    .logo-dot {
      width: 7px; height: 7px; background: var(--red);
      border-radius: 50%; display: inline-block;
      margin-left: 3px; vertical-align: middle; margin-bottom: 4px;
    }
    .search-wrap { flex: 1; max-width: 500px; position: relative; }
    .search-wrap input {
      width: 100%; background: var(--surface2);
      border: 1px solid var(--border2); border-radius: 50px;
      padding: 0.6rem 5.5rem 0.6rem 2.75rem;
      color: var(--text); font-family: 'Inter', sans-serif;
      font-size: 14px; outline: none;
      transition: border-color 0.2s, background 0.2s;
    }
    .search-wrap input::placeholder { color: var(--muted2); }
    .search-wrap input:focus { border-color: var(--gold); background: var(--surface3); }
    .search-icon {
      position: absolute; left: 0.9rem; top: 50%;
      transform: translateY(-50%); color: var(--muted);
      font-size: 15px; pointer-events: none;
    }
    .search-wrap button {
      position: absolute; right: 5px; top: 50%;
      transform: translateY(-50%);
      background: var(--gold); color: #000;
      border: none; border-radius: 50px;
      padding: 0.35rem 1.1rem; font-size: 13px;
      font-weight: 700; cursor: pointer;
      font-family: 'Inter', sans-serif; transition: background 0.2s;
    }
    .search-wrap button:hover { background: var(--gold-dark); }
    nav { display: flex; gap: 1.5rem; margin-left: auto; align-items: center; }
    nav a {
      color: var(--muted); text-decoration: none;
      font-size: 13px; font-weight: 500;
      letter-spacing: 0.02em; transition: color 0.2s;
    }
    nav a:hover { color: var(--gold); }
    .nav-badge {
      background: var(--red); color: #fff;
      font-size: 9px; font-weight: 700;
      padding: 1px 5px; border-radius: 3px;
      vertical-align: middle; margin-left: 3px;
    }

    /* ── HERO ── */
    .hero {
      position: relative; overflow: hidden;
      min-height: 480px; display: flex; align-items: flex-end;
      padding: 3rem 1.5rem;
      background:
        linear-gradient(to right, rgba(8,8,16,0.97) 30%, rgba(8,8,16,0.3) 100%),
        linear-gradient(to bottom, rgba(8,8,16,0.2) 0%, rgba(8,8,16,0.92) 80%, var(--bg) 100%),
        url('https://images.unsplash.com/photo-1536440136628-849c177e76a1?w=1600&q=85') center/cover no-repeat;
    }
    .hero-inner { max-width: 1180px; margin: 0 auto; width: 100%; }
    .hero-eyebrow {
      font-size: 11px; letter-spacing: 0.2em;
      text-transform: uppercase; color: var(--gold);
      font-weight: 700; margin-bottom: 0.85rem;
      display: flex; align-items: center; gap: 0.5rem;
    }
    .hero-eyebrow::before {
      content: ''; display: inline-block;
      width: 28px; height: 2px; background: var(--gold);
    }
    .hero h1 {
      font-family: 'Bebas Neue', sans-serif;
      font-size: clamp(3rem, 7vw, 5.5rem);
      letter-spacing: 0.02em; line-height: 0.95;
      color: var(--text); margin-bottom: 1rem;
    }
    .hero h1 em { color: var(--gold); font-style: normal; }
    .hero p {
      color: var(--muted); max-width: 480px;
      font-size: 15px; margin-bottom: 1.75rem; line-height: 1.75;
    }
    .hero-actions { display: flex; gap: 0.75rem; flex-wrap: wrap; align-items: center; }
    .btn {
      display: inline-flex; align-items: center; gap: 0.45rem;
      padding: 0.7rem 1.6rem; border-radius: 50px;
      font-family: 'Inter', sans-serif; font-size: 14px;
      font-weight: 700; cursor: pointer; text-decoration: none;
      transition: all 0.2s; border: none; letter-spacing: 0.01em;
    }
    .btn-primary { background: var(--gold); color: #000; }
    .btn-primary:hover { background: var(--gold-dark); color: #000; }
    .btn-outline {
      background: transparent; color: var(--text);
      border: 1px solid rgba(255,255,255,0.2);
    }
    .btn-outline:hover { border-color: var(--gold); color: var(--gold); }
    .hero-stats {
      display: flex; gap: 2rem; margin-top: 2rem;
    }
    .hero-stat-num {
      font-family: 'Bebas Neue', sans-serif;
      font-size: 1.8rem; color: var(--gold); letter-spacing: 0.04em;
    }
    .hero-stat-label { font-size: 11px; color: var(--muted); letter-spacing: 0.1em; text-transform: uppercase; }

    /* ── MAIN ── */
    .main { max-width: 1180px; margin: 0 auto; padding: 2.5rem 1.5rem 5rem; }
    .section-label {
      font-size: 10.5px; letter-spacing: 0.18em; text-transform: uppercase;
      color: var(--gold); font-weight: 700; margin-bottom: 0.4rem;
    }
    .section-title {
      font-family: 'Bebas Neue', sans-serif;
      font-size: 2.1rem; letter-spacing: 0.03em;
      color: var(--text); margin-bottom: 1.5rem;
    }

    /* ── GENRE GRID ── */
    .genre-grid {
      display: grid; grid-template-columns: repeat(auto-fill, minmax(130px,1fr));
      gap: 0.65rem; margin-bottom: 3rem;
    }
    .genre-pill {
      display: flex; align-items: center; gap: 0.5rem;
      background: var(--surface); border: 1px solid var(--border);
      border-radius: var(--radius-sm); padding: 0.75rem 0.9rem;
      text-decoration: none; color: var(--text); font-size: 13px;
      font-weight: 500; transition: all 0.18s;
    }
    .genre-pill:hover {
      border-color: var(--gold); color: var(--gold);
      background: var(--gold-faint);
    }

    /* ── MOVIE CARDS ── */
    .movies-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(185px,1fr));
      gap: 1.25rem; margin-bottom: 2rem;
    }
    .movie-card {
      background: var(--surface); border: 1px solid var(--border);
      border-radius: var(--radius); overflow: hidden;
      display: flex; flex-direction: column;
      text-decoration: none; transition: transform 0.2s, border-color 0.2s;
    }
    .movie-card:hover { transform: translateY(-5px); border-color: var(--gold-border); }
    .movie-poster {
      aspect-ratio: 2/3; position: relative;
      background: var(--surface2); overflow: hidden;
    }
    .movie-poster img {
      width: 100%; height: 100%; object-fit: cover;
      display: block; transition: transform 0.3s;
    }
    .movie-card:hover .movie-poster img { transform: scale(1.04); }
    .poster-fallback {
      width: 100%; height: 100%; display: flex;
      align-items: center; justify-content: center;
      font-size: 3.5rem; opacity: 0.18;
      background: linear-gradient(135deg, var(--surface2), var(--surface3));
    }
    .movie-badge {
      position: absolute; top: 8px; left: 8px;
      background: var(--gold); color: #000;
      font-size: 10px; font-weight: 800;
      letter-spacing: 0.06em; padding: 3px 8px;
      border-radius: 4px; line-height: 1;
    }
    .movie-badge.hd { background: #1a6fb5; color: #fff; }
    .movie-badge.cam { background: var(--red); color: #fff; }
    .movie-overlay {
      position: absolute; inset: 0;
      background: linear-gradient(to top, rgba(8,8,16,0.9) 0%, transparent 50%);
      opacity: 0; transition: opacity 0.2s;
      display: flex; align-items: flex-end; padding: 0.75rem;
    }
    .movie-card:hover .movie-overlay { opacity: 1; }
    .overlay-btn {
      display: block; width: 100%; text-align: center;
      background: var(--gold); color: #000;
      font-size: 12px; font-weight: 800;
      padding: 0.45rem; border-radius: 5px;
      text-decoration: none; letter-spacing: 0.04em;
    }
    .movie-info { padding: 0.8rem 0.9rem 0.5rem; flex: 1; }
    .movie-title {
      font-weight: 600; font-size: 13.5px; color: var(--text);
      line-height: 1.35; margin-bottom: 0.3rem;
      display: -webkit-box; -webkit-line-clamp: 2;
      -webkit-box-orient: vertical; overflow: hidden;
    }
    .movie-meta { font-size: 11.5px; color: var(--muted); }
    .movie-tags { display: flex; gap: 0.3rem; flex-wrap: wrap; margin-bottom: 0.2rem; }
    .movie-tag {
      font-size: 10px; padding: 2px 6px; border-radius: 3px;
      background: var(--surface2); color: var(--muted);
      border: 1px solid var(--border); font-weight: 500;
    }
    .watch-btn {
      display: block; margin: 0 0.75rem 0.75rem;
      text-align: center; background: var(--surface2);
      color: var(--gold); font-size: 12px; font-weight: 700;
      letter-spacing: 0.04em; padding: 0.45rem;
      border-radius: 6px; text-decoration: none;
      border: 1px solid var(--gold-border);
      transition: background 0.2s, color 0.2s;
    }
    .watch-btn:hover { background: var(--gold); color: #000; }

    /* ── MOVIE DETAIL PAGE ── */
    .movie-page-hero {
      position: relative; overflow: hidden; border-radius: var(--radius);
      margin-bottom: 2rem;
    }
    .movie-page-backdrop {
      width: 100%; height: 280px; object-fit: cover;
      display: block; filter: blur(3px) brightness(0.35);
    }
    .movie-page-backdrop-fallback {
      width: 100%; height: 280px;
      background: linear-gradient(135deg, var(--surface), var(--surface3));
    }
    .movie-page-overlay {
      position: absolute; inset: 0;
      background: linear-gradient(to right, rgba(8,8,16,0.98) 0%, rgba(8,8,16,0.5) 100%);
      display: flex; align-items: flex-end; padding: 2rem;
      gap: 1.75rem;
    }
    .movie-page-thumb {
      width: 140px; flex-shrink: 0;
      aspect-ratio: 2/3; border-radius: var(--radius);
      object-fit: cover; border: 2px solid var(--gold-border);
      box-shadow: 0 8px 32px rgba(0,0,0,0.6);
    }
    .movie-page-thumb-fallback {
      width: 140px; flex-shrink: 0; aspect-ratio: 2/3;
      border-radius: var(--radius); border: 2px solid var(--gold-border);
      background: var(--surface2); display: flex;
      align-items: center; justify-content: center; font-size: 3rem;
    }
    .movie-page-meta h2 {
      font-family: 'Bebas Neue', sans-serif;
      font-size: clamp(1.8rem, 4vw, 3rem);
      letter-spacing: 0.02em; line-height: 1; color: var(--text);
      margin-bottom: 0.6rem;
    }
    .tag-row { display: flex; gap: 0.45rem; flex-wrap: wrap; margin-bottom: 0.75rem; }
    .tag {
      background: var(--surface2); border: 1px solid var(--border2);
      border-radius: 4px; font-size: 12px; color: var(--muted);
      padding: 3px 10px; font-weight: 500;
    }
    .tag.gold { border-color: var(--gold-border); color: var(--gold); background: var(--gold-faint); }
    .tag.green { border-color: rgba(39,174,96,0.35); color: #4fc878; background: rgba(39,174,96,0.08); }
    .movie-description { color: var(--muted); font-size: 14px; line-height: 1.75; max-width: 600px; }

    /* ── DOWNLOAD SECTION ── */
    .dl-section { margin-bottom: 1.5rem; }
    .dl-quality-row {
      display: flex; align-items: center; gap: 0.75rem;
      margin-bottom: 0.85rem; padding-bottom: 0.75rem;
      border-bottom: 1px solid var(--border);
    }
    .dl-q-badge {
      background: var(--gold); color: #000;
      font-size: 11.5px; font-weight: 800;
      letter-spacing: 0.07em; padding: 4px 12px; border-radius: 4px;
    }
    .dl-q-badge.v4k { background: #8B5CF6; color: #fff; }
    .dl-q-badge.v1080 { background: #2563EB; color: #fff; }
    .dl-q-badge.v720 { background: #059669; color: #fff; }
    .dl-q-label { color: var(--muted); font-size: 13.5px; flex: 1; }
    .dl-q-size { color: var(--muted2); font-size: 12px; font-weight: 500; }

    .dl-primary-card {
      background: var(--surface); border: 1px solid var(--border);
      border-radius: var(--radius); padding: 1.25rem 1.4rem; margin-bottom: 0.75rem;
    }
    .dl-primary-label {
      font-size: 11px; text-transform: uppercase; letter-spacing: 0.12em;
      color: var(--muted2); font-weight: 600; margin-bottom: 0.5rem;
    }
    .dl-url-box {
      font-size: 12px; color: var(--muted); font-family: monospace;
      word-break: break-all; background: var(--surface2);
      padding: 7px 11px; border-radius: 5px; margin-bottom: 0.85rem;
      border: 1px solid var(--border);
    }
    .dl-actions { display: flex; gap: 0.55rem; flex-wrap: wrap; }
    .btn-dl {
      display: inline-flex; align-items: center; gap: 0.35rem;
      padding: 0.5rem 1.1rem; border-radius: 6px;
      font-size: 13px; font-weight: 700; text-decoration: none;
      transition: all 0.18s; cursor: pointer; border: none;
      font-family: 'Inter', sans-serif; letter-spacing: 0.01em;
    }
    .btn-dl-gold { background: var(--gold); color: #000; }
    .btn-dl-gold:hover { background: var(--gold-dark); }
    .btn-dl-ghost {
      background: var(--surface2); color: var(--text);
      border: 1px solid var(--border2);
    }
    .btn-dl-ghost:hover { border-color: var(--gold); color: var(--gold); }
    .btn-dl-hubcloud {
      background: linear-gradient(90deg, #6D28D9, #4F46E5);
      color: #fff;
    }
    .btn-dl-hubcloud:hover { opacity: 0.88; }

    .mirrors-header {
      font-size: 11px; text-transform: uppercase; letter-spacing: 0.14em;
      color: var(--muted2); font-weight: 600; margin: 1rem 0 0.6rem;
      display: flex; align-items: center; gap: 0.5rem;
    }
    .mirrors-header::after {
      content: ''; flex: 1; height: 1px;
      background: var(--border); display: block;
    }
    .mirror-row {
      display: flex; align-items: center; gap: 1rem;
      background: var(--gold-faint);
      border: 1px solid var(--gold-border);
      border-radius: 7px; padding: 0.8rem 1rem;
      margin-bottom: 0.5rem; flex-wrap: wrap;
    }
    .mirror-icon { font-size: 1.2rem; flex-shrink: 0; }
    .mirror-name {
      font-size: 13.5px; font-weight: 700; color: var(--gold);
      flex: 1; min-width: 100px;
    }
    .mirror-url-short { font-size: 11px; color: var(--muted); font-family: monospace; flex: 2; word-break: break-all; }
    .mirror-error { font-size: 13px; color: var(--muted2); font-style: italic; padding: 0.4rem 0; }

    /* ── DIVIDER ── */
    .divider {
      display: flex; align-items: center; gap: 1rem;
      margin: 2rem 0; font-size: 11px; letter-spacing: 0.14em;
      text-transform: uppercase; color: var(--muted);
    }
    .divider::before, .divider::after {
      content: ''; flex: 1; height: 1px; background: var(--border);
    }

    /* ── MISC ── */
    .page-top { display: flex; align-items: center; gap: 0.75rem; margin-bottom: 1.75rem; }
    .back-link {
      display: inline-flex; align-items: center; gap: 0.35rem;
      color: var(--muted); text-decoration: none; font-size: 14px;
      transition: color 0.2s;
    }
    .back-link:hover { color: var(--gold); }
    .result-count { color: var(--muted2); font-size: 13px; margin-left: auto; }
    .empty-state { text-align: center; padding: 5rem 1.5rem; color: var(--muted); }
    .empty-state .icon { font-size: 3rem; margin-bottom: 1rem; opacity: 0.4; }
    .empty-state h3 { font-size: 1.25rem; color: var(--text); margin-bottom: 0.5rem; }
    .alert-error {
      background: rgba(192,57,43,0.1); border: 1px solid rgba(192,57,43,0.3);
      border-radius: var(--radius); padding: 1rem 1.25rem;
      color: #e07070; font-size: 14px;
    }
    .skeleton {
      background: linear-gradient(90deg, var(--surface) 25%, var(--surface2) 50%, var(--surface) 75%);
      background-size: 200% 100%; animation: shimmer 1.4s infinite;
      border-radius: 4px;
    }
    @keyframes shimmer { 0%{background-position:200% 0} 100%{background-position:-200% 0} }

    /* ── FOOTER ── */
    footer {
      border-top: 1px solid var(--border);
      padding: 2.5rem 1.5rem;
    }
    .footer-inner {
      max-width: 1180px; margin: 0 auto;
      display: flex; gap: 2rem; flex-wrap: wrap;
      justify-content: space-between; align-items: center;
    }
    .footer-logo {
      font-family: 'Bebas Neue', sans-serif;
      font-size: 1.6rem; letter-spacing: 0.05em;
    }
    .footer-logo .m { color: var(--gold); }
    .footer-links { display: flex; gap: 1.5rem; flex-wrap: wrap; }
    .footer-links a { color: var(--muted2); font-size: 13px; text-decoration: none; transition: color 0.2s; }
    .footer-links a:hover { color: var(--gold); }
    .footer-copy { color: var(--muted2); font-size: 12px; line-height: 1.8; }

    /* ── RESPONSIVE ── */
    @media (max-width: 700px) {
      .header-inner { flex-wrap: wrap; height: auto; padding: 0.75rem 1rem; gap: 0.6rem; }
      nav { display: none; }
      .hero { min-height: 340px; }
      .hero-stats { gap: 1.25rem; }
      .movies-grid { grid-template-columns: repeat(2, 1fr); gap: 0.85rem; }
      .movie-page-overlay { flex-direction: column; gap: 1rem; }
      .movie-page-thumb, .movie-page-thumb-fallback { width: 90px; }
      .mirror-row { flex-direction: column; align-items: flex-start; }
    }
  </style>
</head>
<body>

<header>
  <div class="header-inner">
    <a class="logo" href="/">
      <span class="logo-ny">NY</span><span class="logo-m">Movies</span><span class="logo-dot"></span>
    </a>
    <div class="search-wrap">
      <form action="/search" method="get">
        <span class="search-icon">&#9906;</span>
        <input name="q" placeholder="Search any movie or series…"
               value="{{ query|default('') }}" autocomplete="off" spellcheck="false">
        <button type="submit">Search</button>
      </form>
    </div>
    <nav>
      <a href="/search?q=action">Action</a>
      <a href="/search?q=thriller">Thriller</a>
      <a href="/search?q=comedy">Comedy</a>
      <a href="/search?q=new+2024">New <span class="nav-badge">NEW</span></a>
    </nav>
  </div>
</header>

{{ content|safe }}

<footer>
  <div class="footer-inner">
    <div>
      <div class="footer-logo">NY<span class="m">Movies</span></div>
      <div class="footer-copy" style="margin-top:0.4rem;">
        Your destination for cinema.<br>
        © 2025 NYMovies. All rights reserved.
      </div>
    </div>
    <div class="footer-links">
      <a href="/">Home</a>
      <a href="/search?q=bollywood">Bollywood</a>
      <a href="/search?q=hollywood">Hollywood</a>
      <a href="/search?q=web+series">Web Series</a>
    </div>
    <div class="footer-copy" style="max-width:280px;text-align:right;">
      NYMovies does not host any files. All links redirect to third-party hosting services. For personal use only.
    </div>
  </div>
</footer>

</body>
</html>
"""

HOME_CONTENT = """
<div class="hero">
  <div class="hero-inner">
    <div class="hero-eyebrow">Premium Cinema</div>
    <h1>Every Film.<br><em>Every Format.</em></h1>
    <p>Search any title and get direct download links — 4K, 1080p, 720p, Dual Audio. No detours, no popups.</p>
    <div class="hero-actions">
      <a href="/search?q=hindi+2024" class="btn btn-primary">&#9654; Latest Hindi</a>
      <a href="/search?q=hollywood+4k" class="btn btn-outline">Hollywood 4K</a>
    </div>
    <div class="hero-stats">
      <div>
        <div class="hero-stat-num">50K+</div>
        <div class="hero-stat-label">Movies</div>
      </div>
      <div>
        <div class="hero-stat-num">4K</div>
        <div class="hero-stat-label">Ultra HD</div>
      </div>
      <div>
        <div class="hero-stat-num">Free</div>
        <div class="hero-stat-label">Always</div>
      </div>
    </div>
  </div>
</div>

<div class="main">
  <div class="section-label">Browse by Genre</div>
  <div class="section-title" style="margin-bottom:1rem;">What Are You Watching Tonight?</div>
  <div class="genre-grid">
    <a href="/search?q=action" class="genre-pill">&#128165; Action</a>
    <a href="/search?q=comedy" class="genre-pill">&#128514; Comedy</a>
    <a href="/search?q=horror" class="genre-pill">&#128123; Horror</a>
    <a href="/search?q=thriller" class="genre-pill">&#128299; Thriller</a>
    <a href="/search?q=drama" class="genre-pill">&#127914; Drama</a>
    <a href="/search?q=sci-fi" class="genre-pill">&#128640; Sci-Fi</a>
    <a href="/search?q=romance" class="genre-pill">&#10084; Romance</a>
    <a href="/search?q=animation" class="genre-pill">&#127912; Animation</a>
    <a href="/search?q=crime" class="genre-pill">&#128373; Crime</a>
    <a href="/search?q=web+series" class="genre-pill">&#128250; Web Series</a>
    <a href="/search?q=bollywood" class="genre-pill">&#127895; Bollywood</a>
    <a href="/search?q=south+hindi" class="genre-pill">&#127900; South Hindi</a>
  </div>

  <div class="section-label" style="margin-top:1rem;">Quick Search Ideas</div>
  <div class="section-title">Popular Right Now</div>
  <div style="display:flex;gap:0.5rem;flex-wrap:wrap;margin-bottom:3rem;">
    {% for term in ['Pushpa 2','Kalki 2898','Animal','Stree 2','Jawan','Dunki','Pathaan','Leo','Crew'] %}
    <a href="/search?q={{ term|urlencode }}"
       style="background:var(--surface2);border:1px solid var(--border2);border-radius:50px;
              padding:0.35rem 0.9rem;font-size:13px;color:var(--muted);text-decoration:none;
              transition:all 0.18s;"
       onmouseover="this.style.borderColor='var(--gold)';this.style.color='var(--gold)'"
       onmouseout="this.style.borderColor='var(--border2)';this.style.color='var(--muted)'">{{ term }}</a>
    {% endfor %}
  </div>
</div>
"""

# ── HELPERS ─────────────────────────────────────────────────────────────────

def rewrite_hubcloud(url: str) -> str:
    """Rewrite any hubcloud.* domain to HUBCLOUD_DOMAIN."""
    if not url:
        return url
    return re.sub(r'hubcloud\.[a-z]+', HUBCLOUD_DOMAIN, url, flags=re.I)


def get_current_site() -> str:
    try:
        r = SESSION.get(LANDING_PAGE, timeout=12, allow_redirects=True)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        for a in soup.find_all("a", href=True):
            if "visit" in a.get_text(" ", strip=True).lower():
                return a["href"].rstrip("/")
        for a in soup.find_all("a", href=True):
            h = a["href"]
            if "dudefilms" in h and h.startswith("http"):
                return h.rstrip("/")
    except Exception:
        pass
    return "https://dudefilms.irish"


def build_url(base: str, url: str) -> str:
    return urljoin(base, url) if url else ""


def parse_quality(text: str):
    if not text:
        return None, None
    q = re.search(r'\b(4K|2160p|1080p|720p|480p|360p|HDCam|CAM|HDCAM|BluRay|WEB-DL|WEBRip|DVDRip|AMZN)\b', text, re.I)
    s = re.search(r'\[?\s*([\d.]+\s*(?:MB|GB))\s*\]?', text, re.I)
    return (q.group(1).upper() if q else None), (s.group(1).upper() if s else None)


KNOWN_HOSTS = [
    "filepress.online", "filepress.today", "filepress.press", "filepress.world",
    "howblogs.xyz", "gofile.io", "googleusercontent.com", "drive.google.com",
    "pixeldrain.dev", "pixeldrain.com", "dtflix.ink", "neolinks.icu",
    "krakenfiles.com", "hubcloud", "filebee", "r2.dev", "gdrive",
    "g-drive", "filepress", "worker.dev", "cf-worker", "1drv.ms",
    "mega.nz", "mediafire.com", "sendcm.com", "streamtape.com",
    "dropgalaxy.com", "uploadhaven.com", "nitroflare.com",
]

DOWNLOAD_KEYWORDS = [
    "download", "direct download", "g-drive", "gdrive",
    "fast server", "download file", "download now",
    "get file", "server", "mirror",
]

SKIP_TEXT = [
    "category", "home", "contact", "privacy", "disclaimer",
    "request", "dmca", "terms", "policy", "about", "sitemap",
]


def extract_dl_links(soup: BeautifulSoup, base_url: str) -> list:
    links = []

    # Strategy 1: WP maxbutton / styled download buttons (most reliable)
    for sel in [
        "a.maxbutton-download-link",
        "a.maxbutton-download",
        "a[class*='download']",
        "a[class*='dl-btn']",
        "a[id*='download']",
    ]:
        for a in soup.select(sel):
            href = build_url(base_url, a.get("href", ""))
            if not href:
                continue
            # Find nearest heading for quality context
            heading = a.find_previous(["h1","h2","h3","h4","h5","h6"])
            htext = heading.get_text(" ", strip=True) if heading else ""
            q, sz = parse_quality(htext or a.get_text(" ", strip=True))
            links.append({
                "title": (f"{q} | {sz}" if q and sz else q or sz or htext or "Download").strip(" |"),
                "url": rewrite_hubcloud(href),
                "quality": q, "size": sz, "heading": htext,
            })

    if links:
        return _dedup(links)

    # Strategy 2: Structured headings → buttons pattern
    for heading in soup.find_all(["h2","h3","h4"]):
        htext = heading.get_text(" ", strip=True)
        if not re.search(r'\d{3,4}p|4K|BluRay|WEB|CAM|HDRip', htext, re.I):
            continue
        q, sz = parse_quality(htext)
        # Collect all anchors until next heading of same/higher level
        siblings = []
        for sib in heading.find_next_siblings():
            if sib.name in ["h1","h2","h3","h4"]:
                break
            siblings.append(sib)
        sib_soup = BeautifulSoup("".join(str(s) for s in siblings), "html.parser")
        for a in sib_soup.find_all("a", href=True):
            href = build_url(base_url, a["href"])
            if not href:
                continue
            atxt = a.get_text(" ", strip=True).lower()
            if any(sk in atxt for sk in SKIP_TEXT):
                continue
            if any(h in href.lower() for h in KNOWN_HOSTS) or any(k in atxt for k in DOWNLOAD_KEYWORDS):
                links.append({
                    "title": (f"{q} | {sz}" if q and sz else q or htext).strip(" |"),
                    "url": rewrite_hubcloud(href),
                    "quality": q, "size": sz, "heading": htext,
                })

    if links:
        return _dedup(links)

    # Strategy 3: Fallback — scan all anchors
    for a in soup.find_all("a", href=True):
        href = build_url(base_url, a["href"])
        if not href:
            continue
        txt = a.get_text(" ", strip=True)
        low_txt = txt.lower()
        low_href = href.lower()
        if any(sk in low_txt for sk in SKIP_TEXT):
            continue
        if any(h in low_href for h in KNOWN_HOSTS) or any(k in low_txt for k in DOWNLOAD_KEYWORDS):
            q, sz = parse_quality(txt)
            links.append({"title": txt or href, "url": rewrite_hubcloud(href), "quality": q, "size": sz, "heading": ""})

    return _dedup(links)


def _dedup(lst: list) -> list:
    seen, out = set(), []
    for it in lst:
        if it["url"] not in seen:
            seen.add(it["url"])
            out.append(it)
    return out


def fetch_mirrors(url: str) -> list:
    """Follow an intermediate link page and extract the real download links."""
    try:
        r = SESSION.get(url, timeout=18, allow_redirects=True)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        links = extract_dl_links(soup, r.url)
        for lk in links:
            lk["url"] = rewrite_hubcloud(lk["url"])
        return links
    except Exception:
        return []


def fetch_search_results(soup: BeautifulSoup) -> list:
    """Extract article title+url+thumbnail from a WordPress search page."""
    results = []
    articles = soup.select("article")
    if not articles:
        articles = soup.select("div.post, div.item, li.post")

    for art in articles:
        # Title & URL
        link = (
            art.select_one("h2 a, h3 a, h1 a, .entry-title a, .post-title a")
            or art.select_one("a")
        )
        if not link:
            continue
        title = link.get_text(" ", strip=True)
        url   = link.get("href", "")
        if not url or not title:
            continue

        # Thumbnail — try multiple sources
        thumb = None
        for sel in ["img.wp-post-image", "img.attachment-post-thumbnail",
                    ".post-thumbnail img", "img[src*='wp-content']", "img"]:
            img = art.select_one(sel)
            if img:
                src = img.get("data-src") or img.get("src") or img.get("data-lazy-src", "")
                if src and not src.endswith(".gif") and "data:image" not in src:
                    thumb = src
                    break

        results.append({"title": title, "url": url, "thumb": thumb})

    # Fallback: generic link scan if article-based failed
    if not results:
        for a in soup.select("h2 a, h3 a"):
            title = a.get_text(" ", strip=True)
            url   = a.get("href", "")
            if title and url:
                results.append({"title": title, "url": url, "thumb": None})

    seen, out = set(), []
    for it in results:
        if it["url"] not in seen:
            seen.add(it["url"])
            out.append(it)
    return out


def scrape_movie_meta(soup: BeautifulSoup) -> dict:
    """Extract title, thumbnail, description, year from a movie page."""
    meta = {"title": "", "thumb": None, "description": "", "year": "", "genres": []}

    # OG tags are most reliable
    og = lambda p: (soup.find("meta", property=p) or {}).get("content", "")
    meta["title"]       = og("og:title") or (soup.find("h1") or {}).get_text(" ", strip=True) or ""
    meta["thumb"]       = og("og:image") or None
    meta["description"] = og("og:description") or ""

    if not meta["thumb"]:
        img = (soup.select_one(".post-thumbnail img, .entry-thumbnail img, article img")
               or soup.select_one("img.wp-post-image"))
        if img:
            meta["thumb"] = img.get("data-src") or img.get("src") or ""

    y = re.search(r'\b(19\d{2}|20\d{2})\b', meta["title"])
    meta["year"] = y.group(1) if y else ""
    meta["description"] = meta["description"][:220].rstrip() + ("…" if len(meta["description"]) > 220 else "")

    return meta


def clean_title(raw: str) -> str:
    t = re.sub(r'\s*[\(\[]\d{4}[\)\]].*', '', raw)
    t = re.sub(r'\s*(Hindi|English|Dual Audio|BluRay|WEB-DL|WEBRip|HDCam|CAM|HD|4K|1080p|720p|480p|Download|Full Movie)\b.*', '', t, flags=re.I)
    return t.strip(" –|-:") or raw


def quality_badge_class(q: str) -> str:
    if not q:
        return ""
    q = q.upper()
    if "4K" in q or "2160" in q:
        return "v4k"
    if "1080" in q:
        return "v1080"
    if "720" in q:
        return "v720"
    return ""


def host_label(url: str) -> tuple:
    """Return (icon, friendly name) for a known download host."""
    low = url.lower()
    if "hubcloud" in low:
        return "⚡", "HubCloud — Fast Server"
    if "drive.google" in low or "googleusercontent" in low or "gdrive" in low:
        return "📁", "Google Drive"
    if "gofile" in low:
        return "📦", "GoFile"
    if "pixeldrain" in low:
        return "🌊", "PixelDrain"
    if "mega.nz" in low:
        return "🔷", "Mega"
    if "mediafire" in low:
        return "🔥", "MediaFire"
    if "krakenfiles" in low:
        return "🐙", "KrakenFiles"
    if "filepress" in low:
        return "📄", "FilePress"
    if "1drv.ms" in low or "onedrive" in low:
        return "☁️", "OneDrive"
    return "🔗", "Direct Server"


# ── ROUTES ──────────────────────────────────────────────────────────────────

@app.route("/")
def home():
    return render_template_string(BASE_HTML, query="", page_title="", content=HOME_CONTENT)


@app.route("/search")
def search():
    query = request.args.get("q", "").strip()
    if not query:
        return render_template_string(BASE_HTML, query="", page_title="", content=HOME_CONTENT)

    try:
        site       = get_current_site()
        search_url = f"{site}/?s={quote(query)}"
        r          = SESSION.get(search_url, timeout=22)
        results    = fetch_search_results(BeautifulSoup(r.text, "html.parser"))
    except Exception as exc:
        err = f'<div class="main"><div class="alert-error"><strong>Error:</strong> {exc}</div></div>'
        return render_template_string(BASE_HTML, query=query, page_title=f'"{query}"', content=err)

    if not results:
        content = f"""
        <div class="main">
          <div class="empty-state">
            <div class="icon">&#128270;</div>
            <h3>No results for &ldquo;{query}&rdquo;</h3>
            <p>Try a different spelling or a broader keyword.</p>
          </div>
        </div>"""
        return render_template_string(BASE_HTML, query=query, page_title=f'"{query}"', content=content)

    cards = []
    for item in results:
        safe_url  = quote(item["url"], safe=":/?=&")
        safe_back = quote(query)
        raw_title = item["title"]
        clean     = clean_title(raw_title)
        year      = (re.search(r'\b(19\d{2}|20\d{2})\b', raw_title) or [None, ""])[1]
        if hasattr(year, 'group'): year = year  # just in case
        quality, _ = parse_quality(raw_title)
        qbcls      = quality_badge_class(quality or "")

        # Thumbnail
        if item.get("thumb"):
            poster_html = f'<img src="{item["thumb"]}" loading="lazy" alt="{clean}" onerror="this.parentElement.innerHTML=\'<div class=poster-fallback>&#127916;</div>\'">'
        else:
            poster_html = '<div class="poster-fallback">&#127916;</div>'

        badge_html = f'<span class="movie-badge {qbcls}">{quality}</span>' if quality else ''
        year_html  = f'<span class="movie-meta">{year}</span>' if year else ''

        cards.append(f"""
        <div class="movie-card">
          <div class="movie-poster">
            {poster_html}
            {badge_html}
            <div class="movie-overlay">
              <a class="overlay-btn" href="/movie?url={safe_url}&back={safe_back}">Get Links</a>
            </div>
          </div>
          <div class="movie-info">
            <div class="movie-title">{clean}</div>
            {year_html}
          </div>
          <a class="watch-btn" href="/movie?url={safe_url}&back={safe_back}">&#9660; Download Links</a>
        </div>""")

    content = f"""
    <div class="main">
      <div class="page-top">
        <span class="section-label">Search Results</span>
        <span class="result-count">{len(results)} titles found</span>
      </div>
      <div class="section-title">Results for &ldquo;{query}&rdquo;</div>
      <div class="movies-grid">{''.join(cards)}</div>
    </div>"""

    return render_template_string(BASE_HTML, query=query, page_title=f'"{query}"', content=content)


@app.route("/movie")
def movie():
    movie_url  = request.args.get("url", "").strip()
    back_query = request.args.get("back", "")

    if not movie_url:
        return render_template_string(BASE_HTML, query="", page_title="",
            content='<div class="main"><div class="alert-error">Missing movie URL.</div></div>')

    try:
        r    = SESSION.get(movie_url, timeout=22)
        soup = BeautifulSoup(r.text, "html.parser")
        meta = scrape_movie_meta(soup)
        downloads = extract_dl_links(soup, r.url)
    except Exception as exc:
        err = f'<div class="main"><div class="alert-error"><strong>Error:</strong> {exc}</div></div>'
        return render_template_string(BASE_HTML, query=back_query, page_title="Error", content=err)

    clean = clean_title(meta["title"]) or "Movie"
    year  = meta["year"]
    desc  = meta["description"]
    thumb = meta["thumb"]

    # ── Build hero section ──
    if thumb:
        backdrop_html = f'<img class="movie-page-backdrop" src="{thumb}" alt="" onerror="this.style.display=\'none\'">'
        poster_html   = f'<img class="movie-page-thumb" src="{thumb}" alt="{clean}" onerror="this.className=\'movie-page-thumb-fallback\';this.innerHTML=\'&#127916;\'">'
    else:
        backdrop_html = '<div class="movie-page-backdrop-fallback"></div>'
        poster_html   = '<div class="movie-page-thumb-fallback">&#127916;</div>'

    year_tag  = f'<span class="tag">{year}</span>' if year else ''
    count_tag = f'<span class="tag green">{len(downloads)} source{"s" if len(downloads)!=1 else ""}</span>'
    desc_html = f'<p class="movie-description">{desc}</p>' if desc else ''

    rows = [f"""
    <div class="movie-page-hero">
      {backdrop_html}
      <div class="movie-page-overlay">
        {poster_html}
        <div class="movie-page-meta">
          <p class="section-label">Now Downloading</p>
          <h2>{clean}</h2>
          <div class="tag-row">
            {year_tag}
            {count_tag}
            <span class="tag gold">Free</span>
          </div>
          {desc_html}
        </div>
      </div>
    </div>
    <div class="divider">Download Options</div>
    """]

    if not downloads:
        rows.append("""
        <div class="empty-state">
          <div class="icon">&#128221;</div>
          <h3>No download links found on this page</h3>
          <p>The page may be behind a login wall or temporarily unavailable.</p>
        </div>""")
    else:
        for idx, item in enumerate(downloads, 1):
            quality = item.get("quality") or ""
            size    = item.get("size") or ""
            label   = item.get("title") or item.get("heading") or f"Option {idx}"
            qbcls   = quality_badge_class(quality)

            q_badge = f'<span class="dl-q-badge {qbcls}">{quality or "HD"}</span>'
            sz_html = f'<span class="dl-q-size">{size}</span>' if size else ''

            rows.append(f"""
            <div class="dl-section">
              <div class="dl-quality-row">
                {q_badge}
                <span class="dl-q-label">{label}</span>
                {sz_html}
              </div>
              <div class="dl-primary-card">
                <div class="dl-primary-label">Primary Source</div>
                <div class="dl-url-box">{item['url']}</div>
                <div class="dl-actions">
                  <a class="btn-dl btn-dl-gold" href="{item['url']}" target="_blank" rel="noopener">&#9660; Download Now</a>
                  <a class="btn-dl btn-dl-ghost" href="{item['url']}" target="_blank" rel="noopener">Open Link &#8599;</a>
                </div>
            """)

            # Fetch mirrors concurrently would be nice but keep sequential for simplicity
            try:
                mirrors = fetch_mirrors(item["url"])
                if mirrors:
                    rows.append('<div class="mirrors-header">Mirror Servers</div>')
                    for m in mirrors:
                        murl   = m.get("url", "")
                        icon, mname = host_label(murl)
                        is_hub = "hubcloud" in murl.lower()
                        btn_cls = "btn-dl-hubcloud" if is_hub else "btn-dl-gold"
                        rows.append(f"""
                        <div class="mirror-row">
                          <span class="mirror-icon">{icon}</span>
                          <span class="mirror-name">{mname}</span>
                          <span class="mirror-url-short">{murl}</span>
                          <a class="btn-dl {btn_cls}" href="{murl}" target="_blank" rel="noopener">&#9660; Download</a>
                        </div>""")
            except Exception:
                rows.append('<p class="mirror-error" style="padding:0.5rem 0;">Could not fetch mirrors for this source.</p>')

            rows.append("</div></div>")  # close dl-primary-card + dl-section

    safe_back = quote(back_query)
    content = f"""
    <div class="main">
      <a class="back-link" href="/search?q={safe_back}">&#8592; Back to results</a>
      <div style="margin-top:1.5rem;">{''.join(rows)}</div>
    </div>"""

    return render_template_string(BASE_HTML, query=back_query, page_title=clean, content=content)


if __name__ == "__main__":
    app.run(debug=True, port=5000, threaded=True)
