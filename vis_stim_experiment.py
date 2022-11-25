import os
import time
import random
import pickle
from psychopy import logging
from visual_stimuli import StaticGratingDual


def vis_stim_experiment_master(stim_type: str, stim_params: dict, experiment_params: dict, communication_params: dict,
                               all_variables: dict):
    """
    Start visual stimulation and recording experiment with specified parameters.
    This function records every trial of every stimulation type in a separate file, and waits for synchronization
    signals from the recording PC before starting every trial.

    Parameters
    ----------
    stim_type: type of visual stimulation to display, from ['retinotopy_longstim', 'orientation_drifting_grating']
    stim_params: dictionary containing all parameters needed by chosen stimulation type. (directions, speed, etc.)
    experiment_params: dictionary containing parameters regarding the experiment (animal_id, imaging position, etc.)
    communication_params: dict containing parameters for communication between stimulator and recording PCs.
    all_variables: dict created using locals() in the calling module.

    Returns
    -------
    None
    """
    # ---Choosing stimulation type---
    if stim_type == 'orientation_drifting_grating':
        StimClass = DriftingGratingStimulation
        stim_specs = stim_params['direction']
    elif stim_type == 'dual_static_grating':
        StimClass = StaticGratingDual
        stim_specs = stim_params['direction']
    elif stim_type == 'retinotopy_longstim':
        StimClass = DriftingFlickeringBar
        stim_specs = stim_params['direction']
    elif stim_type == 'full_screen_white_flash':
        StimClass = FullScreenWhiteStimulation
        stim_specs = stim_params['frequency']
    elif stim_type == 'harmonica':
        StimClass = FlickeringStaticBars
        stim_specs = stim_params['bar_width']
    elif stim_type == 'four_orientations_grating':
        StimClass = FourOrientationsGratingStimulation
        stim_specs = [stim_params['stim_length']]
    elif stim_type == 'full_screen_checkerboard':
        StimClass = FullscreenCheckerboard
        stim_specs = stim_params['frequency']
    elif stim_type == 'flashing_light':
        StimClass = FlashingLightStimulation
        stim_specs = stim_params['light_intensity']
    elif stim_type == 'ttl_stim':
        StimClass = OptogeneticTTLStimulation
        stim_specs = stim_params['light_intensity']
    else:
        raise ValueError("Unknown stim_type provided, quitting.")

    file_timestamp = time.strftime('%Y%m%d_%H%M%S')

    # Calculation of recording parameters
    imaging_framerate = communication_params['imaging_framerate']
    nimag = imaging_framerate * (stim_params['baseline_before'] + stim_params['stim_length'] + stim_params['baseline_after'])
    nstim = imaging_framerate * stim_params['baseline_before']
    stimLen = imaging_framerate * stim_params['stim_length']

    if nstim < 10:  # baseline can not be calculated based on frames 0-5, and 5 frames are the minimum for calculation
        raise ValueError("Baseline period too short. It has to be at least 10 fUS frames")

    # Creating recording output folder structure and filename in the following format:
    # /<stimulus_name>/<YYYYMMDD>/<HHMMSS>/<generated_filename>
    stimulus_name = os.path.splitext(os.path.basename(stim_params['parameter_source_path']))[0]
    changing_parameter = communication_params['changing_parameter']

    recording_filename = stimulus_name + '\\' + file_timestamp[:8] + '\\' + file_timestamp[9:] + '\\' +\
                         experiment_params['animal_name'] + '_' + file_timestamp[:8] + '_' + \
                         experiment_params['awake_anest'] + '_' + file_timestamp[9:] + '_p' + \
                         experiment_params['position'] + '_' + experiment_params['eye'] + 'eye' + \
                         '_' + changing_parameter
    script_params = dict(zip(['out_filename', 'nimag', 'nblocksImage', 'nstim', 'stimLen'],
                             [recording_filename, nimag, 5, nstim, stimLen]))
    script_params = (communication_params['script_path'], script_params)

    # ---Logging---
    if not os.path.exists(stim_params['path_stim_log'] + os.path.split(recording_filename)[0]):
        print(stim_params['path_stim_log'] + os.path.split(recording_filename)[0])
        os.makedirs(stim_params['path_stim_log'] + os.path.split(recording_filename)[0])
    logging.LogFile(f=stim_params['path_stim_log'] + recording_filename + "_psychopy.log", level=logging.EXP, filemode='w')

    # Combined output file in hdf5 format
    # outfile_name = stim_params['path_stim_log'] + recording_filename + '_logs.hdf5'
    outfile_name = recording_filename + '_logs.hdf5'

    if communication_params['debug']:
        # no communication with recording PC in debug mode
        stim = StimClass(params=stim_params)
    else:
        stim = StimClass(params=stim_params, port=communication_params['com_port'])

        client = RpcClient([communication_params['ip'], communication_params['port']])

        # Send script sources to recording PC and save them to disk there
        with open(__file__) as source:
            pipeline_source = source.read()
            print(client.remote.call('save_to_disk', kwargs={'filename': outfile_name, 'data_name': 'pipeline_source',
                                                             'data': pipeline_source}).result)

        with open(stim_params['parameter_source_path']) as source:
            parameter_source = source.read()
            print(client.remote.call('save_to_disk', kwargs={'filename': outfile_name, 'data_name': 'parameter_source',
                                                             'data': parameter_source}).result)

        # Send all stimulation parameters to recording PC and save them to the stimulus hdf5 there
        print(client.remote.call('save_to_disk', kwargs={'filename': outfile_name, 'data_name': 'experiment_settings',
                                                         'data': pickle.dumps(all_variables)}).result)

        # Send stimulation block limits to recording PC and save them to the stimulus hdf5 there
        block_limits = {'baseline': [5, nstim], 'stimulated': [nstim, nstim+stimLen], 'post': [nstim+stimLen, nimag]}
        print(client.remote.call('save_to_disk', kwargs={'filename': outfile_name, 'data_name': 'stim_block_limits',
                                                         'data': block_limits}).result)

        print("Waiting 10 seconds before starting.")
        time.sleep(10)  # so the activation caused by the gray screen goes back to baseline

    presented_values = []
    # ---Starting stimulation---
    trial_index = 0
    for i in range(stim_params['repetitions']):
        random.shuffle(stim_specs)  # randomizing stimulation directions
        presented_values.extend(stim_specs)
        print(f"Starting {i}. repetition.")
        for spec in stim_specs:
            # send start recording signal
            script_params[1]['out_filename'] = recording_filename + '_' + str(spec) + '_' + str(trial_index) + '.mat'
            print(F"Recording: {script_params[1]['out_filename']}")
            if not communication_params['debug']:
                client.call_run_script_service(script_params)

            time.sleep(stim_params['baseline_before'])

            if not communication_params['debug']:
                stim.wait_for_serial()  # wait for matlab to start recording

            # t0 = time.perf_counter()
            stim.start_stim(spec)
            # print(f"Actual length of stimulation: {time.perf_counter()-t0}")

            time.sleep(stim_params['baseline_after'])

            trial_index += 1

            if communication_params['debug']:
                continue
            while not client.recording_finished:
                print("Waiting")
                time.sleep(0.5)

    # Saving psychopy log to combined hdf5 output file
    logging.flush()  # To make sure that everything is written to the log file

    if not communication_params['debug']:  # Save psychopy log on the remote PC together with the stimulation scripts
        with open(stim_params['path_stim_log'] + recording_filename + "_psychopy.log", 'r') as psychopy_log:
            psychopy_log = psychopy_log.read()
            print(client.remote.call('save_to_disk', kwargs={'filename': outfile_name, 'data_name': 'psychopy_log',
                                                             'data': psychopy_log}))

        group_stimulus_parameters = {communication_params['changing_parameter']: presented_values,
                                     'changing_parameter_name': communication_params['changing_parameter']}
        print(client.remote.call('save_to_disk', kwargs={'filename': outfile_name, 'data_name': 'stimulus_parameters',
                                                         'data': group_stimulus_parameters}))


