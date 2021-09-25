import os
import time
import shlex

import termcolor

prefix: str = 'mbsh: '
loggedin: bool = False
output: dict[str, bool] = {
    'output': True,
    'output.log': True,
    'output.success': True,
    'output.warn': True,
    'output.error': True
}


async def wait_loading(page, query: str = '', once: bool = False, eval_query: str = None, val=None, sleep=0.5):
    if eval_query != None:
        element = await page.evaluate(eval_query)
    else:
        element = await page.querySelector(query)

    while element == val and not once:
        if eval_query != None:
            element = await page.evaluate(eval_query)
        else:
            element = await page.querySelector(query)

        time.sleep(sleep)

    return element


async def screenshot(page):
    await page.screenshot({'path': 's.png'})
    os.remove('s.png')


def get_input(text: str, color=None, confirm=True):
    while True:
        if color is None:
            choice = input(text)
        else:
            cprint(color=color, text=text, end='')
            choice = input()

        if confirm:
            prompt = f'is `{choice}` correct (y/n)? '
            confirmation = get_input(text=prompt, color=color, confirm=False)
            confirmation = confirmation.lower()

            if confirmation != 'y':
                continue

        return choice


def get_selection(options: list, _min: int) -> int:
    if len(options) == _min:
        return _min

    cprint(color='blue', text='choose an option from the list below:')
    for i in range(len(options)):
        cprint(color='blue', text=f'    [{i + 1}]. {options[i]}')
    while True:
        try:
            prompt = 'type in your number of choice: '
            answer = get_input(prompt, confirm=False, color='blue')
            answer = int(answer)
            if answer > len(options):
                raise ValueError()

            return answer
        except ValueError:
            prompt = 'please, input the number of one of the given options'
            cprint(color='red', text=prompt)


def cprint(color: str = None, text: str = '', end='\n', _prefix: str = None, force: bool = False) -> None:
    _output = output.get('output', True)
    log = output.get('output.log', True)
    success = output.get('output.success', True)
    warn = output.get('output.warn', True)
    error = output.get('output.error', True)

    hide_output = not _output
    hide_log = color == None and not log
    hide_success = color == 'green' and not success
    hide_warn = color == 'yellow' and not warn
    hide_error = color == 'red' and not error
    hide = hide_output or hide_log or hide_success or hide_warn or hide_error

    if not force and color != 'blue' and hide:
        return

    if _prefix == None:
        _prefix = prefix

    termcolor.cprint(text=_prefix + text, color=color, end=end)


def get_default(lst: list, idx: int, default=None):
    if idx >= len(lst):
        return default

    return lst[idx]


async def goto(page, url: str) -> None:
    if page.url != url:
        await page.goto(url)


def check_login(is_loggedin: bool=None) -> bool:
    if is_loggedin == None:
        is_loggedin = loggedin

    if not is_loggedin:
        prompt = 'in order to complete this action, you must be logged in'
        cprint(color='red', text=prompt)

    return is_loggedin


def is_cmd_safe(cmd: str, report: bool=True):
    cmd = cmd.strip()
    action = get_default(cmd.split(' '), 0)
    is_cmd_allowed = action in ['EOF', 'clear',
                                'config', 'help', 'history', 'login']

    if not is_cmd_allowed and report:
        prompt = f'skipping `{cmd}`'
        cprint(text=prompt, color='yellow', _prefix='', force=True)

    return is_cmd_allowed

def need_help(args: str, help_msg: str) -> bool:
    args = shlex.split(args)
    action = get_default(args, 0)

    if action == 'help':
        cprint(text=help_msg, _prefix='')

    return action == 'help'