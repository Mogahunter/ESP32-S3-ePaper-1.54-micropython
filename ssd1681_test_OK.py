from machine import Pin, SPI
import time

# ========== 引脚定义 ==========
EPD3V3_EN = 6     # 电源使能，输出低电平导通MOS管给屏幕供电
EPD_BUSY = 8      # 忙信号输入
EPD_RST = 9       # 复位输出
EPD_DC = 10       # 数据/命令选择
EPD_CS = 11       # 片选
EPD_SCLK = 12     # SPI时钟
EPD_SDI = 13      # SPI数据输入(MOSI)

# ========== 屏幕参数 ==========
EPD_WIDTH = 200   # 屏幕宽度
EPD_HEIGHT = 200  # 屏幕高度
EPD_BUFFER_SIZE = int(EPD_WIDTH * EPD_HEIGHT / 8)  # 5000字节

class EPD_GDEY0154D67:
    def __init__(self):
        # 初始化电源控制引脚
        self.epd3v3_en = Pin(EPD3V3_EN, Pin.OUT)
        self.epd3v3_en.value(1)  # 初始状态：关闭电源（高电平关闭MOS管）
        
        # 初始化其他引脚
        self.busy = Pin(EPD_BUSY, Pin.IN)
        self.rst = Pin(EPD_RST, Pin.OUT)
        self.dc = Pin(EPD_DC, Pin.OUT)
        self.cs = Pin(EPD_CS, Pin.OUT)
        
        # 拉高片选（空闲状态）
        self.cs.value(1)
        
        # 初始化SPI (10MHz, MSB first, Mode 0)
        self.spi = SPI(2, baudrate=10000000, polarity=0, phase=0,
                       sck=Pin(EPD_SCLK), mosi=Pin(EPD_SDI), miso=None)
        
        print("EPD 引脚初始化完成")
    
    def power_on(self):
        """开启屏幕电源：拉低GPIO6导通MOS管"""
        print("开启屏幕电源 (GPIO6拉低)...")
        self.epd3v3_en.value(0)  # 低电平导通MOS管
        time.sleep_ms(100)  # 等待电源稳定
    
    def power_off(self):
        """关闭屏幕电源"""
        print("关闭屏幕电源 (GPIO6拉高)...")
        self.epd3v3_en.value(1)  # 高电平关闭MOS管
    
    def spi_write(self, data):
        """SPI写入一个字节"""
        self.spi.write(bytes([data]))
    
    def write_command(self, cmd):
        """写入命令"""
        self.dc.value(0)  # DC=0 命令
        self.cs.value(0)
        self.spi_write(cmd)
        self.cs.value(1)
    
    def write_data(self, data):
        """写入数据"""
        self.dc.value(1)  # DC=1 数据
        self.cs.value(0)
        if isinstance(data, int):
            self.spi_write(data)
        else:
            self.spi.write(data)
        self.cs.value(1)
    
    def wait_busy(self):
        """等待屏幕忙信号释放"""
        print("等待屏幕就绪...")
        timeout = 0
        while self.busy.value() == 1:  # BUSY=1表示忙
            time.sleep_ms(10)
            timeout += 10
            if timeout > 5000:  # 5秒超时
                print("警告：等待超时")
                break
        print("屏幕就绪")
    
    def reset(self):
        """硬件复位"""
        print("复位屏幕...")
        self.rst.value(0)
        time.sleep_ms(10)
        self.rst.value(1)
        time.sleep_ms(10)
        self.wait_busy()
    
    def init_full(self):
        """全刷初始化（标准模式）"""
        print("全刷初始化...")
        self.reset()
        
        # 软件复位
        self.write_command(0x12)
        self.wait_busy()
        
        # Driver output control
        self.write_command(0x01)
        self.write_data(0xC7)
        self.write_data(0x00)
        self.write_data(0x00)
        
        # Data entry mode
        self.write_command(0x11)
        self.write_data(0x01)
        
        # Set Ram-X address start/end
        self.write_command(0x44)
        self.write_data(0x00)
        self.write_data(0x18)  # (24+1)*8=200
        
        # Set Ram-Y address start/end
        self.write_command(0x45)
        self.write_data(0xC7)  # 199+1=200
        self.write_data(0x00)
        self.write_data(0x00)
        self.write_data(0x00)
        
        # Border Waveform
        self.write_command(0x3C)
        self.write_data(0x05)
        
        # Reading temperature sensor
        self.write_command(0x18)
        self.write_data(0x80)
        
        # Set RAM x address count
        self.write_command(0x4E)
        self.write_data(0x00)
        
        # Set RAM y address count
        self.write_command(0x4F)
        self.write_data(0xC7)
        self.write_data(0x00)
        
        self.wait_busy()
        print("初始化完成")
    
    def init_fast(self):
        """快速刷新初始化"""
        print("快速刷新初始化...")
        self.reset()
        
        self.write_command(0x12)  # SWRESET
        self.wait_busy()
        
        self.write_command(0x18)  # Read built-in temperature sensor
        self.write_data(0x80)
        
        self.write_command(0x22)  # Load temperature value
        self.write_data(0xB1)
        self.write_command(0x20)
        self.wait_busy()
        
        self.write_command(0x1A)  # Write to temperature register
        self.write_data(0x64)
        self.write_data(0x00)
        
        self.write_command(0x22)  # Load temperature value
        self.write_data(0x91)
        self.write_command(0x20)
        self.wait_busy()
        print("快速初始化完成")
    
    def update_full(self):
        """全刷更新"""
        self.write_command(0x22)
        self.write_data(0xF7)
        self.write_command(0x20)
        self.wait_busy()
    
    def update_fast(self):
        """快刷更新"""
        self.write_command(0x22)
        self.write_data(0xC7)
        self.write_command(0x20)
        self.wait_busy()
    
    def clear(self, color=0xFF):
        """清屏"""
        print(f"清屏 (0x{color:02X})...")
        self.write_command(0x24)  # 写入黑白RAM
        
        # 发送5000字节数据
        data = bytes([color] * EPD_BUFFER_SIZE)
        for i in range(0, len(data), 256):
            chunk = data[i:i+256]
            self.write_data(chunk)
        
        self.update_full()
    
    def display_buffer(self, buffer):
        """显示缓冲区内容"""
        if len(buffer) != EPD_BUFFER_SIZE:
            print(f"错误：缓冲区大小应为{EPD_BUFFER_SIZE}字节，实际{len(buffer)}字节")
            return
        
        self.write_command(0x24)
        for i in range(0, len(buffer), 256):
            chunk = buffer[i:i+256]
            self.write_data(chunk)
        self.update_full()
    
    def display_buffer_fast(self, buffer):
        """快速显示缓冲区"""
        self.write_command(0x24)
        for i in range(0, len(buffer), 256):
            chunk = buffer[i:i+256]
            self.write_data(chunk)
        self.update_fast()
    
    def deep_sleep(self):
        """进入深度睡眠"""
        print("进入深度睡眠...")
        self.write_command(0x10)
        self.write_data(0x01)
        time.sleep_ms(100)


