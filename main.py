from classicOCV.functions import *
import serial

cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("Error: Could not open camera.")
    exit()

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

    cv2.imshow("Filtered Video", filtered)
    cv2.imshow("Contours", contour_frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
