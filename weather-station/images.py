import framebuf

class ImagesTool:
    BLACK = 0x0000
    
    def __init__(self, ssd):
        self.ssd = ssd
        self.icons = []

    def int_to_bytes(self, x: int) -> bytes:
        return x.to_bytes(2, 'big')
    
    def load_icon(self, file, width, height, color):
        fbuf = framebuf.FrameBuffer(bytearray(int(width * height / 2)), width, height, framebuf.GS4_HMSB)
        icon_x = 0
        icon_y = 0
        end = True
        f = open(file, "rb")
        while end:
            length = int(width / 8)
            line = bytearray(f.read(length))
            end = False
            if len(line) >= length:
                end = True
                icon_x = 0
                for byte in line:
                    for idx in range(8):
                        if ((byte << idx) & 0x80) > 0:
                            fbuf.pixel(icon_x, icon_y, color)
                        icon_x += 1
                icon_y += 1
        f.close()
        self.icons.append(fbuf)            

        
    def draw_icon(self, index, x, y, width, height):
        self.ssd.blit(self.icons[index], x, y, -1, None)

    def transform_icon(self, file1, file2, width, height, color_type):
        print("start")
        icon_width = int(width / 8)
        f = open(file1, "rb")
        f2 = open(file2, "wb")
        end = True
        while end:
            length = width * color_type
            rgb = bytearray(f.read(length))
            end = False
            if len(rgb) >= length:
                # print(rgb)
                end = True
                icon_line = bytearray(icon_width)
                icon_index = 0
                icon_index_bit = 0
                icon_byte = 0
                for x_index in range(0, length, color_type):
                    pixel = 1 if int(rgb[x_index]) * int(rgb[x_index + 1]) * int(rgb[x_index + 2] * int(rgb[x_index + 3])) > 0 else 0
                    icon_byte = (icon_byte << 1) | pixel
                    if icon_index_bit == 7:
                        icon_line[icon_index] = icon_byte
                        icon_index += 1
                        icon_index_bit = 0
                    else:
                        icon_index_bit += 1
                print(icon_line)
                f2.write(icon_line)
        f.close()
        f2.close()
        print("end")

    def transform(self, file1, file2):
        print("start")
        self.ssd.fill(self.BLACK)
        x = 0
        y = 0
        f = open(file1, "rb")
        end = True
        while end:
            rgb = bytearray(f.read(960))
            end = False
            if len(rgb) >= 960:
                end = True
                x = 0
                for x_index in range(0, 960, 3):
                    self.ssd.pixel(x, y, self.ssd.rgb(int(rgb[x_index]), int(rgb[x_index + 1]), int(rgb[x_index + 2])))
                    x += 1
                y += 1
        f.close()
        self.ssd.show()
        f = open(file2, "wb")
        for y in range(0,240):
            for x in range(0, 320):
                pixel = ssd.pixel(x, y)
                data = bytearray(self.int_to_bytes(pixel))
                temp = data[1]
                data[1] = data[0]
                data[0] = temp
                f.write(data)
        f.close()
        print("end")

    def draw_data(self, file):
        print("start")
        self.ssd.fill(self.BLACK)
        x = 0
        y = 0
        f = open(file, "rb")
        end = True
        while end:
            rgb = bytearray(f.read(640))
            end = False
            if len(rgb) >= 640:
                end = True
                x = 0
                for x_index in range(0, 640, 2):
                    self.ssd.pixel(x, y, rgb[x_index]<<8 | rgb[x_index + 1])
                    x += 1
                y += 1
        f.close()
        print("end")
        self.ssd.show()
    
    def draw_data_fast(self, file):
        print("start")
        self.ssd.fill(self.BLACK)
        f = open(file, "rb")
        for y in range(0,240,1):
            rgb_buf = bytearray(f.read(320 * 1 * 2))
            fbuf = framebuf.FrameBuffer(rgb_buf, 320, 1, framebuf.RGB565)
            self.ssd.blit(fbuf, 0, y, -1, None)
        f.close()
        print("end")
        self.ssd.show()



