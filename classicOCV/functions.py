import cv2
import numpy as np
from classicOCV.config import *

class ObjectTracker:
    def __init__(self):
        self.filtered = None
        self.contour_frame = None

    def get_hsv_mask(self, frame):
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        lower = np.array([HueLow, SatLow, ValLow])
        upper = np.array([HueHigh, SatHigh, ValHigh])
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
            return None
        return max(contours, key=cv2.contourArea)

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

        return frame, (2 * dx / w), (2 * dy / h)

    def process(self, frame):
        mask = self.get_hsv_mask(frame)
        self.filtered = self.apply_filters(mask)
        contours = self.get_contours(self.filtered)
        selected = self.get_selected_contour(contours)

        out = self.draw_contours(frame, contours, selected)
        self.contour_frame, dx, dy = self.center_to_centroid(out, selected)

        return dx, dy
