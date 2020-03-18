import PySimpleGUI as sg

import logging
import sys
from iec62056_21.client import Iec6205621Client
import time as systime
import datetime

import platform

if platform.system() == 'Windows':
    default_port = 'COM4'
else:
    default_port = '/dev/ttyUSB0'
# Redirect all logs to stdout
root = logging.getLogger()
root.setLevel(logging.DEBUG)

handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
root.addHandler(handler)

ACK_RESP = b'\x06'

all_vals = ['ACCMODE', 'AENERGYA', 'AENERGYB', 'AIGAIN', 'AIRMSOS', 'ALT_OUTPUT', 'ANGLE_A', 'ANGLE_B', 'AP_NOLOAD',
            'APENERGYA', 'APENERGYB', 'AVA', 'AVAGAIN', 'AVAOS', 'AVAR', 'AVARGAIN', 'AVAROS', 'AVGAIN', 'AWATT',
            'AWATTOS', 'AWGAIN', 'BIGAIN', 'BIRMSOS', 'BVA', 'BVAGAIN', 'BVAOS', 'BVAR', 'BVARGAIN', 'BVAROS', 'BVGAIN',
            'BWATT', 'BWATTOS', 'BWGAIN', 'CF1DEN', 'CF2DEN', 'CFMODE', 'CONFIG', 'DISNOLOAD', 'EX_REF', 'IA', 'IAPEAK',
            'IB', 'IBPEAK', 'IRMSA', 'IRMSB', 'IRQENA', 'IRQENB', 'IRQSTATA', 'IRQSTATB', 'LAST_ADD', 'LAST_OP',
            'LAST_RWDATA', 'LCYCMODE', 'LINECYC', 'OILVL', 'OVLVL', 'PERIOD', 'PFA', 'PFB', 'PGA_IA', 'PGA_IB', 'PGA_V',
            'RENERGYA', 'RENERGYB', 'RSTIAPEAK', 'RSTIBPEAK', 'RSTIRQSTATA', 'RSTIRQSTATB', 'RSTVPEAK', 'SAGCYC',
            'SAGLVL', 'SETUP_REG', 'UNLOCK_REG', 'V', 'VA_NOLOAD', 'VAR_NOLOAD', 'VERSION', 'VPEAK', 'VRMS', 'VRMSOS',
            'WPHCALA', 'WPHCALB', 'WRITE_PROTECT', 'ZXTOUT']

shed_state = ['Current', 'Deferred']
shed_days = ['Weekdays', 'Saturday', 'Sunday', 'Holiday']

sg.theme('DarkAmber')  # Add a touch of color
# All the stuff inside your window.

l = []
for i in range(24):
    l.append(sg.Text('{:02}'.format(i)))
    l.append(sg.Input(key=f'sh-{i * 2}', size=(1, 1)))
    l.append(sg.Input(key=f'sh-{i * 2 + 1}', size=(1, 1)))

layout = [
    [sg.Text('port', size=(10, 1)), sg.Input(key='port', default_text=default_port, size=(20, 1))],
    [sg.Text('Dev addr', size=(10, 1)), sg.Input(key='addr', default_text='112609312', size=(20, 1))],
    [sg.Text('Password', size=(10, 1)), sg.Input(key='pass', default_text='', size=(20, 1))],
    [sg.Input(key='factory mode', size=(32, 1)), sg.Button('Get fact state'), sg.Button('Set factory mode'), sg.Button('Reset factory mode')],
    [sg.Text('ADE params')],
    [sg.Text('Choose param'), sg.InputCombo(all_vals, size=(20, 10), default_value=all_vals[0])],
    [sg.Text('bin                                                        dec                        hex')],
    [sg.Input(key='bin', size=(32, 1)), sg.Input(key='dec', size=(15, 1)), sg.Input(key='hex', size=(15, 1))],
    [sg.Button('Set'), sg.Button('Get'), sg.Button('Clear')],
    [sg.Text('Date and time')],
    [sg.Input(key='hour', size=(2, 1)), sg.Input(key='min', size=(2, 1)), sg.Input(key='sec', size=(2, 1)),
     sg.Button('Get time'), sg.Button('Set time'), sg.Button('Set system time')],
    [sg.Input(key='day', size=(2, 1)), sg.Input(key='mon', size=(2, 1)), sg.Input(key='year', size=(2, 1)),
     sg.Button('Get date'), sg.Button('Set date'), sg.Button('Set system date')],
    [sg.Text('Shedule')],
    l[:36],
    l[36:],
    [
        sg.InputCombo(shed_state, default_value=shed_state[0], size=(20, 10), key='shed_state'),
        sg.InputCombo(shed_days, default_value=shed_days[0], size=(20, 10), key='shed_days'),
        sg.Button('Set shed'), sg.Button('Get shed'),
        sg.Input(key='val_to_fill', size=(2, 1)),
        sg.Button('Fill'),
        sg.Button('Clear shed')
    ],
    [
        sg.Text('Change date'), sg.Input(key='shday', size=(2, 1)), sg.Input(key='shmon', size=(2, 1)),
        sg.Input(key='shyear', size=(2, 1)),
        sg.Text('time'), sg.Input(key='shhour', size=(2, 1)), sg.Input(key='shmin', size=(2, 1)),
        sg.Button('Set shed time'), sg.Button('Get shed change'), sg.Button('Clear shed')
    ],
    [sg.Text('Apparent        Active            Reactive        Volt      Current')],
    [
        sg.Input(key='apparent', size=(10, 1)),
        sg.Input(key='active', size=(10, 1)),
        sg.Input(key='reactive', size=(10, 1)),
        sg.Input(key='volt', size=(10, 1)),
        sg.Input(key='current', size=(10, 1))
    ],
    [sg.Button('Calibrate')]
]

