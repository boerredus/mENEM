import os
import time

import termcolor

prefix: str = 'mbsh: '
loggedin: bool = False
output: dict[str, bool] = {
    'output': True,
    'output.log': True,
    'output.success': False,
    'output.warn': True,
    'output.error': True
}


async def wait_loading(page, query: str, once: bool = False):
    element = await page.querySelector(query)
    while element is None and not once:
        element = await page.querySelector(query)
        time.sleep(0.5)

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
                prompt = 'please, pick one of the given options'
                cprint(color='red', text=prompt)
                continue

            return answer
        except ValueError:
            prompt = 'please, input the number of one of the given options'
            cprint(color='red', text=prompt)


def cprint(color: str = None, text: str = '', end='\n', _prefix: str=None) -> None:
    _output = output.get('output', True)
    log = output.get('output.log', True)
    success = output.get('output.success', False)
    warn = output.get('output.warn', True)
    error = output.get('output.error', True)

    hide_output = not _output
    hide_log = color == None and not log 
    hide_success = color == 'green' and not success
    hide_warn = color == 'yellow' and not warn 
    hide_error = color == 'red' and not error
    hide = hide_output or hide_log or hide_success or hide_warn or hide_error

    if color != 'blue' and hide:
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


def is_loggedin() -> bool:
    if not loggedin:
        prompt = 'in order to complete this action, you must be logged in'
        cprint(color='red', text=prompt)
        
    return loggedin