import re
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright

LIST_URL = "https://www.cinemagia.ro/filme-in-curand/"
MAX_TRAILERS = 15


def valid_trailer(url):
    p = urlparse(url)
    return (
        p.scheme == "https"
        and p.hostname in ("www.cinemagia.ro", "cinemagia.ro")
        and bool(re.match(r"^/trailer/[a-z0-9-]+/?$", p.path, re.I))
    )


def main():
    with sync_playwright() as pw:
        browser = pw.firefox.launch(headless=True)
        context = browser.new_context(locale="ro-RO")
        page = context.new_page()

        response = page.goto(
            LIST_URL,
            wait_until="domcontentloaded",
            timeout=60000,
        )
        print("List HTTP:", response.status if response else "none")
        print("Page title:", page.title())
        page.wait_for_timeout(3000)

        anchors = page.locator("a[href]").evaluate_all(
            """els => els.map(a => ({
                href: a.href,
                text: a.innerText || a.textContent || ""
            }))"""
        )
        links = []
        for anchor in anchors:
            url = anchor["href"].split("#")[0].split("?")[0]
            if valid_trailer(url) and url not in links:
                links.append(url)

        print("Trailer pages found:", len(links))
        for url in links[:MAX_TRAILERS]:
            try:
                response = page.goto(
                    url,
                    wait_until="domcontentloaded",
                    timeout=45000,
                )
                page.wait_for_timeout(2000)
                html = page.content()
                frames = page.locator("iframe[src]").evaluate_all(
                    "els => els.map(e => e.src)"
                )
                frames += re.findall(
                    r'https?://video\.cinemagia\.ro/if/[a-z0-9]+[^\s"\'<>]*',
                    html,
                    re.I,
                )
                video_ids = set()
                for frame in frames:
                    frame = frame.replace("&amp;", "&")
                    match = re.match(
                        r"^https://video\.cinemagia\.ro/if/([a-z0-9]+)",
                        frame,
                        re.I,
                    )
                    if match:
                        video_ids.add(match.group(1))
                print(
                    "Trailer:", url,
                    "HTTP:", response.status if response else "none",
                    "Video IDs:", sorted(video_ids),
                )
                for video_id in video_ids:
                    print("DRY RUN: discovered video ID:", video_id)
            except Exception as exc:
                print("ERROR:", url, str(exc)[:250])

        print("=== TEST FINALIZAT ===")
        print("Telegram: NU S-A TRIMIS NIMIC")
        print("Apps Script: NEMODIFICAT")
        browser.close()


if __name__ == "__main__":
    main()
