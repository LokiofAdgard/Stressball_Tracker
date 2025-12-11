import cv2
import numpy as np
from config import *

class ObjectTracker:
    def __init__(self):
        self.filtered = None
        self.contour_frame = None

        self.hueLow = HueLow
        self.hueHigh = HueHigh
        self.satLow = SatLow
        self.satHigh = SatHigh
        self.valLow = ValLow
        self.valHigh = ValHigh

        self.dynBox = False

    def get_hsv_mask(self, frame):
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        lower = np.array([self.hueLow, self.satLow, self.valLow])
        upper = np.array([self.hueHigh, self.satHigh, self.valHigh])
        mask = cv2.inRange(hsv, lower, upper)
        return mask

    def apply_filters(self, mask):
        filtered = cv2.medianBlur(mask, FILTER_KERNEL_SIZE)
        filtered = cv2.erode(filtered, None, iterations=CLEAR_ITERATIONS)
        filtered = cv2.dilate(filtered, None, iterations=CLEAR_ITERATIONS)
        filtered = cv2.dilate(filtered, None, iterations=FILL_ITERATIONS)
        filtered = cv2.erode(filtered, None, iterations=FILL_ITERATIONS)
        return filtered

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

    def draw_contours(self, frame, contours, selected):
        out = frame.copy()
        # if contours:
        #     cv2.drawContours(out, contours, -1, (0, 255, 0), 2)

        if selected is not None:
            cv2.drawContours(out, [selected], -1, (0, 0, 255), 3)
            x, y, w, h = cv2.boundingRect(selected)
            cv2.rectangle(out, (x, y), (x + w, y + h), (255, 0, 0), 2)
        return out

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

    def process(self, frame):
        mask = self.get_hsv_mask(frame)
        self.filtered = self.apply_filters(mask)
        contours = self.get_contours(self.filtered)
        selected, should_track = self.get_selected_contour(contours)

        out = self.draw_contours(frame, contours, selected)
        self.contour_frame, dx, dy = self.center_to_centroid(out, selected)

        return dx, dy, should_track

    def get_center_hsv_range(self, frame, n=boxSize, low_pct=40, high_pct=60):
        h, w, _ = frame.shape
        cx, cy = w // 2, h // 2

        x1, x2 = cx - n//2, cx + n//2
        y1, y2 = cy - n//2, cy + n//2

        x1, y1 = max(x1, 0), max(y1, 0)
        x2, y2 = min(x2, w), min(y2, h)

        roi = frame[y1:y2, x1:x2]
        hsv_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)

        # Flatten to 2D array of pixels
        pixels = hsv_roi.reshape(-1, 3)

        # Percentile per channel
        min_vals = np.percentile(pixels, low_pct, axis=0)
        max_vals = np.percentile(pixels, high_pct, axis=0)

        self.hueLow  = np.clip(int(min_vals[0]) - hueAllowance, 0, 179)
        self.satLow  = np.clip(int(min_vals[1]) - satAllowance, 0, 255)
        self.valLow  = np.clip(int(min_vals[2]) - valAllowance, 0, 255)

        self.hueHigh = np.clip(int(max_vals[0]) + hueAllowance, 0, 179)
        self.satHigh = np.clip(int(max_vals[1]) + satAllowance, 0, 255)
        self.valHigh = np.clip(int(max_vals[2]) + valAllowance, 0, 255)

        # print(self.hueLow, self.hueHigh)
        # print(self.satLow, self.satHigh)
        # print(self.valLow, self.valHigh)

        print("Target Updated")

    def draw_center_box(self, n=boxSize):
        if (not self.dynBox):
            return
        h, w, _ = self.contour_frame.shape
        cx, cy = w // 2, h // 2

        x1, x2 = cx - n//2, cx + n//2
        y1, y2 = cy - n//2, cy + n//2

        cv2.rectangle(self.contour_frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
        self.contour_frame = self.contour_frame
