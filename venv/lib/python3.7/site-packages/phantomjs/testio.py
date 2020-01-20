
from phantomjs import Phantom

phantom = Phantom()

conf = {
    'url': 'http://example.com/',
    'output_type': 'html',      # json for json
    'min_wait': 1000,           # 1 second
    'max_wait': 30000,          # 30 seconds
    'selector': '',             # CSS selector if there's any
    'resource_timeout': 3000,   # 3 seconds
    'headers': {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.72 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3",
        "Sec-Fetch-Mode": "navigate",
        'Sec-Fetch-Site': 'same-origin',
        'Upgrade-Insecure-Requests': '1',
    },
    'cookies': [
        {'name': '_Country', 'value': 'US', 'domain': '.google.com',},
        {'name': '_Currency', 'value': 'USD', 'domain': '.google.com',},
    ],
    'functions': [
        'function(){window.location.replace("http://icanhazip.com/");}',
    ],
}


output = phantom.download_page(conf)

print(output)