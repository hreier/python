"""
############# Script: integrateConditionDistanceCmds ############
---------
 Tool parsing existing missionplan:
 - This assumes to be applied on a 'ready made Mission plan' for Soleon sprayer
 - 'ready made Mission plan' means that it has already all front/back control integrated and working properly 
 - The 'ready made Mission plan' must not have any MAV_CMD_CONDITION_DISTANCE entries already in...
 
 - existing missionplan needs to be located into folder ./in
 - generates modified missionplan with same name into folder ./out
 - generates log file in folder ./logs
 - 

---------
 The script does the following:
 - inserts up to 2 x 'CMD_CONDITION_DISTANCE + DO_SEND_SCRIPT_MESSAGES' couples before it reaches a WP that switches off the spayer 
 
---------
 Command line parameters (with default values):
 - dist1=2   The nearby distance
 - cmd1=0    the DO_SEND_SCRIPT_MESSAGES command to be inserted; if not defined(0) it reverses the active valvecommand (back<-->front);
 
 - dist2=0   The far distance (> dist1); if 0 --> ignored
 - cmd2=15   the DO_SEND_SCRIPT_MESSAGES command to be inserted; if 0 it reverses the active valvecommand (back<-->front);

 

--------------------------------------
History:
 2025.07.28 HRE:  created
 
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

dist1 = 3
cmd1 = 0
dist2 = 6
cmd2 = 15

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
    print("dist1=2     :The nearby distance")
    print("cmd1=0      :the DO_SEND_SCRIPT_MESSAGES command to be inserted;")
    print("             if not defined(0) it reverses the active valvecommand (back < -->front)")
    print("dist2=0     :The far distance (> dist1); if 0 --> ignored")
    print("cmd2=15     :the DO_SEND_SCRIPT_MESSAGES command to be inserted;")
    print("             if not defined(0) it reverses the active valvecommand (back < -->front)")

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

#--- This inverts spray-command (front<->back)
def invertSprayCmd(cmd, active_cmd):
    newCmd = 0
    if (cmd != 0): return cmd
    newCmd = (active_cmd & 0x3) << 2
    newCmd |= (active_cmd & 0xC) >> 2
    newCmd |= (active_cmd & ~0xF)
    return newCmd

#--- This inserts MAV_CMD_CONDITION_DISTANCE(114)+DO_SEND_SCRIPT_MESSAGE(217) couples in front of id
def doInsertConditionCouples(dataFrame, id, dist1, cmd1, dist2, cmd2, active_cmd):
    data_row_cd = {0:0,1:0,2:0,3:114,4:0,5:0,6:0,7:0,8:0,9:0,10:0,11:1}       #MAV_CMD_CONDITION_DISTANCE
    data_row_script = {0:0,1:0,2:0,3:217,4:2,5:0,6:0,7:0,8:0,9:0,10:0,11:1}   #DO_SEND_SCRIPT_MESSAGE

    if (dist2 != 0):
        data_row_cd[4]     = dist2
        data_row_script[5] = invertSprayCmd(cmd2, int(active_cmd))
        dataFrame.loc[len(dataFrame)] = data_row_cd
        dataFrame.loc[len(dataFrame)] = data_row_script
        logging.info("MAV_CMD_CONDITION_DISTANCE+DO_SEND_SCRIPT_MESSAGE couple added: dist=%dm; cmd=%d [%d]", dist2, data_row_script[5], int(active_cmd))

    if (dist1 != 0):
        data_row_cd[4]     = dist1
        data_row_script[5] = invertSprayCmd(cmd1, int(active_cmd))
        dataFrame.loc[len(dataFrame)] = data_row_cd
        dataFrame.loc[len(dataFrame)] = data_row_script
        logging.info("MAV_CMD_CONDITION_DISTANCE+DO_SEND_SCRIPT_MESSAGE couple added: dist=%dm; cmd=%d [%d]", dist1, data_row_script[5], int(active_cmd))



# ------------------------------------------------------------------------------
#
if __name__ == "__main__":
    activeSprayCommand = None

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
    logging.info("#      integrateConditionDistanceCmds V1.0          #")
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
            if (arg.startswith("dist1=")):
                dist1=int(arg[6:])
                continue
            if (arg.startswith("dist2=")):
                dist2=int(arg[6:])
                continue
            if (arg.startswith("cmd1=")):
                cmd1 = int(arg[5:])
                continue
            if (arg.startswith("cmd2=")):
                cmd2 = int(arg[5:])
                continue
            else: usage()
    else: usage()

    if not os.path.isfile(in_f):
        print ("\nfile <%s> doesn't exist..." % in_f)
        usage()

    logging.info("Starting to parse <%s>" % in_f)
    logging.info("Config: dist1=%d; cmd1=%d; dist2=%d; cmd2=%d", dist1, cmd1, dist2, cmd2)

    print("Config: dist1=%d; cmd1=%d; dist2=%d; cmd2=%d;" % (dist1, cmd1, dist2, cmd2))

    dataFrame = pd.read_csv(in_f, sep='\t', skiprows=1, header=None, index_col=False)
    outDataFrame = pd.DataFrame()   #-- copy to outDataFrame to be used to insert new items

    #--- first store not manipulated missionplan dataFrame into logging folder (for eventually needed verification)
    #_storeMission(out_log_f, dataFrame)

    # --- parse the dataFrame and compose outDataFrame
    i=0
    for row in dataFrame.itertuples():
        #print("--> <%d> " % row[4])
        match row[4]:
            #--- MAV_CMD_CONDITION_DISTANCE (just verify thoes are not in; may result with not intended behavior)
            case 114:
                logging.error(
            "Parser[%d]: Something may be wrong with file <%s>; MAV_CMD_CONDITION_DISTANCE command should not be in this file!?",
            i, in_f)

            # --- DO_SEND_SCRIPT_MESSAGE with command do spray
            case 217 if ((row[5] == 2) and (row[6] != 0)):
                activeSprayCommand = dataFrame.iloc[i, 5]
                logging.info("Parser[%d]: SpryCommand found [%d];", i, activeSprayCommand)

            # --- WAYPOINT(16) and following DO_SEND_SCRIPT_MESSAGE with 'stop spraying' command
            #    here we have to insert the MAV_CMD_CONDITION_DISTANCE+DO_SEND_SCRIPT_MESSAGE couples!
            case 16 if ((activeSprayCommand != None) and (dataFrame.iloc[i + 1, 3] == 217) and (dataFrame.iloc[i + 1, 4] == 2) and (dataFrame.iloc[i + 1, 5] == 0)):
                logging.info("Parser[%d]: WayPoint with 'stop spraying found'; insert Conditions before the WP!!", i)
                doInsertConditionCouples(outDataFrame, i, dist1, cmd1, dist2, cmd2, activeSprayCommand)

        #--- insert the rows from incoming dataset to the outgoing
        outDataFrame = pd.concat([outDataFrame, pd.DataFrame([row[1:]])])
        i += 1

        #.iloc[len(outDataFrame)] = row

        # #--- MAV_CMD_CONDITION_DISTANCE (just verify thoes are not in; may result with not intended behavior)
        # if (row[3] == 114):
        #     logging.error(
        #         "Parser[%d]: Something may be wrong with file <%s>; MAV_CMD_CONDITION_DISTANCE command should not be in this file!?", i, in_f)
        #     continue

        # #--- DO_SEND_SCRIPT_MESSAGE with command do spray
        # if ((row[3] == 217) and (row[4] == 2) and (row[5] != 0)):
        #     activeSprayCommand = dataFrame.iloc[i, 5]
        #     logging.info("Parser[%d]: SpryCommand found [%d];", i, activeSprayCommand)
        #     continue
        #
        # #--- DO_SEND_SCRIPT_MESSAGE with command to 'stop spraying' immediately following to WAYPOINT(16)
        # #    here we need to insert the MAV_CMD_CONDITION_DISTANCE+DO_SEND_SCRIPT_MESSAGE couples!
        # if ((i > 0) and (activeSprayCommand != None) and (row[3] == 217) and (row[4] == 2) and (row[5] == 0) and (dataFrame.iloc[i-1, 3] == 16)):
        #     #if ()
        #     #activeSprayCommand = dataFrame.iloc[i, 5]
        #     logging.info("Parser[%d]: inseert [%d];", i, activeSprayCommand)
        #     continue
        #

    # --- store the modified outDataFrame to output file ---
    _storeMission(out_f, outDataFrame)

    logging.info("Outputfile <%s> generated" % out_f)
    logging.info("Main    : done.")
    print ("Outputfile <%s> generated" % out_f)




