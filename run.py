#!/usr/bin/env python3

from argparse import ArgumentParser

import logging_config

parser = ArgumentParser()

parser.add_argument('-u', '--update', action='store_true',
                    help='update the data and exit')

parser.add_argument('-w', '--webhook', action='store_true',
                    help='run in webhook mode')

parser.add_argument('--debug', action='store_true',
                    help='enable debug mode')

args = parser.parse_args()

if args.debug:
    logging_config.force_debug()

if __name__ == '__main__':
    import studentdb_bot

    if args.update:
        studentdb_bot.update_database()
    else:
        studentdb_bot.run()
