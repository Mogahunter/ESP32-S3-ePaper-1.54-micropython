from machine import Pin, SPI
import time
from epaper_driver import EPD_1in54, BLACK, WHITE

from font8 import Font8
from font12 import Font12
from font16 import Font16
from font20 import Font20
from font24 import Font24

update_delay = 0

print("Initializing EPD...")
epd = EPD_1in54()

# 1. 全局刷新测试
print("Full update...")
epd.init_full()
epd.clear(WHITE)
t0 = time.ticks_ms()
epd.draw_string(100, 0, "MICRO", Font8, align="center")
epd.draw_string(100, 10, "MICRO", Font12, align="center")
epd.draw_string(100, 24, "MICRO", Font16, align="center")
epd.draw_string(100, 46, "MICRO", Font20, align="center")
epd.draw_string(100, 68, "MICRO", Font24, align="center")
# 画一个带黑色边框的空心矩形 (按钮外框)
epd.draw_rect(10, 160, 80, 40, color=BLACK, fill=False)
# 在矩形里写字 (Font20)
# 注意：Font20 是 14 宽，"OK" 总宽 28，放在 (100-28)/2 + 10 左右的位置居中
epd.draw_string(46, 170, "OK", Font20)
# 画一个实心的黑色方块 (反色背景)
epd.draw_rect(110, 160, 80, 40, color=BLACK, fill=True)
# 在实心黑块里写白字
epd.draw_string(156, 170, "HI", Font20, color=WHITE)
epd.display()
t1 = time.ticks_ms()
print('full update in ms: '+str(time.ticks_diff(t1,t0)))
# full update in ms: 2010
time.sleep(5)
epd.clear(WHITE)
epd.display()

# 2. 局部刷新测试
print("Switching to Partial mode...")
epd.init_partial()

t0 = time.ticks_ms()
epd.draw_string(100, 0, "MICRO", Font8, align="center")
epd.display_partial()
time.sleep_ms(update_delay) 
epd.draw_string(100, 10, "MICRO", Font12, align="center")
epd.display_partial()
time.sleep_ms(update_delay) 
epd.draw_string(100, 24, "MICRO", Font16, align="center")
epd.display_partial()
time.sleep_ms(update_delay) 
epd.draw_string(100, 46, "MICRO", Font20, align="center")
epd.display_partial()
time.sleep_ms(update_delay) 
epd.draw_string(100, 68, "MICRO", Font24, align="center")
epd.display_partial()
t1 = time.ticks_ms()
print('partial update in ms: '+str(time.ticks_diff(t1,t0)))
# update in ms: 3044


print("Test finished. Entering Sleep.")
epd.sleep()