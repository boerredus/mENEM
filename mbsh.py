import cmd
import shlex
import os
import json
import inspect
import time
import re

import requests
import pyppeteer

import docs
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

        if len(args) == 0:
            utils.cprint(
                color='red', text='`config` needs at least one argument')
            return

        action = args[0]
        args = args[1:]

        if action == 'get':
            key = utils.get_default(args, 1)

            if key is None:
                utils.cprint(color='red', text='`config get` needs a key name')
            else:
                val = self.config.get(key, '[undefined]')
                print(val)

        elif action == 'set':
            key = utils.get_default(args, 1)
            val = utils.get_default(args, 2)

            if key is None or val is None:
                utils.cprint(
                    color='red', text='`config set` needs a key and a value; nothing set')
            else:
                self.config[key] = val
                print(f'{key}: {val}')

        elif action == 'clear':
            key = utils.get_default(args, 1)

            if key is None:
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

        elif action == 'load':
            configfile = utils.get_default(args, 1)

            if configfile is None:
                utils.cprint(text='`config load` needs a file', color='red')
            else:
                if self.readconfigfile(configfile):
                    utils.cprint(
                        text='configs loaded; type `config list` to list them', color='green')
                else:
                    utils.cprint(
                        text=f'no files named `{configfile}` found; nothing loaded', color='red')

        elif action == 'help':
            print(docs.CONFIG)

        else:
            msg = 'option not found; type `config help` for more info'
            self.default(msg=msg)

    async def do_menem(self, arg) -> None:
        'Enter mENEM utility'

        email = self.config.get('email', None)
        password = self.config.get('password', None)
        page = self.pages.get('menem', None)

        if page is None or self.page.isClosed():
            self.pages['menem'] = await self.browser.newPage()

        menem = mENEM(self.pages['menem'], email, password)

        if arg != '':
            await menem.onecmd(arg)
        else:
            await menem.cmdloop('Welcome to menem! Type help or ? for help.\n')

    def do_EOF(self, _=None) -> None:
        'Exit'
        print()
        return 'EOF'

    def hasconfigfile(self, configfile='') -> bool:
        if 'cache' in self.config and configfile == '':
            configfile = self.config['cache']

        return os.path.isfile(configfile)

    def readconfigfile(self, configfile='', return_data=False):
        hasconfigfile = self.hasconfigfile(configfile)

        if hasconfigfile:
            with open(self.config['cache'], 'r') as f:
                config = f.read() or r'{}'

            config = json.loads(config)
            if config != {}:
                self.config = config

        if return_data:
            return config
        else:
            return hasconfigfile

    async def changeprompt(self, prompt) -> None:
        self.prompt = prompt
        await self.onecmd('')

    def default(self, line=None, msg=None) -> None:
        if msg == None:
            msg = f'`{line}` is not a known syntax'

        utils.cprint(color='red', text=msg)

    async def preloop(self) -> None:
        self.readconfigfile()
        self.browser = await pyppeteer.launch()
        utils.prefix = 'mbsh: '

    def postloop(self) -> None:
        config = self.readconfigfile(return_data=True)

        if 'cache' in self.config and config != {} and self.config != config:
            prompt = 'overwrite existing cache file (y/n)? '
            utils.cprint(color='blue', text=prompt, end='')
            overwrite = input()
            overwrite = overwrite.lower()

            if overwrite == 'y':
                with open(self.config['cache'], 'w') as f:
                    json.dump(self.config, f)
                    utils.cprint(color='green', text='settings saved')
            else:
                utils.cprint(text='file not overwritten')

    def emptyline(self) -> None:
        pass

    async def cmdloop(self, intro=None):
        old_completer = None
        completekey = 'tab'
        parent = super()

        if inspect.iscoroutinefunction(self.preloop):
            await self.preloop()
        else:
            self.preloop()

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

            if inspect.iscoroutinefunction(self.postloop):
                await self.postloop()
            else:
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


