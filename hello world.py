from epd_gdey0154d67 import create_epd, EPD_WIDTH, EPD_HEIGHT

# 创建并初始化屏幕
epd, renderer = create_epd()

# 清屏
epd.fill(0xFF)
epd.display()

# 计算居中位置
text = "Hello World"
text_width = renderer.get_text_width(text)
x = (EPD_WIDTH - text_width) // 2
y = (EPD_HEIGHT - 8) // 2

# 绘制文字并显示
renderer.draw_text(text, x, y, color=0)
epd.display()

# 睡眠省电
# epd.deep_sleep()
# epd.power_off()