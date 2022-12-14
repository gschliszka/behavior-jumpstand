'''Decrease motion duration while teaching animal to discriminate vertical vs horizontal orientation.
This code assumes animal knows lickometer and jump stand.
'''
import pdb
import time
import uuid
from psychopy import sound, monitors
import numpy
import random
import pytest
from screeninfo import get_monitors
detected_monitors = get_monitors()

try:
    import lickometer
    lick_o_meter = lickometer.Protocol()
    lickemu = 0
    trialtext = ''
except:
    lickemu = 1
# lickemu = 1
computer = uuid.getnode()
print(f"Running on computer with mac address: {computer}")
if computer == 1:
    # jump stand with two monitors
    monitor_params = {'distance_cm': 40}
    screen_ids = (0, 0) if len(detected_monitors) == 1 else (1, 0)
elif computer == 93181002139480:
    # 2pgoe
    monitor_params = {'distance_cm': 40}
    # set screen_id so that left screen is physically on the left side
    screen_ids = (1, 0)
else:
    mon = monitors.Monitor('testmonitor')
    screen_ids = (0, 0) if len(detected_monitors) == 1 else (1, 0)
mon={}
for i1, k1 in zip(range(len(detected_monitors)), ['left','right']):
    mon[k1] = monitors.Monitor(detected_monitors[i1].name, width=detected_monitors[i1].width_mm/10, distance=monitor_params['distance_cm'])
    mon[k1].setSizePix((detected_monitors[i1].width, detected_monitors[i1].height))

if lickemu:
    print('emulation mode')
    win_size = {'height': 600, 'width': 600}
    # split single screen in half
    grating_size = {gk1: 20 for gk1 in ['left', 'right']}
    grating_pos = {'left': (0,0), 'right': (0,0)}
    win_pos = {'left': (0, 10), 'right': (800, 10)}
    trialtext = 'Hit left key if you think correct pattern is shown on the left side; right key if correct pattern is on right side.'
else:
    print('real mode')
    win_size = {'height': 600, 'width': 600}
    # split single screen in half
    grating_size = {gk1: 20 for gk1 in ['left', 'right']}
    grating_pos = {'left': (0,0), 'right': (0,0)}
    win_pos = {'left': (0, 10), 'right': (800, 10)}
    trialtext = 'Hit left key if you think correct pattern is shown on the left side; right key if correct pattern is on right side.'
feedback_sound = {'reward': sound.Sound('mixkit-gaming-lock-2848.wav'), 'punish': sound.Sound('pinknoise.wav', stopTime=0.6)}

from psychopy import core, visual, gui, data, event
from psychopy.tools.filetools import fromFile, toFile
# create window(s): if only one screen detected, use the same screen for both 'left' and 'right' stimulus windows
win = {sk1: visual.Window([win_size['width'], win_size['height']], allowGUI=True, screen=si1,
                                  monitor=mon[sk1], units='deg', pos=win_pos[sk1]) for si1, sk1 in
               zip(screen_ids,grating_size.keys())}  # emulation mode on single screen
mouse = {wk1: event.Mouse(win=win[wk1]) for wk1 in win.keys()}

def punish():
    feedback_sound['punish'].stop()
    feedback_sound['punish'].play()
    if not lickemu:
        lick_o_meter.punish()

def bridge_reward():
    """
    Emits positive reinforcement sound.
    """
    feedback_sound['reward'].stop()
    feedback_sound['reward'].play()

def deliver_reward(side: str):
    """ Delivers reward with lickometer """
    bridge_reward()
    if not lickemu:
        lick_o_meter.reward(side)

