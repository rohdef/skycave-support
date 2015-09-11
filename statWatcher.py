import os
import urllib.request
import time
import sys
import traceback
import logging
from daemon import runner

class App():
    def __init__(self):
        # Daemon config
        self.stdin_path = '/dev/null'
        self.stdout_path = '/var/log/skycave/logger-out.log'
        self.stderr_path = '/var/log/skycave/logger-err.log'
        self.pidfile_path =  '/var/run/skycave-logger.pid'
        self.pidfile_timeout = 5

    def run(self):
        statsUrl = ""

        lastDiffFile = open("/opt/lastDiffFile", "r+")
        lastDiff = int(lastDiffFile.readline())

        while True:
            try:
                statsResponse = urllib.request.urlopen(statsUrl)
                stats = statsResponse.read().decode("utf-8")

                for stat in stats.split("\n"):
                    if stat.startswith("CSS 25"):
                        stat = " ".join(stat.split())
                        statTokens = stat.split(" ")
                        count = int(statTokens[2])
                        success = int(statTokens[3])
                        diff = count-success

                        print(time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()))
                        print(count)
                        print(success)
                        print(diff)
                        if diff > lastDiff:
                            print("WARNING!!!!")
                        else:
                            print("NO warning")
            except:
                pass

            time.sleep(1800)

app = App()
app.run()
#daemon_runner = runner.DaemonRunner(app)
#daemon_runner.daemon_context.files_preserve=[handler.stream]
#daemon_runner.do_action()
