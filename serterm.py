#!/usr/bin/python3
# Serial terminal
# e.g. python serterm.py acm0

BAUDRATE = 38400

import sys, time, serial
import serial.tools.list_ports as list_ports
import threading
import time
import os

if os.name == 'nt':
    import msvcrt
else:
    import sys
    import termios
    import atexit
    from select import select


class KBHit:
    def __init__(self):
        if os.name == 'nt':
            pass
        else:
            # Save the terminal settings
            self.fd = sys.stdin.fileno()
            self.new_term = termios.tcgetattr(self.fd)
            self.old_term = termios.tcgetattr(self.fd)

            # New terminal setting unbuffered
            self.new_term[3] = (self.new_term[3] & ~termios.ICANON & ~termios.ECHO)
            termios.tcsetattr(self.fd, termios.TCSANOW, self.new_term)

            # Support normal-terminal reset at exit
            atexit.register(self.set_normal_term)


    def set_normal_term(self):
        if os.name == 'nt':
            pass
        else:
            termios.tcsetattr(self.fd, termios.TCSAFLUSH, self.old_term)


    def getch(self):
        # Returns a keyboard character after kbhit() has been called.
        s = ''
        if os.name == 'nt':
            return msvcrt.getch().decode('utf-8')

        else:
            return sys.stdin.read(1)

    def kbhit(self):
        ''' Returns True if keyboard character was hit, False otherwise.
        '''
        if os.name == 'nt':
            return msvcrt.kbhit()

        else:
            dr,dw,de = select([sys.stdin], [], [], 0)
            return dr != []










def get_port(match):
    ports = list(list_ports.comports())
    for port in ports:
        if match.upper() in port[0].upper():
            print('Connected to {}. F1 to quit.'.format(port[0]))
            return port[0]

    print('{} not found'.format(match))
    sys.exit()

quit = False

def input_thread():
    global quit
    kb = KBHit()
    while True:
        c = kb.getch()
        if c == '\x1b': #esc
            c = kb.getch()
            if ord(c) == 79: # 0?
                c = kb.getch()
                if ord(c) == 80: # F1  59?
                    quit = True
        else:
            if c == '\n': c = '\r' # send CR for enter instead of newline
            if s.isOpen(): s.write(c.encode())



try:
    serial_number = sys.argv[1]
    #serial_number = 'TIGER'
except:
    print('Usage: {} serial_number'.format(sys.argv[0]))
    sys.exit()
port = get_port(serial_number)
s = serial.Serial(port, BAUDRATE, timeout=0.5)
thread = threading.Thread(target=input_thread)
thread.daemon = True
thread.start()

while True:
    try:
        print(s.read(1).decode('cp437'), flush=True, end='')

    except Exception as e:
        print(repr(e))
        print('\r\n\t\t--- Disconnected ---')
        s.close()
        while not s.isOpen():
            time.sleep(0.01)
            try:
                s.open()
            except:
                pass
            if quit:
                sys.exit()
        print('\t\t--- Reconnected ---')

    if quit:
        print()
        sys.exit()