# ========== 测试图案 ==========

def create_checkerboard():
    """创建棋盘格图案"""
    buf = bytearray(EPD_BUFFER_SIZE)
    for y in range(EPD_HEIGHT):
        for x in range(EPD_WIDTH):
            byte_idx = y * 25 + x // 8  # 每行25字节 (200/8)
            bit_idx = 7 - (x % 8)
            if ((x // 20) + (y // 20)) % 2 == 0:
                buf[byte_idx] |= (1 << bit_idx)
    return buf

def create_stripes():
    """创建竖条纹"""
    buf = bytearray(EPD_BUFFER_SIZE)
    for y in range(EPD_HEIGHT):
        for x in range(EPD_WIDTH):
            byte_idx = y * 25 + x // 8
            bit_idx = 7 - (x % 8)
            if (x // 10) % 2 == 0:
                buf[byte_idx] |= (1 << bit_idx)
    return buf

def create_gradient():
    """创建渐变图案"""
    buf = bytearray(EPD_BUFFER_SIZE)
    for y in range(EPD_HEIGHT):
        threshold = y % 40
        for x in range(EPD_WIDTH):
            byte_idx = y * 25 + x // 8
            bit_idx = 7 - (x % 8)
            if x % 40 < threshold:
                buf[byte_idx] |= (1 << bit_idx)
    return buf


# ========== 主测试程序 ==========

def main():
    print("=" * 50)
    print("ESP32-S3 GDEY0154D67 墨水屏测试程序")
    print("=" * 50)
    
    # 创建EPD对象
    epd = EPD_GDEY0154D67()
    
    try:
        # 步骤1: 开启屏幕电源（拉低GPIO6）
        epd.power_on()
        
        # 步骤2: 初始化屏幕
        epd.init_full()
        
        # 测试1: 全白
        print("\n--- 测试1: 全白 ---")
        epd.clear(0xFF)  # 0xFF = 全白
        time.sleep(2)
        
        # 测试2: 全黑
        print("\n--- 测试2: 全黑 ---")
        epd.clear(0x00)  # 0x00 = 全黑
        time.sleep(2)
        
        # 测试3: 棋盘格
        print("\n--- 测试3: 棋盘格 ---")
        buf = create_checkerboard()
        epd.init_full()
        epd.display_buffer(buf)
        time.sleep(2)
        
        # 测试4: 竖条纹
        print("\n--- 测试4: 竖条纹 ---")
        buf = create_stripes()
        epd.init_full()
        epd.display_buffer(buf)
        time.sleep(2)
        
        # 测试5: 渐变图案
        print("\n--- 测试5: 渐变图案 ---")
        buf = create_gradient()
        epd.init_full()
        epd.display_buffer(buf)
        time.sleep(2)
        
        # 测试6: 快速刷新模式
        print("\n--- 测试6: 快速刷新模式 ---")
        epd.init_fast()
        buf_white = bytes([0xFF] * EPD_BUFFER_SIZE)
        buf_black = bytes([0x00] * EPD_BUFFER_SIZE)
        
        for i in range(3):
            print(f"  快速刷新 #{i+1}: 白->黑")
            epd.display_buffer_fast(buf_white)
            time.sleep(1)
            epd.display_buffer_fast(buf_black)
            time.sleep(1)
        
        # 最终：全白并进入睡眠
        print("\n--- 最终: 清屏并睡眠 ---")
        epd.init_full()
        epd.clear(0xFF)
        epd.deep_sleep()
        
        # 关闭电源
        epd.power_off()
        
        print("\n" + "=" * 50)
        print("测试完成！")
        print("=" * 50)
        
    except Exception as e:
        print(f"\n错误: {e}")
        epd.power_off()
        raise


main()