""" Implements common argument parser for the production test suite

Copyright (c) 2019-2022, Sportable Technologies. All rights reserved.

"""

import argparse
import src.datatypes as dt

class Parser(argparse.ArgumentParser):
    def __init__(self):
        super().__init__(description='Production testing Software (Sportable Technologies Ltd.)')
        
        self.add_argument('-i', '--id', type=str,
                          default="0", help='Target tag ID')
        
        self.add_argument('-d', '--debug', dest='debug', action='store_true',
                          default=False, help='Enable daemon debug (Does not run daemon internaly to allow for running daemon in GDB)')

        self.add_argument('-c', '--check-version', dest='checkVersion', action='store_true',
                          default=False, help='Check App and UWB version before update.')

        self.add_argument('-B', '--ball-test', dest='stage', action='store_const', const=dt.testStage.BALL,
                          default=dt.testStage.BOOT, help='Runs test for fully assembled ball')

        self.add_argument('-V', '--valve-test', dest='stage', action='store_const', const=dt.testStage.VALVE,
                          default=dt.testStage.BOOT, help='Runs test for the valve assembly')

        self.add_argument('-L', '--bladder-test', dest='stage', action='store_const', const=dt.testStage.BLADDER,
                          default=dt.testStage.BOOT, help='Runs test for the bladder assembly')
                          
        self.add_argument('-M','--mainBoard', dest='stage', action='store_const', const=dt.testStage.MAIN,
                          default=dt.testStage.BOOT, help='Runs test main board')

        self.add_argument('-G', '--gnssBoard', dest='stage', action='store_const', const=dt.testStage.GNSS,
                          default=dt.testStage.BOOT, help='UNUSED! Runs test for GNSS board')

        self.add_argument('-A', '--assembledProduct', dest='stage', action='store_const', const=dt.testStage.ASSEMBLED,
                          default=dt.testStage.BOOT, help='Runs test for fully assembled product')

        self.add_argument('-P', '--pressureBoard', dest='stage', action='store_const', const=dt.testStage.PRESSURE,
                          default=dt.testStage.BOOT, help='Runs test for pressue sensor board')

        self.add_argument('-f', '--full', dest='stage', action='store_const', const=dt.testStage.FULL,
                          default=dt.testStage.BOOT, help='Debug ONLY feature: Runs all production tests in order')

        self.add_argument('-q', '--quick', dest='quick', action='store_true',
                          default=False, help='Skip over any programming of non-volatile (ie serial number and hardware variant')
        
        self.add_argument('--stats', dest='stats', action='store_true',
                          default=False, help='Run stats')
        
        self.add_argument('--ensure-stage', dest='ensureStage', action='store_true',
                          default=False, help='Ensure test stage')
        
        self.add_argument('--show-menu', dest='showMenu', action='store_true',
                          default=False, help='Show test stage menu')
        
        self.add_argument('-n', '--no-flash', dest='noFlash', action='store_true',
                          default=False, help='Do not flash images onto device')

        self.add_argument('-H', '--no-variant', dest='noVariant', action='store_true',
                          default=False, help='Do not programm hardware variant onto device')

        self.add_argument('-e', '--erase-hv', dest='eraseHV', action='store_true',
                          default=False, help='Erase hardware variant')

        self.add_argument('-s', '--skip-config', dest='skipConfigCheck', action='store_true',
                          default=False, help='Do not check issued devices list')

        self.add_argument('-r', '--no-rel-flash', dest='noRelFlash', action='store_true',
                          default=False, help='Do not flash release images onto device')

        self.add_argument('-p', '--pass', dest='passFail', action='store_true',
                          default=False, help='Show pass or fail at the end of the test')

        self.add_argument('-k', '--kick-menu', dest='kickMenu', action='store_true',
                          default=False, help='Do not flash release images onto device if Pre-kick')

        self.add_argument('--master-summary', dest='masterSummary', action='store_true',
                          default=False, help='Generate the master summary in the report')
        self.add_argument('--confirm-serial-number', dest='confirmSerialNumber', action='store_true',
                          default=False, help='Ask the operator if the DUT S/N matches the retrieved serial number')

    def parse_args_list(self, argsList: list = None) -> argparse.Namespace:
        if not argsList:
            return self.parse_args()
        else:
            return self.parse_args(argsList)