import epaper750
import framebuf
import gc
import machine
import time
import ina219
import wifi
from machine import Pin 
import bluetooth
from ble_simple_peripheral import BLESimplePeripheral

epd = epaper750.EPD_7in5()
display_name = ""


def image(epd, name):
    epd.init()
    print(name)
    file = open(name, "r+b")
    imageMeta = bytearray(8)
    
    for i in range(0, 8):
        imageMeta[i] = file.read(1)[0]
        
    xPos = int.from_bytes(imageMeta[:2], "big")
    yPos = int.from_bytes(imageMeta[2:4], "big")
    width = int.from_bytes(imageMeta[4:6], "big")
    height = int.from_bytes(imageMeta[6:8], "big")
    
    print(xPos)
    print(yPos)
    print(width)
    print(height)
    bufferImage = bytearray(width * height // 8)
    fbuf = framebuf.FrameBuffer(bufferImage, width, height, framebuf.MONO_HLSB)
    for i in range(0, width * height // 8):
        bufferImage[i] = file.read(1)[0]

    file.close()
    epd.blit(fbuf, xPos, yPos)
    epd.display(epd.buffer)
    epd.delay_ms(500)
    epd.sleep()
    del fbuf
    del bufferImage
    gc.collect()


def initial_display():
    colorPrimary = 0xFF

    epd.text("Waveshare", 5, 10, colorPrimary)
    epd.text("Pico_ePaper-7.5", 5, 40, colorPrimary)
    epd.text("Raspberry Pico", 5, 70, colorPrimary)

    epd.vline(10, 90, 60, colorPrimary)
    epd.vline(120, 90, 60, colorPrimary)
    epd.hline(10, 90, 110, colorPrimary)
    epd.hline(10, 150, 110, colorPrimary)
    epd.line(10, 90, 120, 150, colorPrimary)
    epd.line(120, 90, 10, 150, colorPrimary)

    epd.rect(10, 180, 50, 80, colorPrimary)
    epd.fill_rect(70, 180, 50, 80, colorPrimary)

    epd.fill_rect(250, 150, 480, 20, colorPrimary)
    epd.fill_rect(250, 310, 480, 20, colorPrimary)
    epd.fill_rect(400, 0, 20, 480, colorPrimary)
    epd.fill_rect(560, 0, 20, 480, colorPrimary)

    for j in range(0, 3):
        for i in range(0, 15):
            epd.line(270+j*160+i, 20+j*160, 375+j*160+i, 140+j*160, colorPrimary)
        for i in range(0, 15):
            epd.line(375+j*160+i, 20+j*160, 270+j*160+i, 140+j*160, colorPrimary)
        for i in range(0, 15):
            epd.line(270+j*160, 20+j*160+i, 390+j*160, 125+j*160+i, colorPrimary)
        for i in range(0, 15):
            epd.line(270+j*160, 125+j*160+i, 390+j*160, 20+j*160+i, colorPrimary)        
    epd.fill_rect(270, 190, 100, 100, colorPrimary)
    epd.fill_rect(270, 350, 100, 100, colorPrimary)
    epd.display(epd.buffer)
    epd.delay_ms(500)
    epd.sleep()


# Create a Bluetooth Low Energy (BLE) object
ble = bluetooth.BLE()

# Create an instance of the BLESimplePeripheral class with the BLE object
sp = BLESimplePeripheral(ble, name = "et")

# Create a Pin object for the onboard LED, configure it as an output
led = Pin("LED", Pin.OUT)

# Initialize the LED state to 0 (off)
led_state = 0

# Define a callback function to handle received data
def on_tx(data):
    global display_name
    print("Data received: ", data)
    global led_state
    global epd
    if data[0] == ord('L'): 
        led.value(not led_state)
        led_state = 1 - led_state
    if data[0] == ord('S'):
        data = data[1:]
        print("Display: ", data)
        display_name = data.decode('utf-8')
        image(epd, display_name)
        
def on_battery_rx():
    data = bytearray(1)
    data[0] = batteryRead(ina219)
    print("Battery: ", data)
    return data

def on_rx():
    global server
    print("ip: ", server.ip)
    return server.ip

def batteryRead(ina219):
    bus_voltage = ina219.getBusVoltage_V()             # voltage on V- (load side)
    current = ina219.getCurrent_mA()                   # current in mA
    P = (bus_voltage -3)/1.2*100
    if(P<0):P=0
    elif(P>100):P=100
    return int(P) #"Voltage:  {:6.3f} V".format(bus_voltage) + "Current:  {:6.3f} A".format(current/1000) + "Percent:  {:6.1f} %".format(P)

# Start an infinite loop
machine.freq(80000000)
time.sleep(1)
print(machine.freq())

ina219 = ina219.INA219(addr=0x43)
server = wifi.Server()
server.connect()
server.start()

#initial_display()
while True:
    if sp.is_connected():
        sp.on_write(on_tx)  
        sp.on_battery_read(on_battery_rx)
        sp.on_read(on_rx)
        server.checkConnection()

        #data = bytearray(1)
        #data[0] = batteryRead(ina219)
        #print(data)
        #sp.send(data)
    else:
        time.sleep_ms(1000)
        #machine.lightsleep(100000)


