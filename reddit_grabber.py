"""
=============================================================================
                    REDDIT DATASET GRABBER (VIBE EDITION)
    High-Performance Multi-Threaded Reddit Media Scraper & Dataset Generator
    100% VIBE CODED | Optimized for LoRA, Stable Diffusion, Flux & AI Training
=============================================================================
"""

import argparse
import html
import json
import os
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, List, Optional, Set
from urllib.parse import parse_qs, unquote, urlparse

import requests
from playwright.sync_api import sync_playwright

# Optional rich formatting for high-tech aesthetic
try:
    from rich import print as rprint
    from rich.box import ROUNDED
    from rich.console import Console
    from rich.panel import Panel
    from rich.progress import (
        BarColumn,
        DownloadColumn,
        Progress,
        SpinnerColumn,
        TextColumn,
        TimeElapsedColumn,
        TimeRemainingColumn,
        TransferSpeedColumn,
    )
    from rich.table import Table

    RICH_AVAILABLE = True
    console = Console()
except ImportError:
    RICH_AVAILABLE = False
    console = None

VERSION = "1.0.0"
VALID_IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)


@dataclass
class ScrapedImage:
    """Represents a scraped image candidate with metadata."""
    file_id: str
    url: str
    extension: str
    title: str = ""
    author: str = ""
    score: int = 0
    permalink: str = ""
    post_id: str = ""
    subreddit: str = ""


def print_banner():
    """Displays a futuristic cyber-style banner."""
    title_text = f"""
 [bold cyan]██████╗ ███████╗██████╗ ██████╗ ██╗████████╗[/bold cyan]  [bold magenta]███████╗ ██████╗██████╗  █████╗ ██████╗ ███████╗██████╗ [/bold magenta]
 [bold cyan]██╔══██╗██╔════╝██╔══██╗██╔══██╗██║╚══██╔══╝[/bold cyan]  [bold magenta]██╔════╝██╔════╝██╔══██╗██╔══██╗██╔══██╗██╔════╝██╔══██╗[/bold magenta]
 [bold cyan]██████╔╝█████╗  ██║  ██║██║  ██║██║   ██║   [/bold cyan]  [bold magenta]███████╗██║     ██████╔╝███████║██████╔╝█████╗  ██████╔╝[/bold magenta]
 [bold cyan]██╔══██╗██╔══╝  ██║  ██║██║  ██║██║   ██║   [/bold cyan]  [bold magenta]╚════██║██║     ██╔══██╗██╔══██║██╔═══╝ ██╔══╝  ██╔══██╗[/bold magenta]
 [bold cyan]██║  ██║███████╗██████╔╝██████╔╝██║   ██║   [/bold cyan]  [bold magenta]███████║╚██████╗██║  ██║██║  ██║██║     ███████╗██║  ██║[/bold magenta]
 [bold cyan]╚═╝  ╚═╝╚══════╝╚═════╝ ╚═════╝ ╚═╝   ╚═╝   [/bold cyan]  [bold magenta]╚══════╝ ╚═════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝     ╚══════╝╚═╝  ╚═╝[/bold magenta]

 [bold yellow]★ Ultra High-Speed Reddit Media & Dataset Grabber ★[/bold yellow]
 [bold green]⚡ 100% VIBE CODED ⚡[/bold green] [dim]| Version {VERSION} | Playwright Engine | Multi-Threaded[/dim]
"""
    if RICH_AVAILABLE:
        console.print(
            Panel(
                title_text.strip(),
                border_style="magenta",
                box=ROUNDED,
                subtitle="[dim cyan]by Boozwooz[/dim cyan]",
            )
        )
    else:
        print("=" * 70)
        print("       REDDIT DATASET GRABBER (100% VIBE CODED)")
        print(f"     Version {VERSION} | High-Performance Playwright Engine")
        print("=" * 70)


def sanitize_filename(name: str, max_length: int = 60) -> str:
    """Sanitizes text for safe cross-platform filesystem filenames."""
    name = unquote(name)
    name = re.sub(r'[\\/*?:"<>|]', "", name)
    name = re.sub(r"[\s_]+", "_", name)
    name = name.strip("._-")
    return name[:max_length] if name else "untitled"


