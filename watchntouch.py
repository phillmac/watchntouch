import time
import os

from watchdog.observers.polling import PollingObserver
from watchdog import events
from watchdog.tricks import LoggerTrick

import argparse
import logging
import random
import subprocess

logger = logging.getLogger('watchntouch')


class PollingHandler(events.FileSystemEventHandler):
    def __init__(self, options):
        self.options = options
        self.skip_next = set()

    def touch_file(self, event):
        if event.src_path == self.options.watchdir:
            logger.debug("Ignoring change to root watchdir...")
            return

        if event in self.skip_next:
            logger.debug("Event on skiplist: %s" % event)
            self.skip_next.remove(event)
            return

        logger.debug("Re-touching file for event: %s" % event)
        subprocess.Popen(["touch", event.src_path])


    on_created = touch_file

    



def run():
    parser = argparse.ArgumentParser(
        description='Poll a directory for changes and re-touch changed paths '
            'so that inotify-incapable mounts (like CIFS) receive inotify '
            'events anyway.')

    parser.add_argument('-i', '--polling-interval',
        default=1.0,
        help="Polling interval in seconds",
        type=float,
        dest='interval'
    )
    parser.add_argument('-l', '--log-level',
        default=11,
        help="Logger verbosity level",
        type=int,
        dest='loglevel'
    )

    parser.add_argument("-r", "--simulate-rm",
        default=False,
        action='store_true',
        dest='simulate_rm',
        help="Simulate rm operations by natively flashing a path in/out of "
        "existance. Only use if you find your tools get confused when a file "
        "disapeared from under them."
    )

    parser.add_argument("-m", "--simulate-mv",
        default=False,
        action='store_true',
        dest='simulate_mv',
        help="Simulate mv operations by natively moving a path back and forth."
        " Only use if you find your tools require specific handling of"
        " move events."
    )

    parser.add_argument('-w', '--watchdir',
        default=".",
        required=False,
        help="the directory to watch for changes",
        dest="watchdir"
    )

    args = parser.parse_args()

    args.watchdir = os.path.realpath(os.path.abspath(args.watchdir))

    logging.basicConfig(level=args.loglevel, format="%(message)s (%(levelname)s)\n")


    logger.info("Watching %r", args.watchdir)

    polling_handler = PollingHandler(args)

    polling_observer = PollingObserver()

    polling_observer.schedule(polling_handler, path=args.watchdir, recursive=True)
    polling_observer.start()

    try:
        while True:
            time.sleep(args.interval)
    except KeyboardInterrupt:
        logger.info("Shutdown")
        polling_observer.stop()

    polling_observer.join()



if __name__ == "__main__":
    run()
