import psychopy
from psychopy import monitors, visual, core, event
from psychopy.tools import monitorunittools
from monitors import mymonitors
import serial
import time
import numpy as np
import pyautogui as pyg


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

        # Set up the psychopy monitor (left) ---------------------------------------------------------------------------
        self.mon = monitors.Monitor(self.params['monitor'], distance=self.params['distance'],
                                    width=mymonitors[self.params['monitor']]['width'],
                                    currentCalib={'sizePix': mymonitors[self.params['monitor']]['resolution']})

        # Set up the psychopy window (left)
        self.win = visual.Window(size=mymonitors[self.params['monitor']]['resolution'],
                                 fullscr=True, screen=self.params['screen'], allowGUI=False, allowStencil=False,
                                 monitor=self.mon, color=self.params['color_bg'], colorSpace='rgb',
                                 blendMode='avg', useFBO=True)

        """
        # Set up the psychopy monitor (right) --------------------------------------------------------------------------
        self.monR = monitors.Monitor(self.params['monitor2'], distance=self.params['distance'],
                                    width=mymonitors[self.params['monitor2']]['width'],
                                    currentCalib={'sizePix': mymonitors[self.params['monitor2']]['resolution']})

        # Set up the psychopy window (right)
        self.winR = visual.Window(size=mymonitors[self.params['monitor2']]['resolution'],
                                 fullscr=True, screen=1, allowGUI=False, allowStencil=False,
                                 monitor=self.monR, color=self.params['color_bg'], colorSpace='rgb',
                                 blendMode='avg', useFBO=True)
        """

        # Set up the psychopy mouse ------------------------------------------------------------------------------------
        self.mouse = event.Mouse(visible=True)

        # store frame rate of monitor ----------------------------------------------------------------------------------
        self.params['framerate'] = self.win.getActualFrameRate(nMaxFrames=500)
        if self.params['framerate'] is not None:
            self.frameDur = 1.0 / round(self.params['framerate'])
        else:
            self.frameDur = 1.0 / 60.0  # couldn't get a reliable measure so set standard 60 Hz
            self.params['framerate'] = 60
        print(f"Window framerate set to: {self.params['framerate']}")


