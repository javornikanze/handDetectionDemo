import math
from time import sleep

import cv2
from cvzone.HandTrackingModule import HandDetector
from cvzone.FPS import FPS
import socket
from math import sqrt
import os

# Initialize camera
print("Initializing camera...")
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("Error: Could not access the camera.")
else:
    print("Camera initialized.")

# Set resolution more explicitly
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
cap.set(cv2.CAP_PROP_FPS, 30)

# Verify the actual resolution
actual_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
actual_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
print(f"Actual resolution: {actual_width}x{actual_height}")


# Initialize HandDetector
print("Initializing Hand Detector...")
detector = HandDetector(staticMode=False, maxHands=2, modelComplexity=1, detectionCon=0.5, minTrackCon=0.5)
print("Hand Detector initialized.")
# Initialize FPS counter
fpsReader = FPS(avgCount=30)

# Initialize socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
serverAddressPort = ("127.0.0.1", 5053)

# Add this global variable to store smoothed data for both hands
smoothed_dataLeft = None
smoothed_dataRight = None

# Initialize smoothing parameter
alpha = 0.35  # Smoothing factor (0 = no smoothing, 1 = full smoothing)

leftHandInit = False
rightHandInit = False

# Gesture detection function with adjusted logic
def detect_gesture(hand):
    lmList = hand["lmList"]  # List of 21 landmarks
    fingers = [0, 0, 0, 0, 0]  # Thumb, Index, Middle, Ring, Pinky
    index_tip = lmList[8]
    index_points = [lmList[7], lmList[6], lmList[5]]
    wrist = lmList[0]

    wristToFinger = sqrt(pow(lmList[5][0] - wrist[0], 2) + pow(lmList[5][1] - wrist[1], 2))

    baseToTipIndex = sqrt(pow(index_tip[0] - lmList[5][0], 2) + pow(index_tip[1] - lmList[5][1], 2))
    baseToTipMiddle = sqrt(pow(lmList[9][0] - lmList[12][0], 2) + pow(lmList[9][1] - lmList[12][1], 2))
    baseToTipRing = sqrt(pow(lmList[13][0] - lmList[16][0], 2) + pow(lmList[13][1] - lmList[16][1], 2))
    baseToTipThumb = sqrt(pow(lmList[1][0] - lmList[4][0], 2) + pow(lmList[1][1] - lmList[4][1], 2))
    baseToTipPinky = sqrt(pow(lmList[17][0] - lmList[20][0], 2) + pow(lmList[17][1] - lmList[20][1], 2))

    #print(str(round(baseToTipThumb/wristToFinger, 2)) + ", " + str(round(baseToTipIndex / wristToFinger, 2)) + ", " + str(round(baseToTipMiddle / wristToFinger, 2)) + ", " + str(round(baseToTipRing / wristToFinger, 2)) + ", " + str(round(baseToTipPinky / wristToFinger, 2)))

    fingers = [baseToTipThumb / wristToFinger > 0.85, baseToTipIndex / wristToFinger > 0.8,
               baseToTipMiddle / wristToFinger > 0.85, baseToTipRing / wristToFinger > 0.85,
               baseToTipPinky / wristToFinger > 0.65]

    #print(wristToFinger / baseToTipIndex, baseToTipIndex)
    #print(fingers)
    #print(not fingers[1], not fingers[3], not fingers[4], baseToTipIndex > 60)

    avgX = 0
    avgY = 0
    maxPointDist = 0
    minPointDist = 0

    for p in index_points:
        avgX += p[0] - index_tip[0]
        avgY += p[1] - index_tip[1]
        newPointDist = sqrt(pow((p[0] - index_tip[0]), 2) + pow((p[1] - index_tip[1]), 2))
        if newPointDist > maxPointDist:
            maxPointDist = newPointDist
        if newPointDist < minPointDist:
            minPointDist = newPointDist

    avgX /= 3
    avgY /= 3
    avg = abs((avgX + avgY) / 2)
    #print(avg < 10)

    diff = abs(maxPointDist - minPointDist)
    #print(diff)


    if not fingers[1] and not fingers[3] and not fingers[4]:
        return "fist"

    if baseToTipIndex == 0 or wristToFinger / baseToTipIndex < 1.3 or diff < 60: #baseToTipIndex < 60
        if diff < 60 and not fingers[0]: #baseToTipIndex < 60
            return "forward"

        if fingers[2] or fingers[3] or fingers[4]: #if any other fingers are up just return
            return ""

        #print(avgX, avgY)
        if abs(avgX) > abs(avgY):
            if avgX > 0:
                return "right"
            else:
                return "left"
        else:
            if avgY > 0 and not fingers[0]:
                return "up"
            else:
                return "down"

    return ""

leftHandPoints = []
rightHandPoints = []
go_sleep = False

