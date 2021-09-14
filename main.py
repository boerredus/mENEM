import asyncio

import mbsh

if __name__ == '__main__':
    _mbsh = mbsh.MbSh()
    event_loop = asyncio.get_event_loop()

    event_loop.run_until_complete(_mbsh.cmdloop())
