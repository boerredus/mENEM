import time

from utils import wait_loading
from utils import get_selection


async def get_simulation_data(page, percentage) -> list:
    subjects = ['CL', 'CH', 'CN', 'MT']
    print('Fetching simulations...')

    await wait_loading(page, 'select#codigoSimulado > option:not([value*=" "])')
    simuls = await page.querySelectorAllEval('select#codigoSimulado > option:not([value*=" "])', '(simuls => simuls.map(simul => simul.innerHTML))')
    sel = await page.querySelector('select#codigoSimulado')
    jvsSelect = "sel => {{ sel.selectedIndex = {}; sel.dispatchEvent(new Event('change', {{ bubbles: true }}))}}"
    simul_choice = get_selection(simuls, 1)

    await page.evaluate(jvsSelect.format(simul_choice), sel)

    await wait_loading(page, 'div#questoesRespostas:not([style*="display: none"])')
    subject_choice = get_selection(subjects, None) - 1
    await page.querySelectorEval(f'ul#simuladoAreas > li:nth-of-type({subject_choice + 1})', 'opt => opt.click()')
    time.sleep(2)

    wrong_questions = await page.querySelectorAll(f'div#{subjects[subject_choice]} > span.question-item[respostacorreta=N]')
    questions = []
    answers = []

    for question in wrong_questions:
        rightness = await page.evaluate('q => Number(q.getAttribute("probabilidade_acerto"))', question)

        if eval(percentage):
            [q, a] = await page.evaluate('q => [q.getAttribute("enunciado"), q.getAttribute("resolucao")]', question)
            questions.append(q)
            answers.append(a)

    print('Fetched simulations!')
    return questions + answers, f'{simuls[simul_choice - 1]} ({subjects[subject_choice]}).pdf'
