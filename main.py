from classicOCV.functions import *
from serialController.functions import *

cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
if not cap.isOpened():
    print("Error: Could not open camera.")
    exit()

controller = SerialController(port="COM3", baud=115200, com_period=0.2, speed=0.01)
tracker = ObjectTracker()

try:
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        dx, dy = tracker.process(frame)

        controller.update(dx, dy)

        cv2.imshow("Filtered Video", tracker.filtered)
        cv2.imshow("Contours", tracker.contour_frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

finally:
    cap.release()
    cv2.destroyAllWindows()
