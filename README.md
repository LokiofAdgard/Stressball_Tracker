# OpenCV Pan and Tilt Ball Tracker

## Introduction
This project showcases an object‑tracking system built with OpenCV and a servo‑mounted camera. The software identifies a predefined target in the camera’s field of view and continuously issues serial commands to a dedicated servo controller, ensuring the object remains centered on screen in real time. The hardware interface follows a fixed command syntax for pan and tilt control. Additionally, the system includes a mechanism for dynamically updating the target object, enabling adaptive tracking behavior.

### Controls
Run main.py to start the script.

| Key | Action (wrt World Frame)|
|----------|----------|
| p   | Start / Pause  |
| b   | Teaching Mode  |
| u   | Teach object  |
| q   | End simulation  |

## Methodology
The project consists of 4 scripts:
 - main.py
 - classicOCV.py
 - classicOCV.pyserialController.py
 - config.py

### classicOCV.py
This module contains all OpenCV‑related functionality. It initializes the camera, applies the necessary filtering operations, and performs object detection based on predefined parameters. The script displays both the filtered image and the final processed view, including the primary contour used for tracking. It outputs the horizontal and vertical pixel offsets (dx, dy) of the detected object relative to the image center.

The "process()" method represents the core of the object‑tracking workflow. It takes a raw camera frame as input and returns the horizontal and vertical pixel offsets (dx, dy) along with a boolean indicating whether the detected object is within the valid tracking range.
```python
def process(self, frame):
    mask = self.get_hsv_mask(frame)
    self.filtered = self.apply_filters(mask)
    contours = self.get_contours(self.filtered)
    selected, should_track = self.get_selected_contour(contours)

    out = self.draw_contours(frame, contours, selected)
    self.contour_frame, dx, dy = self.center_to_centroid(out, selected)

    return dx, dy, should_track
```

"get_hsv_mask()" converts the frame to HSV color space and applies thresholding to isolate pixels within the configured color range. It uses the default thresholds from the config file.
```python
def get_hsv_mask(self, frame):
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    lower = np.array([self.hueLow, self.satLow, self.valLow])
    upper = np.array([self.hueHigh, self.satHigh, self.valHigh])
    mask = cv2.inRange(hsv, lower, upper)
    return mask
```

"apply_filters()" first applies a median blur, then does erode/dilate to remove noise outside the target. Finally it does dialate/erode to remove noise inside the target. The kernel size and number of iterations are as defined in the config file.
```python
def apply_filters(self, mask):
    filtered = cv2.medianBlur(mask, FILTER_KERNEL_SIZE)
    filtered = cv2.erode(filtered, None, iterations=CLEAR_ITERATIONS)
    filtered = cv2.dilate(filtered, None, iterations=CLEAR_ITERATIONS)
    filtered = cv2.dilate(filtered, None, iterations=FILL_ITERATIONS)
    filtered = cv2.erode(filtered, None, iterations=FILL_ITERATIONS)
    return filtered
```

The "get_contours()" function returns all contours and the "get_selected_contour()" function finds the contour with the largest area. It then checks if this area is within the acceptable range set in the config file. It returns the selected contour and a boolean indicating whether the contour should be used for tracking
```python
def get_contours(self, mask):
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    return contours

def get_selected_contour(self, contours):
    if not contours:
        return None, False
    selected = max(contours, key=cv2.contourArea)
    area = cv2.contourArea(selected)
    
    track = True
    if(area < MIN_TRACK_AREA or area > MAX_TRACK_AREA):
        track = False

    return selected, track
```

"center_to_centroid()" finds the center of mass of the selected contour and finds the difference in pixels with the center of the frame. It also draws a line joining the center to centroid and displays the values dx, dy and area on the frame.
```python
def center_to_centroid(self, frame, selected_contour, cross_size=10,
                        cross_color=(0, 255, 255), centroid_color=(255, 0, 255),
                        cross_thickness=1, centroid_thickness=2):

    h, w = frame.shape[:2]
    cx, cy = w // 2, h // 2

    # Center cross
    cv2.line(frame, (cx - cross_size, cy), (cx + cross_size, cy), cross_color, cross_thickness)
    cv2.line(frame, (cx, cy - cross_size), (cx, cy + cross_size), cross_color, cross_thickness)

    if selected_contour is None:
        return frame, 0, 0

    M = cv2.moments(selected_contour)
    if M["m00"] == 0:
        return frame, 0, 0

    tx = int(M["m10"] / M["m00"])
    ty = int(M["m01"] / M["m00"])

    dx = tx - cx
    dy = ty - cy

    # Centroid to center
    cv2.line(frame, (cx, cy), (tx, ty), centroid_color, centroid_thickness)
    cv2.circle(frame, (tx, ty), 6, centroid_color, -1)

    # Display Pixel Delta
    cv2.putText(frame, f"dx: {dx}", (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, centroid_color, 2)
    cv2.putText(frame, f"dy: {dy}", (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.6, centroid_color, 2)
    cv2.putText(frame, f"area: {cv2.contourArea(selected_contour)}", (10, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.6, centroid_color, 2)

    return frame, (2 * dx / w), (2 * dy / h)
```

### serialController.py
This script receives dx and dy values and converts them into serial commands for the servo controller. It maintains the current servo position to compute relative movements and determines how pixel displacement translates into pan and tilt adjustments. It also defines communication parameters such as baud rate and transmission frequency.

The update() function adjusts self.x and self.y based on the incoming dx and dy values. The rate of response is controlled by the speedx and speedy parameters, which determine how aggressively the system reacts to the input offsets. Direction polarity can be flipped using the xinv and yinv configuration parameters, allowing quick inversion of the pan and tilt axes without modifying the core logic. Although update() is executed at high frequency, it only transmits a serial command when the configured com_period has elapsed since the previous transmission, ensuring efficient and rate‑limited communication.
```python
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
```

"send()" function generates a serial message in the predefined format "P T" where P and T are pan and tilt values from -1 to +1. It then transmits the command over serial if serial is available.
```python
def send(self):
    msg = f"{self.x:.3f} {self.y:.3f}\n"
    print(f"[SEND] {msg.strip()}")
    if self.ser and self.ser.is_open:
        try:
            self.ser.write(msg.encode('utf-8'))
        except serial.SerialException as e:
            print(f"[ERROR] Failed to write to serial port: {e}")
```

### config.py
A configuration file containing all preset values used across the system. This includes default openCV parameters, serial parameters and dynamic object tracking parameters.

### main.py
The main script instantiates the SerialController and ObjectTracker classes and coordinates their interaction to perform real‑time object tracking. It manages the primary execution loop, processes keyboard input, and triggers the appropriate system behaviors such as updating tracking parameters, toggling modes and terminating the program.

### Supplementary file: hsv_tuner.py
This utility script provides an interactive interface for tuning HSV color ranges. It opens the camera feed and displays adjustable sliders for minimum and maximum HSV values, allowing the user to manually determine optimal thresholds for object detection. Upon termination, the program prompts the user to copy the selected HSV values to the clipboard. These values can then be directly pasted into the config.py file to update the system’s default configuration.


## Discussion

## Links
 - [Github Repository](https://github.com/LokiofAdgard/Stressball_Tracker.git)
 - [Demonstration Video]()

## References
 - ChatGPT was used to generate the sliders interface for the hsv_tuner.py script