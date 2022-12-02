import logging

from vis_stim_experiment import vis_stim_experiment_master
from lickometer import Protocol

# Parameters for communication between stimulation and recording PC
# port connected to the fUSi
ip = "192.168.0.2"
port = 40000
imaging_framerate = 11
com_port = 'COM5'
# Skip COM port communication (Set to False to use COM port!)
debug = True

# Name of the changing parameter (This should not have to be changed!)
changing_parameter = 'direction'

# matlab script to start on FUS PC
script_path = r"C:\\03_Users\\07_Daniel\\01_Scripts\\05_VisualExperimentCatAU\danielfullexpVisStimRandomScan"

# Experiment parameters
animal_name = "Szöcsi"
awake_anest = "jumpstand"  # {'awake', 'anesthetized'}

position = '1'
eye = 'both'  # {'right', 'left', 'both'}

# ---Parameters of the stimulation display screen---
# Screen name, chosen from users.Abel.monitors.mymonitors
monitor = 'Samsung_LE40C530'
monitor2 = 'Samsung_LE40C530'

# distance of the observer from the screen in cm
distance = 30

# ---Parameters of the stimulation---
# List of directions of drifting grating
# direction = [0, 45, 90, 135, 180, 225, 270, 315]
direction = [0, 270]  # this was used for the rat test

# List of directions rewarded with the lickometer
rewarded_directions = [270]

# Length of baseline recording before stimulation in seconds
baseline_before = 1

# Planned length of stimulation
stim_length = 5  # 0.5 for GCaMP7S

# Length of baseline recording after stimulation in seconds
baseline_after = 0  # originally 5, but we increased by 2 seconds, so all interesting frames are definitely recorded

# Number of repetitions of all given stimulation directions
repetitions = 4

# part of the stimulus that is stationary (in seconds)
stationary_duration = 5

# spatial frequency of the grating in cycle/visual degree
spatial_frequency = 0.05  # 0.1
# temporal frequency (phase) in Hz (cycle/sec)
phase = 1

# contrast of the grating (from 0 to 1)
contrast = 1

# color of the background in RGB (ranges from -1 = black to 1 = white)
color_bg = [0.255, 0.255, 0.255]

# path where stimulation log file will be saved
path_stim_log = r"C:\Data\FUS\vis_stim_logs\ "

# lickometer config
arduino = Protocol()
orders = arduino.Order

# levels


# ---The lines below should not be modified!---
experiment_params = {'animal_name': animal_name, 'awake_anest': awake_anest, 'position': position, 'eye': eye}

stim_params = {'monitor': monitor, 'monitor2': monitor2, "distance": distance, 'direction': direction,
               'rewarded_directions': rewarded_directions, 'baseline_before': baseline_before,
               'stim_length': stim_length, 'baseline_after': baseline_after,
               'repetitions': repetitions, 'stationary_duration': stationary_duration,
               'spatial_frequency': spatial_frequency, "phase": phase, 'contrast': contrast, "color_bg": color_bg,
               'path_stim_log': path_stim_log, 'parameter_source_path': __file__,
               'arduino': arduino, 'orders': orders}

stat_params = {'left': 0, 'left_correct': 0, 'left_wrong': 0,
               'right': 0, 'right_correct': 0, 'right_wrong': 0,
               'correct': 0, 'wrong': 0}

communication_params = {'ip': ip, 'port': port, 'imaging_framerate': imaging_framerate, 'com_port': com_port,
                        'debug': debug, 'script_path': script_path, 'changing_parameter': changing_parameter}

_all_variables = locals()
filtered_all_variables = {key: _all_variables[key] for key in _all_variables.keys() if key[0] != '_'}

if __name__ == '__main__':
    vis_stim_experiment_master('dual_static_grating', stim_params, experiment_params, stat_params, communication_params, filtered_all_variables)

    print("\n------------------------------------------")
    print(f"Left: {stat_params['left']}\nRight: {stat_params['right']}")
    print(f"Correct: {stat_params['correct']}\nWrong: {stat_params['wrong']}")
    print("------------------------------------------")
    print(f"Precision: {stat_params['correct']/(stat_params['correct'] + stat_params['wrong'])} (correct / correct + wrong)")
    print(f"left correct: {stat_params['left_correct']}, left wrong: {stat_params['left_wrong']}")
    print(f"right correct: {stat_params['right_correct']}, right wrong: {stat_params['right_wrong']}")
    print(f"Left side: {stat_params['left_correct']} / {stat_params['left_correct'] + stat_params['left_wrong']} = "
          f"{stat_params['left_correct'] / (stat_params['left_correct'] + stat_params['left_wrong'])}")
    print(f"Right side: {stat_params['right_correct']} / {stat_params['right_correct'] + stat_params['right_wrong']} = "
          f"{stat_params['right_correct'] / (stat_params['right_correct'] + stat_params['right_wrong'])}")

    logging.debug("------------------------------------------")
    logging.debug(f"Left: {stat_params['left']} Right: {stat_params['right']} Correct: {stat_params['correct']} Wrong: {stat_params['wrong']}")
    logging.debug(f"Precision: {stat_params['correct']/(stat_params['correct'] + stat_params['wrong'])} (correct / correct + wrong)")
    logging.debug(f"Left correct: {stat_params['left_correct'] / (stat_params['left_correct'] + stat_params['left_wrong'])}")
    logging.debug(f"Right correct: {stat_params['right_correct'] / (stat_params['right_correct'] + stat_params['right_wrong'])}")