class StaticBars(VisualStimulator):
    def __init__(self, params: dict, port: str = None):
        super(StaticBars, self).__init__(params, port)

        self.active = False     # flag for indicate activity

        # Calculating size of monitor in visual degrees, so stimulation covers it completely ---------------------------
        self.width_deg = monitorunittools.pix2deg(self.mon.getSizePix()[0], self.mon)
        self.height_deg = monitorunittools.pix2deg(self.mon.getSizePix()[1], self.mon)

        print(f'Left monitor (WxH):  {self.width_deg} x {self.height_deg}')

        # creation of the bars -----------------------------------------------------------------------------------------
        self.bars = []
        for i in range(self.params['num_bars']):
            bar = visual.GratingStim(win=self.win, name='grating_' + str(i), units='deg',
                                     tex=np.array([[-1, 1], [-1, 1]]), mask=None, ori=0, pos=[0, 0],
                                     sf=self.params['spatial_frequency'], phase=0.0,
                                     color=self.params['color_bar'], colorSpace='rgb', opacity=1, texRes=128,
                                     interpolate=False)
            bar.setAutoDraw(True)
            self.bars.append(bar)

        # --Positioning the bars ---------------------------------------------------------------------------------------
        max_bar_width = 2 #max(self.params['bar_width'])

        if self.params['orientation'] == 'vertical':
            first_bar_position = -self.width_deg / 2 + (max_bar_width / 2)
            step_size = -1 / ((self.params['num_bars'] - 1) / 2) * first_bar_position

            for i in range(self.params['num_bars']):
                self.bars[i].pos = [first_bar_position + (i * step_size), 0]
        elif self.params['orientation'] == 'horizontal':
            first_bar_position = -self.height_deg/2 + (max_bar_width / 2)
            step_size = -1/((self.params['num_bars']-1)/2) * first_bar_position

            for i in range(self.params['num_bars']):
                self.bars[i].pos = [0, first_bar_position + (i * step_size)]

    def stimulate(self, t=5):
        # Setting the size of the bars ---------------------------------------------------------------------------------
        if self.params['orientation'] == 'vertical':
            for bar in self.bars:
                bar.size = [self.width_deg, self.height_deg]
        elif self.params['orientation'] == 'horizontal':
            for bar in self.bars:
                bar.size = [self.width_deg, self.height_deg]
        else:
            raise ValueError("Possible orientations: {'horizontal', 'vertical}")

        # Creat timers -------------------------------------------------------------------------------------------------
        trial_clock = core.Clock()              # to track the time since trial started
        global_clock = core.Clock()             # to track the time since experiment started
        routine_timer = core.CountdownTimer()   # to track time remaining of each (non-slip) routine

        # Initialize timers
        trial_clock.reset()
        start = global_clock.getTime()
        routine_timer.add(t)                    # count down from t

        # Update component parameters for each repeat ------------------------------------------------------------------
        self.active = True
        for this_component in self.bars:
            if hasattr(this_component, 'setAutoDraw'):
                this_component.setAutoDraw(True)

        self.win.flip()
        #self.winR.flip()

    def end(self):
        # Ending Routine "trial" ---------------------------------------------------------------------------------------
        self.active = False
        for this_component in self.bars:
            if hasattr(this_component, "setAutoDraw"):
                this_component.setAutoDraw(False)

        self.win.flip()

    def start_stim(self, bar_width):
        """
        Start displaying flickering static bars stimulation, in the specified direction.
        Parameters
        ----------
        bar_width: Width of the flickering bars in visual degrees.
        Returns
        -------
        None
        """
        # ---Setting the size of the bars---
        if self.params['orientation'] == 'vertical':
            for bar in self.bars:
                bar.size = [bar_width, self.height_deg]
        elif self.params['orientation'] == 'horizontal':
            for bar in self.bars:
                bar.size = [self.width_deg, bar_width]
        else:
            raise ValueError("Possible orientations: {'horizontal', 'vertical}")

        # Initialize components for Routine "trial"
        trial_clock = core.Clock()

        # Create some handy timers
        global_clock = core.Clock()  # to track the time since experiment started
        start = global_clock.getTime()
        routine_timer = core.CountdownTimer()  # to track time remaining of each (non-slip) routine

        # ------Prepare to start Routine "trial"-------
        trial_clock.reset()  # clock
        routine_timer.add(2) #self.params['stim_length'])

        # update component parameters for each repeat
        # keep track of which components have finished
        trial_components = self.bars
        for this_component in trial_components:
            if hasattr(this_component, 'setAutoDraw'):
                this_component.setAutoDraw(True)

        # -------Start Routine "trial"-------
        continue_routine = True
        t_tmp = trial_clock.getTime()
        while continue_routine and routine_timer.getTime() > 0:
            # get current time
            t = trial_clock.getTime()

            # -----------------------------------
            # my code
            M = self.mouse.getPressed()
            if M != [0, 0, 0]:
                pos_x, pos_y = pyg.position()
                event.clearEvents()
                if (0 <= pos_x <= mymonitors[self.params['monitor']]['resolution'][0] and
                    0 <= pos_x <= mymonitors[self.params['monitor']]['resolution'][1]):
                    print('Monitor-1, left')
                else:
                    print('Monitor-2, Right')
                print(pos_x, pos_y)
            # ----------------------------------

            # checkerboard update
            if t - t_tmp > 1 / 15: #self.params['checker_swap_freq']:
                for bar in self.bars:
                    bar.tex = bar.tex
                t_tmp = t

            # check for quit (the Esc key)
            if event.getKeys(keyList=["escape"]):  # or self.endExpNow
                try:
                    self.port.close()
                except AttributeError:
                    print("No COM port to close.")
                print("Escape key detected. Quitting!")
                core.quit()

            # refresh the screen
            if continue_routine:  # don't flip if this routine is over or we'll get a blank screen
                self.win.flip()
                self.winR.flip()

        # -------Ending Routine "trial"-------
        for this_component in trial_components:
            if hasattr(this_component, "setAutoDraw"):
                this_component.setAutoDraw(False)

        # while (globalClock.getTime() - start) < self.params['duration']: pass
        self.win.color = self.params['color_bg']
        self.winR.color = self.params['color_bg']
        self.win.flip()
        self.winR.flip()


def main():
    stimL = StaticBars(params={'monitor': 'Samsung_LE40C530', 'screen': 0,
                              'distance': 40, 'color_bg': 0,
                              'spatial_frequency': 0.1, 'contrast': 1, 'orientation': 'horizontal',
                              'num_bars': 2, 'color_bar': (1, 1, 1)})

    stimR = StaticBars(params={'monitor': 'Small_LG', 'screen': 1,
                               'distance': 40, 'color_bg': 0,
                               'spatial_frequency': 0.1, 'contrast': 1, 'orientation': 'horizontal',
                               'num_bars': 2, 'color_bar': (1, 1, 1)})
    stimL.stimulate()
    time.sleep(2)
    stimR.stimulate()
    time.sleep(2)
    stimL.end()
    time.sleep(2)
    stimR.end()
    time.sleep(1)


if __name__ == '__main__':
    main()

