from classicOCV.functions import *
from serialController.functions import *

cap = cv2.VideoCapture(1, cv2.CAP_DSHOW)
if not cap.isOpened():
    print("Error: Could not open camera.")
    exit()

controller = SerialController(port="COM3", baud=9600, prescaler=5)

try:
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        mask = get_hsv_mask(frame)
        filtered = apply_filters(mask)
        contours = get_contours(filtered)
        selected = get_selected_contour(contours)
        contour_frame = draw_contours(frame, contours, selected)
        contour_frame, dx, dy = center_to_centroid(contour_frame, selected)

        controller.update(dx, dy)

        cv2.imshow("Filtered Video", filtered)
        cv2.imshow("Contours", contour_frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

finally:
    cap.release()
    cv2.destroyAllWindows()
