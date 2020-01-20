# -*- coding: utf-8 -*-

import json
import sys
from . import Phantom

phantom = Phantom()

conf = {
    'headers': {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.72 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3",
        "Sec-Fetch-Mode": "navigate",
        'Sec-Fetch-Site': 'same-origin',
        'Upgrade-Insecure-Requests': '1',
    }
}
conf.update(json.loads(sys.argv[1]))


if __name__ == '__main__':
    a = phantom.download_page(conf, ssl_verify=False)
    print(a)
