import os
import time

import termcolor

prefix = ''


async def wait_loading(page, query: str, once: bool = False):
    element = await page.querySelector(query)
    while element == None and not once:
        element = await page.querySelector(query)
        time.sleep(0.5)

    return element


async def screenshot(page):
    await page.screenshot({'path': 's.png'})
    os.remove('s.png')


def get_input(text: str, color=None, confirm=True):
    while True:
        if color == None:
            data = input(text)
        else:
            cprint(color=color, text=text, end='')
            data = input()

        if confirm:
            confirmation = get_input(text=f'is `{data}` correct (y/n)? ', color=color, confirm=False)
            confirmation = confirmation.lower()

            if confirmation != 'y':
                continue

        return data


def get_selection(options: list, _min: int) -> int:
    if len(options) == _min:
        return _min

    cprint(color='blue', text='choose an option from the list below:')
    for i in range(len(options)):
        cprint(color='blue', text=f'    [{i + 1}]. {options[i]}')
    while True:
        try:
            answer = get_input('type in your number of choice: ', confirm=False, color='blue')
            answer = int(answer)
            if answer > len(options):
                cprint(color='red', text='please, pick one of the given options')
                continue

            return answer
        except ValueError:
            cprint(color='red', text='please, input the number of one of the given options')


def cprint(color: str, text: str = '', end='\n'):
    if text == '':
        _prefix = ''
    else:
        _prefix = prefix

    termcolor.cprint(text=_prefix + text, color=color, end=end)
