import re
import logging
import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}


def fetch_product_info(url: str) -> dict:
    """
    Fetch product metadata from a URL.
    Returns: {title, description, image_url, price}
    """
    try:
        with httpx.Client(headers=HEADERS, follow_redirects=True, timeout=15) as client:
            resp = client.get(url)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")

            title = _get_meta(soup, "og:title") or _get_tag(soup, "title") or "Товар"
            desc = _get_meta(soup, "og:description") or _get_meta(soup, "description") or ""
            image = _get_meta(soup, "og:image") or ""
            price = _extract_price(soup, resp.text)

            return {
                "title": title.strip()[:200],
                "description": desc.strip()[:500],
                "image_url": image,
                "price": price,
                "url": url,
            }
    except Exception as e:
        logger.warning(f"Could not fetch product info from {url}: {e}")
        return {"title": "Товар", "description": "", "image_url": "", "price": "", "url": url}


def _get_meta(soup, prop):
    tag = soup.find("meta", property=prop) or soup.find("meta", attrs={"name": prop})
    return tag.get("content", "").strip() if tag else ""


def _get_tag(soup, tag_name):
    t = soup.find(tag_name)
    return t.get_text(strip=True) if t else ""


def _extract_price(soup, html_text):
    """Try to find price in common formats."""
    patterns = [
        r'\$\s*[\d,]+\.?\d*',
        r'[\d\s]+[,.]?\d*\s*₴',
        r'[\d\s]+[,.]?\d*\s*грн',
        r'[\d\s]+[,.]?\d*\s*₸',
    ]
    for pat in patterns:
        m = re.search(pat, html_text[:5000])
        if m:
            return m.group(0).strip()
    return ""


def download_image(image_url: str) -> bytes | None:
    """Download image and return bytes, or None on failure."""
    if not image_url:
        return None
    try:
        with httpx.Client(headers=HEADERS, follow_redirects=True, timeout=15) as client:
            resp = client.get(image_url)
            resp.raise_for_status()
            ct = resp.headers.get("content-type", "")
            if "image" in ct:
                return resp.content
    except Exception as e:
        logger.warning(f"Could not download image {image_url}: {e}")
    return None
