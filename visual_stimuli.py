import serial
from math import sqrt, ceil
from psychopy.tools import monitorunittools
from psychopy import monitors, visual, core, event, sound
from monitors import mymonitors


import os
import time
import logging
import pyautogui


class VisualStimulator:
    def __init__(self, params: dict, port: str = None):
        """
        Parent class for all visual stimuli.

        Parameters
        ----------
        params: dictionary containing all the parameters needed for stimulation generation and display.
        port: name of COM port where stimulator PC receives information from recording PC.
        """

        self.params = params
        if port is not None:
            self.port = serial.Serial(port=port, baudrate=9600, timeout=3000)
        self.endExpNow = False  # flag for 'escape' or other condition => quit the exp

        # Set up the psychopy monitor
        self.mon = monitors.Monitor(self.params['monitor'], distance=self.params['distance'],
                                    width=mymonitors[self.params['monitor']]['width'],
                                    currentCalib={'sizePix': mymonitors[self.params['monitor']]['resolution']})

        # Set up the psychopy window
        self.win = visual.Window(size=mymonitors[self.params['monitor']]['resolution'],
                                 fullscr=True, screen=1, allowGUI=False, allowStencil=False,
                                 monitor=self.mon, color=self.params['color_bg'], colorSpace='rgb',
                                 blendMode='avg', useFBO=True)

        # store frame rate of monitor
        self.params['framerate'] = self.win.getActualFrameRate(nMaxFrames=500)
        if self.params['framerate'] is not None:
            self.frameDur = 1.0 / round(self.params['framerate'])
        else:
            self.frameDur = 1.0 / 60.0  # couldn't get a reliable measure so set standard 60 Hz
            self.params['framerate'] = 60
        print(f"Window framerate set to: {self.params['framerate']}")

        """try:
            self.labjack = U3Wrap()
            self.labjack.jack.setDIOState(7, 0)
        except LabJackPython.NullHandleException:
            print("No labjack was found for sending trigger pulse. (NullHandleException)")
        except LabJackPython.LabJackException:
            print("No labjack was found for sending trigger pulse. (LabJackException)")"""

    def wait_for_serial(self):

        """
        @summary: wait for the reception of 'trigger' on the serial port. Once
            it is received, start the visual stimulations.
        """

        val = self.port.read(2)
        val = int.from_bytes(val, byteorder='little')
        print(f"Serial message: {val}")

            
