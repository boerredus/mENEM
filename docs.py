CONFIG = """
The `config` command is used to configure mbsh's behavior.
Syntax: $ mbsh> config [action]

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

MENEM = """"

"""