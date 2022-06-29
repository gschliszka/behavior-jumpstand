"""
Definition of the parameters of the monitors used in the lab.
Add to this dictionary and run main if you want to use a new screen!
Source: fus/fusexperiment/users/Abel/monitors.py
"""

from psychopy import monitors

mymonitors = {'Samsung_LE40C530': {'width': 48.0, 'resolution': (1920, 1080)},
              'Small_LG': {'width': 47.5, 'resolution': (1700, 960)},
              'Asus': {'width': 48.0, 'resolution': (1920, 1080)},
              'Samsung_h': {'width': 48.0, 'resolution': (1700, 960)}}


if __name__ == '__main__':
    mon = monitors.Monitor('Samsung_h')
    print(mon)
    print(mon.name)
    print(mon.calibs)
    mon.save()

    """
    for mon in mymonitors.keys():
        psychopy_mon = monitors.Monitor(mon, width=mymonitors[mon]['width'],
                                        currentCalib={'sizePix': mymonitors[mon]['resolution']})
        psychopy_mon.setSizePix(mymonitors[mon]['resolution'])
        print(mon)
        psychopy_mon.save()
    """