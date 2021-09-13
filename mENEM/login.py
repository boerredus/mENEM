import time

import utils


async def login(page, email, passw) -> None:
    utils.cprint(color='blue', text='logging in')

    userField = await utils.wait_loading(page, 'input#usuario')
    psswField = await utils.wait_loading(page, 'input#senha')
    loginBttn = await utils.wait_loading(page, 'button#btnLogin')
    await userField.type(email)
    await psswField.type(passw)
    await loginBttn.click()

    time.sleep(5)
    await utils.screenshot(page)

    loginBttn = await utils.wait_loading(page, 'button#btnEntrar')
    optMapLbd = '(opts => opts.map(opt => opt.innerHTML))'
    jvsSelect = "sel => {{ sel.selectedIndex = {}; sel.dispatchEvent(new Event('change', {{ bubbles: true }}))}}"

    await utils.wait_loading(page, 'select#codigoPessoaPerfil > option.validOption')
    sel = await page.querySelector('select#codigoPessoaPerfil')
    options = await page.querySelectorAllEval('select#codigoPessoaPerfil > option.validOption', optMapLbd)
    choice = utils.get_selection(options, 1)
    await page.evaluate(jvsSelect.format(choice), sel)
    time.sleep(2)

    await utils.wait_loading(page, 'select#codigoTurmaAno > option.validOption')
    sel = await page.querySelector('select#codigoTurmaAno')
    options = await page.querySelectorAllEval('select#codigoTurmaAno > option.validOption', optMapLbd)
    choice = utils.get_selection(options, 1)
    await page.evaluate(jvsSelect.format(choice - 1), sel)
    time.sleep(1)

    await loginBttn.click()

    time.sleep(5)
    await utils.screenshot(page)

    await utils.wait_loading(page, '#conteudoFeed')
    utils.cprint(color='green', text='logged in')
