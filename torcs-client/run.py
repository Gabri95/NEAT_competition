#! /usr/bin/env python3

from pytocl.main import main
from driver_subsumption import SubsumptionDriver
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
    if driver is not None and isinstance(driver, SubsumptionDriver):
        driver.saveResults()
    sys.exit(0)


signal.signal(signal.SIGINT, sigterm_handler)
signal.signal(signal.SIGTERM, sigterm_handler)


if __name__ == '__main__':
    
    parser = argparse.ArgumentParser(
        description='Client for TORCS racing car simulation with SCRC network'
                    ' server.'
    )
    parser.add_argument(
        '-d',
        '--driver_config',
        help='Configuration file for the Subsumption Structure.',
        type=str
    )
    
    parser.add_argument(
        '-o',
        '--out_file',
        help='File where to print results.',
        type=str
    )

    # parser.add_argument(
    #     '-m',
    #     '--mix',
    #     help='Use the mixed model. Expected proper configuration file with oracle and the other models.',
    #     action='store_true'
    # )
    
    args, _ = parser.parse_known_args()
    
    print(args.driver_config)
    print(args.out_file)
    
    if args.out_file is not None:
        out_dir = os.path.dirname(args.out_file)
        if not os.path.exists(out_dir):
            os.makedirs(out_dir)
    
    if args.driver_config is not None:
        driver = SubsumptionDriver(**args.__dict__)
    else:
        driver = Driver()
    
    try:
        main(driver)
        
    except Exception as exc:
        traceback.print_exc()

        if args.driver_config is not None:
            driver.saveResults()
            
        raise
    
    
