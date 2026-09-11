"""Silently check the live trailer integration without game files or media playback."""
import argparse
import json
from urllib.parse import parse_qs, urlsplit

from playwright.sync_api import sync_playwright


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--url', default='http://127.0.0.1:8073/')
    args = parser.parse_args()
    origin = urlsplit(args.url).netloc
    referrer = f'{urlsplit(args.url).scheme}://{origin}/'
    results = {}
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True, executable_path='/usr/bin/chromium',
                                     args=['--mute-audio'])
        context = browser.new_context()
        requests, errors = [], []
        context.on('request', lambda request: requests.append(request))
        # Verify the real iframe request/referrer, but do not play third-party media.
        context.route('https://www.youtube-nocookie.com/embed/**',
                      lambda route: route.fulfill(content_type='text/html',
                                                 body='<!doctype html><title>Embed check</title>'))
        page = context.new_page()
        page.on('pageerror', lambda error: errors.append(str(error)))
        for width in (375, 768, 1440):
            requests.clear()
            page.set_viewport_size({'width': width, 'height': 1050})
            response = page.goto(args.url)
            assert response.status == 200
            assert 'frame-src https://www.youtube-nocookie.com;' in response.headers['content-security-policy']
            page.wait_for_function("() => document.getElementById('status').textContent.includes('Choose both')")
            button = page.locator('#trailer-play')
            button.scroll_into_view_if_needed()
            assert button.is_visible() and page.locator('iframe, video').count() == 0
            assert all(urlsplit(r.url).netloc == origin and r.method == 'GET'
                       and not r.post_data_buffer for r in requests)
            assert not any('trailer.mp4' in r.url for r in requests)
            assert page.evaluate('() => document.documentElement.scrollWidth <= innerWidth')
            link = page.locator('#trailer-link')
            assert link.get_attribute('href') == 'https://www.youtube.com/watch?v=UloFru4K4Q8'
            # A keyboard user must be able to start it too.
            button.focus()
            with page.expect_request('https://www.youtube-nocookie.com/embed/**') as pending:
                if width == 768:
                    page.keyboard.press('Enter')
                else:
                    button.click()
            request = pending.value
            parameters = parse_qs(urlsplit(request.url).query)
            assert urlsplit(request.url).path == '/embed/UloFru4K4Q8'
            assert parameters['autoplay'] == ['1'] and parameters['mute'] == ['0']
            assert request.all_headers()['referer'] == referrer
            frame = page.locator('#trailer-player iframe')
            assert frame.count() == 1 and page.locator('#trailer-play').count() == 0
            assert frame.get_attribute('referrerpolicy') == 'strict-origin-when-cross-origin'
            assert 'autoplay' in frame.get_attribute('allow')
            box = frame.bounding_box()
            assert box['width'] >= 200 and box['height'] >= 200
            assert all(not r.post_data_buffer for r in requests)
            assert not errors
            results[str(width)] = 'No pre-click YouTube requests; click/keyboard embed, sound parameters, origin referrer, and layout pass'
        context.close()
        browser.close()
    print(json.dumps(results, indent=2))


if __name__ == '__main__':
    main()
