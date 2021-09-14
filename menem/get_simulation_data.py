import time

import utils


async def get_simulation_data(page, rightness_eval, wrongs, rights) -> list:
    subjects = ['CL', 'CH', 'CN', 'MT']
    utils.cprint(text='fetching simulations...')

    await utils.wait_loading(page, 'select#codigoSimulado > option:not([value*=" "])')
    await utils.screenshot(page)
    simuls = await page.querySelectorAllEval('select#codigoSimulado > option:not([value*=" "])', '(simuls => simuls.map(simul => simul.innerHTML))')
    sel = await page.querySelector('select#codigoSimulado')
    jvsSelect = "sel => {{ sel.selectedIndex = {}; sel.dispatchEvent(new Event('change', {{ bubbles: true }}))}}"
    simul_choice = utils.get_selection(simuls, 1)

    await page.evaluate(jvsSelect.format(simul_choice), sel)

    await utils.wait_loading(page, 'div#questoesRespostas:not([style*="display: none"])')
    subject_choice = utils.get_selection(subjects, None) - 1
    await page.querySelectorEval(f'ul#simuladoAreas > li:nth-of-type({subject_choice + 1})', 'opt => opt.click()')
    time.sleep(2)

    questions = f'div#{subjects[subject_choice]} > span.question-item'
    if wrongs and rights:
        pass
    elif wrongs:
        questions += '[respostacorreta=N]'
    elif rights:
        questions += '[respostacorreta=S]'

    questions = await page.querySelectorAll(questions)
    saved_questions = []
    answers = []

    for question in questions:
        rightness = await page.evaluate('q => Number(q.getAttribute("probabilidade_acerto"))', question)

        if eval(rightness_eval):
            [q, a] = await page.evaluate('q => [q.getAttribute("enunciado"), q.getAttribute("resolucao")]', question)
            saved_questions.append(q)
            answers.append(a)

    utils.cprint(color='green', text='fetched simulations!')
    return saved_questions + answers, f'{simuls[simul_choice - 1]} ({subjects[subject_choice]}).pdf'
