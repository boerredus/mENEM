CONFIG = """
The `config` command is used to configure mbsh's behavior.
Syntax: $ mbsh> config [action] [argument]

Actions include: get, set, clear, list and help
Examples:

# get the value of a config entry. prints [undefined] if nothing's found
$ mbsh> config get [key]

# sets the value of a property (identified by `key`)
$ mbsh> config set [key] [val]

# clears the value of a property (identified by `key`)
$ mbsh> config clear [key]

# lists all set configs. prints [undefined] if nothing's found
$ mbsh> config list

# displays this help message and exits
$ mbsh> config help
"""

LOGIN = """
The `login` command is used to log into MeuBernuolli website.
It's necessary to execute it before entering `menem` or `imaginie`
"""

HISTORY = """

"""

QUERY = """
"""

MENEM = """
mENEM stands for melhoraENEM. It's an utility that allows you to easily re-take ENEM simulations.
Its main feature is to download and to generate a PDF based on your selected questions.

To enter it: $ mbsh> menem
Once entered, the prompt will change to `menem>`

Syntax: $ menem> [action] [argument]
Actions include: get_data, download_images, gen_pdf and help

Type `[action] help` to get individual help (e.g $ menem> get_data help)
"""

MENEM_GET_DATA = """
Gets the data of a specific simulation. Must be executed at least once before the other commands.

Syntax: $ menem> get_data [argument]

[argument] may be:
    help: the script will print this help message and exit
    `level`: the script will parse the given level to filter questions
        The `level` is a way to filter questions based on their difficulty.
        Note: QD = question's difficulty
        It follows a simple syntax:
            [number] means the QD is exactly the given number (between 0 and 1);
            > [number] tells mENEM to only fetch questions which difficulty is above a given number;
            < [number] tells the script to only fetch questions easier than the given number;
            [number] may be given in percentage (1% to 100%);
            `easy`, `medium` and `hard` are shortcuts to `>66%`, >=33% and <=66%` and `<33%` respectively.
        QD defaults to >0 (meaning "get all questions with difficulty greater than zero")

        Examples:
            get_data ">10%" # only fetch questions which more than 10% of people got right
            get_data easy   # only fetch questions which more than 66% of people got right
            get_data 0.20   # only fetch questions which exatcly 20% of people got right

Config entries `menem.get_wrongs` and `menem.get_rights` (check `config help`) specify if mENEM will fetch questions the student got right/ wrong.
If both are set to 'True', mENEM will fetch all questions matching the given filter.

The command will get user input (simulation number, subject, etc) when needed. Be sure to select a valid number.
"""

MENEM_DOWNLOAD_IMAGES = """
Downloads the images fetched on `get_data` (which must have been run at least once).

One can optionally provide a `path` in which the images will be downloaded. Defaults to a folder named `images` on the current directory.
Note: if a path is given, it overwrites the config (see `config help`) `menem.image_folder`.

`download_images help` prints this help message and exits.
"""

MENEM_GEN_PDF = """
Generates the PDF with the downloaded images (which must have been run at least once).

One can optionally provide an `output` in which the PDF file will be saved.
Note: if an output is given, it overwrites the config (see `config help`) `menem.output`.

`gen_pdf help` prints this help message and exits.
"""

RUTILS = """
"""

RUTILS_GET_ESSAYS = """
"""

RUTILS_QUERY = """
"""

RUTILS_QUERY_DETAILS = """
"""