window = sg.Window('Window Title', layout)


def write(address, value, val_to_red=''):
    client = Iec6205621Client.with_serial_transport(port=values.get('port'), device_address=values.get('addr'))
    result = ''
    try:
        client.connect()

        if client.send_password(values.get('pass')) != ACK_RESP:
            print("Incorrect pass")
            raise Exception("Incorrect pass")
        client.write_single_value(address, value)
        # result = client.read_single_value(address, val_to_red)
    except Exception as e:
        print(e)
    finally:
        systime.sleep(0.2)
        client.send_break()
        client.disconnect()



def read(address, value):
    client = Iec6205621Client.with_serial_transport(port=values.get('port'), device_address=values.get('addr'))
    print(values.get('port'), values.get('addr'))
    try:
        client.connect()

        if client.send_password(values.get('pass')) != ACK_RESP:
            print("Incorrect pass")
            return None
            # raise Exception("Incorrect pass")
        ans = None
        try:
            ans = client.read_single_value(address, value)
        except Exception as e:
            print(e)
            ans = None

        return ans
    except TimeoutError as e:
        print('Error, try again.', e)

    finally:
        systime.sleep(0.2)
        client.send_break()
        client.disconnect()


while True:
    event, values = window.read()
    if event == 'Clear':
        window['bin'].update('')
        window['dec'].update('')
        window['hex'].update('')

    if event == 'Get':
        if values[0] == '':
            print('Enter param name')
            continue

        ans = read('PARAM', values[0])
        if ans is None:
            window['bin'].update('Incorrect pass')
            continue
        val = int(ans.value)
        window['bin'].update(bin(val))
        window['dec'].update(val)
        window['hex'].update(hex(val))

    if event == 'Set':
        if values[0] == '':
            print('Enter param name')
            continue
        if values['bin'] == '' and values['dec'] == '':
            write('PARAM', f'{values[0]},{int(values["hex"], 16)}')
            continue
        if values['dec'] == '' and values['hex'] == '':
            write('PARAM', f'{values[0]},{int(values["bin"], 2)}')
            continue
        if values['hex'] == '' and values['bin'] == '':
            write('PARAM', f'{values[0]},{int(values["dec"], 10)}')
            continue

        print('First clear fields')
        # window['input'].update(write('PARAM', f'{values[0]},{values["input"]}', f'{values[0]}'))

    if event == 'Set time':
        if values['hour'] == '' or values['min'] == '' or values['sec'] == '' \
                or len(values['hour']) != 2 or len(values['min']) != 2 or len(values['sec']) != 2:
            print('Enter time')
            continue
        write('TIME_', f'{values["hour"]}:{values["min"]}:{values["sec"]}')

    if event == 'Set system time':
        time = datetime.datetime.now().time()

        write('TIME_', '{:02}:{:02}:{:02}'.format(time.hour, time.minute, time.second))

        time = read('TIME_', '').value
        window['hour'].update(time[:2])
        window['min'].update(time[3:5])
        window['sec'].update(time[6:])

    if event == 'Get time':
        time = read('TIME_', '').value
        window['hour'].update(time[:2])
        window['min'].update(time[3:5])
        window['sec'].update(time[6:])

    if event == 'Set date':
        if values['day'] == '' or values['mon'] == '' or values['year'] == '' \
                or len(values['day']) != 2 or len(values['mon']) != 2 or len(values['year']) != 2:
            print('Enter time')
            continue

        write('DATE_', f'00:{values["day"]}:{values["mon"]}:{values["year"]}')

    if event == 'Set system date':
        date = datetime.datetime.now().date()

        write('DATE_', '00.{:02}.{:02}.{:02}'.format(date.day, date.month, date.year - 2000))

        systime.sleep(0.2)
        date = read('DATE_', '').value

        window['day'].update(date[3:5])
        window['mon'].update(date[6:8])
        window['year'].update(date[9:])

    if event == 'Get date':
        date = read('DATE_', '').value
        window['day'].update(date[3:5])
        window['mon'].update(date[6:8])
        window['year'].update(date[9:])

    if event == 'Fill':
        for i in range(48):
            window[f'sh-{i}'].update(values['val_to_fill'])

    if event == 'Set shed':
        val = ''
        flag = False
        for i in range(48):
            if values[f'sh-{i}'] in ['1', '2', '3', '4']:
                val += values[f'sh-{i}']
            else:
                print('Error sign in ', i, values[f'sh-{i}'])
                flag = True
                break
        if flag:
            continue
        addr = f'SH{values["shed_state"][:1].upper()}{values["shed_days"][:2].upper()}'
        write(addr, val)

    if event == 'Get shed':
        addr = f'SH{values["shed_state"][:1].upper()}{values["shed_days"][:2].upper()}'
        val = read(addr, '')

        for i in range(48):
            window[f'sh-{i}'].update(val.value[i])

    if event == 'Clear shed':

        for i in range(48):
            window[f'sh-{i}'].update('')

    if event == 'Clear shed':
        l = ['shday', 'shmon', 'shyear', 'shhour', 'shmin']

        for i in l:
            window[i].update('')

    if event == 'Set shed time':
        l = ['shday', 'shmon', 'shyear', 'shhour', 'shmin']

        for i in l:
            if values[i] == '' or len(values[i]) != 2:
                print('Check field ', i)
                continue

        val = ':'.join([values[i] for i in l])
        write('SHCHD', val)

    if event == 'Get shed change':
        val = read('SHCHD', '')

        window['shday'].update(val.value[0:2])
        window['shmon'].update(val.value[3:5])
        window['shyear'].update(val.value[6:8])
        window['shhour'].update(val.value[9:11])
        window['shmin'].update(val.value[12:14])

    if event == 'Calibrate':
        if values['apparent'] == '' or values['active'] == '' or values['reactive'] == '':
            print('Fill all energy')
            continue
        if int(values['apparent']) > 65535 or int(values['active']) > 65535 or int(values['reactive']) > 65535 or int(values['volt']) > 2**32 or int(values['current']) > 2**32\
                or int(values['apparent']) < 0 or int(values['active']) < 0 or int(values['reactive']) < 0 or int(values['volt']) < 0 or int(values['current']) < 0:
            print('Wrong num. Should be 0:65535')
            continue
        write('CALIB', f'{values["apparent"]}:{values["active"]}:{values["reactive"]}:{values["volt"]}:{values["current"]}')

    if event =='Get fact state':
        ans = read('FACTM', '')
        if ans is None:
            window['factory mode'].update('Inccorrect pass')
            continue
        if ans.value == '1':
            window['factory mode'].update('Factory')
        elif ans.value == '0':
            window['factory mode'].update('Not factory')

    if event =='Set factory mode':
        write('FACTM', '1', '')
        pass
    if event =='Reset factory mode':
        write('FACTM', '0', '')
        pass

    if event is None:
        break
    # print('You entered ', values[0], values[1])

