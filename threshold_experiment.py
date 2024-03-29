"""
Decrease motion duration while teaching animal to discriminate vertical vs horizontal orientation.
This code assumes animal knows lickometer and jump stand.
"""

import sys
sys.modules['debugmp'] = None
import time
import argparse
import uuid
from psychopy import sound, monitors
import numpy
import random
import pytest
from screeninfo import get_monitors
detected_monitors = get_monitors()
# print(f"Detected monitors:")
# [print(f"\t{mon}") for mon in detected_monitors]
from psychopy import core, visual, gui, data, event
from psychopy.tools.filetools import fromFile, toFile

import sys
import pdb
import traceback
def debughook(etype, value, tb):
    traceback.print_exception(etype, value, tb)
    print() # make a new line before launching post-mortem
    # pdb.pm() # post-mortem debugger
sys.excepthook = debughook

machine_dict = {'LabThinkpadStim': 101707888628436,
                '2pgoe': 93181002139480,
                'Gazsi::laptop': 220292358129433}

# TODO: rearrange code as lickomter.py, actions.py and experiment.py
#       - lickometer.py: communication
#       - actions.py: reward, punish, ... ect. (building blocks for experiments/trainings)
#       - experiment.py/training.py: the actual experiment/training (train_jumping, iterate_motion_time_grating_2afc &
#       run_staircase)


