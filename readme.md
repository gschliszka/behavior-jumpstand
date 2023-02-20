# JumpStand training

JumpStand experimental setup is used to determine visual acuity of the subject animals (cats). This automated version 
tries to eliminate human bias and mistakes to make training more efficient.

## Changelog (20.02.2023)
- Added volume control options to reward & punish sounds

## Codes
Note:
> Code will be rearranged into lickometer.py, action.py and training/experiment.py for better transparency.

### lickometer.py
Contains all variables and functions required to the communications between the MASTER and Lickometer.

### threshold_experiment.py
(MASTER) Controls the training. The changing parameter is the motion time of the gradings.