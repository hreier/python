"""
 Tool parsing existing missionplan:
 - existing missionplan needs to be located into folder ./in
 - generates modified missionplan with same name into folder ./out
 - generates log file in folder ./logs
 - 

--------------------------------------
History:
 2025.05.31 HRE:  created
 
 

"""
from __future__ import print_function

import sys
import os
import time
import shutil
import logging
import math
import pandas as pd

#import zipfile
#import msvcrt


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__))))


"""
# ------------------ CONFIGURATION AREA    -------------------
#          select configuration file for your needs
"""   
LoggingFolder = "logs"
OutFolder = "out"
InFolder = "in"
TempFolder = "temp"
log_file = "logs/log_file.txt"



"""
# ------------------ END of CONFIGURATION AREA    ------------
"""


def usage():
    basename = os.path.basename(sys.argv[0])
    print ("\nUsage:")
    print ("output files will be generated in ./out")
    print ("\n ")
    print ("%s in=missionplan_to_be_parsed cleanup"  % basename)
    print("in           [mandatory]:  the missionplan that should be parsed (located in ./in)")
    print("                           Note that outputfiles are generated with same name into ./out")
    print("cleanup       [optional]:  this cleans all data in ./out folder")
    print("                           if not defined only the matching outputfile will be overwritten")
    print ("\n ")

    logging.info("Main    : Usage error")
    logging.info("Main    : interrupted!!!!")
    sys.exit(0)

# --------------------------------
#
def _cleanup_folder(folder):
    for root, dirs, files in os.walk(folder):
        for f in files:
            os.unlink(os.path.join(root, f))
        for d in dirs:
            shutil.rmtree(os.path.join(root, d))

def _storeMission(file_name, dataFrame):
    if os.path.isfile(file_name):
        os.remove(file_name)

    #dataFrame.to_csv(file_name, sep='\t', header=None, index=None, float_format='%.8f')  ### similar to originals
    dataFrame.to_csv(file_name, sep='\t', header=None, index=None)  ### generates output file with smaller size

    #-- now reinsert the first line
    with open(file_name, "r+") as f:
        # Read the content into a variable
        contents = f.readlines()
        contents.insert(0, "QGC WPL 110\n")

        # Reset the reader's location (in bytes)
        f.seek(0)

        # Rewrite the content to the file
        f.writelines(contents)


def _getSprayCommand(flightAngle, minAngle, maxAngle, doInvert):
    if (flightAngle > minAngle) and (flightAngle < maxAngle):
        sameAsDrone = True
    else:
        sameAsDrone = False
    if (doInvert):
        sameAsDrone = not sameAsDrone

    if (sameAsDrone):
        return 3   ## spray with both nozzle sets in back
    else:
        return 12  ## spray with both nozzle sets in front


def _getDistanceToNextWP(dataFrame, id, wpActLat, wpActLong, wpActHeight, longFact, latFact):
    i = id+1
    retVal = 0
    nrWPs = 0
    wpLat = wpActLat
    wpLong = wpActLong
    wpHeight = wpActHeight

    while dataFrame.iloc[i, 3] == 16:  # parse as long WP entries are in the mission plan
        wpLatNext = dataFrame.iloc[i, 8]
        wpLongNext = dataFrame.iloc[i, 9]
        wpHeightNext = dataFrame.iloc[i, 10]
        wpLatDelta = (wpLatNext - wpLat) * longFact
        wpLongDelta = (wpLongNext - wpLong) * latFact
        wpHeightDelta = abs(wpHeightNext - wpHeight)
        retVal = retVal + math.sqrt(wpLatDelta * wpLatDelta + wpLongDelta * wpLongDelta + wpHeightDelta * wpHeightDelta)

        #-- prepare the next round
        wpLat = wpLatNext
        wpLong = wpLongNext
        wpHeight = wpHeightNext
        i = i + 1
        nrWPs = nrWPs + 1

    return round(retVal,  2), nrWPs  ##- round to cm