def normalize_image_url(url: str) -> Optional[str]:
    """
    Normalizes Reddit image URLs, converting preview/thumbnail links
    into full-resolution uncompressed source links.
    """
    if not url:
        return None

    # Unescape entities (e.g. &amp;)
    url = html.unescape(url).strip()

    # Filter out UI assets, emojis, badges, snoos
    lower = url.lower()
    if any(k in lower for k in ["snoo", "avatar", "badge", "award", "icon", "styles.redditmedia.com", "redditstatic.com"]):
        return None

    parsed = urlparse(url)
    netloc = parsed.netloc.lower()

    # Reddit preview -> full resolution i.redd.it
    if "preview.redd.it" in netloc:
        path = parsed.path
        clean_url = f"https://i.redd.it{path}"
        ext = Path(path).suffix.lower()
        if ext in VALID_IMAGE_EXTS:
            return clean_url
        query_params = parse_qs(parsed.query)
        if "format" in query_params:
            return f"https://i.redd.it{path}.{query_params['format'][0].lower()}"
        return clean_url

    # Direct i.redd.it
    if "i.redd.it" in netloc:
        clean_path = parsed.path
        return f"https://i.redd.it{clean_path}"

    # Imgur support
    if "imgur.com" in netloc:
        if "i.imgur.com" in netloc:
            ext = Path(parsed.path).suffix.lower()
            if ext in VALID_IMAGE_EXTS:
                return f"https://i.imgur.com{parsed.path}"
        else:
            stem = Path(parsed.path).stem
            if stem and len(stem) in (5, 7):
                return f"https://i.imgur.com/{stem}.jpg"

    return None


def verify_image_bytes(data: bytes, min_size_bytes: int = 5000) -> bool:
    """Verifies that bytes constitute a valid, non-corrupted image file."""
    if len(data) < min_size_bytes:
        return False

    # JPEG signature
    if data.startswith(b"\xff\xd8\xff"):
        return True
    # PNG signature
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return True
    # GIF signature
    if data.startswith(b"GIF87a") or data.startswith(b"GIF89a"):
        return True
    # WebP signature
    if data.startswith(b"RIFF") and len(data) > 12 and data[8:12] == b"WEBP":
        return True

    return False