class TwoAFC:
    def __init__(self, lickemu, touchscreen=False, show_messages=False, windowed=None):
        self.lickemu = lickemu
        print(self.lickemu)
        self.touchsc = touchscreen
        self.show_messages = show_messages
        self.windowed = windowed
        self.init_environment()

    def init_environment(self):
        if not self.lickemu:
            try:
                import lickometer
                self.lick_o_meter = lickometer.Lickometer()
                trialtext = ''
            except:
                self.lickemu = 1
        print(f'lickemu: {self.lickemu}')
        computer = uuid.getnode()
        print(f"Running on computer with mac address: {computer}")
        if computer == 101707888628436:
            # jump stand with two monitors
            monitor_params = {'distance_cm': 40}
            screen_ids = (2, 1) # if len(detected_monitors) == 1 else (1, 0)
        elif computer == 93181002139480:
            # 2pgoe
            monitor_params = {'distance_cm': 40}
            # set screen_id so that left screen is physically on the left side
            screen_ids = (1, 0)
        elif computer == 220292358129433:
            # Gazsi's laptop
            # BUG: this machine switches L-R lickometers
            monitor_params = {'distance_cm': 40}
            screen_ids = (2, 1)
        else:
            # Gazsi added monitor_params
            monitor_params = {'distance_cm': 40}
            screen_ids = (0, 0) if len(detected_monitors) == 1 else (1, 0)
        mon={}
        for i1, k1 in zip(range(len(detected_monitors)), ['left','right']):
            mon[k1] = monitors.Monitor(detected_monitors[i1].name, width=detected_monitors[i1].width_mm/10, distance=monitor_params['distance_cm'])
            mon[k1].setSizePix((detected_monitors[i1].width, detected_monitors[i1].height))

        if self.windowed:
            print('windowed mode')
            self.window_p = {
                'size' : {'height': 600, 'width': 800},
                'pos' : {'left': (0, 0), 'right': (0, 0)},
                'unit': 'pix'
            }
        else:
            print('fullscreen mode')
            self.window_p = {
                'size': {mk: getattr(detected_monitors[-1], mk) for mk in ['height', 'width']},
                'pos': {'left': (0, 0), 'right': (0, 0)},
                'unit': 'pix'
            }
        if computer == 220292358129433 or computer == 101707888628436:
            # my laptop monitor is much smaller then externals
            monitor_pixelsize = detected_monitors[1].width_mm / detected_monitors[1].width  # mm
        else:
            monitor_pixelsize = detected_monitors[0].width_mm/detected_monitors[0].width  # mm
        grating_size_deg = numpy.arctan(detected_monitors[0].width_mm/10/2 / monitor_params['distance_cm'])
        print(detected_monitors)

        # half pixel is viewed in right angled triangle -> multiply by 2 at the end to get visual degree for a full pixel
        one_pixel_in_visual_degrees = numpy.arctan(monitor_pixelsize/2/monitor_params['distance_cm']/10) * 180/numpy.pi * 2

        grating_period_in_visual_degrees = 20 # spatial frequency in visual degrees
        grating_period_in_pixels = grating_period_in_visual_degrees/one_pixel_in_visual_degrees
        self.grating_p = {
            'size': {gk1: [self.window_p['size']['height'], self.window_p['size']['width']] for gk1 in ['left', 'right']},
            'pos': {'left': (0, 0), 'right': (0, 0)},
            'spatial_freq_deg_per_pix': grating_period_in_pixels,
            'speed_Hz': 7.5,   # how many periods pass in a second
        }

        # absolute volume: set the default volume of the sound cues
        self.feedback_sound_absolute_volume = {'reward': 1, 'punish': 1}
        self.feedback_sound = {'reward': sound.Sound('mixkit-gaming-lock-2848.wav', volume=self.feedback_sound_absolute_volume['reward']),
                               'punish': sound.Sound('pinknoise.wav', volume=self.feedback_sound_absolute_volume['punish'], stopTime=0.6)}

        # create window(s): if only one screen detected, use the same screen for both 'left' and 'right' stimulus windows
        self.win = {sk1: visual.Window([self.window_p['size']['width'], self.window_p['size']['height']], allowGUI=True, screen=si1,
                                          monitor=mon[sk1], units=self.window_p['unit'], pos=self.window_p['pos'][sk1]) for si1, sk1 in
                       zip(screen_ids,self.window_p['pos'].keys())}  # emulation mode on single screen
        self.mouse = {wk: event.Mouse(win=wv) for wk,wv in self.win.items()}

    def punish(self, volume=1):
        """
        Gives punish cue.

        Parameters
        ----------
        volume : float, optional (default is 1)
            Multiply the volume of the last time played punishing sound then apply to this punishing.
            new_volume = last_volume * volume
        Returns
        -------

        """

        if volume == 1:
            self.feedback_sound['punish'].volume = 1
        else:
            self.feedback_sound['punish'].volume = volume
            self.feedback_sound_absolute_volume['punish'] *= volume
            print(f"Punish sound's volume: {volume}x last_punish_played_volume, absolute volume: "
                  f"{self.feedback_sound_absolute_volume['punish']}")

        self.feedback_sound['punish'].stop()
        self.feedback_sound['punish'].play()

    def bridge_reward(self, volume=1):
        """
        Emits positive reinforcement sound.

        Parameters
        ----------
        volume : float, optional (default is 1)
            Multiply the volume of the last time played rewarding sound then apply to this rewarding.
            new_volume = last_volume * volume

        Returns
        -------

        """

        if volume == 1:
            self.feedback_sound['reward'].volume = 1
        else:
            self.feedback_sound['reward'].volume = volume
            self.feedback_sound_absolute_volume['reward'] *= volume
            print(f"Reward sound's volume: {volume}x last_reward_played_volume, absolute volume: "
                  f"{self.feedback_sound_absolute_volume['reward']}")

        self.feedback_sound['reward'].stop()
        self.feedback_sound['reward'].play()

    def deliver_reward(self, side: str):
        """
        Delivers reward with lickometer
        """

        self.bridge_reward()
        if not self.lickemu:
            self.lick_o_meter.reward(side)

    def wait_for_lickometer(self, enabled_lickometers:list, timeout=float('inf')):
        """
        Wait for subject to respond.

        Parameters
        ----------
        enabled_lickometers : list
            Which lickometer response is valid. possible options 'up', 'left', 'right'
        timeout : int, optional, (0; inf]
            Duration of waiting for licking in seconds. Default is inf.

        Returns
        -------
        str: Which lickometer the subject was licking into. If timeout return None.
        """

        kopt = ['up', 'left', 'right']
        print(f"Waiting for lick for {timeout} seconds")

        # wait for pressed keys
        if self.lickemu:
            tc = core.Clock()
            print(f"started! {tc.getTime()}")
            key = event.waitKeys(maxWait=timeout, clearEvents=True)  # wait for participant to respond
            print(f"Got {key}, timeout {timeout}")
            if key is not None and 'q' in key:
                print("'q' key detected, quit")
                core.quit()
            event.clearEvents()

            # no key hit (timeout)
            if key is None:
                print('no lickometer response (timeout)')
                return  # there was no lick, timeout
            #  key is not left/right/up
            elif not any([k1 in key for k1 in kopt]):
                print('wrong response (invalid, e.g. wrong keyboard key hit)')
                return
            # activated lickometer was disabled
            elif any([k2 not in enabled_lickometers for k2 in key]):
                print(f'lickometer acitvated: {key[-1]} but this lickometer was actually disabled!')
                return key[-1]  # since it was a lick, return it
            else:
                print(f'good: {key[-1]}')
                return key[-1]

        # wait for mouse press
        else:
            # if cat licks into non-valid lickometers, give punishment
            tc = core.Clock()
            # print(f"started! {tc.getTime()}")
            self.lick_o_meter.set_timeout(timeout)
            t = time.time()
            licks = self.lick_o_meter.watch_licks()
            t = time.time()-t
            print(f"-----> waited for: {t}s")

            # Quit if Esc pressed
            if event.getKeys(keyList=["escape"]):
                print("'ESC' key detected, quit")
                core.quit()

            # Transform licks to resp
            if licks in ['100', '010', '001']:
                resp = kopt[licks.index('1')]
            else:
                resp = None
            # print(resp)

            # Return None or resp
            if resp is None:
                print('no lickometer response (timeout)')
                return  # there was no lick, timeout
            if resp not in enabled_lickometers:
                print(f'lickometer acitvated: {resp} but this lickometer was actually disabled!')
                return resp  # since it was a lick, return it
            else:
                print(f'good: {resp}')
                return resp

    def is_touched(self, stimuli: dict, m_loc):
        """
        Check if the stimulus was touched.

        Parameters
        ----------
        stimuli : dict
            Left & Right stimuli
        m_loc : list of list, [[left_x, left_y], [right_x, right_y]]
            Initial location of each mouse to check they moved

        Returns
        -------
        list: [<left_touched>, <right_touched>]
        """

        win_keys = [sk1 for sk1 in self.win.keys()]
        fix_pos = [-960, 0]  # to set mouses' position out of screen

        # if touchscreens are used
        if self.touchsc:
            m_pos = [self.mouse[k1].getPos() for k1 in win_keys]
            if all([(m_pos[i] == m_loc[i]).all() for i in range(len(m_pos))]):
                return [0, 0]
            else:
                s_contain = [stimuli[k].contains(self.mouse[k]) for k in win_keys]
                if all(s_contain):
                    print(f"both stimulus touched, pos: {m_pos}, contains: {s_contain} << {[stimuli[k].contains(self.mouse[k]) for k in win_keys]}")
                    sys.modules['debugmp'] = [m_pos[0], m_pos[1], stimuli.values()]
                    # print(sys.modules['debugmp'])
                    k1 = list(stimuli.keys())[1]
                    [self.mouse[k1].setPos(fix_pos) for k1 in win_keys]
                    s_contain = [stimuli[k1].contains(self.mouse[k1]) for k1 in win_keys]
                    print(f"  '>s_contain: {s_contain}")
                    return [0, 0]

                if any(s_contain):
                    print(f"single touch detected: {s_contain}")
                    m_press = s_contain
                    # move mice out of grating stimuli
                    [self.mouse[k1].setPos(fix_pos) for k1 in win_keys]
                    return s_contain

                else:
                    return [0, 0]

        """
        else:
            # this is basically the same of 'if' part --> if mouse will be used, it must be rewrite
            if any([any(self.mouse[k1].getPressed()) for k1 in grating.keys()]):
                mouse_pos = [self.mouse[k1].getPos() for k1 in grating.keys()]
                if all([(mouse_pos[i] == mouse_loc[i]).all() for i in range(len(mouse_pos))]):
                    pass
                else:
                    stim_contain = [grating[k1].contains(self.mouse[k1]) for k1 in grating.keys()]
                    # print(stim_contain)
                    if all(stim_contain):
                        print(f"both stimulus touched")
                        sys.modules['debugmp'] = [mouse_pos[0], mouse_pos[1], grating.values()]
                        print(sys.modules['debugmp'])

                        k1 = list(grating.keys())[1]
                        [self.mouse[k1].setPos([-900, 0]) for k1 in grating.keys()]
                        stim_contain = [grating[k1].contains(self.mouse[k1]) for k1 in grating.keys()]
                        continue
                    if any(stim_contain):
                        mpress = stim_contain
                        # move mice out of grating stimuli
                        [self.mouse[k1].setPos([-900, 0]) for k1 in grating.keys()]
                        break
        """

    def iterate_motion_time_grating_2afc(self, grating, messages, time_dict, trial_clock):
        # TODO: documentation
        # TODO: save data as train_jumping

        if messages: messages['pre'].draw()
        [self.win[sk1].flip() for sk1 in self.win.keys() if self.win[sk1] is not None]
        core.wait(time_dict['message'])

        # keep screens blank until subject licks into lickometer on the stand
        # TODO: after timeout, no need to lick
        entry_response = self.wait_for_lickometer(['up'])
        if not self.lickemu and entry_response == 'up':
            self.lick_o_meter.reward('up')
        print(f"licked at {entry_response}, entry response")

        # animal licked into stand-lickometer: show stimulus
        # set orientation of gratings on two screens
        random_swap(grating)

        # set duration of motion as the staircase sets the next value
        if messages: messages['trial'].draw()
        [self.win[sk1].flip() for sk1 in self.win.keys() if self.win[sk1] is not None]
        core.wait(time_dict['message'])
        # show moving grating on both screens
        trial_clock.reset()
        mpress = [0, 0]
        ctime = trial_clock.getTime()
        [self.mouse[k1].getPos() for k1 in self.mouse.keys()]
        mouse_loc = [self.mouse[k1].getPos() for k1 in grating.keys()]
        print(mouse_loc)
        while (ctime < time_dict['jump_timeout']) and not any(mpress):
            for sk in grating.keys():
                # move grating until specified time then leave last grating phase constant until timeout time
                if (
                    trial_clock.getTime() < time_dict['motion'] or
                    time_dict['jump_timeout']/2 < trial_clock.getTime() < time_dict['jump_timeout']/2 + time_dict['motion']
                ):
                    grating[sk].phase = numpy.mod(trial_clock.getTime(), 1)
                grating[sk].draw()

                sys.modules['debugmp'] = None

                mpress = self.is_touched(grating, mouse_loc)

                if any(mpress) and not all(mpress):
                    break

            ctime = trial_clock.getTime()
            [self.win[sk1].flip() for sk1 in self.win.keys() if self.win[sk1] is not None]

        return mpress, trial_clock.getTime()  # [True False] if first screen chosen

    def train_jumping(self, jump_within_s: float, percent_correct_required: int, enter_timeout_s: int = 10, remind_to_target_s: int = 5):
        """
        Training level: expect licking into upper lickometer, then jump within jump_within_s amount of time and get reward.

        trial_time_elapsed = time elapsed until jumping
        eval_win = take the last 'eval_win' number trials

        if trial_time_elapsed < jump_within_s:
            reward()
            if 'percent_correct_required'% of trial_outcomes[-eval_win] is successful:
                phase completed, exit train_jumping
            else:
                continue (do another trial)

        if trial_time_elapsed > jump_within_s:
            punish()
            restart trial (without lickometer, just show stimuli)

        Parameters
        ----------
        jump_within_s : int
            After cat licked into 'up' lickometer (trial initiated), cat has to jump within this amount of time
            (in seconds).
        percent_correct_required : int
            Cat has to complete steps within timeouts to complete this training, e.g. 80 means from 5 trials 4
            has to be completed in time.
        enter_timeout_s : int
            After completing a trial, cat has this amount of time (in seconds) to lick into the 'up' lickometer
            to initiate next trial.
        remind_to_target_s : ???

        Returns
        -------
        list: trial_outcome
            1: success, 0: fail
        list: trial_times
            Duration of each trial (second)
        list: entry_times
            Times elapsed between trials
        """

        print("\n\tStarting train_jumping()...")
        print(f"within: {jump_within_s}\n%: {percent_correct_required}\nenter: {enter_timeout_s}")

        # TODO: add self.init_train_jumping_stimulus()

        fix_pos = [-960, 0]     # to set mouses' position out of screen

        trialclock = core.Clock()
        trial_time_elapsed = 0

        # define stimuli
        win_keys = [sk1 for sk1 in self.win.keys()]

        gray_stim = {k: visual.GratingStim(self.win[k], sf=0, color=0, colorSpace='rgb', size=self.win[k].size[0],
                                           name='gray', tex=None) for k in win_keys}
        grating_stim = {k: visual.GratingStim(self.win[k], sf=self.grating_p['spatial_freq_deg_per_pix'],
                                              size=self.grating_p['size'][k], pos=self.grating_p['pos'][k],
                                              mask='gauss', ori=0, name='grating') for k in win_keys}

        stim_list = [gray_stim, grating_stim]

        # randomize stimuli
        t_stim = random_training_stim(stim_list, win_keys)

        # draw gray stimulus on both side
        [sv.draw() for sv in gray_stim.values()]
        [self.win[sk1].flip() for sk1 in win_keys if self.win[sk1] is not None]

        # deliver small reward to attract attention/lure animal to lickometer
        self.lick_o_meter.reward('up')

        # jump to striped side (other side is uniform gray) and add reward with 80% contingency, 20% leads to silent omission (no sound, no reward)
        # TODO: if needed add randomness into the process
        #       after first trainings...
        entry_response = None

        trial_times = []
        trial_outcome = []
        entry_times = []

        eval_win = 5  # look at the outcomes of the last 5 trials (or any other number set here)
        motion_time = 0.5  # short moving grating to elicit attention

        print(f">>> Train jumping started...")

        # keep doing trials until N successful trials in the last 5 trials is less than the percent_correct_required
        while len(trial_outcome) < eval_win or sum(trial_outcome[-eval_win:])/eval_win < percent_correct_required/100:

            # Entry by licking into 'up' (if not timeout before = (entry_response is not None))
            print(f"\n>>> Wait for initiating licking... iteration: {len(trial_outcome)-1}.")
            entry_times.append([])
            while entry_response is None:
                entry_response = self.wait_for_lickometer(['up'], timeout=enter_timeout_s)

                if not self.lickemu and entry_response == 'up':
                    self.bridge_reward()
                    # TODO: after wrong jump, no reward?
                    self.lick_o_meter.reward('up')
                    print(f"licked at {entry_response}, entry response")

                if entry_response is None:
                    self.punish()
                    print(f"\n PUSH CAT HEAD GENTLY TOWARDS LICKOMETER!\n")

                entry_times[-1].append(trialclock.getTime())
            entry_response = None  # reset so that licking into 'up' lickometer is required in next trial again

            trialclock.reset()
            m_press = [0, 0]  # initialize screen responses

            # one screen gray full field, other screen: grating
            [sv.draw() for sv in t_stim.values()]
            [self.win[sk1].flip() for sk1 in win_keys if self.win[sk1] is not None]  # show phase 0 of moving grating

            # wait for touch on screens
            print(f"\n>>> Training loop, iteration: {len(trial_outcome)-1}.")
            while (trial_time_elapsed < jump_within_s) and not any(m_press):
                """
                After no-jump trials we punish, wait 3s and restart next trial without wait_for_lickometer
                """

                # maybe needed if a real mouse is used instead of IR screen: m_press = [0, 0]
                [self.mouse[k1].setPos(fix_pos) for k1 in win_keys]  # set to outside screen so that actual touch represents a big change between current mouse position and the touch coordinate
                m_loc = [self.mouse[sk1].getPos() for sk1 in win_keys]

                for sk in win_keys:
                    # move grating (const or vibrate) until a specified time
                    ctime = trialclock.getTime()

                    # move grating at the beginning and halfway to timeout
                    if ctime < motion_time or jump_within_s/2 < ctime < jump_within_s/2+motion_time:
                        t_stim[sk].phase = numpy.mod(trialclock.getTime(), 1)

                    [sv.draw() for sv in t_stim.values()]
                    [self.win[sk1].flip() for sk1 in win_keys if self.win[sk1] is not None]

                    # read touches
                    m_press = self.is_touched(t_stim, m_loc)

                    if any(m_press) and not all(m_press):
                        break

                    trial_time_elapsed = trialclock.getTime()

            [sv.draw() for sv in gray_stim.values()]  # after cat jumps or timeout: switch both screens to gray
            [self.win[sk1].flip() for sk1 in win_keys if self.win[sk1] is not None]

            print(f">>> Result:")

            # Evaluation of response
            j_choice = 'left' if m_press[0] else 'right'
            print(f"j_choice: {j_choice}, t_stim[j_choice].name: {t_stim[j_choice].name}")

            # add fail trial and punish if timeout, it has to restart from licking into the 'up' lickometer
            if trial_time_elapsed > jump_within_s:
                self.punish()

                trial_outcome.append(False)
                trial_times.append(trialclock.getTime())

                print("timeout, you are too slow...")

                # in next trial, do not wait for entry response
                entry_response = ''

            # add fail trial and punish if jumped to non-target
            elif t_stim[j_choice].name != 'grating':
                self.punish()

                trial_outcome.append(False)
                trial_times.append(trialclock.getTime())

                print(f"bad choice")

            # add success trial if jumped within time, has to restart from 'up' lickometer
            else:
                self.bridge_reward()

                trial_outcome.append(True)
                trial_times.append(trialclock.getTime())

                print("good job, level up")

                # active rewarding: reward delivered only if cat licks
                jump_rew_response = self.wait_for_lickometer([j_choice], timeout=enter_timeout_s)
                if jump_rew_response == j_choice:
                    self.deliver_reward(jump_rew_response)
                core.wait(1)

            t_stim = random_training_stim(stim_list, win_keys)
            # TODO: add timing parameter to wait()
            core.wait(0.1)
            trialclock.reset()
            trial_time_elapsed = trialclock.getTime()

        print(f"Trial successes: {trial_outcome} --> percent correct: {sum(trial_outcome[-eval_win:])/eval_win}\n"
              f"\t>>> result: {sum(trial_outcome[-eval_win:])/eval_win >= percent_correct_required/100}\n"
              f"Trial completed (s): {trial_times}\n Trial init times (up lick):{entry_times}")

        return trial_outcome, trial_times, entry_times

    def init_output(self, motion):
        """
        Create all output files and read input files.

        Parameters
        ----------
        motion : dict
            Time variables used for motion control.

        Returns
        -------
        expInfo, dataFile, fileName
        """

        # TODO: include train_jumping files too (?)
        # try to get a previous parameters file
        try:
            expInfo = fromFile('lastParams.pickle')
        # if not there then use a default set
        except:
            expInfo = {'observer': 'jwp', 'motion_duration': motion['duration_max_s']}

        expInfo['dateStr'] = data.getDateStr()  # add the current time

        # present a dialogue to change params
        if 0:
            dlg = gui.DlgFromDict(expInfo, title='motion duration experiment', fixed=['dateStr'])
        if 1:  # dlg.OK:
            toFile('lastParams.pickle', expInfo)  # save params to file for next time
        else:
            core.quit()  # the user hit cancel so exit
    
        # make a text file to save data
        fileName = expInfo['observer'] + expInfo['dateStr']
        dataFile = open(fileName + '.csv', 'w')  # a simple text file with 'comma-separated-values'
        dataFile.write('targetOri,jumpedOri,motionTime,correct\n')

        return expInfo, dataFile, fileName

    def init_stimulus(self):
        """
        Initiate stimuli

        Define required parameters for stimuli generation and stimuli timing.

        Returns
        -------
        grating : dict
            Stimuli in a dictionary where keys are sides.
        messages : dict or None
            All text shown on screens in a dictionary (pre, trial, post) if self.show_messages.
            Else None
        time_dict : dict
            Jump & lick timeouts and message duration.
        intertrial : dict
            Gray screens (stimuli)
        trial_clock : psychopy.core.Clock()

        motion : dict
            Stimuli motion controlling parameters.
        orientation : dict
            Target and alternative stimulus's orientation.
        """

        # Parameters
        motion = {'duration_max_s': 3, 'speed_cycles_per_second': 0.5}
        time_dict = {'jump_timeout': motion['duration_max_s'] + 3,
                     'message': 0.5,
                     'lick_timeout': 2}

        # target is rewarded, alternative is not rewarded
        orientation = {'target': 0, 'alternative': 90}

        grating = {sk1: visual.GratingStim(self.win[sk1], sf=self.grating_p['spatial_freq_deg_per_pix'],
                                           size=self.grating_p['size'][sk1], pos=self.grating_p['pos'][sk1], mask='gauss',
                                           ori=orientation[k1],) for k1, sk1 in zip(orientation.keys(), self.win.keys())}

        if not self.windowed:
            for sk1 in self.win.keys():
                size1 = [ss1*0.1 for ss1 in self.win[sk1].size]
                # size2: make stimulus size greater
                min_size = min([ss1 for ss1 in self.win[sk1].size])
                size2 = [min_size, min_size]
                grating[sk1].setSize(size2, units='pix')

        from psychopy.tools.monitorunittools import posToPix
        ptxt = ' '.join([repr(posToPix(grating[gk1])) for gk1 in grating.keys()])
        print(f"grating positions {ptxt}")
    
        intertrial = {sk1: visual.GratingStim(self.win[sk1], sf=0, color=0, colorSpace='rgb',
                                              size=self.win[sk1].size[0], tex=None,) for sk1 in self.win.keys()}
    
        # and some handy clocks to keep track of time
        trial_clock = core.Clock()
    
        # display instructions and wait
        if self.show_messages:
            trialtext = 'Hit left key if you think correct pattern is shown on the left side; right key if correct pattern is on right side.'
            messages = {'pre': visual.TextStim(self.win['left'], pos=[0, +3],
                                           text='Hit up arrow key to start trial within 3s, q to abort experiment'),
                    'trial': visual.TextStim(self.win['left'], pos=[0, +3], text=trialtext),
                    'post': visual.TextStim(self.win['left'], pos=[0, +3], text='Put back animal to stand')}
        else:
            messages = None
    
        return grating, messages, time_dict, intertrial, trial_clock, motion, orientation
    
    def run_staircase(self, up_steps=1, down_steps=3):
        """"""

        grating, messages, time_dict, intertrial, trial_clock, motion, orientation = self.init_stimulus()
        # TODO: rearrange code?: move init_output() out if this function to use in train_jumping too
        expInfo, dataFile, fileName = self.init_output(motion)
    
        # create the staircase handler
        staircase = data.StairHandler(startVal = motion['duration_max_s'],
                                  stepType = 'db', stepSize=8, minVal=0,
                                  nUp=up_steps, nDown=down_steps,  # will home in on the 80% threshold
                                  nTrials=3, # nTrials means at least this many time the parameter will change even if all responses are correct
                                  nReversals=3)

        # will continue the staircase until it terminates!
        for thisIncrement in staircase:
            # Show stimulus and let subject make a choice (mouse/touch screen response)
            time_dict['motion'] = thisIncrement
            print(f"--------\ntrial {len(staircase.data)}, motion time: {thisIncrement}, staircase trial {staircase.thisTrialN} reversals {len(staircase.reversalIntensities)}")

            result = None  # initialize to non-defined so that staircase is updated only after checking all possible outcomes

            # Run 2AFC trial
            mouse_choice, choice_time_s = self.iterate_motion_time_grating_2afc(grating, messages, time_dict, trial_clock)

            # did not jump within allowed time interval
            if choice_time_s >= time_dict['jump_timeout']:
                self.punish()
                [intertrial[sk1].draw() for sk1 in intertrial.keys()]
                if messages:
                    messages['post'].text = f"Jump timeout, make your choice faster"
                core.wait(1)
                continue
    
            print(f"mouse clicked {mouse_choice}")

            # remove patterns from screen upon jump
            [i1.draw() for i1 in intertrial.values()]
            [w.flip() for w in self.win.values()]
            jump_choice = 'left' if mouse_choice[0] else 'right'

            # Provide bridge reward for correct mouse click/touchscreen choice
            if grating[jump_choice].ori != orientation['target']:
                # if wrong choice, no need to wait for lickometer
                self.punish()
                result = 0
                print(f'\t>>> jumped on wrong side, mouse_clicked --> jump_choice = {mouse_choice} --> {jump_choice}')
            else: # jumped to correct side
                self.bridge_reward()
                lick_choice = self.wait_for_lickometer([jump_choice], time_dict['lick_timeout'])  # now has to lick at same side
                print(f"licked at {lick_choice} while {jump_choice} was enabled")
    
                # evaluate lick response
                if lick_choice is not None:
                    if lick_choice not in grating:  # this should not happen, can happen in emulation mode when user clicks a non-valid response key
                        self.punish()
                        continue
                    if lick_choice != jump_choice:  # should not normally happen
                        if messages: messages['post'].text = f"Oups, you landed on one side and lickometer on the other side? Hit any key or q to exit"
                        self.punish()
                        core.wait(1)
                        # ignore this trial
                        continue
    
                    # only accept lick from lickometer that is next to the screen where cat jumped, if lick event in other lickometer-> punish
                    if grating[lick_choice].ori != orientation['target']:
                        self.punish()
                        if messages: messages['post'].text = f"Beeee! Wrong choice. Hit any key or q to exit"
                        result = 0
                    else:
                        self.deliver_reward(lick_choice)
                        if messages: messages['post'].text = f"Yipie! Correct choice. Hit any key or q to exit"
                        result = 1
                else:  # subject did not lick within given time. Accept good choice silently but also punish to coerce doing the whole sequence.
                    result = 1
                    if messages: messages['post'].text = f"Correct choice but no lick. No need for food? Hit any key or q to exit"
    
            staircase.addResponse(result)
            dataFile.write(f"{orientation['target']},{grating[jump_choice].ori},{thisIncrement},{grating[jump_choice].ori == orientation['target']}\n")
            print(f"left:{grating['left'].ori} right:{grating['right'].ori}")
            # blank screen
            [intertrial[sk1].draw() for sk1 in intertrial]
            if messages: messages['post'].draw()
            [w.flip() for w in self.win.values()]
            allKeys = event.waitKeys(maxWait=time_dict['message'])
            if allKeys is not None and 'q' in allKeys:
                print('user abort')
                core.quit()  # manual abort experiment
            event.clearEvents()  # clear other (e.g. mouse) events - they clog the buffer
    
        # staircase has ended
        dataFile.close()
        staircase.saveAsPickle(fileName)  # special python binary file to save all the info
    
        # give some output to user in the command line in the output window
        print('reversals:')
        print(staircase.reversalIntensities)
        approxThreshold = numpy.average(staircase.reversalIntensities[-6:])
        print('mean of final reversals = %.3f' % (approxThreshold))
    
        # give some on-screen feedback
        feedback1 = visual.TextStim(self.win['left'], pos=[0,+3], text='mean of final 6 reversals = %.3f' % (approxThreshold))
    
        feedback1.draw()
    
        self.win['left'].flip()
        core.wait(1)
        [w.close() for w in self.win.values()]
        core.quit()
    

