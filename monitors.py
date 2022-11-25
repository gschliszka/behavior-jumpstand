"""
Definition of the parameters of the monitors used in the lab.
Add to this dictionary and run main if you want to use a new screen!
"""

from psychopy import monitors

mymonitors = {'Samsung_LE40C530': {'width': 97.0, 'resolution': (1920, 1080)},
              'Small_LG': {'width': 45.0, 'resolution': (1920, 1080)},
              'Fujitsu_rodent': {'width': 47.5, 'resolution': (1920, 1080)},
              'Dell_24_inch': {'width': 52.5, 'resolution': (1920, 1080)}}


if __name__ == '__main__':
    for mon in mymonitors.keys():
        psychopy_mon = monitors.Monitor(mon, width=mymonitors[mon]['width'],
                                        currentCalib={'sizePix': mymonitors[mon]['resolution']})
        psychopy_mon.setSizePix(mymonitors[mon]['resolution'])
        psychopy_mon.save()
