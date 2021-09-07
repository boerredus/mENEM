import os
import time


async def wait_loading(page, query: str, once: bool = False):
    element = await page.querySelector(query)
    while element == None and not once:
        element = await page.querySelector(query)
        time.sleep(0.5)

    return element


async def screenshot(page):
    await page.screenshot({'path': 's.png'})
    os.remove('s.png')


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
