#!/usr/bin/env python3

"""Daemon cli.
Simple translations of commands into strings and output in ./tagCli

Author: Christos Bontozoglou
Date: 18 Oct 2019

Copyright (c) 2019, Sportable Technologies. All rights reserved.

"""

import argparse
import os
import time

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Daemon CLI (Sportable Technologies Ltd.)')
    parser.add_argument(
        'command',
        type=str,
        help='Command to tag or help for more info')
    parser.add_argument(
        '-d',
        '--data',
        type=str,
        default='0',
        help='Supporting data. See datastructs.h')
    parser.add_argument(
        '-t',
        '--tag',
        type=str,
        default='0',
        help='Target specific tag id')
    parser.add_argument(
        '-s',
        '--string',
        type=str,
        default='0',
        help='String data')
    args = parser.parse_args()

    if args.command == 'help':
        print('Available commands: ')
        print('\tformat - Format Aeolus external flash')
        print('\treset - Restarts MCU')
        print('\tstart - Starts a session')
        print('\tstop - Stops the currently running session.')
        print(
            '\tsessions - Downloads new session configurations from json files')
        print('\tdelete - Removes a session configuration')
        print('\ttime - Sends the system time')
        print('\ttoggle - Toggles the gnss bridge')
        print('\tcharger - Enables/Disables the battery charger')
        print('\toffload - Triggers data offload')
        print('\tconfiggnss - Downloads GNSS configuration')
        print('\tephemeris - Downloads GNSS ephemeris')
        print('\tidgnss - Gets GNSS device ID')
        print('\tflashfw - Downloads new firmware')
        print('\tgetdev - Get device context')
        print('\tgetsesctx - Get session context')
        print('\tgetsescfg - Get session configuration')
        print('\tsetid - set OTP serial (use only if you know what this does)')
        print('\texit - Shuts Daemon down.')
        print('\tshutdown - Shuts DUT down.')
        print('or any string command you might want to add in Daemon')
        exit()

    f = open('./tagCli', 'w+')
    f.write(
        args.tag +
        " " +
        args.command +
        " " +
        args.data +
        " " +
        args.string)
    f.close()
