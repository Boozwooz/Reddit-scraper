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