class mENEM(MbSh):
    page = None
    email = None
    images = None
    prompt = 'menem> '
    password = None
    loggedin = False

    def __init__(self, page, email: str, password: str) -> None:
        super().__init__()

        self.page = page
        self.email = email
        self.password = password

    async def do_login(self, args):
        args = shlex.split(args)

        if args[0] == 'help':
            print(docs.MENEM)
            return

        email = utils.get_default(args, 0) or self.email
        password = utils.get_default(args, 1) or self.password

        if email is None:
            prompt = 'type in your email address: '
            email = utils.get_input(text=prompt, color='blue')

        if password is None:
            prompt = 'type in your password: '
            password = utils.get_input(text=prompt, color='blue')

        print('logging in')
        userField = await utils.wait_loading(self.page, 'input#usuario')
        psswordField = await utils.wait_loading(self.page, 'input#senha')
        loginBtn = await utils.wait_loading(self.page, 'button#btnLogin')
        await userField.type(email)
        await psswordField.type(password)
        await loginBtn.click()

        time.sleep(5)
        await utils.screenshot(self.page)

        loginBtn = await utils.wait_loading(self.page, 'button#btnEntrar')
        SelectJS = "select => {{ select.selectedIndex = {}; select.dispatchEvent(new Event('change', {{ bubbles: true }}))}}"
        optionExtractor = '(opts => opts.map(opt => opt.innerHTML))'

        await utils.wait_loading(self.page, 'select#codigoPessoaPerfil > option.validOption')
        select = await self.page.querySelector('select#codigoPessoaPerfil')
        options = await self.page.querySelectorAllEval('select#codigoPessoaPerfil > option.validOption', optionExtractor)
        choice = utils.get_selection(options, 1)
        await self.page.evaluate(SelectJS.format(choice), select)
        time.sleep(2)

        await utils.wait_loading(self.page, 'select#codigoTurmaAno > option.validOption')
        select = await self.page.querySelector('select#codigoTurmaAno')
        options = await self.page.querySelectorAllEval('select#codigoTurmaAno > option.validOption', optionExtractor)
        choice = utils.get_selection(options, 1)
        await self.page.evaluate(SelectJS.format(choice - 1), select)
        time.sleep(1)

        await loginBtn.click()

        time.sleep(5)
        await utils.screenshot(self.page)
        await utils.wait_loading(self.page, '#conteudoFeed')

        self.loggedin = True
        utils.cprint(color='green', text='logged in')

    async def do_get_data(self, args):
        if not self.loggedin:
            prompt = 'in order to complete this action, you must be logged in'
            utils.cprint(color='red', text=prompt)
            return

        args = shlex.split(args)

        level = utils.get_default(args, 0, '>0')
        parsed, err = mENEM.level_parser(level)

        if err is not None:
            utils.cprint(color='red', text=err)
            return

        print(parsed)

        # await self.page.goto('https://meu.bernoulli.com.br/simulados/aluno/provas_correcoes')
        # urls, pdf_name = await get_simulation_data(page, args.rightness, args.wrongs, args.rights)

        # utils.cprint(text='downloading images')
        # paths = []

        # if not os.path.isdir(f'images'):
            # os.mkdir(f'images')

        # for url in urls:
            # path = f'images/{os.path.basename(url)}'
            # # r = requests.get(url)
# 
            # # if r.ok:
                # # with open(path, 'wb') as f:
                    # # f.write(r.content)
                    # # paths.append(path)
# 
        # utils.cprint(color='green', text='downloaded all images')


    @staticmethod
    def level_parser(level: str) -> list:
        parsed = None
        level = level.replace(' ', '')
        err_msg = "level can't include characters that aren't in [<, >, %, ., 0-9]"
        levels = {
            'easy': [{'op': 'ge', 'val': 2 / 3}],
            'medium': [{'op': 'lt', 'val': 2 / 3}, {'op': 'gt', 'val': 1 / 3}],
            'hard': [{'op': 'le', 'val': 1 / 3}]
        }

        if level in levels.keys():  # level is easy medium or hard
            parsed = levels[level]

        # level has anything that's not in ['<', '>', '%', [0-9]+, '.']
        elif re.match(r'[^\<\>\%\d\.]', level) is not None:
            return None, err_msg

        elif '>' in level or '<' in level:  # level has <, >
            if '>' in level:
                op = '>'
            else:
                op = '<'
            level = level.replace(op, '')
            mENEM.recursion += 1
            # in case there's a percentage sign
            level, err = mENEM.level_parser(level)
            mENEM.recursion -= 1

            if err is not None:
                return None, err

            if op == '>':
                parsed = {'op': 'gt', 'val': float(level)}
            else:
                parsed = {'op': 'lt', 'val': float(level)}

            parsed = [parsed]

        elif '%' in level:  # if level has a percentage sign
            level = level.replace('%', '')

            if re.match(r'[^\d\>\<]', level) is not None:
                return None, err_msg
            else:
                level = float(level) / 100
                if mENEM.recursion == 0:
                    parsed = [{'op': 'eq', 'val': level}]
                else:
                    parsed = level

        # if level is between 0 and 1 or if it's an integer
        elif re.match(r'^(0(\.\d+)?|1(\.0+)?)$', level) is not None or re.match(r'[^\d]', level) is None:
            parsed = float(level)
            if mENEM.recursion == 0:
                parsed = [{'op': 'eq', 'val': level}]

        return parsed, None

    def preloop(self) -> None:
        utils.prefix = 'menem: '
        mENEM.recursion = 0

    async def postloop(self) -> None:
        choice = utils.get_input(
            text='close MB tab (y/n)? ', color='blue', confirm=False)

        if choice == 'y':
            await self.self.page.close()

        utils.prefix = 'mbsh: '
        del mENEM.recursion
