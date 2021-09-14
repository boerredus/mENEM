# import argparse
# import re

# import pyppeteer

# import utils
# import menem.images

# from menem.login import login
# from menem.get_simulation_data import get_simulation_data


# # async def start(email, password, args, page) -> None:
# #     recursion = 0

# #     def output(out: str) -> str:
# #         if out is None or out.endswith('.pdf'):
# #             return out

# #         return out + '.pdf'

# #     def rightness(diff):
# #         nonlocal recursion

# #         char_err_msg = "can't include characters that aren't numbers or aren't in [<, >, %, .]"
# #         diff = diff.replace(' ', '')
# #         levels = {
# #             'easy': 'rightness >= 2/3',
# #             'medium': 'rightness < 2/3 and rightness > 1/3',
# #             'hard': 'rightness <= 1/3'
# #         }

# #         # if diff is easy medium or hard
# #         if diff in levels.keys():
# #             return levels[diff]

# #         # if diff has anything that's not in ['<', '>', '%', [0-9]+, '.']
# #         if re.match(r'[^\<\>\%\d\.]', diff) is not None:
# #             raise argparse.ArgumentTypeError(char_err_msg)

# #         # if diff has > or < signs
# #         if any(op in diff for op in ['>', '<']):
# #             op = '>' if '>' in diff else '<'
# #             diff = diff.replace(op, '')
# #             recursion += 1
# #             diff = rightness(diff)
# #             recursion -= 1

# #             return f'rightness {op} {float(diff)}'

# #         # if diff has a percentage sign
# #         if '%' in diff:
# #             diff = diff.replace('%', '')
# #             if re.match(r'[^\d\>\<]', diff) is not None:
# #                 raise argparse.ArgumentTypeError(char_err_msg)

# #             diff = float(diff) / 100
# #             if recursion == 0:
# #                 return f'rightness == {diff}'

# #             return diff

# #         # if diff is between 0 and 1 or if it's an integer
# #         if re.match(r'^(0(\.\d+)?|1(\.0+)?)$', diff) is not None or re.match(r'[^\d]', diff) is None:
# #             diff = float(diff)
# #             if recursion == 0:
# #                 diff = f'rightness == {diff}'

# #             return diff

# #         return diff

# #     if email is None:
# #         email = utils.get_input(text='type in your email address: ', color='blue')

# #     if password is None:
# #         password = utils.get_input(text='type in your password: ', color='blue')

# #     parser = argparse.ArgumentParser()
# #     parser.add_argument('--output', type=output, default=None)
# #     parser.add_argument('--wrongs', action='store_true', default=True)
# #     parser.add_argument('--rights', action='store_true', default=False)
# #     parser.add_argument('--rightness', type=rightness, default='>0')
# #     args = parser.parse_args(args)

# #     await page.goto('https://meu.bernoulli.com.br/')
# #     await login(page, email, password)
#     await page.goto('https://meu.bernoulli.com.br/simulados/aluno/provas_correcoes')

#     urls, pdf_name = await get_simulation_data(page, args.rightness, args.wrongs, args.rights)
#     paths = menem.images.download(urls)

#     menem.images.generate_pdf(paths, args.output or pdf_name)
#     utils.cprint(color='green', text='done')