def random_training_stim(stim_list: list, win_keys: list):
    """
    Randomly swap training stimulus

    Parameters
    ----------
    stim_list : list
        Set of stimuli
    win_keys : list
        Windows keys

    Returns
    -------
    dict : {k: stim_list[i][k] for i, k in enumerate(win_keys)}
    """

    if random.choice([0, 1]):
        s1 = stim_list[0]
        stim_list[0] = stim_list[1]
        stim_list[1] = s1

    return {k: stim_list[i][k] for i, k in enumerate(win_keys)}


def random_swap(previous: dict):
    """
    Randomly swap dictionary's values

    Parameters
    ----------
    previous: dict with two keys

    Returns
    -------
    dict with values swapped in a random fashion (i.e. sometimes swapped, other times left as is)
    """

    if random.choice([0, 1]):
        dkeys = list(previous.keys())
        r_temp = previous[dkeys[0]].ori
        previous[dkeys[0]].ori = previous[dkeys[1]].ori
        previous[dkeys[1]].ori = r_temp

    return previous


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        prog='MotionTrainer',
        description='2AFC training for cats',
        epilog='written by D Hillier, G Schliszka (c) 2022-2023')
    parser.add_argument('--lickometer','-L', help='Use lickometers', action='store_false')
    parser.add_argument('--windowed', '-W', help='Show stimulus in smaller window, not full screen.', action='store_true')
    args = parser.parse_args()
    lickemu = not args.lickometer #not args.lickometer
    # teaching task:
    # level 1: no waiting time enforced after licking 'up' (lickometer on the jump stand)
    train_basic_task = False
    n_down = 6 if train_basic_task else 3
    n_up = 2 if train_basic_task else 1
    experiment = TwoAFC(lickemu=lickemu, touchscreen=True, show_messages=False, windowed=args.windowed)
    stair_params = {'up_steps': n_up, 'down_steps': n_down}

    experiment.train_jumping(jump_within_s=3, percent_correct_required=80, enter_timeout_s=3)
    experiment.run_staircase(**stair_params)

