'''Decrease motion duration while teaching animal to discriminate vertical vs horizontal orientation.
This code assumes animal knows lickometer and jump stand.
'''
import time

from psychopy import prefs
import pyglet
prefs.general['winType']=pyglet
prefs.validate()
from psychopy import core, visual, gui, data, event, sound, monitors
from psychopy.tools.filetools import fromFile, toFile
import numpy
import random
import pytest
try:
    import lickometer
    lickemu = 0
    trialtext = ''
except:
    lickemu = 1
# lickemu = 1

if lickemu:
    print('emulation mode')
    win_size = {'height': 600, 'width': 600}
    # split single screen in half
    grating_size = {gk1: 20 for gk1 in ['left', 'right']}
    grating_pos = {'left': (0,0), 'right': (0,0)}
    win_pos = {'left': (0, 10), 'right': (800, 10)}
    feedback_sound = {'reward': sound.Sound('A'), 'punish': sound.Sound('pinknoise.wav', stopTime=1)}
    trialtext = 'Hit left key if you think correct pattern is shown on the left side; right key if correct pattern is on right side.'

if not lickemu:
    print('real mode')
    win_size = {'height': 600, 'width': 600}
    # split single screen in half
    grating_size = {gk1: 20 for gk1 in ['left', 'right']}
    grating_pos = {'left': (0,0), 'right': (0,0)}
    win_pos = {'left': (0, 10), 'right': (800, 10)}
    feedback_sound = {'reward': sound.Sound('A'), 'punish': sound.Sound('pinknoise.wav', stopTime=1)}
    trialtext = 'Hit left key if you think correct pattern is shown on the left side; right key if correct pattern is on right side.'
    try:
        lick_o_meter = lickometer.Protocol()
    except:
        print('No lickometer found, quit')
        core.quit()


def punish():
    feedback_sound['punish'].stop()
    feedback_sound['punish'].play()
    if not lickemu:
        lick_o_meter.punish()


