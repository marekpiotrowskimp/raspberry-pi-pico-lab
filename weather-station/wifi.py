from machine import I2C
from secrets import WIFI_SSID, WIFI_PASSWORD  # patrz secrets_example.py
import time

class WIFI(object):
    AT = b'AT\r\n'
    ATCWMODE = b'AT+CWMODE=1\r\n'
    ATCIPMODE = b'AT+CIPMODE=0\r\n'
    ATCIPMUX = b'AT+CIPMUX=1\r\n'
    ATCWLAP = b'AT+CWLAP\r\n'
    ATJAP = ('AT+CWJAP=\"{}\",\"{}\"\r\n'.format(WIFI_SSID, WIFI_PASSWORD)).encode()
    ATQAP = b'AT+CWQAP\r\n'
    ATCIPSERVER = b'AT+CIPSERVER=1,80\r\n'
    ATCIPSERVERCLOSE = b'AT+CIPSERVER=0\r\n'
    ATCIFSR = b'AT+CIFSR\r\n'
    ATCIPSTO = b'AT+CIPSTO=5\r\n'
    ATEOFF = b'ATE0\r\n'
    ATRFPOWER = b'AT+RFPOWER=20\r\n'
    ATSNTP = b'AT+CIPSNTPCFG=1,8,\"0.pool.ntp.org\",\"1.pool.ntp.org\",\"2.pool.ntp.org\"\r\n'
    ATDNS = b'AT+CIPDNS_DEF=1,\"91.212.2.19\"\r\n'
    ATTIME = b'AT+CIPSNTPTIME?\r\n'
    ATCIPSEND = b'AT+CIPSEND='
    ATCIPCLOSE = b'AT+CIPCLOSE='
    ATCIPSTA = b'AT+CIPSTA?\r\n'
    ATCIPSTAMAC = b'AT+CIPSTAMAC?'

    commands = []
    
    def __init__(self, uart, ssd, color, background):
        self.progress = ""
        self.uart = uart
        self.show_progress(ssd, color, background)
        self.send_cmd(self.AT)
        self.show_progress(ssd, color, background)
        self.send_cmd(self.ATEOFF)
        self.show_progress(ssd, color, background)
        self.send_cmd(self.ATCWMODE)
        self.show_progress(ssd, color, background)
        self.send_cmd(self.ATCIPMODE)
        self.show_progress(ssd, color, background)
        self.send_cmd(self.ATCIPMUX)
        self.show_progress(ssd, color, background)
        self.send_cmd(self.ATRFPOWER)
        self.show_progress(ssd, color, background)
        self.send_cmd(self.ATJAP)
        self.show_progress(ssd, color, background)
        time.sleep_ms(1500)
        self.show_progress(ssd, color, background)
        self.send_cmd(self.ATCIPSERVERCLOSE)
        self.show_progress(ssd, color, background)
        time.sleep_ms(1500)
        self.show_progress(ssd, color, background)
        self.send_cmd(self.ATCIPSERVER)
        self.show_progress(ssd, color, background)
        time.sleep_ms(200)
        self.show_progress(ssd, color, background)
        self.send_cmd(self.ATCIPSTA)
        self.show_progress(ssd, color, background)
        self.progress += " [END]"
        ssd.text(self.progress, 0, 12, color)
        ssd.show()
        time.sleep_ms(350)

        
    def show_progress(self, ssd, color, background):
        self.progress += "#"
        ssd.text(self.progress, 0, 12, color)
        ssd.fill_rect(0, 30, 320, 210, background)
        index = 0
        if len(self.commands) > 22:
            self.commands = self.commands[len(self.commands) - 20:]
        for com in self.commands:
            ssd.text(com, 0, 30 + index * 10, color)
            index += 1
        ssd.show()
        
    def read(self):
        char = self.uart.read(1)
        buf = char if char != None else None
        lastChar = b''
        while char != None and char != b'\n' and lastChar != b'\r':
            time.sleep_ms(10)
            lastChar = char
            char = self.uart.read(1)
            if char != None:
                buf += char
        return buf
        
         
    def send_cmd(self, cmd):
        self.commands.append(cmd[:len(cmd) - 2])
        self.uart.write(cmd)
        time.sleep_ms(150)
        response = self.read()
        if response != None and len(response) > 3:
            self.commands.append(response[:len(response) - 2])
        while not response is None or (not response is None and response.contains("busy")):
            time.sleep_ms(250)
            response = self.read()
            if response != None and len(response) > 3:
                self.commands.append(response[:len(response) - 2])
            
    def send_data(self, connection, data):
        command = str(self.ATCIPSEND, 'utf-8') + str(connection) + "," + str(len(data)) + "\r\n"
        print(command)
        self.uart.write(command)
        time.sleep_ms(200)
        self.uart.write(data)
    
    def close_connection(self, connection):
        self.uart.write(self.ATCIPCLOSE)
        self.uart.write(str(connection))
        self.uart.write(b'\r\n')
    
    def receive(self, data_json):
        buf = "OK"
        buf = self.uart.readline()
        if not buf is None:
            print(buf)
            if buf.find(b'CONNECT') != -1:
                con = int(str(buf[0])) - 48
                print(str(con))
            if buf.find(b'CLOSED') != -1:
                con = int(str(buf[0])) - 48
                print(str(con))
            if buf.find(b'+IPD') != -1 and buf.find(b'GET') != -1 and buf.find(b'HTTP') != -1 and buf.find(b'favicon.ico') != -1:
                connection = int(str(buf[5])) - 48
                count = int(buf[7:buf.find(b':GET')])
                count -= (len(buf) - buf.find(b':GET') - 1)
                print("html " + str(count))
                while count > 0:
                    count -= 1
                    self.uart.read()
                print("all")
                time.sleep_ms(550)
                self.close_connection(connection)
            if buf.find(b'+IPD') != -1 and buf.find(b'GET') != -1 and buf.find(b'HTTP') != -1 and buf.find(b'favicon.ico') == -1:
                count = int(buf[7:buf.find(b':GET')])
                count -= (len(buf) - buf.find(b':GET') - 1)
                print("html " + str(count))
                while count > 0:
                    count -= 1
                    self.uart.read()
                print("all")
                time.sleep_ms(100)
                connection = int(str(buf[5])) - 48
                with open('html.txt') as f:
                    lines = f.readlines()
                    data = ""
                    for line in lines:
                        data += line
                    f.close()
                self.send_data(connection, data_json)
                time.sleep_ms(550)
                self.close_connection(connection)
            if buf.find(b'+IPD') != -1 and buf.find(b'state') != -1:
                connection = int(str(buf[5])) - 48
                self.send_data(connection, data_json)
                time.sleep_ms(550)
                self.close_connection(connection)
         

