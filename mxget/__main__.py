import logging

from mxget.cmd import cmd


def cli():
    logging.basicConfig(format='%(asctime)s [%(levelname)s] %(message)s', level=logging.INFO)
    cmd.root()


if __name__ == '__main__':
    cli()
