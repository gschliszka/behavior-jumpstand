'''Decrease motion duration while teaching animal to discriminate vertical vs horizontal orientation.
This code assumes animal knows lickometer and jump stand.
'''
from psychopy import prefs
import pyglet
prefs.general['winType']=pyglet
prefs.validate()
from psychopy import core, visual, gui, data, event, sound
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
lickemu = 1

if lickemu:
    print('emulation mode')
    win_size = {'height': 600, 'width': 800}
    # split single screen in half
    grating_size = {gk1: 20 for gk1 in ['left', 'right']}
    grating_pos = {'left': (-5,0), 'right': (5,0)}
    feedback_sound = {'reward': sound.Sound('A'), 'punish': sound.Sound('pinknoise.wav')}
    trialtext = 'Hit left key if you think correct pattern is shown on the left side; right key if correct pattern is on right side.'

def punish():
    feedback_sound['punish'].play()

def deliver_reward():
    feedback_sound['reward'].play()

def wait_for_lickometer(lickometer_id:list, timeout=float('inf')):
    '''

    Parameters
    ----------
    id: which lickometer response is valid. possible options 'up', 'left', 'right'
    timeout: in seconds, will return with None if no lick event occurred.

    Returns
    -------

    '''
    kopt = ['left', 'right','up']
    print(f"Waiting for lick for {timeout} seconds")
    if lickemu:  # wait for mouse press
        key = event.waitKeys(maxWait=timeout, clearEvents=True)  # wait for participant to respond
        print(key)
        if key is None or not any([k1 in key for k1 in kopt]) or any([k2 not in lickometer_id for k2 in key]):
            event.clearEvents()
            return
        event.clearEvents()
        return key[-1]
    else:
        # TODO: Gazsi please complete
        # if cat licks into non-valid lickometers, give punishment
        return lickometer.lick(timeout)

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

def run_trial():
    # Parameters
    motion = {'duration_max_s': 3, 'speed_cycles_per_second': 0.5}

    sf = 0.1 # cycles/visual degree
    orientation = {'target': 0, 'alternative':90}  # target is rewarded, alternative is not rewarded

    try:  # try to get a previous parameters file
        expInfo = fromFile('lastParams.pickle')
    except:  # if not there then use a default set
        expInfo = {'observer':'jwp', 'motion_duration':motion['duration_max_s']}
    expInfo['dateStr'] = data.getDateStr()  # add the current time
    # present a dialogue to change params
    if 0:
        dlg = gui.DlgFromDict(expInfo, title='motion duration experiment', fixed=['dateStr'])
    if 1: #dlg.OK:
        toFile('lastParams.pickle', expInfo)  # save params to file for next time
    else:
        core.quit()  # the user hit cancel so exit

    # make a text file to save data
    fileName = expInfo['observer'] + expInfo['dateStr']
    dataFile = open(fileName+'.csv', 'w')  # a simple text file with 'comma-separated-values'
    dataFile.write('targetSide,oriIncrement,correct\n')

    # create the staircase handler
    staircase = data.StairHandler(startVal = motion['duration_max_s'],
                              stepType = 'db', stepSize=[8,4,2], minVal=0.1,
                              nUp=1, nDown=3,  # will home in on the 80% threshold
                              nTrials=1, nReversals=2)

    # create window and stimuli
    if lickemu:
        win0 =  visual.Window([win_size['width'], win_size['height']],allowGUI=True,
                        monitor='testMonitor', units='deg', backendConf={'winType':'pyglet'})
        win = {sk1: win0 for sk1 in grating_size.keys()}  # emulation mode on single screen
    else:
        raise NotImplementedError('add creation of two windows')

    sk = ['left', 'right']  # screen keys
    mouse = {k1: event.Mouse(win=win[k1]) for k1 in sk}
    grating = {sk1: visual.GratingStim(win[sk1], sf=sf, size=grating_size[sk1], pos=grating_pos[sk1], mask='gauss',
                                ori=orientation[k1]) for k1, sk1 in zip(orientation.keys(), sk)}
    from psychopy.tools.monitorunittools import posToPix
    ptxt = ' '.join([repr(posToPix(grating[gk1])) for gk1 in grating.keys()])
    print(f"grating positions {ptxt}")

    intertrial = visual.GratingStim(win['left'], sf=0, color = -1, colorSpace='rgb', size=win_size['width'], tex=None, )

    # and some handy clocks to keep track of time
    trial_clock = core.Clock()

    # display instructions and wait
    messages = {'pre': visual.TextStim(win['left'], pos=[0,+3],text='Hit up arrow key to start trial within 3s, q to abort experiment'),
                'trial': visual.TextStim(win['left'], pos=[0,+3],text=trialtext),
                'post': visual.TextStim(win['left'], pos=[0,+3],text='Put back animal to stand')}
    message_time = 1.5
    if lickemu:
        win['right'] = None  # no double flips of the same window if in emulation mode
    for thisIncrement in staircase:  # will continue the staircase until it terminates!
        messages['pre'].draw()
        [win[sk1].flip() for sk1 in win.keys() if win[sk1] is not None]
        core.wait(message_time)
        # keep screens blank until subject licks into lickometer on the stand
        entry_response = 'timeout'
        while entry_response == 'timeout':
            entry_response = wait_for_lickometer(['up'], timeout=3)

        # animal licked into stand-lickometer: show stimulus
        # set orientation of gratings on two screens
        random_swap(grating)

        # set duration of motion as the staircase sets the next value
        motion_dur = expInfo['motion_duration'] + thisIncrement
        print(f"increment {thisIncrement} motion_duration: {expInfo['motion_duration']}")
        messages['trial'].draw()
        [win[sk1].flip() for sk1 in win.keys() if win[sk1] is not None]
        core.wait(message_time)
        # show moving grating on both screens
        # TODO Abel, please insert here. After motion_dur seconds gratings should stop and stay last phase, return here and wait for full trial duration
        trial_clock.reset()

        while trial_clock.getTime() < thisIncrement:
            for sk in grating.keys():
                grating[sk].phase = numpy.mod(trial_clock.getTime(), 1)
                grating[sk].draw()
            [win[sk1].flip() for sk1 in win.keys() if win[sk1] is not None]

        lick_choice = wait_for_lickometer(['left', 'right'])
        print(f"licked {lick_choice}")
        if lick_choice is not None:  # subject did respond
            if grating[lick_choice].ori != orientation['target']:
                punish()
                messages['post'].text = f"Beeee! Wrong choice. Hit any key or q to exit"
                staircase.addResponse(0)
            else:
                deliver_reward()
                messages['post'].text = f"Yipie! Correct choice. Hit any key or q to exit"
                staircase.addResponse(1)
            dataFile.write(f"{orientation['target']},{thisIncrement}, {grating[lick_choice].ori}")
        print(f"left:{grating['left'].ori} right:{grating['right'].ori}")
        # blank screen
        intertrial.draw()
        messages['post'].draw()
        [win[sk1].flip() for sk1 in win.keys() if win[sk1] is not None]
        allKeys=event.waitKeys(maxWait=message_time)
        if allKeys is not None and 'q' in allKeys:
            print('user abort')
            break  # manual abort experiment
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
    run_trial()