import socket
from secrets import WIFI_SSID, WIFI_PASSWORD  # patrz secrets_example.py
import network
import time


class Server:
    def __init__(self):
        self.ip = None
        self.server = None
        self.wlan = network.WLAN(network.STA_IF)
        
    def connect(self):
        self.wlan.active(True)
        self.wlan.connect(WIFI_SSID, WIFI_PASSWORD)
        max_wait = 10
        while max_wait > 0:
            if self.wlan.status() < 0 or self.wlan.status() >= 3:
                break
            max_wait -= 1
            print('waiting for connection...')
            time.sleep(1)

        if self.wlan.status() != 3:
            print('error...')
            #raise RuntimeError('network connection failed')
        else:
            print('connected')
            status = self.wlan.ifconfig()
            self.ip = status[0]
            print( 'ip = ' + status[0] )

    def start(self):
        addr = socket.getaddrinfo('0.0.0.0', 5000)[0][-1]
        self.server = socket.socket()
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind(addr)
        self.server.listen(1)
        self.server.setblocking(0)

    def checkConnection(self):
        try:
            cl, addr = self.server.accept()
            print('client connected')
            self.server.setblocking(1)
            time.sleep(1)
            data = cl.recv(100)
            index = 0
            header_len = data[index]
            index += 1
            file_name = data[index:header_len + index].decode('utf-8')
            index += header_len
            data_len = int.from_bytes(data[index:index + 2], "big")
            index += 2
            
            print(file_name)
            print(data_len)
            
            file = open(file_name, "w+b")
            data = data[index:]
            start_len = len(data)
            file.write(data) 
            file.flush()
            while start_len < data_len:
                time.sleep(150 / 1000)
                read_len = data_len - start_len
                if read_len > 4096:
                    read_len = 4096
                print(start_len)
                print(read_len)
                data = cl.recv(read_len)
                file.write(data) 
                file.flush()
                start_len += len(data)
            file.close()
            
            print('END...')
            #response = 'dupa' 
            cl.send('end')
            time.sleep(1)
            #cl.send(response)
            cl.close()
            self.server.setblocking(0)
        except:
            self.server.setblocking(0)
