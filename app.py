# coding=utf-8
import logging
import sys
from iec62056_21.client import Iec6205621Client
import time

# Redirect all logs to stdout
root = logging.getLogger()
root.setLevel(logging.DEBUG)

handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
root.addHandler(handler)


def print_values(en_type, values):
    print(f'{en_type}:\n'
          f'    Полная: {values[0].value}\n'
          f'    Тариф 1: {values[1].value}\n'
          f'    Тариф 2: {values[2].value}\n'
          f'    Тариф 3: {values[3].value}\n'
          f'    Тариф 4: {values[4].value}\n')


client = Iec6205621Client.with_serial_transport(port='/dev/ttyUSB0', device_address='112609312')
# client = Iec6205621Client.with_serial_transport(port='/dev/ttyUSB1', device_address='112609312')

ACK_RESP = b'\x06'

import PySimpleGUI as sg

all_vals = ['ACCMODE', 'AENERGYA', 'AENERGYB', 'AIGAIN', 'AIRMSOS', 'ALT_OUTPUT', 'ANGLE_A', 'ANGLE_B', 'AP_NOLOAD', 'APENERGYA', 'APENERGYB', 'AVA', 'AVAGAIN', 'AVAOS', 'AVAR', 'AVARGAIN', 'AVAROS', 'AVGAIN', 'AWATT', 'AWATTOS', 'AWGAIN', 'BIGAIN', 'BIRMSOS', 'BVA', 'BVAGAIN', 'BVAOS', 'BVAR', 'BVARGAIN', 'BVAROS', 'BVGAIN', 'BWATT', 'BWATTOS', 'BWGAIN', 'CF1DEN', 'CF2DEN', 'CFMODE', 'CONFIG', 'DISNOLOAD', 'EX_REF', 'IA', 'IAPEAK', 'IB', 'IBPEAK', 'IRMSA', 'IRMSB', 'IRQENA', 'IRQENB', 'IRQSTATA', 'IRQSTATB', 'LAST_ADD', 'LAST_OP', 'LAST_RWDAT', 'LAST_RWDATA', 'LAST_RWDATA', 'LCYCMODE', 'LINECYC', 'OILVL', 'OVLVL', 'PERIOD', 'PFA', 'PFB', 'PGA_IA', 'PGA_IB', 'PGA_V', 'RENERGYA', 'RENERGYB', 'RSTIAPEAK', 'RSTIBPEAK', 'RSTIRQSTATA', 'RSTIRQSTATB', 'RSTVPEAK', 'SAGCYC', 'SAGLVL', 'SETUP_REG', 'UNLOCK_REG', 'V', 'VA_NOLOAD', 'VAR_NOLOAD', 'VERSION', 'VPEAK', 'VRMS', 'VRMSOS', 'WPHCALA', 'WPHCALB', 'WRITE_PROTECT', 'ZXTOUT']

shed_state = ['Current', 'Deferred']
shed_days = ['Weekdays', 'Saturday', 'Sunday', 'Holiday']

sg.theme('DarkAmber')  # Add a touch of color
# All the stuff inside your window.

l = []
for i in range(24):
    l.append(sg.Text('{:02}'.format(i)))
    l.append(sg.Input(key=f'sh-{i*2}', size=(1, 1)))
    l.append(sg.Input(key=f'sh-{i*2+1}', size=(1, 1)))

layout = [[sg.Text('ADE params')], [sg.Text('Choose param'), sg.InputCombo(all_vals, size=(20, 10), default_value=all_vals[0])],  [sg.Input(key='input', size=(60, 1))],
          [sg.Button('Set'), sg.Button('Get'), sg.Button('Clear')],
          [sg.Text('Date and time')],
          [sg.Input(key='hour', size=(2, 1)), sg.Input(key='min', size=(2, 1)), sg.Input(key='sec', size=(2, 1)),
           sg.Button('Set time')],
          [sg.Input(key='day', size=(2, 1)), sg.Input(key='mon', size=(2, 1)), sg.Input(key='year', size=(2, 1)),
           sg.Button('Set date')],
            [sg.Text('Shedule')],
           l[:36],
          l[36:],
          [sg.InputCombo(shed_state, default_value=shed_state[0], size=(20, 10), key='shed_state'),
           sg.InputCombo(shed_days, default_value=shed_days[0], size=(20, 10), key='shed_days'),
           sg.Button('Set shed'), sg.Button('Get shed'),
           sg.Input(key='val_to_fill', size=(2, 1)),
           sg.Button('Fill'),
           sg.Button('Clear shed')],
          [sg.Text('Change date'), sg.Input(key='shday', size=(2, 1)), sg.Input(key='shmon', size=(2, 1)), sg.Input(key='shyear', size=(2, 1)),
           sg.Text('time'), sg.Input(key='shhour', size=(2, 1)), sg.Input(key='shmin', size=(2, 1)), sg.Button('Set shed time'), sg.Button('Get shed change'), sg.Button('Clear shed')]]

window = sg.Window('Window Title', layout)


def write(address, value, val_to_red=''):
    try:
        client.connect()

        if client.send_password('777777') != ACK_RESP:
            print("Incorrect pass")
            raise Exception("Incorrect pass")
        client.write_single_value(address, value)
        return client.read_single_value(address, val_to_red)
    except Exception as e:
        print(e)
    finally:
        time.sleep(0.2)
        client.send_break()
        client.disconnect()


def read(address, value):
    try:
        client.connect()

        if client.send_password('777777') != ACK_RESP:
            print("Incorrect pass")
            raise Exception("Incorrect pass")

        return client.read_single_value(address, value)

    finally:
        time.sleep(0.2)
        client.send_break()
        client.disconnect()


while True:
    event, values = window.read()
    if event == 'Clear':
        window['input'].update('')
    if event == 'Get':
        if values[0] == '':
            print('Enter param name')
            continue

        window['input'].update(read('PARAM', values[0]))

    if event == 'Set':
        if values[0] == '':
            print('Enter param name')
            continue
        if values['input'] in (None, ''):
            print('Enter value')
            continue

        window['input'].update(write('PARAM', f'{values[0]},{values["input"]}', f'{values[0]}'))

    if event == 'Set time':
        if values['hour'] == '' or values['min'] == '' or values['sec'] == ''\
                or len(values['hour']) != 2 or len(values['min']) != 2 or len(values['sec']) != 2:
            print('Enter time')
            continue

        window['input'].update(write('TIME_', f'{values["hour"]}:{values["min"]}:{values["sec"]}'))
    if event == 'Set date':
        if values['day'] == '' or values['mon'] == '' or values['year'] == ''\
                or len(values['day']) != 2 or len(values['mon']) != 2 or len(values['year']) != 2:
            print('Enter time')
            continue

        window['input'].update(write('DATE_', f'00:{values["day"]}:{values["mon"]}:{values["year"]}'))

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
