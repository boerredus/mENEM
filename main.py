# if I remove the screenshots: pyppeteer.errors.NetworkError: Execution context was destroyed, most likely because of a navigation.

import asyncio
import os
import shutil
import time

import pyppeteer
import requests
from PIL import Image

page = None


async def wait_loading(query: str, once: bool = False):
    while (element := await page.querySelector(query)) == None and not once:
        time.sleep(0.5)

    return element


def get_selection(options: list, _min: int) -> int:
    if len(options) == _min:
        return _min

    print('\nChoose an option from the list below:')
    for i in range(len(options)):
        print(f'    [{i + 1}]. {options[i]}')
    while True:
        try:
            answer = int(input('> Input your number of choice: '))
            if answer > len(options):
                print('Please, pick one of the given options.')
                continue

            return answer
        except ValueError:
            print('Please, input the number of one of the given options.')


async def screenshot():
    await page.screenshot({'path': 's.png'})
    os.remove('s.png')


async def login() -> None:
    print('Logging in...')

    # todo: wrong password
    email = input('> Type in meubernoulli email: ')
    passw = input('> Type in meubernoulli password: ')

    userField = await wait_loading('input#usuario')
    psswField = await wait_loading('input#senha')
    loginBttn = await wait_loading('button#btnLogin')
    await userField.type(email)
    await psswField.type(passw)
    await loginBttn.click()

    time.sleep(5)
    await screenshot()

    loginBttn = await wait_loading('button#btnEntrar')
    optMapLbd = '(opts => opts.map(opt => opt.innerHTML))'
    jvsSelect = "sel => {{ sel.selectedIndex = {}; sel.dispatchEvent(new Event('change', {{ bubbles: true }}))}}"

    await wait_loading('select#codigoPessoaPerfil > option.validOption')
    sel = await page.querySelector('select#codigoPessoaPerfil')
    options = await page.querySelectorAllEval('select#codigoPessoaPerfil > option.validOption', optMapLbd)
    choice = get_selection(options, 1)
    await page.evaluate(jvsSelect.format(choice), sel)
    time.sleep(2)

    await wait_loading('select#codigoTurmaAno > option.validOption')
    sel = await page.querySelector('select#codigoTurmaAno')
    options = await page.querySelectorAllEval('select#codigoTurmaAno > option.validOption', optMapLbd)
    choice = get_selection(options, 1)
    await page.evaluate(jvsSelect.format(choice - 1), sel)
    time.sleep(1)

    await loginBttn.click()

    time.sleep(5)
    await screenshot()

    await wait_loading('#conteudoFeed')
    print('Logged in!')


async def get_simulation_data() -> list:
    subjects = ['CL', 'CH', 'CN', 'MT']
    print('Fetching simulations...')

    await wait_loading('select#codigoSimulado > option:not([value*=" "])')
    simuls = await page.querySelectorAllEval('select#codigoSimulado > option:not([value*=" "])', '(simuls => simuls.map(simul => simul.innerHTML))')
    sel = await page.querySelector('select#codigoSimulado')
    jvsSelect = "sel => {{ sel.selectedIndex = {}; sel.dispatchEvent(new Event('change', {{ bubbles: true }}))}}"
    simul_choice = get_selection(simuls, 1)

    await page.evaluate(jvsSelect.format(simul_choice), sel)

    await wait_loading('div#questoesRespostas:not([style*="display: none"])')
    subject_choice = get_selection(subjects, None) - 1
    await page.querySelectorEval(f'ul#simuladoAreas > li:nth-of-type({subject_choice + 1})', 'opt => opt.click()')
    time.sleep(2)

    wrong_questions = await page.querySelectorAll(f'div#{subjects[subject_choice]} > span.question-item[respostacorreta=N]')
    questions = []
    answers = []

    for question in wrong_questions:
        [q, a] = await page.evaluate('q => [q.getAttribute("enunciado"), q.getAttribute("resolucao")]', question)

        questions.append(q)
        answers.append(a)

    print('Fetched simulations!')
    return questions + answers, f'{simuls[simul_choice - 1]} ({subjects[subject_choice]}).pdf'


def download_images(urls: list, abspath: str) -> list:
    print('Downloading images...')

    paths = []

    if not os.path.isdir(f'{abspath}/images'):
        os.mkdir(f'{abspath}/images')

    for url in urls:
        path = f'{abspath}/images/{os.path.basename(url)}'
        r = requests.get(url)

        if r.ok:
            with open(path, 'wb') as f:
                f.write(r.content)
                paths.append(path)

    print('Downloaded all images!')
    return paths


def generate_pdf(paths: list, pdf_name: str, abspath: str) -> None:
    first_img = Image.open(paths.pop(0)).convert('RGB')
    images = [Image.open(img).convert('RGB') for img in paths]
    pdf_path = f'{abspath}/{pdf_name}'

    first_img.save(pdf_path, 'PDF', resolution=100.0,
                   save_all=True, append_images=images)
    shutil.rmtree(f'{abspath}/images')


async def main() -> int:
    global page

    browser = await pyppeteer.launch()
    page = await browser.newPage()
    abspath = os.path.abspath(os.path.dirname(__file__))

    await page.goto('https://meu.bernoulli.com.br/')
    await login()
    await page.goto('https://meu.bernoulli.com.br/simulados/aluno/provas_correcoes')

    urls, pdf_name = await get_simulation_data()
    paths = download_images(urls, abspath)

    generate_pdf(paths, pdf_name, abspath)

    return 0

if __name__ == '__main__':
    asyncio.get_event_loop().run_until_complete(main())
