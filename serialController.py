import time
import serial
from config import *

class SerialController:
    def __init__(self, port=comPort, baud=baudRate, com_period=comPeriod, speedx=speedx, speedy=speedy, xinv=xinv, yinv=yinv):
        self.x = 0.0
        self.y = 0.0
        self.ser = None
        
        self.speedx = speedx
        self.speedy = speedy
        self.com_period = com_period
        self.last_sent_time = time.time()
        self.xinv = xinv
        self.yinv = yinv

        self.paused = True
        
        try:
            self.ser = serial.Serial(port, baud, timeout=0.1)
            print(f"[INFO] Opened serial port {port} at {baud} baud.")
        except serial.SerialException as e:
            print(f"[ERROR] Could not open serial port {port}: {e}")

    def clamp(self, v):
        return max(-1.0, min(1.0, v))

    def update(self, dx, dy):
        if(self.paused):
            return
        
        if self.xinv:
            dx = -dx
        if self.yinv:
            dy = -dy
        self.x = self.clamp(self.x + (dx * self.speedx))
        self.y = self.clamp(self.y + (dy * self.speedy))

        if time.time() > (self.last_sent_time + self.com_period):
            self.send()
            self.last_sent_time = time.time()

    def send(self):
        msg = f"{self.x:.3f} {self.y:.3f}\n"
        print(f"[SEND] {msg.strip()}")
        if self.ser and self.ser.is_open:
            try:
                self.ser.write(msg.encode('utf-8'))
            except serial.SerialException as e:
                print(f"[ERROR] Failed to write to serial port: {e}")

