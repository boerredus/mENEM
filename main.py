import asyncio
import argparse
import io
import os

from tssplit import tssplit

import mbsh
import utils


def parse_args():
    parser = argparse.ArgumentParser(prog='mbsh')
    parser.add_argument('file', type=str, nargs='?')
    parser.add_argument('-e', '--eval', type=str, required=False, default=None)
    parser.add_argument('--foreground', action='store_true')

    return parser.parse_args()


async def parse_file(fp: io.TextIOWrapper, _mbsh: mbsh.MbSh):
    lines = fp.readlines()

    for line in lines:
        line = line.strip()
        line = tssplit(line, delimiter=';')

        for cmd in line:
            if utils.is_cmd_safe(cmd):
                await _mbsh.onecmd(cmd)


async def main():
    args = parse_args()
    _mbsh = mbsh.MbSh()

    if args.file != None:
        if not os.path.isfile(args.file):
            prompt = 'given file was not found'
            utils.cprint(text=prompt, color='red', _prefix='', force=True)
        else:
            with open(args.file) as fp:
                await parse_file(fp, _mbsh)
    elif args.eval != None:
        cmds = tssplit(args.eval, delimiter=';')

        for cmd in cmds:
            if utils.is_cmd_safe(cmd):
                await _mbsh.onecmd(cmd)
    else:
        await _mbsh.cmdloop(headless=not args.foreground)

if __name__ == '__main__':
    asyncio.get_event_loop().run_until_complete(main())
