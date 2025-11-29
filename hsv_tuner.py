import cv2
import numpy as np
import pyperclip

def nothing(x):
    pass

cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)

cv2.namedWindow("Controls")
cv2.createTrackbar("H Low", "Controls", 0, 179, nothing)
cv2.createTrackbar("S Low", "Controls", 0, 255, nothing)
cv2.createTrackbar("V Low", "Controls", 0, 255, nothing)
cv2.createTrackbar("H High", "Controls", 179, 179, nothing)
cv2.createTrackbar("S High", "Controls", 255, 255, nothing)
cv2.createTrackbar("V High", "Controls", 255, 255, nothing)

while True:
    ret, frame = cap.read()
    if not ret:
        break

    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    hL = cv2.getTrackbarPos("H Low", "Controls")
    sL = cv2.getTrackbarPos("S Low", "Controls")
    vL = cv2.getTrackbarPos("V Low", "Controls")
    hH = cv2.getTrackbarPos("H High", "Controls")
    sH = cv2.getTrackbarPos("S High", "Controls")
    vH = cv2.getTrackbarPos("V High", "Controls")

    lower = np.array([hL, sL, vL])
    upper = np.array([hH, sH, vH])
    mask = cv2.inRange(hsv, lower, upper)
    output = cv2.bitwise_and(frame, frame, mask=mask)

    cv2.imshow("HSV Output", output)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()

choice = input("\nCopy slider values to clipboard? (y/n): ").strip().lower()

if choice == "y":
    text = (
        f"HueLow = {hL}\n"
        f"HueHigh = {hH}\n"
        f"SatLow = {sL}\n"
        f"SatHigh = {sH}\n"
        f"ValLow = {vL}\n"
        f"ValHigh = {vH}"
    )
    pyperclip.copy(text)
    print("\nCopied to clipboard:\n")
    print(text)
else:
    print("Not copied.")
