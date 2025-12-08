from classicOCV import *
from serialController import *

cap = cv2.VideoCapture(1, cv2.CAP_DSHOW)
if not cap.isOpened():
    print("Error: Could not open camera.")
    exit()

controller = SerialController()
tracker = ObjectTracker()

try:
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        dx, dy = tracker.process(frame)

        controller.update(dx, dy)
        tracker.draw_center_box()

        cv2.imshow("Filtered Video", tracker.filtered)
        cv2.imshow("Contours", tracker.contour_frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('u'):
            tracker.get_center_hsv_range(tracker.contour_frame)
        elif key == ord('b'):
            tracker.dynBox = not tracker.dynBox
        elif key == ord('p'):
            controller.paused = not controller.paused

finally:
    cap.release()
    cv2.destroyAllWindows()