class StaticGratingDual(VisualStimulator):
    def __init__(self, params: dict, stat_params: dict, port: str = None):
        super(StaticGratingDual, self).__init__(params, port)
        self.stat_params = stat_params

        # Set sound cues:
        self.w_sound = sound.backend_sounddevice.SoundDeviceSound(value='C', secs=0.5, octave=6, stereo=-1, volume=1.0,
                                                                  loops=0,
                                                                  sampleRate=44100, blockSize=128, preBuffer=- 1,
                                                                  hamming=True,
                                                                  startTime=0, stopTime=- 1, name='', autoLog=True)

        self.c_sound = sound.backend_sounddevice.SoundDeviceSound(value='C', secs=0.5, octave=5, stereo=-1, volume=1.0,
                                                                  loops=0,
                                                                  sampleRate=44100, blockSize=128, preBuffer=- 1,
                                                                  hamming=True,
                                                                  startTime=0, stopTime=- 1, name='', autoLog=True)
        # Set up the 2nd psychopy monitor
        self.mon2 = monitors.Monitor(self.params['monitor2'], distance=self.params['distance'],
                                     width=mymonitors[self.params['monitor2']]['width'],
                                     currentCalib={'sizePix': mymonitors[self.params['monitor2']]['resolution']})

        # Set up the 2nd psychopy window
        self.win2 = visual.Window(size=mymonitors[self.params['monitor2']]['resolution'],
                                  fullscr=True, screen=2, allowGUI=False, allowStencil=False,
                                  monitor=self.mon2, color=self.params['color_bg'], colorSpace='rgb',
                                  blendMode='avg', useFBO=True)      # screen: set to 2 if 3 monitors used

        # Make win object clear
        self.win_l = self.win2
        self.win_r = self.win

        # Set up mouse and mouse2
        self.mouse_l = event.Mouse(win=self.win_l)  # old: self.mouse2
        self.mouse_r = event.Mouse(win=self.win_r)  # old: self.mouse

        self.states = self.params['orders']

        # Calculating size of monitor in visual degrees, so stimulation covers it completely
        diagonal_in_pix = sqrt(self.mon.getSizePix()[0]**2 + self.mon.getSizePix()[1]**2)
        diagonal_in_deg = ceil(monitorunittools.pix2deg(diagonal_in_pix, self.mon, correctFlat=False))

        self.l_stim = visual.GratingStim(win=self.win_l, name='left', units='deg',
                                         sf=self.params['spatial_frequency'], contrast=self.params['contrast'],
                                         pos=[0, 0], size=(diagonal_in_deg, diagonal_in_deg), tex='sqr', phase=1, ori=0,
                                         colorSpace='rgb', opacity=1, interpolate=False)

        self.r_stim = visual.GratingStim(win=self.win_r, name='right', units='deg',
                                         sf=self.params['spatial_frequency'], contrast=self.params['contrast'],
                                         pos=[0, 0], size=(diagonal_in_deg, diagonal_in_deg), tex='sqr', phase=1, ori=0,
                                         colorSpace='rgb', opacity=1, interpolate=False)

        self.l_green = visual.rect.Rect(self.win_l, width=0.1, height=0.1, units='', lineWidth=1.5, lineColor=None,
                                        lineColorSpace=None, fillColor='green', fillColorSpace=None, pos=(0.0, 0.0),
                                        size=None, anchor=None, ori=0.0, opacity=None, contrast=1.0, depth=-1,
                                        interpolate=True, lineRGB=False, fillRGB=False, name=None, autoLog=None,
                                        autoDraw=False, color=None, colorSpace='rgb')

        self.r_red = visual.rect.Rect(self.win_r, width=0.1, height=0.1, units='', lineWidth=1.5, lineColor=None,
                                      lineColorSpace=None, fillColor='red', fillColorSpace=None, pos=(0.0, 0.0),
                                      size=None, anchor=None, ori=0.0, opacity=None, contrast=1.0, depth=-1,
                                      interpolate=True, lineRGB=False, fillRGB=False, name=None, autoLog=None,
                                      autoDraw=False, color=None, colorSpace='rgb')

        # Set up temporary logger
        current_dir = os.path.dirname(__file__)
        parent_dir = os.path.split(current_dir)[0]
        path = os.path.join(current_dir, 'JumpStandLog')

        name = "Gazsi"
        logging.basicConfig(filename=f"{path}/log_test_{name}_{time.strftime('%Y_%m_%d_%H_%M_%S', time.localtime())}.txt",
                            level=logging.DEBUG, format="%(asctime)s : %(message)s")

        logging.debug(f"{time.strftime('%Y_%m_%d_%H_%M_%S', time.localtime())}")
        logging.debug(self.params['arduino'].version)
        logging.debug(self.params['arduino'].initial_values)

    def start_stim(self, direction: int):
        """
        Start displaying static grating stimulation for JumpStand.

        Parameters
        ----------
        direction: direction of "movement" in degree in the [0, 360) interval on the left monitor.

        Returns
        -------
        None
        """
        logging.debug("")
        state = self.states.CAT

        horizontal_left = (270 - direction == 0)
        side_of_horizontal = 'left' if 270 - direction == 0 else 'right'
        side_of_vertical = 'right' if 270 - direction == 0 else 'left'

        self.params['arduino'].write_order(self.states.SIDE)
        # time.sleep(0.1)
        if horizontal_left:
            self.params['arduino'].write_order(self.states.LEFT)
        else:
            self.params['arduino'].write_order(self.states.RIGHT)
        # time.sleep(0.1)
        print("elotte vok -->>")
        print(self.params['arduino'].read_order())

        print(f'Horizontal stim on <{side_of_horizontal}> side\nVertical stim on <{side_of_vertical}> side')
        print(F"Direction: {direction} --> left horizontal? - {horizontal_left}")

        # logging.debug(f"Horizontal on the left side: {horizontal_left}")
        self.stat_params['left'] += 1 if horizontal_left else 0
        self.stat_params['right'] += 1 if not horizontal_left else 0
        logging.debug(f"Horizontal:<{side_of_horizontal}> Vertical:<{side_of_vertical}>")

        self.r_stim.ori = direction
        self.l_stim.ori = 270 - direction

        offset = self.params['stationary_duration']

        # ------Prepare to start Routine "trial"-------
        self.mouse_l.clickReset(buttons=[0, 1, 2])
        self.mouse_r.clickReset(buttons=[0, 1, 2])

        self.mouse_l.setPos([-1.5, -1.5])
        self.mouse_r.setPos([-1.5, -1.5])

        trial_components = [self.l_stim, self.r_stim]

        # -------Start Routine "trial"-------
        for thisComponent in trial_components:
            if hasattr(thisComponent, "setAutoDraw"):
                thisComponent.setAutoDraw(True)

        print("Press Enter to show stimuli if the cat is ready to jump!")

        continue_routine = True
        left_response = ""
        event.clearEvents()
        while continue_routine:
            # Esc to quit
            if event.getKeys(keyList=["escape"]):
                logging.debug("Esc is pressed --> quit")
                try:
                    self.port.close()
                except AttributeError:
                    print("No COM port to close.")
                core.quit()

            # States:
            if state == self.states.OFF:    # needed only if IR gate is already implemented
                if event.getKeys(keyList=['return']):
                    print(f"State: {state} --> {self.states['CAT']}")
                    state = self.states.CAT

            if state == self.states.CAT:
                if event.getKeys(keyList=['return']):   # key press will be replaced with IR gate signal
                    logging.debug("Enter pressed to show stimuli")
                    state = self.states.RPI

                    self.mouse_l.clickReset()
                    self.mouse_r.clickReset()
                    self.mouse_l.setPos([-1.5, -1.5])
                    self.mouse_r.setPos([-1.5, -1.5])

                    event.clearEvents()
                    self.win_l.flip()
                    self.win_r.flip()

            if state == self.states.RPI:
                for mouse, stimulus in zip([self.mouse_l, self.mouse_r], trial_components):
                    if mouse.isPressedIn(stimulus):
                        state = self.states.RAC

                        left_response = stimulus.name
                        response = stimulus.name

                        # Correct response
                        print(f"\nHorizontal: {side_of_horizontal}, Response: {response}")
                        if side_of_horizontal == response:
                            print('--> Good job!')
                            logging.debug(f"Correct")
                            self.stat_params['correct'] += 1
                            self.stat_params['left_correct'] += 1 if horizontal_left else 0
                            self.stat_params['right_correct'] += 1 if not horizontal_left else 0
                            self.c_sound.stop()
                            self.c_sound.play()
                            core.wait(0.5)
                            self.params['arduino'].write_order(self.states.REW)
                            # self.l_green.setAutoDraw(True)
                        else:
                            print('--> Wrong! ')
                            logging.debug(f"Wrong")
                            self.stat_params['wrong'] += 1
                            self.stat_params['left_wrong'] += 1 if horizontal_left else 0
                            self.stat_params['right_wrong'] += 1 if not horizontal_left else 0
                            self.w_sound.stop()
                            self.w_sound.play()
                            core.wait(0.5)
                            self.params['arduino'].write_order(self.states.NOR)
                            # self.r_red.setAutoDraw(True)

                        self.win_l.flip()
                        self.win_r.flip()
                        core.wait(1)
                        break

            if state == self.states.RAC:
                print(f"Left response:   {left_response}\nLeft waited: {horizontal_left}\nCorrect:     {horizontal_left == left_response}")
                continue_routine = False

        # -------Ending Routine "trial"-------
        for thisComponent in trial_components:
            if hasattr(thisComponent, "setAutoDraw"):
                thisComponent.setAutoDraw(False)

        for fg in [self.r_red, self.l_green]:
            fg.setAutoDraw(False)

        self.win_l.color = self.params['color_bg']
        self.win_r.color = self.params['color_bg']

        self.win_l.flip()
        self.win_l.flip()
        self.win_r.flip()
        self.win_r.flip()
        event.clearEvents()
        pyautogui.moveTo(200, 200)
        print()


if __name__ == '__main__':
    stim = FlickeringStaticBars(params={'monitor': 'Samsung_LE40C530', 'distance': 40, 'color_bg': 0,
                                        'spatial_frequency': 0.1, 'contrast': 1, 'orientation': 'horizontal',
                                        'num_bars': 5, 'color_bar': (1, 1, 1)})
