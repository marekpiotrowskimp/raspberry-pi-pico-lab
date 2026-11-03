import json
from collections import namedtuple
import Tkinter as tk
import tkMessageBox
import sys
import threading
import time
import socket
import sqlite3

class WeatherStation:
    def __init__(self, sock=None):
        if sock is None:
            self.sock = socket.socket(
                            socket.AF_INET, socket.SOCK_STREAM)
        else:
            self.sock = sock

    def connect(self, host, port):
        try:
            self.sock.settimeout(10)
            self.sock.connect((host, port))
            return True
        except:
            return False

    def send(self, msg):
        totalsent = 0
        msg_len = len(msg)
        while totalsent < msg_len:
            sent = self.sock.send(msg[totalsent:])
            if sent != 0:
               totalsent = totalsent + sent
            else:
               totalsent = msg_len

    def receive(self):
        chunks = []
        chunk = b'D'
        bytes_recd = 0
        self.sock.settimeout(10)
        try:
            while chunk != b'':
                chunk = self.sock.recv(min(2048 - bytes_recd, 2048))
                chunks.append(chunk)
                bytes_recd = bytes_recd + len(chunk)
            return b''.join(chunks)
        except socket.timeout as e:
            return None

    def disconnect(self):
        self.sock.close()
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)