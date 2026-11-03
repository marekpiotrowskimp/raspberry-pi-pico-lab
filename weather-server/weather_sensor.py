import json
from collections import namedtuple
import Tkinter as tk
import tkMessageBox
import sys
import threading
import time
import socket
import sqlite3
from json_converter import JsonConverter

class WeatherSensor:
    endApp = False

    def __init__(self, root, canvas, con, cur, weather, ip_address, possition_x):
        self.canvas = canvas
        self.con = con
        self.cur = cur
        self.root = root
        self.weather = weather
        self.ip_address = ip_address
        self.possition_x = possition_x
        self.lines = []
        self.label_time = self.canvas.create_text(self.possition_x, 20, text="---", anchor='w', font=("Courier", 10), fill="white")
        self.label_preasure = self.canvas.create_text(self.possition_x, 35, text="---", anchor='w', font=("Courier", 10), fill="white")
        self.label_humidity = self.canvas.create_text(self.possition_x, 50, text="---", anchor='w', font=("Courier", 10), fill="white")
        self.label_temp = self.canvas.create_text(self.possition_x, 65, text="---", anchor='w', font=("Courier", 10), fill="white")
        self.label_pm1 = self.canvas.create_text(self.possition_x, 80, text="---", anchor='w', font=("Courier", 10), fill="white")
        self.label_pm25 = self.canvas.create_text(self.possition_x, 95, text="---", anchor='w', font=("Courier", 10), fill="white")
        self.label_pm10 = self.canvas.create_text(self.possition_x, 110, text="---", anchor='w', font=("Courier", 10), fill="white")

    def remove_lines(self):
        for line in self.lines:
            self.canvas.delete(line)
        self.lines = []

    def draw(self, x, y, width, height, type):
        self.lines.append(self.canvas.create_line(x, y, x, y + height, width = 4, fill='white'))
        self.lines.append(self.canvas.create_line(x, y + height, x + width, y + height, width = 4, fill='white'))
        self.lines.append(self.canvas.create_text(x + width, y, text=type, anchor='ne', font=("Courier", 10), fill="green"))
        index = 1
        for row in self.cur.execute('SELECT datetime, sensor, json FROM weather ORDER BY datetime DESC LIMIT 50'):
            obj = JsonConverter().json2obj(row[2])
            if obj != None and obj.pms != None and obj.pms.PM2_5 != None and obj.pms.PM10_0 != None:
                field = obj.pms.PM2_5 if type == 'PM2_5' else obj.pms.PM10_0
                color = 'green' if field < 80 else 'orange' if field < 120 else 'red'
                field_normalized = (field / 2) if (field / 2) < (height - 2) else (height - 2)
                self.lines.append(self.canvas.create_line(x + index * 4, y + height - 2, x + index * 4, y + height - 2 - field_normalized, width = 4, fill = color))
                index += 1

    def exit(self):
        endApp = True
        self.root.destroy()
    
    def printit(self):
        if not(self.endApp):
            self.root.after(60000, self.printit)

        if self.weather.connect(self.ip_address, 80):
            self.weather.send(b'state')
            data = self.weather.receive()

            if data != None:
                self.cur.execute("INSERT INTO weather (datetime, sensor, json) VALUES (datetime('now', 'localtime'),'1',\'" + str(data) + "\')")
                self.con.commit()
                obj = JsonConverter().json2obj(data)

                temp =     "Tempe.:    " + str(obj.temperature) + "C"
                humidity = "Humidity:  " + str(obj.humidity) + "%"
                preasure = "Preasure:  " + str(obj.preasure) + " hPa"
                time =     "Time:      " + str(obj.time) # str(obj.date) + " | " + str(obj.time)
                pm1  =     "PM1_0      " + str(obj.pms.PM1_0)
                pm25 =     "PM2_5      " + str(obj.pms.PM2_5)
                pm10 =     "PM10_0     " + str(obj.pms.PM10_0)
                self.canvas.itemconfig(self.label_temp, text=temp)
                self.canvas.itemconfig(self.label_humidity, text=humidity)
                self.canvas.itemconfig(self.label_preasure, text=preasure)
                self.canvas.itemconfig(self.label_time, text=time)
                self.canvas.itemconfig(self.label_pm1, text=pm1)
                self.canvas.itemconfig(self.label_pm25, text=pm25)
                self.canvas.itemconfig(self.label_pm10, text=pm10)
        self.weather.disconnect()
        self.remove_lines()
        self.draw(self.possition_x, 120, 220, 80, 'PM2_5')
        self.draw(self.possition_x, 220, 220, 80, 'PM10_0')