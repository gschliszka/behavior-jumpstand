'''Decrease motion duration while teaching animal to discriminate vertical vs horizontal orientation.
This code assumes animal knows lickometer and jump stand.
'''
from psychopy import core, visual, gui, data, event
from psychopy.tools.filetools import fromFile, toFile
import numpy, random
try:
    import lickometer
    lickemu = 0
except:
    lickemu = 1

def wait_for_lickometer(timeout=0):
    if lickemu:  # wait for mouse press
        key = event.waitKeys(maxWait=timeout, clearEvents=True)  # wait for participant to respond
        if key != 'left' and key != 'right':
            core.quit()
        event.clearEvents()
        return key
    else:
        # TODO: Gazsi please complete
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
    swap = random.choice([0, 1])
    if swap:
        dkeys = previous.keys()
        r_temp = previous[dkeys[0]].ori
        previous[dkeys[1]].ori = previous[dkeys[0]].ori
        previous[dkeys[0]].ori = r_temp
    return previous

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
dlg = gui.DlgFromDict(expInfo, title='motion duration experiment', fixed=['dateStr'])
if dlg.OK:
    toFile('lastParams.pickle', expInfo)  # save params to file for next time
else:
    core.quit()  # the user hit cancel so exit

# make a text file to save data
fileName = expInfo['observer'] + expInfo['dateStr']
dataFile = open(fileName+'.csv', 'w')  # a simple text file with 'comma-separated-values'
dataFile.write('targetSide,oriIncrement,correct\n')

# create the staircase handler
staircase = data.StairHandler(startVal = motion['duration_max_s'],
                          stepType = 'lin', stepSize=0.1, minVal=0,
                          nUp=1, nDown=3,  # will home in on the 80% threshold
                          nTrials=1)

# create window and stimuli
win_size = {'height':600, 'width':800}
win = visual.Window([win_size['width'], win_size['height']],allowGUI=True,
                    monitor='testMonitor', units='deg')

sk = ['left', 'right']  # screen keys
grating = {sk1: visual.GratingStim(win, sf=sf, size=win_size['height'], mask='gauss',
                            ori=orientation[k1]) for k1, sk1 in zip(orientation.keys(), sk)}

intertrial = visual.GratingStim(win, sf=0, color = -1, colorsys='rgb', size=win_size['width'], tex=None, )

# and some handy clocks to keep track of time
globalClock = core.Clock()
trialClock = core.Clock()

# display instructions and wait
messages = {'pre': visual.TextStim(win, pos=[0,+3],text='Hit q to abort experiment'),
            'trial': visual.TextStim(win, pos=[0,+3],text='Hit left or right to respond where target is.'),
            'post': visual.TextStim(win, pos=[0,+3],text='Put back animal to stand')}

for thisIncrement in staircase:  # will continue the staircase until it terminates!
    messages['pre'].draw()
    # keep screens blank until subject licks into lickometer on the stand
    entry_response = 'timeout'
    while entry_response == 'timeout':
        entry_response = wait_for_lickometer('stand', timeout=3)

    # animal licked into stand-lickometer: show stimulus
    # set orientation of gratings on two screens
    random_swap(grating)

    # set duration of motion as the staircase sets the next value
    motion_dur = expInfo['motion_duration'] + thisIncrement
    messages['trial'].draw()
    # show moving grating on both screens
    # TODO Abel, please insert here. After motion_dur seconds gratings should stop and stay last phase, return here and wait for full trial duration
    jump_choice = movinggrating(min_time = 0.5, )
    lick_choice = wait_for_lickometer(timeout=remaining_trial_time)


    if grating[lick_choice].ori != orientation['target']:
        punish()
    else:
        deliver_reward()

    # blank screen
    intertrial.draw()
    win.flip()


    allKeys=event.waitKeys()
    if 'q' in allKeys:
        core.quit()  # manual abort experiment
    event.clearEvents()  # clear other (eg mouse) events - they clog the buffer

    # add the data to the staircase so it can calculate the next level
    staircase.addData(thisResp)
    dataFile.write('%i,%.3f,%i\n' %(targetSide, thisIncrement, thisResp))
    core.wait(1)

# staircase has ended
dataFile.close()
staircase.saveAsPickle(fileName)  # special python binary file to save all the info

# give some output to user in the command line in the output window
print('reversals:')
print(staircase.reversalIntensities)
approxThreshold = numpy.average(staircase.reversalIntensities[-6:])
print('mean of final 6 reversals = %.3f' % (approxThreshold))

# give some on-screen feedback
feedback1 = visual.TextStim(
        win, pos=[0,+3],
        text='mean of final 6 reversals = %.3f' % (approxThreshold))

feedback1.draw()
fixation.draw()
win.flip()

win.close()
core.quit()
