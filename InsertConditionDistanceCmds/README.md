# MissionPlan parser tool

## insertConditionDistanceCmds
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

 
---------
 Notes:
 - MAV_CMD_CONDITION_DISTANCE (114) 
    param 1: distance in meters 
    param 2-7: empty (0)
 
## History:
 - HaRe[2025_07_29]: generated
 - ...