def wait_for_lickometer(enabled_lickometers:list, timeout=float('inf')):
    '''

    Parameters
    ----------
    id: which lickometer response is valid. possible options 'up', 'left', 'right'
    timeout: in seconds, will return with None if no lick event occurred.

    Returns
    -------
    str: which lickometer the subject was licking into
    '''
    kopt = ['left', 'right', 'up']
    print(f"Waiting for lick for {timeout} seconds")
    if lickemu:  # wait for mouse press
        tc = core.Clock()
        print(f"started! {tc.getTime()}")
        key = event.waitKeys(maxWait=timeout, clearEvents=True)  # wait for participant to respond
        print(f"Got {key}, timeout {timeout}")
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
    else:
        # TODO: Gazsi are lickometers always enabled? If not some unexpected results can occur (e.g. experimenter forgets to wait until cat licks and puts back to stand
        # if cat licks into non-valid lickometers, give punishment
        licks = lick_o_meter.watch_licks(enabled_lickometers[0])
        if licks == '100':
            return 'up'
        elif licks == '010':
            return 'left'
        elif licks == '001':
            return 'right'
        else:
            return None


def random_swap(previous:dict):
    """

   Parameters
   ----------
   previous: dict with two keys

   Returns
   -------
   dict with values swapped in a random fashion (i.e. sometimes swapped, othertimes left as is)

    """
    if random.choice([0, 1]):
        dkeys = list(previous.keys())
        r_temp = previous[dkeys[0]].ori
        previous[dkeys[0]].ori = previous[dkeys[1]].ori
        previous[dkeys[1]].ori = r_temp
    return previous


def iterate_motion_time_grating_2afc(win, grating, mouse, messages, time_dict, trial_clock):
    if messages: messages['pre'].draw()
    [win[sk1].flip() for sk1 in win.keys() if win[sk1] is not None]
    core.wait(time_dict['message'])

    # keep screens blank until subject licks into lickometer on the stand
    entry_response = wait_for_lickometer(['up'])
    if not lickemu and entry_response == 'up':
        lick_o_meter.reward('up')
    print(f"licked at {entry_response}, entry response")

    # animal licked into stand-lickometer: show stimulus
    # set orientation of gratings on two screens
    random_swap(grating)

    # set duration of motion as the staircase sets the next value
    if messages: messages['trial'].draw()
    [win[sk1].flip() for sk1 in win.keys() if win[sk1] is not None]
    core.wait(time_dict['message'])
    # show moving grating on both screens
    trial_clock.reset()
    mpress = [0,0]
    while (trial_clock.getTime() < time_dict['jump_timeout']) and not any(mpress):
        for sk in grating.keys():
            # move grating until specified time then leave last grating phase constant until timeout time
            if trial_clock.getTime() < time_dict['motion']:
                grating[sk].phase = numpy.mod(trial_clock.getTime(), 1)
            grating[sk].draw()
            mpress = [mouse[k1].isPressedIn(grating[k1]) for k1 in grating.keys()]
            time.sleep(0.01)
            # mouse[sk].isPressedIn(grating[sk])
            if any(mpress):
                break
        [win[sk1].flip() for sk1 in win.keys() if win[sk1] is not None]

    return mpress, trial_clock.getTime()  # [True False] if first screen chosen


def init_experiment(motion):

    try:  # try to get a previous parameters file
        expInfo = fromFile('lastParams.pickle')
    except:  # if not there then use a default set
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


def init_stimulus(show_messages=False):
    # Parameters
    motion = {'duration_max_s': 3, 'speed_cycles_per_second': 0.5}
    time_dict = {'jump_timeout': motion['duration_max_s'] + 3,
                 'message': 0.5,
                 'lick_timeout': 2}

    sf = 0.1  # cycles/visual degree
    orientation = {'target': 0, 'alternative': 90}  # target is rewarded, alternative is not rewarded

    grating = {sk1: visual.GratingStim(win[sk1], sf=sf, size=grating_size[sk1], pos=grating_pos[sk1], mask='gauss',
                                       ori=orientation[k1]) for k1, sk1 in zip(orientation.keys(), win.keys())}
    from psychopy.tools.monitorunittools import posToPix
    ptxt = ' '.join([repr(posToPix(grating[gk1])) for gk1 in grating.keys()])
    print(f"grating positions {ptxt}")

    intertrial = {sk1: visual.GratingStim(win[sk1], sf=0, color=0, colorSpace='rgb', size=win_size['width'], tex=None,) for sk1 in win.keys()}

    # and some handy clocks to keep track of time
    trial_clock = core.Clock()

    # display instructions and wait
    if show_messages:
        messages = {'pre': visual.TextStim(win['left'], pos=[0, +3],
                                       text='Hit up arrow key to start trial within 3s, q to abort experiment'),
                'trial': visual.TextStim(win['left'], pos=[0, +3], text=trialtext),
                'post': visual.TextStim(win['left'], pos=[0, +3], text='Put back animal to stand')}
    else:
        messages = None

    return win, grating, mouse, messages, time_dict, intertrial, trial_clock, motion, orientation


