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
from tssplit.tssplit import tssplit

import docs
import utils


class MbSh(cmd.Cmd):
    intro: str = 'Welcome to mbsh! Type help or ? for help.\n'
    prompt: str = 'mbsh> '
    browser = None
    history: list[str] = []
    menem = None
    rutils = None
    pages: dict = {}
    config: dict[str] = {
        'cache': os.path.dirname(__file__) + '/config.json',
        'histfile': os.path.dirname(__file__) + '/histfile',
        'overwrite.cache': False,
        'overwrite.histfile': True,
        'menem.output': None,
        'menem.level': '>0',
        'menem.get_wrongs': True,
        'menem.get_rights': False,
        'menem.image_folder': 'images',
        'output': utils.output.get('output', True),
        'output.log': utils.output.get('output.log', True),
        'output.success': utils.output.get('output.success', True),
        'output.warn': utils.output.get('output.warn', True),
        'output.error': utils.output.get('output.error', True),
        'on.start': 'config load; history load; login',
        'on.stop': None
    }

    def do_config(self, args) -> None:
        "Configure mbsh's behavior"

        args = shlex.split(args)

        if len(args) == 0:
            prompt = '`config` needs at least one argument'
            utils.cprint(color='red', text=prompt)
            return

        action = args[0]
        args = args[1:]

        if action == 'get':
            key = utils.get_default(args, 0)

            if key is None:
                utils.cprint(color='red', text='`config get` needs a key name')
            else:
                val = self.config.get(key, '[undefined]')
                utils.cprint(text=val, _prefix='')

        elif action == 'set':
            key = utils.get_default(args, 0)
            val = utils.get_default(args, 1)

            if key is None or val is None:
                prompt = '`config set` needs a key and a value; nothing set'
                utils.cprint(color='red', text=prompt)
            else:
                if val == 'True':
                    val = True
                elif val == 'False':
                    val = False

                self.config[key] = val
                self.update_output()
                utils.cprint(text=f'{key}: {val}', _prefix='')

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
                utils.cprint(text='[undefined]', _prefix='')
            else:
                for key, val in self.config.items():
                    utils.cprint(text=f'{key}: {val}', _prefix='')

        elif action == 'load':
            configfile = utils.get_default(
                args, 0) or self.config.get('cache', None)

            if configfile is None:
                prompt = '`config load` needs a reference to the config file'
                utils.cprint(text=prompt, color='red')
            else:
                if self.file_exists(file=configfile, key=None):
                    newconfig = self.read_configfile(configfile=configfile)
                    self.config = newconfig
                    prompt = 'configs loaded; type `config list` to list them'
                    utils.cprint(text=prompt, color='green')
                    self.update_output()
                else:
                    prompt = f'no files named `{configfile}` found; nothing loaded'
                    utils.cprint(text=prompt, color='red')

        elif action == 'save':
            # default config file or given as argument
            configfile = utils.get_default(
                args, 0) or self.config.get('cache', None)

            if configfile is None or not self.file_exists(configfile, key=None):
                prompt = '`config save` needs a reference to the config file'
                utils.cprint(text=prompt, color='red')
            else:
                with open(self.config['cache'], 'w') as f:
                    json.dump(self.config, f)
                    utils.cprint(color='green', text='settings saved')

        elif action == 'help':
            utils.cprint(text=docs.CONFIG, _prefix='')

        else:
            self.not_found_error('config', action)

    async def do_history(self, args) -> None:
        'View history'

        args = shlex.split(args)
        action = utils.get_default(args, 0)
        args = args[1:]

        history = ''
        for entry in self.history:
            history += entry.strip() + '\n'
        history = history[0:-1]

        if action == None or action == 'print':
            utils.cprint(text=history, _prefix='')

        elif action == 'save':
            histfile = self.get_histfile(args, 'save')
            if histfile == None:
                return

            with open(histfile, 'w') as f:
                f.write(history)

            prompt = f'history saved successfully (on {histfile})'
            utils.cprint(color='green', text=prompt)

        elif action == 'load':
            histfile = self.get_histfile(args, 'load')
            if histfile == None:
                return

            with open(histfile) as f:
                lines = f.readlines()
                self.history += lines

        elif action == 'help':
            utils.cprint(text=docs.HISTORY, _prefix='')

        else:
            self.not_found_error('history', action)

    async def do_login(self, args):
        'Login on MeuBernoulli'

        if utils.loggedin:
            prompt = 'already logged in'
            utils.cprint(text=prompt, force=True)
            return

        if self.need_help(args, docs.LOGIN):
            return

        args = shlex.split(args)
        given_email = utils.get_default(args, 0)
        saved_email = self.config.get('email', None)
        email = given_email or saved_email

        given_password = utils.get_default(args, 1)
        saved_password = self.config.get('password', None)
        password = given_password or saved_password

        page = await self.get_page('login')
        await utils.goto(page, 'https://meu.bernoulli.com.br/login')

        if email is None:
            prompt = 'type in your email address: '
            email = utils.get_input(text=prompt, color='blue')
            choice = utils.get_input(
                text='save email (y/n)? ', color='blue', confirm=False)
            choice = choice.lower()
            if choice == 'y':
                self.config['email'] = email
                utils.cprint(text='email saved', color='green')

        if password is None:
            prompt = 'type in your password: '
            password = utils.get_input(text=prompt, color='blue')
            prompt = 'save password (y/n)? '
            choice = utils.get_input(text=prompt, color='blue', confirm=False)
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

    async def do_menem(self, args) -> None:
        'Enter mENEM utility'
        await self.start_utility(args, 'menem', 'mENEM', docs.MENEM)

    async def do_rutils(self, args) -> None:
        'Enter rUtils'
        await self.start_utility(args, 'rutils', 'rUtils', docs.RUTILS)

    async def start_utility(self, args, utility: str, utility_name: str, docs: str):
        obj = getattr(self, utility)

        page = await self.get_page(utility)
        if page != obj.get_page():
            obj.set_page(page)

        if args == 'help':
            utils.cprint(text=docs, _prefix='')
        elif args != '':
            await obj.onecmd(args)
        else:
            await obj.cmdloop(f'Welcome to {utility_name}! Type help or ? for help.\n')

    def do_EOF(self, args=None) -> None:
        'Exit'
        print()
        return 'EOF'

    def do_clear(self, args) -> None:
        'Clear the terminal'
        os.system('cls' if os.name == 'nt' else 'clear')

    def update_output(self) -> None:
        for key, val in self.config.items():
            if key.startswith('output'):
                old_val = utils.output[key]

                if old_val != val:
                    utils.output[key] = val

    def not_found_error(self, cmd, action) -> None:
        msg = f'`{cmd} {action}` not found; type `{cmd} help` for more info'
        self.default(msg=msg)

    def get_histfile(self, args, action):
        histfile = utils.get_default(args, 1)
        histfile = histfile or self.config.get('histfile', None)

        if histfile == None:
            prompt = f'`history {action}` needs a reference to the histfile'
            utils.cprint(color='red', text=prompt)
        else:
            file_exists = self.file_exists(key='histfile')
            if not file_exists:
                histfile = None

        return histfile

    async def get_page(self, key):
        page = self.pages.get(key, None)

        if page is None or page.isClosed():
            self.pages[key] = await self.browser.newPage()

        return self.pages[key]

    def file_exists(self, file='', key='cache') -> bool:
        if key in self.config and file == '':
            file = self.config[key]

        return os.path.isfile(file)

    def read_configfile(self, configfile):
        config = r'{}'

        if self.file_exists(configfile):
            with open(self.config['cache'], 'r') as f:
                config = f.read() or r'{}'

        return json.loads(config)

    async def changeprompt(self, prompt) -> None:
        self.prompt = prompt
        await self.onecmd('')

    def need_help(self, args, help_msg) -> bool:
        args = shlex.split(args)
        action = utils.get_default(args, 0)

        if action == 'help':
            utils.cprint(text=help_msg, _prefix='')

        return action == 'help'

    def default(self, line=None, msg=None) -> None:
        if msg == None:
            msg = f'`{line}` is not a known syntax'

        utils.cprint(color='red', text=msg)

    def emptyline(self) -> None:
        pass

    async def close(self, target: str, overwrite: bool) -> None:
        _overwrite = False

        if target == 'cache':
            configfile = self.read_configfile(self.config.get('cache', ''))
            has_configfile = 'cache' in self.config
            configfile_empty = configfile == {}
            has_new_configs = self.config != configfile

            if has_configfile and not configfile_empty and has_new_configs:
                if not overwrite:
                    prompt = 'overwrite existing cache file (y/n)? '
                    overwrite = utils.get_input(
                        text=prompt, color='blue', confirm=False)
                    overwrite = overwrite.lower()

                    if overwrite == 'y':
                        _overwrite = True
                    else:
                        utils.cprint(text='file not overwritten')

            if _overwrite:
                await self.onecmd('config save')

        elif target == 'history':
            if len(self.history) > 0:
                if not overwrite:
                    prompt = 'save history to file (y/n)? '
                    save_history = utils.get_input(
                        text=prompt, color='blue', confirm=False)
                    save_history = save_history.lower()

                    if save_history == 'y':
                        _overwrite = True
                    else:
                        utils.cprint(text='unsaved history discarded')

            if _overwrite:
                await self.onecmd('history save')

    async def preloop(self, headless) -> None:
        self.browser = await pyppeteer.launch({'headless': headless})

        page = await self.get_page('menem')
        self.menem = mENEM(page, self)

        page = await self.get_page('rutils')
        self.rutils = rUtils(page, self)

        prestart = self.config.get('on.start', None)
        if prestart != None:
            output_bak = self.config.get('output', None)
            cmds = tssplit(prestart, delimiter=';')

            for cmd in cmds:
                if utils.is_cmd_safe(cmd):
                    self.config['output'] = False
                    self.update_output()
                    await self.onecmd(cmd)

            if output_bak == None:
                del self.config['output']
            else:
                self.config['output'] = output_bak

            self.update_output()

    async def postloop(self) -> None:
        prestop = self.config.get('on.stop', None)
        if prestop != None:
            output_bak = self.config.get('output', None)
            cmds = tssplit(prestop, delimiter=';')

            for cmd in cmds:
                if utils.is_cmd_safe(cmd):
                    self.config['output'] = False
                    self.update_output()
                    await self.onecmd(cmd)

            if output_bak == None:
                del self.config['output']
            else:
                self.config['output'] = output_bak

        overwrite = self.config.get('overwrite', False)
        overwrite_cache = self.config.get('overwrite.cache', False)
        overwrite_history = self.config.get('overwrite.histfile', False)

        overwrite_cache = overwrite or overwrite_cache
        overwrite_history = overwrite or overwrite_history

        await self.close('cache', overwrite_cache)
        await self.close('history', overwrite_history)

    async def cmdloop(self, intro=None, headless=True):
        old_completer = None
        completekey = 'tab'
        parent = super()

        if inspect.iscoroutinefunction(self.preloop):
            await self.preloop(headless=headless)
        else:
            self.preloop(headless=headless)

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
        self.history.append(line)

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
    urls: list = []
    images: list = []
    parent: MbSh = None
    prompt: str = 'menem> '
    parsing_recursion: int = 0

    def __init__(self, page, parent) -> None:
        super().__init__()

        self.urls = []
        self.images = []
        self.page = page
        self.parent = parent

    async def do_get_data(self, args):
        'Get the URLs of the simulations (questions & answers)'

        if self.parent.need_help(args, docs.MENEM_GET_DATA):
            return

        if not utils.check_login():
            return

        await utils.goto(self.page, 'https://meu.bernoulli.com.br/simulados/aluno/provas_correcoes')
        utils.cprint(text='fetching simulations...')

        get_wrongs = self.parent.config.get('menem.get_wrongs', True)
        get_rights = self.parent.config.get('menem.get_rights', False)

        default_level = self.parent.config.get('level', '>0')
        level = utils.get_default(args, 0) or default_level

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
            self.parent.config.get('menem.output', None),
            # 'Simul_Num (Subj).pdf'; default fallback
            f'{simulations[simulation_choice - 1]} ({subjects[subject_choice]}).pdf'
        )

        for output in output_alternatives:
            if output != None:
                self.parent.config['output'] = output
                break

        prompt = 'fetched simulations, questions and answers'
        utils.cprint(color='green', text=prompt)

    def do_download_images(self, args):
        'Download images from the URLs'

        if self.parent.need_help(args, docs.MENEM_DOWNLOAD_IMAGES):
            return

        args = shlex.split(args)
        default_path = self.parent.config.get('menem.image_folder', 'images')
        path = utils.get_default(args, 0) or default_path

        if len(self.urls) == 0:
            prompt = 'no urls to download images from\ntry running `get_data`'
            utils.cprint(text=prompt, color='red')
            return

        utils.cprint(text='downloading images')

        if not os.path.isdir(path):
            os.mkdir(path)

        for url in self.urls:
            image = f'{path}/{os.path.basename(url)}'
            r = requests.get(url)

            if r.ok:
                with open(image, 'wb') as f:
                    f.write(r.content)

                self.images.append(image)
            else:
                prompt = f'404 error on `{url}`; skipping'
                utils.cprint(color='yellow', text=prompt)

        utils.cprint(color='green', text='all images downloaded')

    def do_gen_pdf(self, args):
        'Generate a pdf with the downloaded images'

        if self.parent.need_help(args, docs.MENEM_GEN_PDF):
            return

        args = shlex.split(args)
        output = utils.get_default(args, 0) or self.parent.config['menem.output']
        imgs = []

        if not output.endswith('.pdf'):
            output += '.pdf'

        if len(self.images) == 0:
            prompt = 'no images to generate pdf from\ntry running `download_images`'
            utils.cprint(color='red', text=prompt)
            return

        for img in self.images:
            img = Image.open(img)
            img = img.convert('RGB')

            imgs.append(img)

        pdf = imgs[0]
        pdf.save(output, 'PDF', resolution=100.0, save_all=True, append_images=imgs[1:])

        prompt = 'delete downloaded images (y/n)? '
        choice = utils.get_input(text=prompt, color='blue', confirm=False)
        choice = choice.lower()

        if choice == 'y':
            for img in self.images:
                os.remove(img)

            os.rmdir('images')

            prompt = 'all images deleted'
            utils.cprint(text=prompt, color='green')

        prompt = 'generated PDF file; find it in {}'.format(
            self.parent.config['menem.output'])
        utils.cprint(text=prompt, color='green')

        self.images = []
        self.urls = []

    def do_clear(self, args) -> None:
        'Clear the terminal'
        self.parent.do_clear(args)

    async def do_history(self, args) -> None:
        'View history'
        await self.parent.do_history(args)

    def do_EOF(self, args=None) -> None:
        'Exit'
        print()
        return 'EOF'

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
        prompt = 'close MeuBernoulli tab (y/n)? '
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

        if inspect.iscoroutinefunction(self.preloop):
            await self.preloop()
        else:
            self.preloop()

        try:
            import readline

            old_completer = readline.get_completer()
            readline.set_completer(self.parent.complete)
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

                line = self.parent.precmd(line)
                stop = await self.onecmd(line)
                stop = self.parent.postcmd(stop, line)

            if inspect.iscoroutinefunction(self.postloop):
                await self.postloop()
            else:
                self.postloop()

        finally:
            if self.parent.use_rawinput and completekey:
                try:
                    import readline

                    readline.set_completer(old_completer)
                except ImportError:
                    pass

    async def onecmd(self, line):
        self.parent.history.append(line)
        cmd, arg, line = self.parent.parseline(line)

        if not line:
            return self.emptyline()

        if cmd is None:
            return self.default(line)

        self.lastcmd = line

        if line == 'EOF':
            self.lastcmd = ''

        if cmd == '':
            return self.parent.default(line)
        else:
            try:
                func = getattr(self, 'do_' + cmd)
            except AttributeError:
                return self.default(line)

            if inspect.iscoroutinefunction(func):
                return await func(arg)

            return func(arg)


