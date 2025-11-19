import time
import serial

class SerialController:
    def __init__(self, port="COM4", baud=9600, prescaler=1):
        self.x = 0.0
        self.y = 0.0
        self.speed = 0.01
        self.last_sent_time = time.time()

        self.xinv = True
        self.yinv = True

        self.prescaler = prescaler
        self._counter = 0

        self.ser = None
        try:
            self.ser = serial.Serial(port, baud, timeout=0.1)
            print(f"[INFO] Opened serial port {port} at {baud} baud.")
        except serial.SerialException as e:
            print(f"[ERROR] Could not open serial port {port}: {e}")

    def clamp(self, v):
        return max(-1.0, min(1.0, v))

    def update(self, dx, dy):
        if self.xinv:
            dx = -dx
        if self.yinv:
            dy = -dy
        self.x = self.clamp(self.x + (dx * self.speed))
        self.y = self.clamp(self.y + (dy * self.speed))

        # self._counter += 1
        # if self._counter >= self.prescaler:
        #     self._counter = 0
        #     self.send()

        if time.time() > (self.last_sent_time + 1):
            self.send()
            # print("e")
            self.last_sent_time = time.time()

    def send(self):
        msg = f"{self.x:.3f} {self.y:.3f}\n"
        # print(f"[SEND] {msg.strip()}")
        if self.ser and self.ser.is_open:
            try:
                self.ser.write(msg.encode('utf-8'))
            except serial.SerialException as e:
                print(f"[ERROR] Failed to write to serial port: {e}")

    def set_prescaler(self, n):
        self.prescaler = max(1, int(n))
        print(f"[INFO] Prescaler set to {self.prescaler}")
