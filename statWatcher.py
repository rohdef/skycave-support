#import serial
import os
import sys
import urllib.request

class CruncherMonster():
    def __init__(self):
        pass

    def crunch(self):
        result = False
        statsUrl = "http://users-cs.au.dk/baerbak/c/cloud/current-score-operations-socket.txt"

        try:
            with open("/opt/lastDiffFile", "r+") as lastDiffFile:
                fileContents = lastDiffFile.read()
                fileContentsList = fileContents.split("\n")

                lastDiff = int(fileContentsList[0])

                statsResponse = urllib.request.urlopen(statsUrl)
                stats = statsResponse.read().decode("utf-8")

                for stat in stats.split("\n"):
                    if stat.startswith("CSS 25"):
                        stat = " ".join(stat.split())
                        statTokens = stat.split(" ")
                        count = int(statTokens[2])
                        success = int(statTokens[3])
                        diff = count-success

                        #ser = serial.Serial('/dev/ttyUSB0', 9600)
                        if diff > lastDiff:
                            result = False
                        #    ser.write(b'\x01')
                        else:
                            result = True
                        #    ser.write(b'\x00')
                        #del ser

                        lastDiff = diff

                #add
                lastDiffFile.seek(0,0)
                lastDiffFile.truncate()
                lastDiffFile.write(str(lastDiff) + "\n" + "\n".join(fileContentsList[:5]))
        except:
            print("Unexpected error:", sys.exc_info()[0])
            raise
        return result

if __name__ == "__main__":
    cruncherMonster = CruncherMonster()
    cruncherMonster.crunch()
