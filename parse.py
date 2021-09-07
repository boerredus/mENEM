import argparse
import re

recursion_level = 0

def difficulty_parser(diff: str) -> str:
    global recursion_level

    char_err_msg = "can't include characters that aren't numbers or aren't in [<, >, %, .]"
    diff = diff.replace(' ', '')
    levels = {
        'easy': 'rightness >= 2/3',
        'medium': 'rightness < 2/3 and rightness > 1/3',
        'hard': 'rightness <= 1/3'
    }


    # if diff is easy medium or hard
    if diff in levels.keys():
        return levels[diff]


    # if diff has anything that's not in ['<', '>', '%', [0-9]+, '.']
    if re.match(r'[^\<\>\%\d\.]', diff) != None:
        raise argparse.ArgumentTypeError(char_err_msg)


    # if diff has > or < signs
    if any(op in diff for op in ['>', '<']):
        op = '>' if '>' in diff else '<'
        diff = diff.replace(op, '')
        recursion_level += 1
        diff = difficulty_parser(diff)
        recursion_level -= 1

        return f'rightness {op} {float(diff)}'


    # if diff has a percentage sign
    if '%' in diff:
        diff = diff.replace('%', '')
        if re.match(r'[^\d\>\<]', diff) != None:
            raise argparse.ArgumentTypeError(char_err_msg)

        diff = float(diff) / 100
        if recursion_level == 0:
            return f'rightness == {diff}'
        
        return diff


    # if diff is between 0 and 1 or if it's an integer
    if re.match(r'^(0(\.\d+)?|1(\.0+)?)$', diff) != None or re.match(r'[^\d]', diff) == None:
        diff = float(diff)
        
        if recursion_level == 0:
            diff = f'rightness == {diff}'

        return diff


    return diff


def output(out: str) -> str:
    if out == None or out.endswith('.pdf'):
        return out

    return out + '.pdf'


def parse() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument('--email',
                        required=False,
                        type=str,
                        help='meu.bernoulli.com.br email')
    parser.add_argument('--password',
                        required=False,
                        type=str,
                        help='meu.bernoulli.com.br password')
    parser.add_argument('--output',
                        required=False,
                        type=output,
                        help='Custom name for the generated PDF')
    parser.add_argument('--percentage',
                        required=False,
                        type=difficulty_parser,
                        default='>0',
                        help='Custom percentage of "rights" of questions to fetch (default: >=0 - meaning all)')

    return parser.parse_args()