class rUtils(cmd.Cmd):
    page = None
    parent: MbSh = None
    prompt: str = 'rutils> '
    token: str = None
    loggedin: bool = False

    def __init__(self, page, parent) -> None:
        super().__init__()

        self.page = page
        self.parent = parent

    async def do_login(self, args) -> None:
        'Enter Imaginie page'

        if self.loggedin:
            prompt = 'already logged in'
            utils.cprint(text=prompt, force=True)
            return

        args = shlex.split(args)
        given_token = utils.get_default(args, 0)
        saved_token = self.parent.config.get('rutils.token', None)
        token = given_token or saved_token or self.token
        utils.cprint(text='logging in')

        if token != None:
            url = f'https://alunos.imaginie.com.br/?token={token}'
            await utils.goto(self.page, url)
        else:
            await utils.goto(self.page, 'https://meu.bernoulli.com.br/')
            fetchReq = """
            (async function(){
                const endpoint = 'https://meu.bernoulli.com.br/simulados/aluno/redacao';
                let res = await fetch(endpoint, { method: 'GET' });
                res = await res.json()
                return res.mensagem.url
            })()
            """
            url = await self.page.evaluate(fetchReq)
            token = url.replace('https://alunos.imaginie.com.br/?token=', '')

        self.token = token
        self.loggedin = True
        await utils.goto(self.page, f'https://alunos.imaginie.com.br/?token={token}')
        utils.cprint(text='logged in', color='green')

    async def do_get_essays(self, args) -> None:
        'Get essays'

        if self.parent.need_help(args, docs.RUTILS_GET_ESSAYS):
            return

        if not utils.check_login(self.loggedin):
            return

        args = shlex.split(args)
        essay_types = ['themes', 'my-essays']

        essay_type = utils.get_default(args, 0, essay_types[1])
        if essay_type not in essay_types:
            prompt = 'essay type unknown; see `get_essays help` for more info'
            utils.cprint(text=prompt, color='red')
            return

        essay_type_idx = essay_types.index(essay_type)
        essay_type_btns = await self.page.querySelectorAll('.mat-tab-label-content')
        essay_type_btn_selected = essay_type_btns[essay_type_idx]
        await essay_type_btn_selected.click()
        eval_query = "document.querySelectorAll('.loading_modal:not([hidden])').length === 0"
        await utils.wait_loading(self.page, eval_query=eval_query, val=False, sleep=2)

    def do_clear(self, args) -> None:
        'Clear the terminal'
        self.parent.do_clear(args)

    async def do_history(self, args) -> None:
        'View history'
        await self.parent.do_history(args)

    def do_EOF(self, args=None) -> None:
        'Exit'
        print()
        return 'EOF'

    def get_page(self):
        return self.page

    def set_page(self, page) -> None:
        self.page = page

    async def preloop(self) -> None:
        utils.prefix = 'rutils: '

        if not utils.check_login():
            utils.prefix = 'mbsh: '
            return 'EOF'

    async def postloop(self) -> None:
        stored_token = self.parent.config.get('rutils.token', None)
        if stored_token != self.token:
            prompt = 'save new Imaginie token (y/n)? '
            choice = utils.get_input(text=prompt, color='blue', confirm=False)
            choice = choice.lower()

            if choice == 'y':
                self.parent.config['rutils.token'] = self.token
                prompt = 'new token saved successfully'
                utils.cprint(text=prompt, color='green')
            else:
                prompt = 'new token discarded'
                utils.cprint(text=prompt)

        prompt = 'close Imaginie tab (y/n)? '
        choice = utils.get_input(text=prompt, color='blue', confirm=False)
        choice = choice.lower()

        if choice == 'y':
            await self.page.close()

        utils.prefix = 'mbsh: '

    def default(self, line=None, msg=None) -> None:
        self.parent.default(line=line, msg=msg)

    def emptyline(self) -> None:
        pass

    async def cmdloop(self, intro=None):
        old_completer = None
        completekey = 'tab'

        if inspect.iscoroutinefunction(self.preloop):
            stop = await self.preloop()
        else:
            stop = self.preloop()

        if stop == 'EOF':
            return

        try:
            import readline

            old_completer = readline.get_completer()
            readline.set_completer(self.parent.complete)
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

                line = self.parent.precmd(line)
                stop = await self.onecmd(line)
                stop = self.parent.postcmd(stop, line)

            if inspect.iscoroutinefunction(self.postloop):
                await self.postloop()
            else:
                self.postloop()

        finally:
            if self.parent.use_rawinput and completekey:
                try:
                    import readline

                    readline.set_completer(old_completer)
                except ImportError:
                    pass

    async def onecmd(self, line):
        self.parent.history.append(line)
        cmd, arg, line = self.parent.parseline(line)

        if not line:
            return self.emptyline()

        if cmd is None:
            return self.default(line)

        self.lastcmd = line

        if line == 'EOF':
            self.lastcmd = ''

        if cmd == '':
            return self.parent.default(line)
        else:
            try:
                func = getattr(self, 'do_' + cmd)
            except AttributeError:
                return self.default(line)

            if inspect.iscoroutinefunction(func):
                return await func(arg)

            return func(arg)
