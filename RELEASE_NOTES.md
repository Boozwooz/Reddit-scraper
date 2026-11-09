# 🚀 Reddit Scraper v1.1.0 — Ad-Free & Precision Extraction Release

Welcome to **v1.1.0** of **Reddit Scraper**. This release completely eliminates advertisements, fixes preview URL resolution, and brings high-speed atomic DOM extraction. **100% Vibe Coded.**

---

### ✨ What's New in v1.1.0

- 🚫 **Zero Ads & Sponsored Posts**:
  - Complete elimination of sponsored posts, promoted campaigns, and banner ads.
  - Excludes `<shreddit-ad-post>`, `shreddit-async-loader[bundlename*="ad"]`, and elements with `promoted`, `is-promoted="true"`, `is-sponsored="true"`, `adclick`, or `ad-id`.
  - Built-in Playwright network ad blocker intercepting requests to `alb.reddit.com`, `reddit-promoted.com`, `doubleclick.net`, and tracking domains.
  - Injected CSS styling rules to disable and hide ad elements during scraping.
- 🎯 **Strictly Scoped Organic Media Extraction**:
  - Image harvesting is now strictly scoped inside verified organic `<shreddit-post>` containers.
  - Full support for multi-image galleries, carousels, and figures while ensuring every image is linked to the real post title, author, and upvote score.
- 🔧 **Fixed Preview URLs (No More 403 Forbidden)**:
  - Properly strips Reddit `-v0-` slug prefixes from `preview.redd.it` URLs to target the canonical `https://i.redd.it/<id>.<ext>`.
- ⚡ **10x Faster Atomic Scanning**:
  - Replaced hundreds of sequential Python locator IPC round-trips with high-speed atomic `page.evaluate()` DOM extraction.

---

# 🚀 Reddit Scraper v1.0.0 — Initial Vibe-Coded Release

Welcome to the official **v1.0.0** release of **Reddit Scraper**, an ultra-fast, multi-threaded Reddit image and dataset downloader built for AI creators, researchers, and digital collectors. **100% Vibe Coded.**

---

### ✨ What's New in v1.0.0

- 🌐 **Modern Playwright Chromium Engine**: Seamlessly bypasses Reddit's dynamic client-side rendering (shreddit components, shadow DOM, infinite feeds) without brittle API keys.
- ⚡ **High-Speed Multi-Threaded Downloader**: Concurrent downloads with configurable worker pools (`--workers 16`), streaming chunks directly to disk with exponential retry backoff.
- 🎯 **Full-Resolution Extraction**: Automatically transforms low-res thumbnails and `preview.redd.it` compressed links into raw, uncompressed `i.redd.it` source images.
- 🤖 **AI Dataset Generator (`--save-metadata`)**: Automatically exports:
  - `.txt` caption files (post title) alongside each image — instantly ready for Kohya_ss, LoRA, SDXL, and Flux training!
  - `.json` rich metadata sidecars (author, upvotes, permalink, dimensions).
  - Consolidated `dataset_manifest.json` for the entire batch.
- 🛡️ **Zero Corruptions & Smart Validation**: Inspects magic bytes (JPEG, PNG, WebP, GIF) and filters out empty placeholder images and HTML error pages.
- 🔄 **Intelligent Deduplication**: Automatically skips images already saved on disk.
- 💻 **Cyberpunk Rich Terminal UI**: Interactive prompts with defaults, animated spinners, real-time download progress bars, and execution summary tables.
- 🖱️ **1-Click Launchers**:
  - Windows: `RUN.bat` with auto-dependency installer.
  - Linux / macOS: `run.sh` bash script.

---

### 📦 Installation & Quickstart

```bash
git clone https://github.com/Boozwooz/Reddit-scraper.git
cd Reddit-scraper
pip install -r requirements.txt
playwright install chromium
python reddit_grabber.py
```

### 🤝 Author & Acknowledgments

- **Creator**: [Boozwooz](https://github.com/Boozwooz)
- **Status**: 100% Vibe Coded ✨
