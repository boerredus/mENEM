import cmd
import shlex
import os
import json
import inspect
import time
import re

from PIL import Image

import requests
import pyppeteer

import docs
import utils


class MbSh(cmd.Cmd):
    intro = 'Welcome to mbsh! Type help or ? for help.\n'
    prompt = 'mbsh> '
    browser = None
    menem = None
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
            key = utils.get_default(args, 0)
            val = utils.get_default(args, 1)

            if key is None or val is None:
                prompt = '`config set` needs a key and a value; nothing set'
                utils.cprint(color='red', text=prompt)
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

    async def do_login(self, args):
        'Login on MeuBernoulli'

        args = shlex.split(args)

        if utils.get_default(args, 0) == 'help':
            print(docs.MENEM)
            return

        email = utils.get_default(args, 0) or self.config.get('email', None)
        password = utils.get_default(
            args, 1) or self.config.get('password', None)
        page = await self.get_page('login')
        await utils.goto(page, 'https://meu.bernoulli.com.br/login')

        if email is None:
            prompt = 'type in your email address: '
            email = utils.get_input(text=prompt, color='blue')
            choice = utils.get_input(text='save email (y/n)? ', color='blue')
            choice = choice.lower()
            if choice == 'y':
                self.config['email'] = email
                utils.cprint(text='email saved', color='green')

        if password is None:
            prompt = 'type in your password: '
            password = utils.get_input(text=prompt, color='blue')
            prompt = 'save password (y/n)? '
            choice = utils.get_input(text=prompt, color='blue')
            choice = choice.lower()
            if choice == 'y':
                self.config['password'] = password
                utils.cprint(text='password saved', color='green')

        utils.cprint(text='logging in')
        userField = await utils.wait_loading(page, 'input#usuario')
        psswordField = await utils.wait_loading(page, 'input#senha')
        loginBtn = await utils.wait_loading(page, 'button#btnLogin')
        await userField.type(email)
        await psswordField.type(password)
        await loginBtn.click()

        time.sleep(5)
        await utils.screenshot(page)

        loginBtn = await utils.wait_loading(page, 'button#btnEntrar')
        SelectJS = "select => {{ select.selectedIndex = {}; select.dispatchEvent(new Event('change', {{ bubbles: true }}))}}"
        optionExtractor = '(opts => opts.map(opt => opt.innerHTML))'

        await utils.wait_loading(page, 'select#codigoPessoaPerfil > option.validOption')
        select = await page.querySelector('select#codigoPessoaPerfil')
        options = await page.querySelectorAllEval('select#codigoPessoaPerfil > option.validOption', optionExtractor)
        choice = utils.get_selection(options, 1)
        await page.evaluate(SelectJS.format(choice), select)
        time.sleep(2)

        await utils.wait_loading(page, 'select#codigoTurmaAno > option.validOption')
        select = await page.querySelector('select#codigoTurmaAno')
        options = await page.querySelectorAllEval('select#codigoTurmaAno > option.validOption', optionExtractor)
        choice = utils.get_selection(options, 1)
        await page.evaluate(SelectJS.format(choice - 1), select)
        time.sleep(1)

        await loginBtn.click()

        time.sleep(5)
        await utils.screenshot(page)
        await utils.wait_loading(page, '#conteudoFeed')

        await page.close()
        del self.pages['login']

        utils.loggedin = True
        utils.cprint(color='green', text='logged in')

    async def do_menem(self, arg) -> None:
        'Enter mENEM utility'

        config = {}
        for key, val in self.config.items():
            if 'menem.' in key:
                key = key.replace('menem.', '')
                config[key] = val

        self.menem.set_config(config)

        page = await self.get_page('menem')
        if page != self.menem.get_page():
            self.menem.set_page(page)

        if arg != '':
            await self.menem.onecmd(arg)
        else:
            await self.menem.cmdloop('Welcome to menem! Type help or ? for help.\n')

    async def get_page(self, key):
        page = self.pages.get(key, None)

        if page is None or page.isClosed():
            self.pages[key] = await self.browser.newPage()

        return self.pages[key]

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

    def emptyline(self) -> None:
        pass

    async def preloop(self) -> None:
        self.readconfigfile()
        self.browser = await pyppeteer.launch()

        page = await self.get_page('menem')
        self.menem = mENEM(page)

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