class RedditGrabber:
    """Core Reddit scraper leveraging Playwright and multi-threaded concurrency."""

    def __init__(
        self,
        subreddit: str,
        limit: int = 100,
        sort: str = "top",
        time_filter: str = "all",
        output_dir: Optional[Path] = None,
        workers: int = 16,
        min_size_kb: int = 10,
        save_metadata: bool = False,
        headless: bool = True,
        user_agent: str = DEFAULT_USER_AGENT,
    ):
        self.subreddit = subreddit.strip().lstrip("r/").strip("/")
        self.limit = max(1, limit)
        self.sort = sort.lower()
        self.time_filter = time_filter.lower()
        self.output_dir = output_dir or Path(f"dataset_{self.subreddit}")
        self.workers = max(1, workers)
        self.min_size_bytes = min_size_kb * 1024
        self.save_metadata = save_metadata
        self.headless = headless
        self.user_agent = user_agent

        self.images: Dict[str, ScrapedImage] = {}
        self.existing_ids: Set[str] = set()

    def _setup_output_dir(self):
        """Creates target folder and discovers already downloaded files for instant deduplication."""
        self.output_dir.mkdir(parents=True, exist_ok=True)
        if self.output_dir.exists():
            for f in self.output_dir.iterdir():
                if f.is_file() and f.suffix.lower() in VALID_IMAGE_EXTS:
                    self.existing_ids.add(f.stem)

    def _build_url(self) -> str:
        """Constructs target subreddit URL."""
        base = f"https://www.reddit.com/r/{self.subreddit}"
        if self.sort == "top":
            return f"{base}/top/?t={self.time_filter}"
        elif self.sort in ["hot", "new", "rising"]:
            return f"{base}/{self.sort}/"
        return f"{base}/top/?t=all"

    def scan(self) -> List[ScrapedImage]:
        """Runs the Playwright browser engine to scan and discover Reddit images."""
        self._setup_output_dir()
        target_url = self._build_url()

        if RICH_AVAILABLE:
            table = Table(title="Scraping Configuration", box=ROUNDED, border_style="cyan")
            table.add_column("Parameter", style="bold yellow")
            table.add_column("Value", style="bold white")
            table.add_row("Subreddit", f"r/{self.subreddit}")
            table.add_row("Target Limit", str(self.limit))
            table.add_row("Sort & Time", f"{self.sort.upper()} ({self.time_filter})")
            table.add_row("Existing Files", str(len(self.existing_ids)))
            table.add_row("Output Directory", str(self.output_dir.resolve()))
            table.add_row("Save Metadata", "Yes (.txt caption + .json)" if self.save_metadata else "No")
            table.add_row("Concurrent Workers", str(self.workers))
            console.print(table)
            console.print(f"\n[bold green]►[/bold green] Launching browser engine and navigating to [cyan]{target_url}[/cyan]...\n")
        else:
            print(f"[*] Target: r/{self.subreddit} | Limit: {self.limit} | Sort: {self.sort} ({self.time_filter})")
            print(f"[*] Found {len(self.existing_ids)} existing files. Skipping duplicates.")
            print(f"[*] Navigating to {target_url}...\n")

        scan_start = time.time()

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=self.headless)
                context = browser.new_context(
                    viewport={"width": 1920, "height": 1080},
                    user_agent=self.user_agent,
                )
                page = context.new_page()
                page.goto(target_url, wait_until="domcontentloaded", timeout=45000)
                time.sleep(2.5)

                stuck_cycles = 0
                last_count = 0

                status_ctx = console.status("[bold cyan]Scanning feed for images...[/bold cyan]") if RICH_AVAILABLE else None
                if status_ctx:
                    status_ctx.start()

                while len(self.images) < self.limit:
                    # 1. Parse <shreddit-post> web components
                    try:
                        posts = page.locator("shreddit-post").all()
                        for post in posts:
                            content_href = post.get_attribute("content-href") or ""
                            norm_url = normalize_image_url(content_href)
                            if norm_url:
                                img_id = Path(urlparse(norm_url).path).stem
                                file_id = f"{self.subreddit}_{img_id}"
                                if file_id not in self.existing_ids and file_id not in self.images:
                                    ext = Path(urlparse(norm_url).path).suffix.lower() or ".jpg"
                                    post_title = post.get_attribute("post-title") or ""
                                    post_author = post.get_attribute("author") or ""
                                    score_raw = post.get_attribute("score") or "0"
                                    permalink = post.get_attribute("permalink") or ""
                                    try:
                                        score = int(score_raw)
                                    except ValueError:
                                        score = 0

                                    self.images[file_id] = ScrapedImage(
                                        file_id=file_id,
                                        url=norm_url,
                                        extension=ext,
                                        title=post_title,
                                        author=post_author,
                                        score=score,
                                        permalink=f"https://www.reddit.com{permalink}" if permalink.startswith("/") else permalink,
                                        post_id=img_id,
                                        subreddit=self.subreddit,
                                    )
                    except Exception:
                        pass

                    # 2. Extract standard <img> elements
                    try:
                        for img in page.locator("img").all():
                            src = img.get_attribute("src") or ""
                            norm_url = normalize_image_url(src)
                            if norm_url:
                                img_id = Path(urlparse(norm_url).path).stem
                                file_id = f"{self.subreddit}_{img_id}"
                                if file_id not in self.existing_ids and file_id not in self.images:
                                    ext = Path(urlparse(norm_url).path).suffix.lower() or ".jpg"
                                    alt = img.get_attribute("alt") or ""
                                    self.images[file_id] = ScrapedImage(
                                        file_id=file_id,
                                        url=norm_url,
                                        extension=ext,
                                        title=alt,
                                        post_id=img_id,
                                        subreddit=self.subreddit,
                                    )
                    except Exception:
                        pass

                    # 3. Extract direct <a> image links
                    try:
                        for link in page.locator("a[href*='i.redd.it'], a[href*='preview.redd.it']").all():
                            href = link.get_attribute("href") or ""
                            norm_url = normalize_image_url(href)
                            if norm_url:
                                img_id = Path(urlparse(norm_url).path).stem
                                file_id = f"{self.subreddit}_{img_id}"
                                if file_id not in self.existing_ids and file_id not in self.images:
                                    ext = Path(urlparse(norm_url).path).suffix.lower() or ".jpg"
                                    self.images[file_id] = ScrapedImage(
                                        file_id=file_id,
                                        url=norm_url,
                                        extension=ext,
                                        post_id=img_id,
                                        subreddit=self.subreddit,
                                    )
                    except Exception:
                        pass

                    current_count = len(self.images)
                    display_count = min(current_count, self.limit)

                    if status_ctx:
                        status_ctx.update(
                            f"[bold cyan]Scanning r/{self.subreddit}:[/bold cyan] "
                            f"[bold yellow]{display_count}[/bold yellow] / [bold green]{self.limit}[/bold green] images discovered "
                            f"[dim](stuck count: {stuck_cycles})[/dim]"
                        )
                    else:
                        sys.stdout.write(f"\r[*] Discovered images: {display_count}/{self.limit} (stuck: {stuck_cycles})")
                        sys.stdout.flush()

                    if current_count >= self.limit:
                        break

                    # Anti-stuck and scroll detection
                    if current_count == last_count:
                        stuck_cycles += 1
                        page.keyboard.press("PageDown")
                        time.sleep(0.4)
                        if stuck_cycles > 15:
                            if status_ctx:
                                status_ctx.stop()
                            if RICH_AVAILABLE:
                                console.print("\n[yellow]⚠ End of subreddit reached or feed locked by Reddit.[/yellow]")
                            else:
                                print("\n[*] End of subreddit reached or feed locked.")
                            break
                    else:
                        stuck_cycles = 0

                    last_count = current_count

                    # Smooth scrolling
                    page.evaluate("window.scrollBy(0, 1800)")
                    time.sleep(0.7)

                if status_ctx:
                    status_ctx.stop()

                browser.close()

        except KeyboardInterrupt:
            if RICH_AVAILABLE:
                console.print("\n[bold red]✖ Scanning interrupted by user.[/bold red]")
            else:
                print("\n[!] Scanning interrupted by user.")
        except Exception as e:
            if RICH_AVAILABLE:
                console.print(f"\n[bold red]✖ Browser error occurred:[/bold red] {e}")
            else:
                print(f"\n[!] Browser error occurred: {e}")

        elapsed = time.time() - scan_start
        total_found = len(self.images)
        if RICH_AVAILABLE:
            console.print(f"[bold green]✔ Scan complete in {elapsed:.1f}s.[/bold green] Found [bold cyan]{total_found}[/bold cyan] unique new images.")
        else:
            print(f"[+] Scan finished in {elapsed:.1f}s. Found {total_found} images.")

        return list(self.images.values())[: self.limit]

    def download_image(self, session: requests.Session, item: ScrapedImage) -> Optional[int]:
        """Downloads a single image with streaming and validates byte integrity."""
        filepath = self.output_dir / f"{item.file_id}{item.extension}"

        # If already exists with sufficient size, skip
        if filepath.exists() and filepath.stat().st_size >= self.min_size_bytes:
            return None

        for attempt in range(3):
            try:
                response = session.get(item.url, timeout=20, stream=True)
                if response.status_code == 200:
                    content = bytearray()
                    for chunk in response.iter_content(chunk_size=65536):
                        if chunk:
                            content.extend(chunk)

                    if not verify_image_bytes(content, self.min_size_bytes):
                        return None

                    # Write image file
                    with open(filepath, "wb") as f:
                        f.write(content)

                    # Save dataset metadata sidecars if requested
                    if self.save_metadata:
                        # Plain text caption file (useful for Kohya LoRA / Flux / SDXL)
                        if item.title:
                            txt_path = self.output_dir / f"{item.file_id}.txt"
                            with open(txt_path, "w", encoding="utf-8") as f_txt:
                                f_txt.write(item.title.strip())

                        # Detailed JSON metadata
                        json_path = self.output_dir / f"{item.file_id}.json"
                        with open(json_path, "w", encoding="utf-8") as f_json:
                            json.dump(asdict(item), f_json, indent=2, ensure_ascii=False)

                    return len(content)

                elif response.status_code in [429, 500, 502, 503, 504]:
                    time.sleep(1.0 * (attempt + 1))
                else:
                    return None
            except Exception:
                time.sleep(0.5 * (attempt + 1))

        return None

    def download_all(self, target_list: List[ScrapedImage]) -> Dict[str, any]:
        """Downloads all scraped images in parallel using ThreadPoolExecutor."""
        total = len(target_list)
        if total == 0:
            if RICH_AVAILABLE:
                console.print("[yellow]⚠ No new images to download.[/yellow]")
            else:
                print("[!] No new images to download.")
            return {"downloaded": 0, "bytes": 0, "skipped": 0, "time": 0}

        if RICH_AVAILABLE:
            console.print(f"\n[bold green]►[/bold green] Launching multi-threaded download for [bold cyan]{total}[/bold cyan] images with [bold yellow]{self.workers}[/bold yellow] workers...\n")
        else:
            print(f"\n[*] Starting download of {total} images using {self.workers} workers...\n")

        dl_start = time.time()
        success_count = 0
        total_bytes = 0
        skipped_count = 0

        with requests.Session() as session:
            session.headers.update({"User-Agent": self.user_agent})

            with ThreadPoolExecutor(max_workers=self.workers) as executor:
                future_to_item = {
                    executor.submit(self.download_image, session, item): item
                    for item in target_list
                }

                if RICH_AVAILABLE:
                    with Progress(
                        SpinnerColumn(),
                        TextColumn("[progress.description]{task.description}"),
                        BarColumn(complete_style="cyan", finished_style="green"),
                        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                        TextColumn("•"),
                        DownloadColumn(),
                        TextColumn("•"),
                        TransferSpeedColumn(),
                        TextColumn("•"),
                        TimeElapsedColumn(),
                        TextColumn("• ETA:"),
                        TimeRemainingColumn(),
                        console=console,
                    ) as progress:
                        task = progress.add_task("[bold cyan]Downloading images...", total=total)

                        for future in as_completed(future_to_item):
                            try:
                                res_bytes = future.result()
                                if res_bytes is not None:
                                    success_count += 1
                                    total_bytes += res_bytes
                                else:
                                    skipped_count += 1
                            except Exception:
                                skipped_count += 1
                            progress.advance(task)
                else:
                    completed = 0
                    for future in as_completed(future_to_item):
                        completed += 1
                        try:
                            res_bytes = future.result()
                            if res_bytes is not None:
                                success_count += 1
                                total_bytes += res_bytes
                            else:
                                skipped_count += 1
                        except Exception:
                            skipped_count += 1
                        sys.stdout.write(f"\r[*] Download progress: {completed}/{total} (Saved: {success_count})")
                        sys.stdout.flush()
                    print()

        elapsed_dl = time.time() - dl_start

        # Consolidated dataset manifest
        manifest_path = self.output_dir / "dataset_manifest.json"
        manifest_data = {
            "subreddit": self.subreddit,
            "version": VERSION,
            "vibe_coded": True,
            "download_date": time.strftime("%Y-%m-%d %H:%M:%S"),
            "total_images": success_count,
            "total_bytes": total_bytes,
            "items": [asdict(item) for item in target_list],
        }
        try:
            with open(manifest_path, "w", encoding="utf-8") as f:
                json.dump(manifest_data, f, indent=2, ensure_ascii=False)
        except Exception:
            pass

        total_mb = total_bytes / (1024 * 1024)
        avg_speed = total_mb / elapsed_dl if elapsed_dl > 0 else 0

        if RICH_AVAILABLE:
            summary = Table(title="Scraping & Download Summary", box=ROUNDED, border_style="green")
            summary.add_column("Metric", style="bold yellow")
            summary.add_column("Result", style="bold white")
            summary.add_row("Images Saved", f"[bold green]{success_count}[/bold green]")
            summary.add_row("Skipped / Invalid", str(skipped_count))
            summary.add_row("Total Size", f"{total_mb:.2f} MB")
            summary.add_row("Elapsed Time", f"{elapsed_dl:.1f} s")
            summary.add_row("Average Speed", f"{avg_speed:.2f} MB/s")
            summary.add_row("Target Directory", str(self.output_dir.resolve()))
            console.print("\n", summary)
            console.print(Panel(
                f"[bold green]✔ Successfully downloaded {success_count} images to '{self.output_dir.resolve()}'[/bold green]\n"
                "[dim]Ready for AI training (Kohya, LoRA, SDXL, Flux) or personal archiving![/dim]",
                border_style="green",
                box=ROUNDED,
            ))
        else:
            print("\n" + "=" * 55)
            print("                 DOWNLOAD COMPLETE")
            print("=" * 55)
            print(f"[+] Downloaded:  {success_count} images ({total_mb:.2f} MB)")
            print(f"[+] Skipped:     {skipped_count} images")
            print(f"[+] Time Taken:  {elapsed_dl:.1f}s ({avg_speed:.2f} MB/s)")
            print(f"[+] Saved to:    {self.output_dir.resolve()}")
            print("=" * 55)

        return {
            "downloaded": success_count,
            "bytes": total_bytes,
            "skipped": skipped_count,
            "time": elapsed_dl,
        }


