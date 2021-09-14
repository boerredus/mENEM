import os
import requests
from PIL import Image
import shutil

import utils


def download(urls: list) -> list:
    utils.cprint(text='downloading images')
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

    utils.cprint(color='green', text='downloaded all images')
    return paths


def generate_pdf(paths: list, name: str) -> None:
    imgs = []

    pdf = paths.pop(0)
    pdf = Image.open(pdf)
    pdf = pdf.convert('RGB')

    for img in paths:
        img = Image.open(img)
        img = img.convert('RGB')

        imgs.append(img)

    pdf.save(name, 'PDF', resolution=100.0, save_all=True, append_images=imgs)
    shutil.rmtree('images')
