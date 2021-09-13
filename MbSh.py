import cmd
import shlex
import argparse
import os
import json
import inspect

import pyppeteer

import docs

import mENEM
import utils


class MbSh(cmd.Cmd):
    intro = 'Welcome to mbsh! Type help or ? for help.\n'
    prompt = 'mbsh> '
    browser = None
    pages = {}
    config = {
        'cache': os.path.dirname(__file__) + '/config.json'
    }

    def do_config(self, args) -> None:
        "Configure mbsh's behavior"

        args = shlex.split(args)
        parser = argparse.ArgumentParser()

        if len(args) == 0:
            utils.cprint(
                color='red', text='`config` needs at least one argument')
            return

        action = args[0]
        args = args[1:]

        if action == 'get':
            parser.add_argument('key', type=str, nargs='?', default=None)
            args = parser.parse_args(args)
            key = args.key

            if key == None:
                utils.cprint(color='red', text='`config get` needs a key name')
            else:
                val = self.config.get(key, '[undefined]')
                print(val)

        elif action == 'set':
            parser.add_argument('key', type=str, nargs='?', default=None)
            parser.add_argument('val', type=str, nargs='?', default=None)
            args = parser.parse_args(args)
            key, val = args.key, args.val

            if key == None or val == None:
                utils.cprint(color='red', text='`config set` needs a key and a value; nothing set')
            else:
                self.config[key] = val
                print(f'{key}: {val}')

        elif action == 'clear':
            parser.add_argument('key', type=str, nargs='?', default=None)
            args = parser.parse_args(args)
            key = args.key

            if key == None:
                self.config = {}
                utils.cprint(color='green', text='cleared all configs')
            elif key in self.config:
                del self.config[key]
            else:
                utils.cprint(color='red', text=f'no confing named {key} found')

        elif action == 'list':
            if len(self.config) == 0:
                print('[undefined]')
            else:
                for key, val in self.config.items():
                    print(f'{key}: {val}')

        elif action == 'help':
            print(docs.CONFIG)

        else:
            utils.cprint(color='red', text='option not found; type `config help` for more info')

    async def do_menem(self, args) -> None:
        'Enter mENEM utility'

        args = shlex.split(args)
        args = args[1:]

        email = self.config.get('email', None)
        password = self.config.get('password', None)

        page = await self.browser.newPage()
        self.pages['menem'] = page

        await self.changeprompt('menem> ')
        utils.prefix = 'menem: '

        await mENEM.start(email, password, args, page)

        await self.changeprompt('mbsh> ')
        utils.prefix = 'mbsh: '

    def do_EOF(self, _) -> None:
        'Exit mbsh'
        print()
        return 'EOF'

    def readcachefile(self) -> dict:
        config = r'{}'

        # if there's a cache file
        if 'cache' in self.config and os.path.isfile(self.config['cache']):
            with open(self.config['cache'], 'r') as f:
                config = f.read()

        return json.loads(config)

    async def changeprompt(self, prompt) -> None:
        self.prompt = prompt
        await self.onecmd('')

    def default(self, line) -> None:
        utils.cprint(color='red', text=f'`{line}` is not a known syntax')

    async def preloop(self) -> None:
        stored_config = self.readcachefile()
        if stored_config != {}:
            self.config = stored_config

        self.browser = await pyppeteer.launch()
        utils.prefix = 'mbsh: '

    def postloop(self) -> None:
        config = self.readcachefile()

        if 'cache' in self.config and config != {} and self.config != config:
            utils.cprint(color='yellow', text='overwrite existing cache file (y/n)? ', end='')
            overwrite = input()
            overwrite = overwrite.lower()

            if overwrite == 'y':
                with open(self.config['cache'], 'w') as f:
                    json.dump(self.config, f)
                    utils.cprint(color='green', text='settings saved')
            else:
                utils.cprint(color='yellow', text='file not overwritten')

    def emptyline(self) -> None:
        pass

    async def cmdloop(self, intro=None):
        old_completer = None
        completekey = 'tab'
        parent = super()

        await self.preloop()

        try:
            import readline

            old_completer = readline.get_completer()
            readline.set_completer(parent.complete)
            readline.parse_and_bind(completekey+": complete")
        except ImportError:
            pass

        try:
            if intro is not None:
                self.intro = intro

            if self.intro:
                self.stdout.write(str(self.intro)+"\n")

            stop = None

            while not stop:
                try:
                    line = input(self.prompt)
                except EOFError:
                    line = 'EOF'

                line = parent.precmd(line)
                stop = await self.onecmd(line)
                stop = parent.postcmd(stop, line)

            self.postloop()
        finally:
            if parent.use_rawinput and completekey:
                try:
                    import readline

                    readline.set_completer(old_completer)
                except ImportError:
                    pass

    async def onecmd(self, line):
        parent = super()

        cmd, arg, line = parent.parseline(line)

        if not line:
            return self.emptyline()

        if cmd is None:
            return self.default(line)

        self.lastcmd = line

        if line == 'EOF':
            self.lastcmd = ''

        if cmd == '':
            return parent.default(line)
        else:
            try:
                func = getattr(self, 'do_' + cmd)
            except AttributeError:
                return self.default(line)

            if inspect.iscoroutinefunction(func):
                return await func(arg)

            return func(arg)
