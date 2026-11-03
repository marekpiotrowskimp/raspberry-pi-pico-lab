#!/usr/bin/env python
import Tkinter as tk
import tkMessageBox
import sys
import threading
import time
import socket
import sqlite3
from weather_station import WeatherStation
from weather_sensor import WeatherSensor

root = tk.Tk()
root.overrideredirect(True)
root.geometry("{0}x{1}+0+0".format(root.winfo_screenwidth(), root.winfo_screenheight()))

bg_image = tk.PhotoImage(file = "weather2.png")
canvas = tk.Canvas(root, width = 480, height = 320,)
canvas.pack(fill="both", expand=True)

image_canvas = canvas.create_image(0, 0, image=bg_image, anchor="nw")

weather = WeatherStation()

con = sqlite3.connect('weather.db')
cur = con.cursor()

sensor1 = WeatherSensor(root, canvas, con, cur, weather, "192.168.22.188", 10)
sensor1.printit()

sensor2 = WeatherSensor(root, canvas, con, cur, weather, "192.168.22.188", 250)
sensor2.printit()

def exit():
    sensor1.endApp = True
    sensor2.endApp = True
    root.destroy()

B1 = tk.Button(root, text = "X", fg="White", bg="Black", command = exit)
B1.place(x=440, y=2)

root.after(60000, sensor1.printit)
root.after(60000, sensor2.printit)
root.mainloop()

for row in cur.execute('SELECT datetime, sensor, json FROM weather ORDER BY datetime DESC LIMIT 1'):
   print(row[2])

con.close()


