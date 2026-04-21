"""
GDEY0154D67 1.54 inch e-Paper Driver (SSD1681 Controller)
Compatible with ESP32-S3 platform, MicroPython environment
https://docs.waveshare.net/ESP32-S3-ePaper-1.54
# Pin Definitions 
EPD3V3_EN = 6   # Power enable, turns on EPD power (Low level enables MOS gate)
EPD_BUSY = 8    # Busy signal
EPD_RST = 9     # Reset
EPD_DC = 10     # Data/Command selection
EPD_CS = 11     # Chip select
EPD_SCLK = 12   # SPI Clock
EPD_SDI = 13    # SPI Data Input (MOSI)
SDA_PIN = 47    # SHTC3, RTC SDA
SCL_PIN = 48    # SHTC3, RTC SCL
"""
from machine import Pin, SPI
import time

# Color Constants
WHITE = 0xFF
BLACK = 0x00

class EPD_1in54:
    # Look-up Table (LUT) copied from C++ source code
    WF_FULL = bytes([
        0x80, 0x48, 0x40, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0,
        0x40, 0x48, 0x80, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0,
        0x80, 0x48, 0x40, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0,
        0x40, 0x48, 0x80, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0,
        0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0,
        0xA, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x8, 0x1, 0x0, 0x8, 0x1, 0x0, 0x2,
        0xA, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0,
        0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0,
        0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0,
        0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0,
        0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0,
        0x22, 0x22, 0x22, 0x22, 0x22, 0x22, 0x0, 0x0, 0x0, 0x22, 0x17, 0x41, 0x0, 0x32, 0x20
    ])

    WF_PARTIAL = bytes([
        0x0, 0x40, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0,
        0x80, 0x80, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0,
        0x40, 0x40, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0,
        0x0, 0x80, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0,
        0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0,
        0xF, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x1, 0x1, 0x0, 0x0, 0x0, 0x0, 0x0,
        0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0,
        0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0,
        0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0,
        0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0,
        0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0,
        0x22, 0x22, 0x22, 0x22, 0x22, 0x22, 0x0, 0x0, 0x0, 0x02, 0x17, 0x41, 0xB0, 0x32, 0x28
    ])

    def __init__(self):
        self.width = 200
        self.height = 200
        self.pages = self.width // 8
        self.buffer = bytearray(self.width * self.pages)
        
        # Pin Configuration
        self.pwr_en = Pin(6, Pin.OUT, value=1) # High level is OFF
        self.busy = Pin(8, Pin.IN)             
        self.rst = Pin(9, Pin.OUT, value=1)
        self.dc = Pin(10, Pin.OUT, value=0)
        self.cs = Pin(11, Pin.OUT, value=1)
        
        # SPI Initialization: Use slower frequency for troubleshooting (4MHz)
        self.spi = SPI(2, baudrate=4000000, polarity=0, phase=0, sck=Pin(12), mosi=Pin(13))
        
        # Power On (Low level enables MOS gate)
        self.pwr_en.value(0)
        time.sleep_ms(100)

    def _command(self, reg):
        self.dc.value(0)
        self.cs.value(0)
        self.spi.write(bytes([reg]))
        self.cs.value(1)

    def _data(self, data):
        self.dc.value(1)
        self.cs.value(0)
        if isinstance(data, int):
            self.spi.write(bytes([data]))
        else:
            self.spi.write(data)
        self.cs.value(1)

    def wait_until_idle(self):
        while self.busy.value() == 1: # 1: Busy, 0: Idle
            time.sleep_ms(5)

    def reset(self):
        self.rst.value(1)
        time.sleep_ms(50)
        self.rst.value(0)
        time.sleep_ms(20)
        self.rst.value(1)
        time.sleep_ms(50)
        self.wait_until_idle()

    def set_lut(self, lut):
        self._command(0x32)
        self._data(lut[0:153])
        self.wait_until_idle()
        
        self._command(0x3f)
        self._data(lut[153])
        
        self._command(0x03)
        self._data(lut[154])
        
        self._command(0x04)
        self._data(lut[155])
        self._data(lut[156])
        self._data(lut[157])

        self._command(0x2c)
        self._data(lut[158])

    def set_window(self, x_start, y_start, x_end, y_end):
        self._command(0x44)
        self._data((x_start >> 3) & 0xFF)
        self._data((x_end >> 3) & 0xFF)
        
        self._command(0x45)
        self._data(y_start & 0xFF)
        self._data((y_start >> 8) & 0xFF)
        self._data(y_end & 0xFF)
        self._data((y_end >> 8) & 0xFF)

    def set_cursor(self, x, y):
        self._command(0x4E)
        self._data(x & 0xFF)
        self._command(0x4F)
        self._data(y & 0xFF)
        self._data((y >> 8) & 0xFF)

    def init_full(self):
        self.reset()
        self._command(0x12) # SWRESET
        self.wait_until_idle()

        self._command(0x01) # Driver output control
        self._data(0xC7)
        self._data(0x00)
        self._data(0x01)

        self._command(0x11) # Data entry mode
        self._data(0x01)    # X increment, Y increment

        # --- Key Correction: Must strictly match C++ window parameters ---
        # C++: EPD_SetWindows(0, Width-1, Height-1, 0);
        # Xstart=0, Xend=199, Ystart=199, Yend=0
        self.set_window(0, 199, 199, 0) 

        self._command(0x3C) # BorderWaveform
        self._data(0x01)

        self._command(0x18)
        self._data(0x80)

        self._command(0x22) # Load Temperature and waveform setting
        self._data(0xB1)
        self._command(0x20)
        
        # C++: EPD_SetCursor(0, Height-1);
        self.set_cursor(0, 199)
        self.wait_until_idle()
        
        self.set_lut(self.WF_FULL)

    def display(self):
        # Reposition before sending data
        self.set_cursor(0, 199)
        self._command(0x24) # Write RAM
        self._data(self.buffer)
        
        self._command(0x22) # Display Update Control 2
        self._data(0xC7)
        self._command(0x20) # Master Activation
        self.wait_until_idle()

    def init_partial(self):
        self.reset()
        self.set_lut(self.WF_PARTIAL)

        self._command(0x37) 
        self._data(bytes([0x00]*5 + [0x40] + [0x00]*4))
        
        self._command(0x3C) # BorderWaveform
        self._data(0x80)
        
        self._command(0x22) 
        self._data(0xC0) 
        self._command(0x20) 
        self.wait_until_idle()

    def clear(self, color=WHITE):
        for i in range(len(self.buffer)):
            self.buffer[i] = color

    def draw_pixel(self, x, y, color):
        if x >= self.width or y >= self.height:
            return
        # Corresponding to C++: index = y * 25 + (x >> 3)
        index = y * (self.width // 8) + (x >> 3)
        bit = 7 - (x & 0x07)
        if color == WHITE:
            self.buffer[index] |= (0x01 << bit)
        else:
            self.buffer[index] &= ~(0x01 << bit)
            
    def draw_rect(self, x, y, w, h, color=BLACK, fill=False):
        """
        Draw a rectangle
        :param x: Starting X coordinate
        :param y: Starting Y coordinate
        :param w: Width
        :param h: Height
        :param color: Color (BLACK or WHITE)
        :param fill: Whether to fill the rectangle
        """
        if fill:
            # Fill rectangle: traverse all pixels
            for i in range(x, x + w):
                for j in range(y, y + h):
                    self.draw_pixel(i, j, color)
        else:
            # Draw border only
            for i in range(x, x + w):
                self.draw_pixel(i, y, color)           # Top border
                self.draw_pixel(i, y + h - 1, color)   # Bottom border
            for j in range(y, y + h):
                self.draw_pixel(x, j, color)           # Left border
                self.draw_pixel(x + w - 1, j, color)   # Right border

    def display_partial(self):
        self._command(0x24)
        self._data(self.buffer)
        
        self._command(0x22)
        self._data(0xCF)
        self._command(0x20)
        self.wait_until_idle()

    def sleep(self):
        self._command(0x10) # Deep sleep
        self._data(0x01)

    def draw_char(self, x, y, char, font, color=BLACK):
        if char not in font['data']:
            return
        
        char_data = font['data'][char]
        f_width = font['width']
        f_height = font['height']
        
        # Core logic: Calculate how many bytes per row
        # Font12 is 1, Font20 is 2
        bytes_per_row = (f_width + 7) // 8
        
        for h in range(f_height):
            for b in range(bytes_per_row):
                idx = h * bytes_per_row + b
                if idx >= len(char_data): continue
                
                line = char_data[idx]
                for i in range(8):
                    if (line << i) & 0x80:
                        px = x + (b * 8) + i
                        py = y + h
                        # Keep drawing within font width boundaries
                        if (b * 8) + i < f_width:
                            self.draw_pixel(px, py, color)

    def draw_string(self, x, y, text, font, color=BLACK, align="left"):
        """
        Display a string with support for different alignments
        """
        # Note: Using font.get('width') for compatibility
        f_width = font['width']
        total_width = len(text) * f_width
        
        start_x = x
        if align == "center":
            start_x = x - (total_width // 2)
        elif align == "right":
            start_x = x - total_width
            
        curr_x = start_x
        for char in text:
            # Simple boundary check
            if curr_x + f_width > self.width:
                break
            self.draw_char(curr_x, y, char, font, color)
            curr_x += f_width