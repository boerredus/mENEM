import os
import requests

def download_images(urls: list) -> list:
    print('Downloading images...')
    paths = []

    if not os.path.isdir(f'images'):
        os.mkdir(f'images')

    for url in urls:
        path = f'images/{os.path.basename(url)}'
        r = requests.get(url)

        if r.ok:
            with open(path, 'wb') as f:
                f.write(r.content)
                paths.append(path)

    print('Downloaded all images!')
    return paths