window.close()
#
# try:
#     client.connect()
#
#     if client.send_password('777777') != ACK_RESP:
#         print("Incorrect pass")
#         raise Exception("Incorrect pass")
#
#     # client.write_single_value('TIME_', '14:52:00')
#     # client.write_single_value('DATE_', '05:07:03:20')
#
#     client.write_single_value('PARAM', 'BIGAIN,4194304')
#
#     print(client.read_single_value('PARAM', 'BIGAIN'))
#
#
#     # t = client.read_single_value('TIME_')
#     # print(f'Current time om meter is {t.value}')
#     #
#     # values = client.read_multi_value('ET0PE')
#     # print_values('Активная потребленая', values)
#     #
#     # values = client.read_multi_value('ET0PI')
#     # print_values('Активная отпущенная', values)
#     #
#     # values = client.read_multi_value('ET0QE')
#     # print_values('Реактивная потребленая', values)
#     #
#     # values = client.read_multi_value('ET0QI')
#     # print_values('Реактивная отпущенная', values)
#
# finally:
#     time.sleep(0.2)
#     client.send_break()
#     client.disconnect()


# client.read_single_value('ET0PE')

# values = client.read_multi_value('ET0PE')
# print_values('Активная потребленая', values)
#
#

#
# time.sleep(0.2)
#