class mENEM(cmd.Cmd):
    page = None
    urls = None
    images = None
    prompt = 'menem> '
    parsing_recursion = 0
    config = {
        'output': None,
        'level': '>0',
        'get_wrongs': True,
        'get_rights': False
    }

    def __init__(self, page) -> None:
        super().__init__()

        self.urls = []
        self.images = []
        self.page = page

    async def do_get_data(self, args):
        'Get the URLs of the simulations (questions & answers)'

        if not utils.loggedin:
            prompt = 'in order to complete this action, you must be logged in'
            utils.cprint(color='red', text=prompt)
            return

        await utils.goto(self.page, 'https://meu.bernoulli.com.br/simulados/aluno/provas_correcoes')
        args = shlex.split(args)
        utils.cprint(text='fetching simulations...')

        get_wrongs = self.config['get_wrongs']
        get_rights = self.config['get_rights']

        level = utils.get_default(args, 0) or self.config['level']
        parsed, err = self.level_parser(level)

        subjects = ['CL', 'CH', 'CN', 'MT']
        simulations_query = 'select#codigoSimulado > option:not([value*=" "])'
        simulationsJS = '(simulations => simulations.map(simul => simul.innerHTML))'
        selectorJS = "sel => {{ sel.selectedIndex = {}; sel.dispatchEvent(new Event('change', {{ bubbles: true }}))}}"

        if err != None:
            utils.cprint(color='red', text=err)
            return

        await utils.wait_loading(self.page, simulations_query)
        await utils.screenshot(self.page)
        simulations = await self.page.querySelectorAllEval(simulations_query, simulationsJS)
        selector = await self.page.querySelector('select#codigoSimulado')
        simulation_choice = utils.get_selection(simulations, 1)

        await self.page.evaluate(selectorJS.format(simulation_choice), selector)

        await utils.wait_loading(self.page, 'div#questoesRespostas:not([style*="display: none"])')
        subject_choice = utils.get_selection(subjects, None) - 1
        await self.page.querySelectorEval(f'ul#simuladoAreas > li:nth-of-type({subject_choice + 1})', 'opt => opt.click()')
        time.sleep(2)

        questions_query = f'div#{subjects[subject_choice]} > span.question-item'
        if get_wrongs and get_rights:
            pass
        elif get_wrongs:
            questions_query += '[respostacorreta=N]'
        elif get_rights:
            questions_query += '[respostacorreta=S]'

        questions = await self.page.querySelectorAll(questions_query)
        saved_questions = []
        saved_answers = []

        for question in questions:
            question_level = await self.page.evaluate('q => Number(q.getAttribute("probabilidade_acerto"))', question)
            save_question = False

            for test in parsed:
                op = test['op']
                val = test['val']

                if op == 'gt':
                    save_question = question_level > val
                elif op == 'ge':
                    save_question = question_level >= val
                elif op == 'eq':
                    save_question = question_level == val
                elif op == 'le':
                    save_question = question_level <= val
                elif op == 'lt':
                    save_question = question_level < val

                if not save_question:
                    break

            if save_question:
                [q, a] = await self.page.evaluate('q => [q.getAttribute("enunciado"), q.getAttribute("resolucao")]', question)
                saved_questions.append(q)
                saved_answers.append(a)

        self.urls.extend(saved_questions + saved_answers)
        output_alternatives = (
            # optional CLI arg; None if nothing's given
            utils.get_default(args, 1),
            # None by default; user can overwrite on config menem.output 'output_here'
            self.config['output'],
            # 'Simul_Num (Subj).pdf'; default fallback
            f'{simulations[simulation_choice - 1]} ({subjects[subject_choice]}).pdf'
        )

        for output in output_alternatives:
            if output != None:
                self.config['output'] = output
                break

        prompt = 'fetched simulations, questions and answers'
        utils.cprint(color='green', text=prompt)

    def do_download_images(self, _):
        'Download images from the URLs'

        if len(self.urls) == 0:
            prompt = 'no urls to download images from\ntry running `get_data`'
            utils.cprint(text=prompt, color='red')
            return

        utils.cprint(text='downloading images')

        if not os.path.isdir(f'images'):
            os.mkdir(f'images')

        for url in self.urls:
            image = f'images/{os.path.basename(url)}'
            r = requests.get(url)

            if r.ok:
                with open(image, 'wb') as f:
                    f.write(r.content)

                self.images.append(image)
            else:
                prompt = f'404 error on `{url}`; skipping'
                utils.cprint(color='yellow', text=prompt)

        utils.cprint(color='green', text='all images downloaded')

    def do_gen_pdf(self, _):
        'Generate a pdf with the downloaded images'

        imgs = []

        if len(self.images) == 0:
            prompt = 'no images to generate pdf from\ntry running `download_images`'
            utils.cprint(color='red', text=prompt)
            return

        pdf = self.images.pop(0)
        pdf = Image.open(pdf)
        pdf = pdf.convert('RGB')

        for img in self.images:
            img = Image.open(img)
            img = img.convert('RGB')

            imgs.append(img)

        output = self.config['output']
        pdf.save(output, 'PDF', resolution=100.0,
                 save_all=True, append_images=imgs)

        prompt = 'delete downloaded images (y/n)? '
        choice = utils.get_input(text=prompt, color='blue', confirm=False)
        choice = choice.lower()

        if choice == 'y':
            for img in self.images:
                os.remove(img)

            os.rmdir('images')

            prompt = 'all images deleted'
            utils.cprint(text=prompt, color='green')

        prompt = 'generated pdf; find it in {}'.format(self.config['output'])
        utils.cprint(text=prompt, color='green')

        self.images = []
        self.urls = []

    def do_EOF(self, _=None) -> None:
        'Exit'
        print()
        return 'EOF'

    def set_config(self, config: dict):
        self.config.update(config)

    def get_page(self):
        return self.page

    def set_page(self, page) -> None:
        self.page = page

    def level_parser(self, level: str) -> tuple[list[dict], None]:
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
            return [], err_msg

        elif '>' in level or '<' in level:  # level has <, >
            if '>' in level:
                op = '>'
            else:
                op = '<'
            level = level.replace(op, '')
            self.parsing_recursion += 1
            # in case there's a percentage sign
            level, err = self.level_parser(level)
            self.parsing_recursion -= 1

            if err is not None:
                return [], err

            if op == '>':
                parsed = {'op': 'gt', 'val': float(level)}
            else:
                parsed = {'op': 'lt', 'val': float(level)}

            parsed = [parsed]

        elif '%' in level:  # if level has a percentage sign
            level = level.replace('%', '')

            if re.match(r'[^\d\>\<]', level) is not None:
                return [], err_msg
            else:
                level = float(level) / 100
                if self.parsing_recursion == 0:
                    parsed = [{'op': 'eq', 'val': level}]
                else:
                    parsed = level

        # if level is between 0 and 1 or if it's an integer
        elif re.match(r'^(0(\.\d+)?|1(\.0+)?)$', level) is not None or re.match(r'[^\d]', level) is None:
            parsed = float(level)
            if self.parsing_recursion == 0:
                parsed = [{'op': 'eq', 'val': level}]

        return parsed, None

    def preloop(self) -> None:
        utils.prefix = 'menem: '

    async def postloop(self) -> None:
        prompt = 'close MB tab (y/n)? '
        choice = utils.get_input(text=prompt, color='blue', confirm=False)

        if choice == 'y':
            await self.page.close()

        utils.prefix = 'mbsh: '

    def default(self, line=None, msg=None) -> None:
        if msg == None:
            msg = f'`{line}` is not a known syntax'

        utils.cprint(color='red', text=msg)

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