def deliver_reward(side: str):
    feedback_sound['reward'].stop()
    feedback_sound['reward'].play()
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

    '''
    kopt = ['left', 'right', 'up']
    print(f"Waiting for lick for {timeout} seconds")
    if lickemu:  # wait for mouse press
        key = event.waitKeys(maxWait=timeout, clearEvents=True)  # wait for participant to respond
        print(key)
        # either no key hit (timeout) or key is not left/right/up or key is not enabled
        if key is None or not any([k1 in key for k1 in kopt]) or any([k2 not in enabled_lickometers for k2 in key]):
            event.clearEvents()
            if any([k2 not in enabled_lickometers for k2 in key]):
                # punish if subject activates wrong (not enabled) lickometer
                punish()
                print(f'wrong: {key[-1]}')
                return key[-1]  # since it was a lick, return it
            print('none key detected')
            return  # there was no lick, timeout
        event.clearEvents()
        print(f'good: {key[-1]}')
        return key[-1]
    else:
        # TODO: Gazsi please complete
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
   dict with values swapped in a random fashion (ie. sometimes swapped sometimes left as is)

    """
    if random.choice([0, 1]):
        dkeys = list(previous.keys())
        r_temp = previous[dkeys[0]].ori
        previous[dkeys[0]].ori = previous[dkeys[1]].ori
        previous[dkeys[1]].ori = r_temp
    return previous


def iterate_motion_time_grating_2afc(win, grating, mouse, messages, message_time, trial_clock, motion_time, timeout_time):
    if messages: messages['pre'].draw()
    [win[sk1].flip() for sk1 in win.keys() if win[sk1] is not None]
    core.wait(message_time)
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
    core.wait(message_time)
    # show moving grating on both screens
    trial_clock.reset()
    mpress = [0,0]
    while (trial_clock.getTime() < timeout_time) and not any(mpress):
        for sk in grating.keys():
            # move grating until specified time then leave last grating phase constant until timeout time
            if trial_clock.getTime() < motion_time:
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
    dataFile.write('targetSide,oriIncrement,correct\n')
    return expInfo, dataFile, fileName


def init_stimulus(show_messages=False):
    # Parameters
    motion = {'duration_max_s': 3, 'speed_cycles_per_second': 0.5}
    timeout_time = motion['duration_max_s'] + 3

    sf = 0.1  # cycles/visual degree
    orientation = {'target': 0, 'alternative': 90}  # target is rewarded, alternative is not rewarded

    # create window and stimuli
    # TODO : monitor objects?
    if lickemu:
        mon = monitors.Monitor('Samsung_LE40C530', distance=40, width=47.0, currentCalib={'sizePix': (1920, 1080)})
        win = {sk1: visual.Window([win_size['width'], win_size['height']], allowGUI=True, screen=0,
                                  monitor=mon, units='deg', pos=win_pos[sk1]) for si1, sk1 in
               enumerate(grating_size.keys())}  # emulation mode on single screen
        mouse = {wk1: event.Mouse(win=win[wk1]) for wk1 in win.keys()}
    else:
        win = {sk1: visual.Window([win_size['width'], win_size['height']], allowGUI=True, screen=0,
                                  monitor='testMonitor', units='deg', pos=win_pos[sk1]) for si1, sk1 in
               enumerate(grating_size.keys())}  # fullscr=True: use only if you have 3 screens or working q event!
        mouse = {wk1: event.Mouse(win=win[wk1]) for wk1 in win.keys()}
        # raise NotImplementedError('add creation of two windows')

    sk = ['left', 'right']  # screen keys
    grating = {sk1: visual.GratingStim(win[sk1], sf=sf, size=grating_size[sk1], pos=grating_pos[sk1], mask='gauss',
                                       ori=orientation[k1]) for k1, sk1 in zip(orientation.keys(), sk)}
    from psychopy.tools.monitorunittools import posToPix
    ptxt = ' '.join([repr(posToPix(grating[gk1])) for gk1 in grating.keys()])
    print(f"grating positions {ptxt}")

    intertrial = visual.GratingStim(win['left'], sf=0, color=-1, colorSpace='rgb', size=win_size['width'], tex=None, )

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
    message_time = 1.5
    return win, grating, mouse, messages, message_time, intertrial, trial_clock, motion, orientation, timeout_time


def run_staircase():
    win, grating, mouse, messages, message_time, intertrial, trial_clock, motion, orientation, timeout_time = init_stimulus(show_messages=True)
    expInfo, dataFile, fileName = init_experiment(motion)

    # create the staircase handler
    staircase = data.StairHandler(startVal = motion['duration_max_s'],
                              stepType = 'db', stepSize=[8,4,2], minVal=0.1,
                              nUp=1, nDown=3,  # will home in on the 80% threshold
                              nTrials=1, nReversals=2)

    for thisIncrement in staircase:  # will continue the staircase until it terminates!

        mouse_choice, choice_time_s = iterate_motion_time_grating_2afc(win, grating, mouse, messages, message_time, trial_clock, thisIncrement, timeout_time)

        if choice_time_s >= timeout_time:
            punish()
            if messages:
                messages['post'].text = f"Timeout, make your choice faster"
            core.wait(1)
            continue

        # This should not happen but best to be in control: if subject activates lickometer on the other side->punish
        enable_lickometer = 'left' if mouse_choice[0] else 'right'
        # TODO : only accept lick from lickometer that is next to the screen where cat jumped, if lick event in other lickometer-> punish
        lick_choice = wait_for_lickometer([enable_lickometer])
        print(f"licked at {lick_choice} while {enable_lickometer} was enabled")

        if lick_choice is not None:  # subject did respond
            if grating[lick_choice].ori != orientation['target'] or lick_choice != enable_lickometer:
                punish()
                if lick_choice != enable_lickometer:
                    if messages:
                        messages['post'].text = f"Oups, you landed on one side and lickometer on the other side? Hit any key or q to exit"
                        core.wait(1)
                    # ignore this trial
                    continue
                else:
                    if messages: messages['post'].text = f"Beeee! Wrong choice. Hit any key or q to exit"
                    staircase.addResponse(0)
            else:
                deliver_reward(lick_choice)
                if messages: messages['post'].text = f"Yipie! Correct choice. Hit any key or q to exit"
                staircase.addResponse(1)
            dataFile.write(f"{orientation['target']},{thisIncrement}, {grating[lick_choice].ori}")
        print(f"left:{grating['left'].ori} right:{grating['right'].ori}")
        # blank screen
        intertrial.draw()
        if messages: messages['post'].draw()
        [win[sk1].flip() for sk1 in win.keys() if win[sk1] is not None]
        allKeys = event.waitKeys(maxWait=message_time)
        if allKeys is not None and 'q' in allKeys:
            print('user abort')
            core.quit()  # manual abort experiment
        event.clearEvents()  # clear other (eg mouse) events - they clog the buffer

    # staircase has ended
    dataFile.close()
    staircase.saveAsPickle(fileName)  # special python binary file to save all the info

    # give some output to user in the command line in the output window
    print('reversals:')
    print(staircase.reversalIntensities)
    approxThreshold = numpy.average(staircase.reversalIntensities[-6:])
    print('mean of final reversals = %.3f' % (approxThreshold))

    # give some on-screen feedback
    feedback1 = visual.TextStim(
            win['left'], pos=[0,+3],
            text='mean of final 6 reversals = %.3f' % (approxThreshold))

    feedback1.draw()

    win['left'].flip()
    core.wait(1)
    win['left'].close()
    core.quit()


if __name__ == '__main__':
    run_staircase()

