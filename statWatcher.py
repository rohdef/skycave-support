import serial
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
        statsUrl = "http://users-cs.au.dk/baerbak/c/cloud/current-score-operations-socket.txt"

        while True:
            try:
                with open("/opt/lastDiffFile", "r+") as lastDiffFile:
                    fileContents = lastDiffFile.read()
                    fileContentsList = fileContents.split("\n")
                    del fileContents

                    lastDiff = int(fileContentsList[0])

                    statsResponse = urllib.request.urlopen(statsUrl)
                    stats = statsResponse.read().decode("utf-8")
                    del statsResponse

                    for stat in stats.split("\n"):
                        if stat.startswith("CSS 25"):
                            stat = " ".join(stat.split())
                            statTokens = stat.split(" ")
                            count = int(statTokens[2])
                            success = int(statTokens[3])
                            diff = count-success

                            ser = serial.Serial('/dev/ttyUSB0', 9600)
                            if diff > lastDiff:
                                ser.write(b'\x01')
                            else:
                                ser.write(b'\x00')
                            del ser

                            lastDiff = diff

                    del stat
                    del statTokens
                    del count
                    del success
                    del diff

                    #add
                    lastDiffFile.seek(0,0)
                    lastDiffFile.truncate()
                    lastDiffFile.write(str(lastDiff) + "\n" + "\n".join(fileContentsList[:5]))
                    del lastDiff
                del lastDiffFile
            except:
                print("Unexpected error:", sys.exc_info()[0])
                pass

            #time.sleep(60)
            time.sleep(1800)

app = App()
#app.run()
daemon_runner = runner.DaemonRunner(app)
#daemon_runner.daemon_context.files_preserve=[handler.stream]
daemon_runner.do_action()
