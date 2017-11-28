"""Application entry point."""
import argparse
import logging

from pytocl.protocol import Client
from pytocl.driver import Driver


def main(driver):
    """Main entry point of application."""
    parser = argparse.ArgumentParser(
        description='Client for TORCS racing car simulation with SCRC network'
                    ' server.'
    )
    parser.add_argument(
        '--hostname',
        help='Racing server host name.',
        default='localhost'
    )
    parser.add_argument(
        '-p',
        '--port',
        help='Port to connect, 3001 - 3010 for clients 1 - 10.',
        type=int,
        default=3001
    )
    
    parser.add_argument(
        '-f',
        '--data_file',
        help='File where to store data.',
        type=str
    )
    
    parser.add_argument('-v', help='Debug log level.', action='store_true')
    
    #args = parser.parse_args()
    args, _ = parser.parse_known_args()

    # switch log level:
    if args.v:
        level = logging.DEBUG
    else:
        level = logging.INFO
    
    del args.v
    
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)7s %(name)s %(message)s"
    )
    
    print('Using port', args.port)
    
    # start client loop:
    client = Client(driver=driver, **args.__dict__)
    client.run()
    
    

if __name__ == '__main__':

    main(Driver())
