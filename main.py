# if I remove the screenshots: pyppeteer.errors.NetworkError: Execution context was destroyed, most likely because of a navigation.

import asyncio

import pyppeteer

from login import login
from download_images import download_images
from generate_pdf import generate_pdf
from get_simulation_data import get_simulation_data
from parse import parse

async def main() -> int:
    args = parse()

    browser = await pyppeteer.launch()
    page = await browser.newPage()

    await page.goto('https://meu.bernoulli.com.br/')
    await login(page, args.email, args.password)
    await page.goto('https://meu.bernoulli.com.br/simulados/aluno/provas_correcoes')

    urls, pdf_name = await get_simulation_data(page, args.percentage)
    paths = download_images(urls)

    generate_pdf(paths, args.output or pdf_name)

    return 0

if __name__ == '__main__':
    asyncio.get_event_loop().run_until_complete(main())