def parse_arguments() -> argparse.Namespace:
    """Parses command-line arguments."""
    parser = argparse.ArgumentParser(
        description="High-Speed Reddit Image & Dataset Grabber (100% Vibe Coded)",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "-s", "--subreddit",
        type=str,
        default="",
        help="Target Subreddit name (e.g. LiminalSpace, wallpapers, Cyberpunk)",
    )
    parser.add_argument(
        "-n", "--limit",
        type=int,
        default=0,
        help="Number of images to scrape and download",
    )
    parser.add_argument(
        "--sort",
        type=str,
        choices=["top", "hot", "new", "rising"],
        default="top",
        help="Reddit sorting filter",
    )
    parser.add_argument(
        "-t", "--time",
        type=str,
        choices=["all", "year", "month", "week", "day", "hour"],
        default="all",
        help="Time window filter for 'top' sort",
    )
    parser.add_argument(
        "-o", "--output",
        type=str,
        default="",
        help="Destination directory (default: dataset_<subreddit>)",
    )
    parser.add_argument(
        "-w", "--workers",
        type=int,
        default=16,
        help="Number of concurrent download threads",
    )
    parser.add_argument(
        "--min-size",
        type=int,
        default=10,
        help="Minimum file size in KB to keep (filters icons and thumbnails)",
    )
    parser.add_argument(
        "--save-metadata",
        action="store_true",
        help="Save companion .txt (caption) and .json (metadata) sidecars for AI training",
    )
    parser.add_argument(
        "--no-headless",
        action="store_true",
        help="Run browser in visible mode (default is headless)",
    )
    return parser.parse_args()


