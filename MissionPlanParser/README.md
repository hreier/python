# MissionPlan parser tool

## genFrontBackCmds
This parses existing MissionPlan and modifies DO_SEND_SCRIPT_MESSAGES (217) 
 - detects the orientation of the drone
 - Spray with back valve-set if the drone flys forward (12; bit0+bit1)
 - Spray with front valve-set if the drone flys backward (3; bit2+bit3) <br><br>
  
 - Enters the distance to next WP to the areas when 'spraying is active'

## History:
 - HaRe[2025_06_06]: generated
 - ...

