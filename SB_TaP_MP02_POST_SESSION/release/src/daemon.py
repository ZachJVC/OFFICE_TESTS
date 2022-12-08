"""Implements daemon functions for the production test suite

Author: Rob Arrow
Date: 20 Feb 2020

Copyright (c) 2020, Sportable Technologies. All rights reserved.
"""

import os
import time
import shutil
import datetime
import subprocess
import src.prettyPrint as pretty

from typing import Optional
from threading import Thread

class Daemon:
    DAEMON_LOG_FILE = "./daemon.log"
    DAEMON_LOG_PATH = "./coms_log/"
    DAEMON_DELAY = 2    # Delay in seconds

    @property
    def thread(self):
        return self._thread
    
    @thread.setter
    def thread(self, thr: Thread):
        self._thread = thr
    
    @property
    def subProc(self):
        return self._subProc
    
    @subProc.setter
    def subProc(self, proc: subprocess.Popen):
        self._subProc = proc

    @property
    def debug(self):
        return self._debug
    
    @debug.setter
    def debug(self, dbg: bool):
        self._debug = dbg

    
    def __init__(self,
                 targetProduct: str,
                 debug: Optional[bool] = None) -> None:
        self._thread = None
        self._subProc = None
        self._targetProduct = targetProduct
        self._debug = False
        if debug is not None:
            self.debug = debug
        if self.isRunning():
            print("\nAnother Daemon detected." +
                  "Please turn off the Daemon.")
            raise Exception("Another Daemon detected.")
        self.initLogFile()


    def isRunning(self):
        instancesByte = subprocess.run(['pgrep', '-fc', 'aDaemon'],
                                        stdout=subprocess.PIPE).stdout
        instances = int(instancesByte)
        if instances > 0:
            return True
        else:
            return False

    def ensureRunning(self):
        running = self.isRunning()
        if not running:
            pretty.printPrompt("Please start daemon...")
            while not running:
                running = self.isRunning()
                time.sleep(0.1)
        print("Daemon detected")

    def ensureStopped(self):
        running = self.isRunning()
        if running:
            pretty.printPrompt("Please stop daemon...")
            while running:
                running = self.isRunning()
                time.sleep(0.1)
        print("Daemon stopped")

    def aDaemonDebugThread(self):
        directory = os.getcwd()
        # TODO Move into daemon and do more elegantly
        os.system(f'rm -Rf {directory}/*.Lock')

    def aDaemonThread(self):
        """Runs Aeolus Daemon instance (without log messages)
        To be called in a new thread.

        """
        directory = os.getcwd()
        # TODO Move into daemon and do more elegantly
        os.system('rm -Rf ' + directory + '/*.Lock')
        # TODO replace with call to production aDaemon
        os.system(f'sudo ./aDaemon -noconfig -a handlers -d filter '
                  f'json ignore live >> {str(Daemon.DAEMON_LOG_FILE)} 2>&1')
        #os.system('sudo ./aDaemon -noconfig -a handlers > /dev/null 2>&1')
        #os.system('sudo ./aDaemon -noconfig -a handlers')

    def startDaemonThread(self):
        if self.thread is not None:
            return
        if self.debug:
            self.ensureRunning()
            self.thread = Thread(target=self.aDaemonDebugThread)
        else:
            self.thread = Thread(target=self.aDaemonThread)
        
        self.thread.start()
    
    def startDaemon(self):
        if self.debug:
            self.ensureRunning()
            self.aDaemonDebugThread()
            return
        if self.subProc is not None:
            return
        self.subProc = subprocess.Popen(('sudo ./aDaemon '
                                         '-noconfig '
                                         '-a handlers '
                                         '-d filter json ignore live '
                                         '-load file productionTest.cfg '
                                         '-load file IMU.cfg '
                                         '-load file PSR.cfg '
                                         f'>> {str(Daemon.DAEMON_LOG_FILE)} 2>&1'),
                                         shell=True,
                                         stdin=subprocess.PIPE)
        self.subProc.stdin.flush()
        time.sleep(Daemon.DAEMON_DELAY)

    def closeDaemonThread(self):
        """Terminates Aeolus Daemon and joins thread.

        Parameters
        ----------
        thread : Thread
            Thread running Daemon.

        """
        if self.thread is None:
            return
        if self.debug:
            self.ensureStopped()
        else:
            os.system('sudo ./aeolus.py exit')
        self.thread.join()
        while self.thread.is_alive():
            pass
        self.thread = None
    
    def closeDaemon(self):
        if self.debug:
            self.ensureStopped()
            return
        if self.subProc is not None:
            os.system('sudo ./aeolus.py exit')
            self.subProc.communicate()
            while self.subProc.poll() is None:
                pass
            self.subProc = None

    def restartDaemon(self):
        self.closeDaemon()
        time.sleep(Daemon.DAEMON_DELAY)
        self.startDaemon()

    def initLogFile(self):
        """Creates daemon log file"""

        now = datetime.datetime.now()
        date = now.strftime("%Y_%m_%d")
        time = now.strftime("%H_%M_%S")

        with open(str(Daemon.DAEMON_LOG_FILE), "w") as logFile:
            logFile.write("------------------------------------------" +
                          "--------------------------------------\n")
            logFile.write(f'{str(self._targetProduct)} production '
                          f'test {str(date)} {str(time)}\n')
            logFile.write("----------------------------------------------------" +
                          "----------------------------\n\n")
    
    def copyLogFile(self, serialNumber: str):
        if os.path.isfile(Daemon.DAEMON_LOG_FILE):
            now = datetime.datetime.now()
            test_date = now.strftime("%Y_%m_%d")
            test_time = now.strftime("%H_%M_%S")
            if not os.path.exists(Daemon.DAEMON_LOG_PATH):
                os.makedirs(Daemon.DAEMON_LOG_PATH, exist_ok=True)
            shutil.copyfile(
                Daemon.DAEMON_LOG_FILE,
                f"{Daemon.DAEMON_LOG_PATH}{serialNumber}_{test_date}_{test_time}.log")

    def createDaemonConfig(self,
                           dutType: str,
                           dutSerialNumber: str,
                           masterType: str = None,
                           masterSerialNumber: str = None,
                           dutBlocking: bool = True,
                           masterBlocking: bool = False,
                           productionConfigTemplatePath: str = "./productionTest.cfg.templ",
                           productionConfigPath: str = "./productionTest.cfg",):
        """Creates daemon.cfg with designated serial numbers
        
        Params:
            productionConfigTemplatePath: string containing path to the production
                                  config template file
            productionConfigPath: string containing path to the production
                                  config file
            dutType: string containing the DUT device type
            dutSerialNumber: string containing the DUT serial number
            masterType: string containing the Master device type
            masterSerialNumber: string containing the Master serial number

        Returns:
            None
        """
        dutString = (f"{dutType}_{dutSerialNumber}")
        if masterType and masterSerialNumber:
            masterString = (f"{masterType}_{masterSerialNumber}")
        else:
            masterString = "NoMasterDevice"
        if dutBlocking:
            dutBlockingString = "true"
        else:
            dutBlockingString = "false"
        if masterBlocking:
            masterBlockingString = "true"
        else:
            masterBlockingString = "false"
        with open(str(productionConfigTemplatePath), "r") as productionTemplate,\
            open(str(productionConfigPath), "w") as productionFile:
            for line in productionTemplate:
                line = str(line).replace("$(DUT)", str(dutString))
                line = str(line).replace("$(MASTER)", str(masterString))
                line = str(line).replace("$(DUT_BLOCKING)", str(dutBlockingString))
                line = str(line).replace("$(MASTER_BLOCKING)", str(masterBlockingString))
                productionFile.write(line)
