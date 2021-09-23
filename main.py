import asyncio
import argparse
import io
import os

import mbsh
import utils


def parse_args():
    parser = argparse.ArgumentParser(prog='mbsh')
    parser.add_argument('file', type=str, nargs='?')
    parser.add_argument('-e', '--eval', type=str, required=False)

    return parser.parse_args()


async def parse_file(fp: io.TextIOWrapper, _mbsh: mbsh.MbSh):
    allowed = ['EOF', 'clear', 'config', 'help', 'history']
    lines = fp.readlines()

    for line in lines:
        line = line.strip()
        cmd = utils.get_default(line.split(' '), 0)

        if not cmd in allowed:
            prompt = f'skipping `{line}`'
            utils.cprint(text=prompt, color='yellow', _prefix='')
        else:
            await _mbsh.onecmd(line)


async def main():
    args = parse_args()
    _mbsh = mbsh.MbSh()

    if args.file != None:
        if not os.path.isfile(args.file):
            prompt = 'given file was not found'
            utils.cprint(text=prompt, color='red', _prefix='')
        else:
            with open(args.file) as fp:
                await parse_file(fp, _mbsh)
    elif args.eval:
        await _mbsh.onecmd(args.eval)
    else:
        await _mbsh.cmdloop()

if __name__ == '__main__':
    asyncio.get_event_loop().run_until_complete(main())