def avgPointDistance(handType, dataRight, dataLeft):
    avg = 0
    avg_other = 0
    global rightHandPoints, leftHandPoints, go_sleep
    #print(handType, len(dataRight))

    if len(dataRight) == 126:
        maybe_right1 = dataRight[0:63]
        maybe_right2 = dataRight[63:126]
        for i in range(21):
            avg += math.sqrt(
                pow(maybe_right1[i] - rightHandPoints[i], 2) + pow(maybe_right1[i + 1] - rightHandPoints[i + 1], 2) + pow(
                    maybe_right1[i + 2] - rightHandPoints[i + 2], 2))
            avg_other += math.sqrt(
                pow(maybe_right2[i] - rightHandPoints[i], 2) + pow(maybe_right2[i + 1] - rightHandPoints[i + 1], 2) + pow(
                    maybe_right2[i + 2] - rightHandPoints[i + 2], 2))

        avg /= 21
        avg_other /= 21
        if avg > avg_other:
            rightHandPoints = maybe_right2
        else:
            rightHandPoints = maybe_right1
    elif len(dataRight) == 63:
        rightHandPoints = dataRight


    if len(dataLeft) == 126:
        maybe_left1 = dataLeft[0:63]
        maybe_left2 = dataLeft[63:126]
        for i in range(21):
            avg += math.sqrt(
                pow(maybe_left1[i] - leftHandPoints[i], 2) + pow(maybe_left1[i + 1] - leftHandPoints[i + 1], 2) + pow(
                    maybe_left1[i + 2] - leftHandPoints[i + 2], 2))
            avg_other += math.sqrt(
                pow(maybe_left2[i] - leftHandPoints[i], 2) + pow(maybe_left2[i + 1] - leftHandPoints[i + 1], 2) + pow(
                    maybe_left2[i + 2] - leftHandPoints[i + 2], 2))

        avg /= 21
        avg_other /= 21
        if avg > avg_other:
            leftHandPoints = maybe_left2
        else:
            leftHandPoints = maybe_left1
    elif len(dataLeft) == 63:
        leftHandPoints = dataLeft

while True:
    success, img = cap.read()
    if not success:
        print("Failed to capture frame. Check your camera.")
        break

    hands, img = detector.findHands(img)
    dataLeft = []
    dataRight = []
    gestureLeft = ""
    gestureRight = ""

    if hands:
        for hand in hands:
            lmList = hand["lmList"]
            h, w, _ = img.shape
            for lm in lmList:
                mirrored_x = w - lm[0]
                #print(hand["type"])
                if hand["type"] == "Right":
                    dataRight.extend([mirrored_x, h - lm[1], lm[2]])
                elif hand["type"] == "Left":
                    dataLeft.extend([mirrored_x, h - lm[1], lm[2]])

            if len(rightHandPoints) == 0:
                rightHandPoints = dataRight
            if len(leftHandPoints) == 0:
                leftHandPoints = dataLeft

            avgPointDistance(hand["type"], dataRight, dataLeft)


            #gesture = detect_gesture(hand)
            #hand_type = hand["type"]  # Left or Right hand
            #print(f"{hand_type} Hand: {gesture}")
            if hand["type"] == "Left":
                gestureLeft = detect_gesture(hand)
            elif hand["type"] == "Right":
                gestureRight = detect_gesture(hand)

        #print("gestureLeft: " + gestureLeft + " gestureRight: " + gestureRight)
        #print("")
        #print(dataRight)
        #print(dataLeft)

        # Initialize smoothed_data with zeros if not already initialized
        if smoothed_dataLeft is None:
            smoothed_dataLeft = [0] * len(leftHandPoints)

        if smoothed_dataRight is None:
            smoothed_dataRight = [0] * len(rightHandPoints)

        if len(smoothed_dataRight) != len(rightHandPoints):
            smoothed_dataRight = [0] * len(rightHandPoints)

        if len(smoothed_dataLeft) != len(leftHandPoints):
            smoothed_dataLeft = [0] * len(leftHandPoints)

        # Apply smoothing to each point
        smoothed_dataLeft = [
            alpha * new + (1 - alpha) * old for new, old in zip(leftHandPoints, smoothed_dataLeft)
        ]

        smoothed_dataRight = [
            alpha * new + (1 - alpha) * old for new, old in zip(rightHandPoints, smoothed_dataRight)
        ]

        # Send the smoothed data
        dataLeftString = ""
        for x in smoothed_dataLeft:
            dataLeftString += str(round(x, 3)) + ","

        dataRightString = ""
        for x in smoothed_dataRight:
            dataRightString += str(round(x, 3)) + ","

        #print(dataLeftString[0:-1])
        #print(dataRightString[0:-1])
        sock.sendto(str.encode(gestureLeft + "|" + gestureRight + "|" + str(dataLeftString[0:-1]) + "|" + dataRightString[0:-1]), serverAddressPort)

    fps, img = fpsReader.update(img, pos=(20, 50), bgColor=(255, 0, 255), textColor=(255, 255, 255), scale=3, thickness=3)
    # Show the image (optional)
    cv2.imshow("Hand Tracking", img)

    if go_sleep:
        sleep(30)
        go_sleep = False

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