def run_staircase(show_messages=False, up_steps=1, down_steps=3):
    win, grating, mouse, messages, time_dict, intertrial, trial_clock, motion, orientation = init_stimulus(show_messages=show_messages)
    expInfo, dataFile, fileName = init_experiment(motion)

    # create the staircase handler
    staircase = data.StairHandler(startVal = motion['duration_max_s'],
                              stepType = 'db', stepSize=[8,4,2], minVal=0.1,
                              nUp=up_steps, nDown=down_steps,  # will home in on the 80% threshold
                              nTrials=1, nReversals=2)

    for thisIncrement in staircase:  # will continue the staircase until it terminates!
        # Show stimulus and let subject make a choice (mouse/touch screen response)
        time_dict['motion'] = thisIncrement
        result = None  # initialize to non-defined so that staircase is updated only after checking all possible outcomes
        mouse_choice, choice_time_s = iterate_motion_time_grating_2afc(win, grating, mouse, messages, time_dict, trial_clock)

        if choice_time_s >= time_dict['jump_timeout']:  # did not jump within allowed time interval
            punish()
            [intertrial[sk1].draw() for sk1 in intertrial.keys()]
            if messages:
                messages['post'].text = f"Jump timeout, make your choice faster"
            core.wait(1)
            continue

        print(f"mouse clicked {mouse_choice}")
        jump_choice = 'left' if mouse_choice[0] else 'right'
        # Provide bridge reward for correct mouse click/touchscreen choice
        if grating[jump_choice].ori != orientation['target']:
            # if wrong choice, no need to wait for lickometer
            punish()
            result = 0
        else: # jumped to correct side
            bridge_reward()
            lick_choice = wait_for_lickometer([jump_choice], time_dict['lick_timeout'])  # now has to lick at same side
            print(f"licked at {lick_choice} while {jump_choice} was enabled")

            # evaluate lick response
            if lick_choice is not None:
                if lick_choice not in grating:  # this should not happen, can happen in emulation mode when user clicks a non-valid response key
                    punish()
                    continue
                if lick_choice != jump_choice:  # should not normally happen
                    if messages: messages['post'].text = f"Oups, you landed on one side and lickometer on the other side? Hit any key or q to exit"
                    punish()
                    core.wait(1)
                    # ignore this trial
                    continue

                # only accept lick from lickometer that is next to the screen where cat jumped, if lick event in other lickometer-> punish
                if grating[lick_choice].ori != orientation['target']:
                    punish()
                    if messages: messages['post'].text = f"Beeee! Wrong choice. Hit any key or q to exit"
                    result = 0
                else:
                    deliver_reward(lick_choice)
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
        [win[sk1].flip() for sk1 in win.keys()]
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
    feedback1 = visual.TextStim(win['left'], pos=[0,+3], text='mean of final 6 reversals = %.3f' % (approxThreshold))

    feedback1.draw()

    win['left'].flip()
    core.wait(1)
    [win[sk1].close() for sk1 in win]
    core.quit()


if __name__ == '__main__':
    # teaching task:
    # level 1: no waiting time enforced after licking 'up' (lickometer on the jump stand)
    train_basic_task = True
    n_down = 6 if train_basic_task else 3
    n_up = 2 if train_basic_task else 1
    run_staircase(show_messages=True, up_steps=n_up, down_steps=n_down)