def one_block_vis_stim_experiment(stim_type: str, stim_params: dict, experiment_params: dict,
                                  communication_params: dict, all_variables: dict):
    """
    Start visual stimulation and a single recording containing the whole experiment with specified parameters.

    Parameters
    ----------
    stim_type: type of visual stimulation to display, from ['retinotopy_longstim', 'orientation_drifting_grating']
    stim_params: dictionary containing all parameters needed by chosen stimulation type. (directions, speed, etc.)
    experiment_params: dictionary containing parameters regarding the experiment (animal_id, imaging position, etc.)
    communication_params: dict containing parameters for communication between stimulator and recording PCs.
    all_variables: dict created using locals() in the calling module.

    Returns
    -------
    None

    """
    # ---Choosing stimulation type---
    if stim_type == 'retinotopy_ksstim':
        StimClass = DriftingFlickeringBar
        stim_specs = stim_params['direction']
    else:
        raise ValueError("Unknown stim_type provided, quitting.")

    file_timestamp = time.strftime('%Y%m%d_%H%M%S')

    # Calculation of recording parameters
    imaging_framerate = communication_params['imaging_framerate']
    nimag = imaging_framerate * (stim_params['repetitions'] * (stim_params['baseline_before'] +
                                                               stim_params['stim_length'] +
                                                               stim_params['baseline_after']))
    nstim = imaging_framerate * stim_params['baseline_before']
    stimLen = imaging_framerate * stim_params['stim_length']

    # Creating recording output folder structure and filename in the following format:
    # /<stimulus_name>/<YYYYMMDD>/<HHMMSS>/<generated_filename>
    stimulus_name = os.path.splitext(os.path.basename(stim_params['parameter_source_path'])[0])
    changing_parameter = communication_params['changing_parameter']

    recording_filename = stimulus_name + '\\' + file_timestamp[:8] + '\\' + file_timestamp[9:] + '\\' + \
                         experiment_params['animal_name'] + '_' + file_timestamp[:8] + '_' + \
                         experiment_params['awake_anest'] + '_' + file_timestamp[9:] + '_' + '_p' + \
                         experiment_params['position'] + '_' + experiment_params['eye'] + 'eye' + \
                         '_' + changing_parameter
    script_params = dict(zip(['out_filename', 'nimag', 'nblocksImage', 'nstim', 'stimLen'],
                             [recording_filename, nimag, 5, nstim, stimLen]))
    script_params = (communication_params['script_path'], script_params)

    # ---Logging---
    if not os.path.exists(stim_params['path_stim_log'] + os.path.split(recording_filename)[0]):
        print(stim_params['path_stim_log'] + os.path.split(recording_filename)[0])
        os.makedirs(stim_params['path_stim_log'] + os.path.split(recording_filename)[0])
    logging.LogFile(f=stim_params['path_stim_log'] + recording_filename + "_psychopy.log", level=logging.EXP,
                    filemode='w')

    # Combined output file in hdf5 format
    outfile_name = stim_params['path_stim_log'] + recording_filename + '_logs.hdf5'
    # outfile_name = '/home/hillierlab/Users/Abel/' + recording_filename + '_logs.hdf5'

    if communication_params['debug']:
        # no communication with recording PC in debug mode
        stim = StimClass(params=stim_params)
    else:
        stim = StimClass(params=stim_params, port=communication_params['com_port'])

        client = RpcClient([communication_params['ip'], communication_params['port']])

        # Send script sources to recording PC and save them to disk there
        with open(__file__) as source:
            pipeline_source = source.read()
            print(client.remote.call('save_to_disk', kwargs={'filename': outfile_name, 'data_name': 'pipeline_source',
                                                             'data': pipeline_source}))

        with open(stim_params['parameter_source_path']) as source:
            parameter_source = source.read()
            print(client.remote.call('save_to_disk', kwargs={'filename': outfile_name, 'data_name': 'parameter_source',
                                                             'data': parameter_source}))

        # Send all stimulation parameters to recording PC and save them to the stimulus hdf5 there
        print(client.remote.call('save_to_disk', kwargs={'filename': outfile_name, 'data_name': 'experiment_settings',
                                                         'data': pickle.dumps(all_variables)}).result)

    print("Waiting 10 seconds before starting.")
    time.sleep(10)  # so the activation caused by the gray screen goes back to baseline

    # send start recording signal
    if not communication_params['debug']:
        script_params[1]['out_filename'] = recording_filename + '.mat'
        client.call_run_script_service(script_params)
        print(F"Recording: {script_params[1]['out_filename']}")

    if not communication_params['debug']:
        stim.wait_for_serial()  # wait for matlab to start recording
        time.sleep(stim_params['start_baseline'])

    presented_values = []
    # ---Starting stimulation---
    trial_index = 0
    for i in range(stim_params['repetitions']):
        random.shuffle(stim_specs)  # randomizing stimulation directions
        presented_values.extend(stim_specs)
        print(f"Starting {i}. repetition.")
        for spec in stim_specs:
            time.sleep(stim_params['baseline_before'])

            # t0 = time.perf_counter()
            stim.start_stim(spec)
            # print(f"Actual length of stimulation: {time.perf_counter()-t0}")

            time.sleep(stim_params['baseline_after'])

            trial_index += 1

    # Saving psychopy log to combined hdf5 output file
    logging.flush()  # To make sure that everything is written to the log file

    if not communication_params['debug']:  # Save psychopy log on the remote PC together with the stimulation scripts
        with open(stim_params['path_stim_log'] + recording_filename + "_psychopy.log", 'r') as psychopy_log:
            psychopy_log = psychopy_log.read()
            print(client.remote.call('save_to_disk', kwargs={'filename': outfile_name, 'data_name': 'psychopy_log',
                                                             'data': psychopy_log}))

        group_stimulus_parameters = {communication_params['changing_parameter']: presented_values,
                                     'changing_parameter_name': communication_params['changing_parameter']}
        print(client.remote.call('save_to_disk', kwargs={'filename': outfile_name, 'data_name': 'stimulus_parameters',
                                                         'data': group_stimulus_parameters}))
