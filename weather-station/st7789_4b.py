from time import sleep_ms
import framebuf
import gc
import micropython
import uasyncio as asyncio
import time

LANDSCAPE = 0
REFLECT = 1
USD = 2
PORTRAIT = 4
GENERIC = (0, 0, 0)
TDISPLAY = (52, 40, 1)

LCD_DC   = 8
LCD_CS   = 9
LCD_SCK  = 10
LCD_MOSI = 11
LCD_MISO = 12
LCD_BL   = 13
LCD_RST  = 15
TP_CS    = 16
TP_IRQ   = 17

@micropython.viper
def _lcopy(dest:ptr16, source:ptr8, lut:ptr8, length:int):
    n = 0
    for x in range(length):
        ind1 = (source[x] & 0xF0) >> 3
        ind2 = (source[x] << 1) & 0x0F
        dest[n] = (lut[ind1] << 8) | lut[ind1 + 1]
        n += 1
        dest[n] = (lut[ind2] << 8) | lut[ind2 + 1]
        n += 1

class ST7789(framebuf.FrameBuffer):

    lut =  bytearray(0xFF for _ in range(32))

    @staticmethod
    def rgb(r, g, b):
        return ((b & 0xf8) << 5 | (g & 0x1c) << 11 | (g & 0xe0) >> 5 | (r & 0xf8)) ^ 0xffff

    def __init__(self, spi, cs, dc, rst, tp_cs, irq, height=320, width=240,
                 disp_mode=LANDSCAPE, init_spi=False, display=GENERIC):
        if not 0 <= disp_mode <= 7:
            raise ValueError('Invalid display mode:', disp_mode)
        if not display in (GENERIC, TDISPLAY):
            raise ValueError('Invalid display type.')
        self._spi = spi
        self._rst = rst
        self._dc = dc
        self._cs = cs
        self.height = height
        self.width = width
        self._offset = display[:2]
        orientation = display[2]
        self._spi_init = init_spi
        self._lock = asyncio.Lock()
        mode = framebuf.GS4_HMSB #.RGB565
        gc.collect()
        buf = bytearray(height * -(-width // 2))
        self._mvb = memoryview(buf)
        super().__init__(buf, width, height, mode)
        self._linebuf = bytearray(self.width * 2)
        self._init(disp_mode, orientation)
        self.tp_cs = tp_cs
        self.irq = irq
        self.tp_cs(1)
        self.palette()

    def palette(self):
        self.set_palette(0, int(self.rgb(0x00, 0x00, 0x00)))
        self.set_palette(1, self.rgb(0x33, 0x33, 0x33))
        self.set_palette(2, self.rgb(0x55, 0x55, 0x55))
        self.set_palette(3, self.rgb(0xAA, 0x11, 0x11))
        self.set_palette(4, self.rgb(0xEE, 0xEE, 0xEE))
        self.set_palette(5, self.rgb(0x00, 0xFF, 0x00))
        self.set_palette(6, self.rgb(0xFF, 0xFF, 0xFF))
        self.set_palette(7, self.rgb(0xFF, 0xFF, 0xFF))
        self.set_palette(8, self.rgb(0xFF, 0xFF, 0xFF))
        self.set_palette(9, self.rgb(0xFF, 0xFF, 0xFF))
        self.set_palette(10, self.rgb(0xFF, 0xFF, 0xFF))
        self.set_palette(11, self.rgb(0xFF, 0xFF, 0xFF))
        self.set_palette(12, self.rgb(0xFF, 0xFF, 0xFF))
        self.set_palette(13, self.rgb(0xAA, 0xFF, 0xAA))
        self.set_palette(14, self.rgb(0xFF, 0xAA, 0xAA))
        self.set_palette(15, self.rgb(0x00, 0xFF, 0xFF))
        
    def set_palette(self, idx, color):
        #self.lut.append(color)
        #self.lut[idx] = color
        self.lut[idx * 2] = (color >> 8) & 0xFF
        self.lut[idx * 2 + 1] = color & 0xFF
        #print(hex(color), hex(lut[col_index]), hex(lut[col_index + 1]))

    def _hwreset(self):
        self._dc(0)
        self._rst(1)
        sleep_ms(1)
        self._rst(0)
        sleep_ms(1)
        self._rst(1)
        sleep_ms(1)

    def _wcmd(self, buf):
        self._dc(0)
        self._cs(0)
        self._spi.write(buf)
        self._cs(1)

    def _wcd(self, c, d):
        self._dc(0)
        self._cs(0)
        self._spi.write(c)
        self._cs(1)
        self._dc(1)
        self._cs(0)
        self._spi.write(d)
        self._cs(1)

    def _init(self, user_mode, orientation):
        self._hwreset()
        if self._spi_init:
            self._spi_init(self._spi)
        cmd = self._wcmd
        wcd = self._wcd
        cmd(b'\x01')
        sleep_ms(150)
        cmd(b'\x11')
        sleep_ms(10)
        wcd(b'\x3a', b'\x55')
        cmd(b'\x20')
        cmd(b'\x13')

        if not orientation:
            user_mode ^= PORTRAIT
        mode = (0x60, 0xe0, 0xa0, 0x20, 0, 0x40, 0xc0, 0x80)[user_mode]
        self.set_window(mode)
        wcd(b'\x36', int.to_bytes(mode, 1, 'little'))
        cmd(b'\x29')

    def set_window(self, mode):
        portrait, reflect, usd = 0x20, 0x40, 0x80
        rht = 320
        rwd = 240
        wht = self.height
        wwd = self.width
        if mode & portrait:
            xoff = self._offset[1]
            yoff = self._offset[0]
            xs = xoff
            xe = wwd + xoff - 1
            ys = yoff
            ye = wht + yoff - 1
            if mode & reflect:
                ys = rwd - wht - yoff
                ye = rwd - yoff - 1
            if mode & usd:
                xs = rht - wwd - xoff
                xe = rht - xoff - 1
        else:
            xoff = self._offset[0]
            yoff = self._offset[1]
            xs = xoff
            xe = wwd + xoff - 1
            ys = yoff
            ye = wht + yoff - 1
            if mode & usd:
                ys = rht - wht - yoff
                ye = rht - yoff - 1
            if mode & reflect:
                xs = rwd - wwd - xoff
                xe = rwd - xoff - 1

        self._wcd(b'\x2a', int.to_bytes((xs << 16) + xe, 4, 'big'))
        self._wcd(b'\x2b', int.to_bytes((ys << 16) + ye, 4, 'big'))

    def write_cmd(self, cmd):
        self._cs(1)
        self._dc(0)
        self._cs(0)
        self._spi.write(bytearray([cmd]))
        self._cs(1)
        
    def write_data(self, buf):
        self._cs(1)
        self._dc(1)
        self._cs(0)
        self._spi.write(bytearray([buf]))
        self._cs(1)
    
    @micropython.native
    def show(self):
        clut = memoryview(self.lut)
        wd = -(-self.width // 2)
        end = self.height * wd
        lb = memoryview(self._linebuf)
        
        buf = self._mvb
        if self._spi_init:
            self._spi_init(self._spi)
        
        self.write_cmd(0x2C)
        
        self._cs(1)
        self._dc(1)
        self._cs(0)
        
        for start in range(0, end, wd):
            _lcopy(lb, buf[start:], clut, wd)
            self._spi.write(lb)
        self._cs(1)

    async def do_refresh(self, split=5):
        async with self._lock:
            lines, mod = divmod(self.height, split)
            if mod:
                raise ValueError('Invalid do_refresh arg.')
            clut = ST7789.lut
            wd = -(-self.width // 2)
            lb = memoryview(self._linebuf)
            buf = self._mvb
            line = 0
            for n in range(split):
                if self._spi_init:
                    self._spi_init(self._spi)
                self._dc(0)
                self._cs(0)
                self._spi.write(b'\x3c' if n else b'\x2c')
                self._dc(1)
                for start in range(wd * line, wd * (line + lines), wd):
                    _lcopy(lb, buf[start :], clut, wd)
                    self._spi.write(lb)
                line += lines
                self._cs(1)
                await asyncio.sleep(0)
                
                
    def touch_get(self, getSPI): 
        if self.irq() == 0:
            self._spi = getSPI(False)
            self.tp_cs(0)
            X_Point = 0
            Y_Point = 0
            for i in range(0,3):
                self._spi.write(bytearray([0XD0]))
                Read_date = self._spi.read(2)
                time.sleep_us(10)
                X_Point=X_Point+(((Read_date[0]<<8)+Read_date[1])>>3)
                
                self._spi.write(bytearray([0X90]))
                Read_date = self._spi.read(2)
                Y_Point=Y_Point+(((Read_date[0]<<8)+Read_date[1])>>3)

            X_Point=X_Point/3
            Y_Point=Y_Point/3
            
            self.tp_cs(1) 
            self._spi = getSPI(True)
            Result_list = [X_Point,Y_Point]
            return(Result_list)

