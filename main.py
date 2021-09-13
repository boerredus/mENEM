import asyncio

from MbSh import MbSh

if __name__ == '__main__':
    mbsh = MbSh()
    event_loop = asyncio.get_event_loop()

    event_loop.run_until_complete(mbsh.cmdloop())
