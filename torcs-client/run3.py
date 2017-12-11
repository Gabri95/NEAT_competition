#! /usr/bin/env python3

from pytocl.main import main
from simple_driver import SimpleDriver
from pytocl.driver import Driver
import argparse
import sys
import traceback
import signal
import os

driver = None


def sigterm_handler(_signo, _stack_frame):
    print('Someone killed me')
    global driver
    if driver is not None and isinstance(driver, SimpleDriver):
        driver.saveResults()
    sys.exit(0)


signal.signal(signal.SIGINT, sigterm_handler)
signal.signal(signal.SIGTERM, sigterm_handler)


if __name__ == '__main__':
    
    
    driver = SimpleDriver()
    
    try:
        main(driver)
        
    except Exception as exc:
        traceback.print_exc()
        raise
    
    
