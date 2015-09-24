import logging
import sys
import time
import traceback
import rfcruncher
import statWatcher
from daemon import runner

class Daemon():
    def __init__(self):
        # Sleep 60 secs * 5 mins
        self.sleep_time = 60*5
        # Crunch the cruncher frequency
        self.cruncher_frequency = 60*60/self.sleep_time
        self.counter = 0

        # Daemon config
        self.stdin_path = '/dev/null'
        self.stdout_path = '/var/log/rfcruncher_out.log'
        self.stderr_path = '/var/log/rfcruncher_err.log'
        self.pidfile_path =  '/var/run/rfcruncher.pid'
        self.pidfile_timeout = 5

    def run(self):
        logger.info("Starting the RF Cruncher daemon")

        while True:
            if self.counter%self.cruncher_frequency == 0:
                # Crunch the cruncher
                pass

            try:
                rfcruncher.execute_friendly_crunch(handler)
                rfcruncher.execute_nasty_crunch(handler)
            except:
                logger.error("Crunching stopped due to error in the tests")

            self.counter += 1
            time.sleep(self.sleep_time)


logger = logging.getLogger("rf_cruncher_daemon")
logger.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
handler = logging.FileHandler("/var/log/rfcruncher.log")
handler.setFormatter(formatter)
logger.addHandler(handler)

if __name__ == "__main__":
    rfcruncher.execute_friendly_crunch(handler)
    rfcruncher.execute_nasty_crunch(handler)

    cruncherMonster = statWatcher.CruncherMonster()
    cruncherMonster.crunch()
else:
    daemon = Daemon()
    daemon.run()
    daemon_runner = runner.DaemonRunner(daemon)
    #This ensures that the logger file handle does not get closed during daemonization
    daemon_runner.daemon_context.files_preserve=[handler.stream]
    daemon_runner.do_action()
