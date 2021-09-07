import time

from utils import wait_loading
from utils import screenshot
from utils import get_selection


async def login(page, email, passw) -> None:
    print('Logging in...')

    # todo: wrong password
    if email == None:
        email = input('> Type in meubernoulli email: ')

    if passw == None:
        passw = input('> Type in meubernoulli password: ')

    userField = await wait_loading(page, 'input#usuario')
    psswField = await wait_loading(page, 'input#senha')
    loginBttn = await wait_loading(page, 'button#btnLogin')
    await userField.type(email)
    await psswField.type(passw)
    await loginBttn.click()

    time.sleep(5)
    await screenshot(page)

    loginBttn = await wait_loading(page, 'button#btnEntrar')
    optMapLbd = '(opts => opts.map(opt => opt.innerHTML))'
    jvsSelect = "sel => {{ sel.selectedIndex = {}; sel.dispatchEvent(new Event('change', {{ bubbles: true }}))}}"

    await wait_loading(page, 'select#codigoPessoaPerfil > option.validOption')
    sel = await page.querySelector('select#codigoPessoaPerfil')
    options = await page.querySelectorAllEval('select#codigoPessoaPerfil > option.validOption', optMapLbd)
    choice = get_selection(options, 1)
    await page.evaluate(jvsSelect.format(choice), sel)
    time.sleep(2)

    await wait_loading(page, 'select#codigoTurmaAno > option.validOption')
    sel = await page.querySelector('select#codigoTurmaAno')
    options = await page.querySelectorAllEval('select#codigoTurmaAno > option.validOption', optMapLbd)
    choice = get_selection(options, 1)
    await page.evaluate(jvsSelect.format(choice - 1), sel)
    time.sleep(1)

    await loginBttn.click()

    time.sleep(5)
    await screenshot(page)

    await wait_loading(page, '#conteudoFeed')
    print('Logged in!')
