""" Implements wait indicator for the production test suite

Copyright (c) 2019-2022, Sportable Technologies. All rights reserved.

"""

import time

from threading import Thread, Event

class WaitIndicator:
    def __init__(self) -> None:
        self._event = Event()
        self._thread = None
    
    def start(self, msg: str = "Working"):
        self._thread = Thread(target=self._waitingIndicator, args=(msg,))
        self._event.clear()
        self._thread.start()
    
    def stop(self):
        self._event.set()
        if self._thread:
            self._thread.join()
            while self._thread.is_alive():
                pass
        self._thread = None
    
    def _waitingIndicator(self, msg: str):
        counter = 0
        while not self._event.isSet():
            if counter == 0:
                dots = "   "
            elif counter == 1:
                dots = ".  "
            elif counter == 2:
                dots = ".. "
            else:
                dots = "..."
                counter = -1
            print(f"{msg} {dots}", end="\r")
            counter += 1
            time.sleep(1)
        print()