# ------------------------------------------------------------------------------
#
if __name__ == "__main__":
    in_f = None
    out_f = None
    droneAngle = None
    longFact = None    ##- unknown - will be calculated from the first WP lat position value
    latFact = 113000   ##- for distances in m

    dateAndTime = time.strftime("%Y%m%d-%H%M%S")


    # --- setup logging
    if not os.path.isdir(LoggingFolder):
        os.makedirs(LoggingFolder)
    if not os.path.isdir(OutFolder):
        os.makedirs(OutFolder)


    format = "%(asctime)s: %(message)s"
    logging.basicConfig(filename=log_file, format=format, level=logging.INFO, datefmt="%H:%M:%S")

    logging.info("")
    logging.info("")
    logging.info("#####################################################")
    logging.info("#              genFrontBackCmds V1.1                #")
    logging.info("#####################################################")
    logging.info("")
    logging.info("------------------------------------------------")
    logging.info("Main    : starting...")
    logging.info("")
    logging.info("")


    # --- parse arguments
    if len(sys.argv) > 1:
        for i,arg in enumerate(sys.argv):
            if (i==0):
                continue
            if (arg.startswith("in=")):
                in_f = '.\\' + InFolder + '\\' + arg[3:]
                out_f = '.\\' + OutFolder + '\\' + arg[3:]
                out_log_f = '.\\' + LoggingFolder + '\\' + arg[3:]
                continue
            if (arg.startswith("cleanup")):
                _cleanup_folder(OutFolder)
                continue
            else: usage()
    else: usage()

    if not os.path.isfile(in_f):
        print ("\nfile <%s> doesn't exist..." % in_f)
        usage()

    logging.info("Starting to parse <%s>" % in_f)

    dataFrame = pd.read_csv(in_f, sep='\t', skiprows=1, header=None, index_col=False)

    #--- first store not manipulated missionplan dataFrame into logging folder (for eventually needed verification)
    _storeMission(out_log_f, dataFrame)

    # --- parse the dataFrame
    for i, row in dataFrame.iterrows():
        if (row[3] == 115):  #-- CONDITION_YAW
            droneAngle = row[4]
            if (droneAngle < 90):
                minAngle = droneAngle+90
                maxAngle = droneAngle+270
                doInvert = True
            elif (droneAngle > 180):
                maxAngle = droneAngle - 90
                minAngle = droneAngle - 270
                doInvert = True
            else:
                minAngle = droneAngle - 90
                maxAngle = droneAngle + 90
                doInvert = False
            logging.info("Parser[%d]: DroneOrientation set to %d°; min=%d°; max=%d°; doInvert=%d", i, droneAngle, minAngle, maxAngle, doInvert)
            continue
        if (row[3] == 16):  #-- WAYPOINT
            wpLat = row[8]
            wpLong = row[9]
            wpHeight = row[10]
            if (longFact == None):  ##- first WP found calculate it factor from actual position
                longFact = abs(latFact * math.cos(wpLat*(math.pi/180)))  ##- for distances in m
                logging.info("Parser[%d]: first WP found --> latFact=%f; longFact=%f;", i, latFact, longFact)
            continue

        if ((row[3] == 217) and (row[4] == 2) and (row[5] != 0)):  # -- DO_SEND_SCRIPT_MESSAGE with command do spray
            wpLatNext = dataFrame.iloc[i + 1, 8]
            wpLongNext = dataFrame.iloc[i + 1, 9]
            wpLatDelta = (wpLatNext - wpLat) * longFact
            wpLongDelta = (wpLongNext - wpLong) * latFact

            #-- calculate the angle and the matching spray command
            flightAngle = (90 - (math.atan2(wpLatDelta, wpLongDelta) * (180.0 / math.pi)) + 360) % 360
            sprayCommand = _getSprayCommand(flightAngle, minAngle, maxAngle, doInvert)

            # -- calculate the distance over all following WP (3D); returns duple: distance and 'number of parsed WPs'
            wpDistance, nrWPs = _getDistanceToNextWP(dataFrame, i, wpLat, wpLong, wpHeight, longFact, latFact)
            if nrWPs==0:
                logging.error("Parser[%d]: Something is wrong with file <%s>; At least one WP is needed after spraying command", i, in_f)


            #-- write the data into missionplan dataFrame
            dataFrame.iloc[i, 5] = sprayCommand
            dataFrame.iloc[i, 6] = wpDistance
            logging.info("Parser[%d]: SpryCommand issued; droneAngle=%d°; flightAngle=%d°; SpryCmd=%d; Distance=%0.2fm; NrWPs=%d", i, droneAngle, flightAngle, sprayCommand, wpDistance, nrWPs)

            continue


    # --- store the modified dataFrame to output file ---
    _storeMission(out_f, dataFrame)

    logging.info("Outputfile <%s> generated" % out_f)
    logging.info("Main    : done.")
    print ("Outputfile <%s> generated" % out_f)




