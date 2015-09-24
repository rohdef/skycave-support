import logging
import logging.handlers
import sys
import time
import traceback
import rfcruncher
import statWatcher
from daemon import runner

class DummyHandler():
    def __init__(self):
        pass

    def cruncherMonster(self, wasSuccess=True):
        if wasSuccess:
            logger.info("CrunchMoster was successful")
        else:
            logger.error("CrunchMonster failed")

    def rfcrunchStatus(self, testTotal, success, fails, errors):
        logger.info(" *** We ran {0} tests, {1} of them was successes, {2} was failures and {3} made errors. *** ".format(testTotal, success, fails, errors))

    def criticalFail(self, message):
        logger.error("Critical failure occured with message: {0}".format(message))

class Daemon():
    def __init__(self, crunchHandler):
        # Sleep 60 secs * 5 mins
        self.sleep_time = 60*5
        # Crunch the cruncher frequency
        self.cruncher_frequency = 30*60/self.sleep_time
        self.counter = 0

        self.crunchHandler = crunchHandler

        # Daemon config
        self.stdin_path = '/dev/null'
        self.stdout_path = '/var/log/rfcruncher_out.log'
        self.stderr_path = '/var/log/rfcruncher_err.log'
        self.pidfile_path =  '/var/run/rfcruncher.pid'
        self.pidfile_timeout = 5

    def run(self):
        logger.info("Starting the RF Cruncher daemon")

        while True:
            logger.info(" *** Running tests *** ")
            if self.counter%self.cruncher_frequency == 0:
                self.counter = 0
                logger.info("*** Time for cruncher ***")
                # Crunch the cruncher
                try:
                    cruncherMonster = statWatcher.CruncherMonster()
                    self.crunchHandler.cruncherMonster(cruncherMonster.crunch())
                except:
                    logger.exception("Cruncher Monster stopped due to an error")
                    self.crunchHandler.cruncherMonster(False)

            try:
                testSuite = rfcruncher.TestSuite(handler, False)

                testSuite.execute_friendly_crunch()
                testSuite.execute_nasty_crunch()

                self.crunchHandler.rfcrunchStatus(*testSuite.get_test_tuple())
            except:
                logger.exception("Crunching stopped due to error in the tests")
                self.crunchHandler.criticalFail("Crunching of tests stopped due to critical failure")

            self.counter += 1
            time.sleep(self.sleep_time)


logger = logging.getLogger("rf_cruncher_daemon")
logger.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
handler = logging.handlers.RotatingFileHandler("/var/log/rfcruncher.log", maxBytes=1048576, backupCount=0)
handler.setFormatter(formatter)
logger.addHandler(handler)

daemon = Daemon(DummyHandler())
daemon.run()
daemon_runner = runner.DaemonRunner(daemon)
#This ensures that the logger file handle does not get closed during daemonization
daemon_runner.daemon_context.files_preserve=[handler.stream]
daemon_runner.do_action()