def interactive_prompt() -> dict:
    """Provides a sleek interactive prompt when run without CLI flags."""
    print_banner()
    if RICH_AVAILABLE:
        console.print("[bold yellow]Interactive Setup Mode[/bold yellow] [dim](Press Enter to use defaults)[/dim]\n")
    else:
        print("\n--- Interactive Setup Mode (Press Enter for defaults) ---\n")

    subreddit = input("[?] Target Subreddit [Default: LiminalSpace]: ").strip() or "LiminalSpace"

    limit_input = input("[?] Number of images to download [Default: 100]: ").strip() or "100"
    try:
        limit = int(limit_input)
    except ValueError:
        limit = 100

    sort_input = input("[?] Sort method (top/hot/new/rising) [Default: top]: ").strip().lower() or "top"
    if sort_input not in ["top", "hot", "new", "rising"]:
        sort_input = "top"

    time_filter = "all"
    if sort_input == "top":
        t_input = input("[?] Time filter (all/year/month/week/day) [Default: all]: ").strip().lower() or "all"
        if t_input in ["all", "year", "month", "week", "day"]:
            time_filter = t_input

    meta_input = input("[?] Save AI dataset metadata (.txt caption & .json) [y/N]: ").strip().lower()
    save_metadata = meta_input in ["y", "yes", "true", "1"]

    workers_input = input("[?] Download workers [Default: 16]: ").strip() or "16"
    try:
        workers = int(workers_input)
    except ValueError:
        workers = 16

    return {
        "subreddit": subreddit,
        "limit": limit,
        "sort": sort_input,
        "time_filter": time_filter,
        "save_metadata": save_metadata,
        "workers": workers,
        "output_dir": None,
        "min_size_kb": 10,
        "headless": True,
    }


def main():
    args = parse_arguments()

    if not args.subreddit and args.limit == 0:
        config = interactive_prompt()
    else:
        print_banner()
        config = {
            "subreddit": args.subreddit or "LiminalSpace",
            "limit": args.limit if args.limit > 0 else 100,
            "sort": args.sort,
            "time_filter": args.time,
            "save_metadata": args.save_metadata,
            "workers": args.workers,
            "output_dir": Path(args.output) if args.output else None,
            "min_size_kb": args.min_size,
            "headless": not args.no_headless,
        }

    grabber = RedditGrabber(
        subreddit=config["subreddit"],
        limit=config["limit"],
        sort=config["sort"],
        time_filter=config["time_filter"],
        output_dir=config["output_dir"],
        workers=config["workers"],
        min_size_kb=config["min_size_kb"],
        save_metadata=config["save_metadata"],
        headless=config["headless"],
    )

    # Phase 1: Browser-based Infinite Scroll Scan
    items = grabber.scan()

    # Phase 2: Parallel High-Speed Download
    grabber.download_all(items)


if __name__ == "__main__":
    main()
