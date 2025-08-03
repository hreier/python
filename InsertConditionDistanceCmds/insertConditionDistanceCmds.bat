echo off
echo e.g. cmd-line params (defaults): dist1=3 cmd1=0 dist2=6 cmd2=15
call insertConditionDistanceCmds.exe in=5b-Lahn-SV.waypoints
call insertConditionDistanceCmds.exe in=Flugplan-1b-Hof-SV.waypoints
pause