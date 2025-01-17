from vidgear.gears import ScreenGear
import cv2
import pygetwindow as gw
import numpy as np
from decimal import Decimal
import sys
import platform
import time
import random
import pyautogui
from pynput.keyboard import Key, Listener, KeyCode, Controller

# Check if we are running lower version of Python and exit, as we need Python 3.10 or higher
if sys.version_info[0] <= 3 and sys.version_info[1] < 10:
    print("FATAL ERROR: SHIT'S FUCKED")
    raise EnvironmentError("ERROR: Please use Python 3.10 and above!")
    sys.exit(0)

print("================================")
print("Thrym 2.0 - Odin's Eye Starting.")
print("Now with Fair Fight technology! ")
print("================================")

pyautogui.PAUSE = 0.01
# It's stupid, just ignore the names and use x1, y1, x2, y2
options = {"left": 380, "top": 250, "width": 1920, "height": 1080}
# ROI (Left, Top, Width, Height)
noteROI = (64, 352, 1035, 280)
# Note size to be detected (Min, Max) - You need to see if things are working correctly
noteSize = (5000, 24000)
# Note color (H, S, V)
noteColor = (147, 255, 48)
# Note color tolerance (-/+n from set value)
# Wrong color list: 
# Nidavallir water is 131,172,197
# Midgard water near the center is 149,174,56
noteColorTol = (7, 5)
# Note saturation
noteSaturation = (49, 255)
# Note brightness
noteBrightness = (40, 255)
# Adaptive block thresholding parameters
erosionConstant = 9
blockSize = 5
constantOffset = 5
# When to hit the notes
beatLine = (1099, 450)

# Shield detection area
# ROI (Left, Top, Width, Height)
shieldROI = (1415, 655, 100, 145)

shieldLvl0 = (128, 128, 128)
shieldLvl1 = (255, 255, 0)
shieldLvl2 = (0, 255, 255)

# State machine variable
sm_Shield = 0

# Fair Fight config
ff_State = 0
ff_Level = 8
toggleOutput = True

# Fair Fight fatigue simulation
# Changing this to True will disable the conventional fixed difficulty system
ff_fatigueEnabled = True
# Current level variable
ff_fatigueLevel = 0.0
# How fast should Thrym get tired? (addition of score per note pair)
ff_fatigueSpeed = 0.01
# How many keys were pressed so far
ff_keyStack = 0
# After this time, the fatigue timer should reset
ff_fatigueTimer = 5.0
ff_currentTime = 0.0
ff_fatigueTemp = 0.0
# Window title detection
targetWin = "Ragnarock "
#targetWin = "Ragnarock.txt - Notepad"

font=cv2.FONT_HERSHEY_SIMPLEX
stream = ScreenGear(logging=True, **options).start()
stream.color_space = cv2.COLOR_RGB2BGR
# prometheus = Controller()

def on_press(*key):
    global ff_Level
    global ff_fatigueSpeed
    global toggleFatigue
    # Read keys and see if it's V, B or N 
    # V = Lower level, B = Higher level, N = Disable key output until pressed again
    
    # tbh I have no idea what I am doing here because the documentation does not mention whether or not it will return lowercase or uppercase letter
    # print("Received", key)
    # print(key)
    finger = key[0]
    if finger == KeyCode.from_char("v") and ff_fatigueEnabled == False:
        ff_Level -= 1
    elif finger == KeyCode.from_char("v") and ff_fatigueEnabled == True:
        if ff_fatigueSpeed >= 0.02:
            ff_fatigueSpeed -= 0.01
        else: 
            ff_fatigueSpeed = 0.01
        print("Fatigue speed:", ff_fatigueSpeed)
    elif finger == KeyCode.from_char("b") and ff_fatigueEnabled == False:
        ff_Level += 1
    elif finger == KeyCode.from_char("b") and ff_fatigueEnabled == True:
        if ff_fatigueSpeed < 1.0:
            ff_fatigueSpeed += 0.01
        else: 
            ff_fatigueSpeed = 1.0
        print("Fatigue speed:", ff_fatigueSpeed)
    elif finger == KeyCode.from_char("n"):
        xyz = enableOutput()
    elif finger == KeyCode.from_char("m"):
        abc = toggleFatigue()
    # Cap the value of level to 0~9
    if ff_Level > 9:
        ff_Level = 9
    elif ff_Level < 0:
        ff_Level = 0

def doNothing(x):
    # Discard input
    pass

listener = Listener(on_press=on_press, on_release=doNothing)
listener.start()    

def maskArea(frame):
    # Area must be defined first
    # area01 = Left side to the middle
    # area02 = Right side
    area01 = np.array([[[0,0], [541,0], [541,87], [45,550], [45, 831], [0, 831]]], np.int32)
    area02 = np.array([[[617,0], [1542,0], [1542, 622], [1387, 622], [1387, 831], [1120, 832], [1120, 550], [617, 87]]], np.int32)
    frame = cv2.fillPoly(frame, area01, (0,0,0))
    frame = cv2.fillPoly(frame, area02, (0,0,0))
    
    return frame

def calcROIArea(left, top, width, height, image_x, image_y):
    # Within image_x and image_y, calculate the area of pixels requested
    # Add small delay to lower CPU usage
    time.sleep(0.001)
    # Convert all values to integer
    left = int(left)
    top = int(top)
    width = int(width)
    height = int(height)
    
    # Pre-calculate the area first regardless of its validity
    x2 = left + width
    y2 = top + height
    
    if image_x < 0 or image_y < 0:
        raise ValueError("Image size cannot be less than 0!")
    elif image_x - width < 0 or image_y - height < 0:
        raise ValueError("Area size too large!")
    elif left > image_x or top > image_y:
        raise ValueError("Capture area offset exceeds the screen size!")
    elif x2 > image_x or y2 > image_y:
        raise ValueError("Area size exceeds input image size!")
    else:
        return [top, y2, left, x2]

def clamp(n, minn, maxn):
    return max(min(maxn, n), minn)

def calcColorRange(h, tolerance):
    # First calculate the values without checking its validity
    hMin = h - tolerance[0]
    hMax = h + tolerance[1]
    # Clamp value to maximum and minimum value
    hMin = clamp(hMin, 0, 255)
    hMax = clamp(hMax, 0, 255)
    # Just to be safe... (HSV calculation explodes if it's over 255 or under 0)
    if hMin < 0:
        hMin = 0
    elif hMax > 255:
        hMax = 255
    else:
        # Return the result
        return [hMin, hMax]

def isShieldActive(frame, x, y, w, h):
    # Add small delay to lower CPU usage
    time.sleep(0.001)
    # Trim input frame to size
    frame = frame[y:y+h, x:x+w]
    # Hack: Flip "RGB" image to "BGR"
    frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
    # Convert input frame to HSV colorspace
    colorbug = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV_FULL)
    # Convert this one to grayscale for the brightness comparison
    shieldROI = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    # Tune this part to avoid triggering on hammer and camera shakes
    (asdf, thres) = cv2.threshold(shieldROI, 127, 255, 0)
    # Blur image to reduce noise
    blur = cv2.GaussianBlur(thres, (3, 3), 0)
    # Finally apply Otsu's Threshold to clean up image
    aaaaa, final = cv2.threshold(blur, -1, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
    # Look for white things in image
    mean_V = np.mean(final[:, :])
    # What is the color closest to?
    mean_H = np.mean(colorbug[:, :, 0])
    # Set color upper and lower bounds
    yellowBound = [26,44]
    cyanBound = [100,145]
    lumaBound = [25, 40]
    # lumaBound = [25, 140]
    # Initialize variables
    isActive = False
    comboLevel = 0
    # Apply logic to prevent most of the false positives
    if lumaBound[0] <= mean_V <= lumaBound[1]:
        isActive = True
    else:
        isActive = False
    # Do maths
    if cyanBound[0] <= mean_H <= cyanBound[1]:
    # if isBlue == True and isYellow == False:
        comboLevel = 1
    elif yellowBound[0] <= mean_H <= yellowBound[1]:
    # elif isBlue == False and isYellow == True:
        comboLevel = 2
    else:
        isActive = False
        comboLevel = 0
    # print("Hue:", Decimal(mean_H).quantize(Decimal("1.0000")), "Brightness:", Decimal(mean_V).quantize(Decimal("1.0000")), "isActive:", isActive, "Level:", comboLevel)
    return (isActive, comboLevel)

def checkRanges(value1, value2):
    # Add small delay to lower CPU usage
    time.sleep(0.001)
    ranges = [
    (50, 400), 
    (430, 570), 
    (600, 790), 
    (830, 1110)
    ]
    
    # Check which range the first value belongs to
    range_index1 = None
    for i, (start, end) in enumerate(ranges):
        if start <= value1 <= end:
            range_index1 = i
            break

    # Check if the second value is above a certain threshold
    condition_met = value2 > beatLine[1]

    # Return True for the first range if both conditions are met
    return condition_met, range_index1

def erodeFrame(frame):
    # 0 = Rect, 1 = Cross, 2 = Ellipse
    shape = 2
    
    if shape == 0:
        shape = cv2.MORPH_RECT
    elif shape == 1:
        shape = cv2.MORPH_CROSS
    elif shape == 2:
        shape = cv2.MORPH_ELLIPSE
    else:
        shape = cv2.MORPH_RECT
    
    # element = cv2.getStructuringElement(shape, (2 * erosionConstant + 1, 2 * erosionConstant + 1))
    element = np.ones((erosionConstant,erosionConstant),np.uint8)
    result = cv2.erode(frame, element)
    
    return result
    
def buildKeyCombo(list):
    global conv
    conv = [False, False, False, False]

    for sublist in list:
        # Extract the first and second values of the sublist
        value1, value2 = sublist[0], sublist[1]
        # Check the ranges for the first value and the condition for the second value
        condition_met, range_index1 = checkRanges(value1, value2)
        # Update the results list based on the conditions
        if range_index1 is not None:
            if condition_met:
                conv[range_index1] = True        
        else:
            print("OOPS! Pls tune your settings.")
    # print(list, conv)
    return conv


def createKeys(inputList):
    # List valid key combinations
    in_valid = [(False, False, False, False), (True, False, False, False), (False, True, False, False), (False, False, True, False), (False, False, False, True), (True, True, False, False), (True, False, True, False), (True, False, False, True), (False, True, False, True), (False, True, True, False), (False, False, True, True)]
    #int_valid = [[False, False, False, False], [True, False, False, False], [False, True, False, False], [False, False, True, False], [False, False, False, True], [True, True, False, False], [True, False, True, False], [True, False, False, True], [False, True, False, True], [False, True, True, False], [False, False, True, True]]
    
    # If input is all False, do not do anything and send empty list
    if not any(inputList):
        return []
    # If input is all True, then send empty list
    if all(inputList):
        return []
    # Catch malformed list with less than 4 or more than 4 values
    if len(inputList) != 4:
        raise ValueError("Something went wrong!! Input length incorrect!!")
    # Catch malformed list with non-Boolean values
    if not all(isinstance(value, bool) for value in inputList):
        raise ValueError("ERROR: Incorrect list content, acceptable type: Bool.")
        
    # If input has 3 True values...
    if inputList.count(True) == 3:
        # Change the rightmost True value to False
        # inputList[inputList.index(True, 0, 3)] = False
        # Even dumber approach
        if inputList == [True, True, True, False]:
            inputList = [True, True, False, False]
        elif inputList == [False, True, True, True]:
            inputList = [False, False, True, True]
        
    # Lookup table for output
    keystrokes = { 
        (False, False, False, False): [],
        (True, False, False, False): ["q"], 
        (False, True, False, False): ["w"], 
        (False, False, True, False): ["o"], 
        (False, False, False, True): ["p"], 
        (True, True, False, False): ["q", "i"], 
        (True, False, True, False): ["q", "o"], 
        (True, False, False, True): ["q", "p"], 
        (False, True, False, True): ["w", "p"], 
        (False, True, True, False): ["w", "o"], 
        (False, False, True, True): ["e", "p"]
        }
    keyResult = keystrokes.get(tuple(inputList), [])
    return keyResult

def enableOutput():
    global toggleOutput
    # When N is pressed
    if toggleOutput == True:
        toggleOutput = False
    elif toggleOutput == False:
        toggleOutput = True
    else:
        toggleOutput = True
    print("Fair Fight output enabled:", toggleOutput)
    return None    

def toggleFatigue():
    global ff_fatigueEnabled
    # When M is pressed
    if ff_fatigueEnabled == True:
        ff_fatigueEnabled = False
    elif ff_fatigueEnabled == False:
        ff_fatigueEnabled = True
    else:
        ff_fatigueEnabled = False
    print("Fatigue mode enabled:", ff_fatigueEnabled)
    return None 

def fatigueSim(input, level):
    global ff_keyStack
    global ff_fatigueSpeed
    global ff_fatigueTimer
    global ff_fatigueLevel
    global ff_currentTime
    global ff_fatigueTemp
    
    if ff_fatigueSpeed < 0.01:
        ff_fatigueSpeed = 0.01
    
    if level > 4:
        min_value = 100 - (level * 10)
    else:
        min_value = 70
    
    if len(input) >= 1:
        ff_keyStack += 1
        # print("Detected", ff_keyStack, "notes")
        ff_currentTime = 0
        
    if len(input) == 0:
        ff_currentTime += 0.01
        # print("Time: ", ff_currentTime)
    # If left idle for x amount of time:
    if ff_fatigueTimer < ff_currentTime:
        ff_keyStack = 0
    
    ff_fatigueLevel = ff_keyStack * ff_fatigueSpeed + min_value
    
    # Hard cap at 90%
    if ff_fatigueLevel > 90.0:
        ff_fatigueLevel = 90.0
    # print("Fatigue:", ff_fatigueLevel)
    return ff_fatigueLevel
    
def fairFightGovernor(input, shieldActive, shieldLevel, level, toggleOutput):
    global sm_Shield
    global ff_keyStack
    # Add small delay to lower CPU usage
    time.sleep(0.001)
    
    fatigueSimOutput = fatigueSim(input, level)
    
    shieldEnabled = True
    if len(input) > 0 and ff_fatigueEnabled == False:
        # print(input, shieldActive, shieldLevel, level, toggleOutput)
        if level is not None and toggleOutput is True:
            # print("FF output is enabled")
            # Cap the value of level to 0~9
            if int(level) > 9:
                level = 9
            elif int(level) < 0:
                level = 0
            # Dummy = 0 (only hits 1 in 2 notes, shield disabled)
            # Easy = 1~2 (only misses 1 in 4~5 notes, shield disabled)
            # Medium = 3~5 (only misses 1 in 6~8 notes, shield enabled)
            # Hard = 6~8 (only misses 1 in 9~11 notes, shield enabled)
            # Expert = 9 (No changes)
            if level < 9:
                # Some huge default value to handle errors
                cfg_missChance = 100
                
                if level == 0:
                    # Disable shield
                    cfg_missChance = 90
                    sm_Shield = 0
                    shieldEnabled = False
                elif level == 1:
                    # Disable shield
                    cfg_missChance = 80
                    sm_Shield = 0
                    shieldEnabled = False
                elif level == 2:
                    # Disable shield
                    cfg_missChance = 70
                    sm_Shield = 0
                    shieldEnabled = False
                elif level == 3:
                    # Disable shield
                    cfg_missChance = 60
                    sm_Shield = 0
                    shieldEnabled = False
                elif level == 4:
                    # Disable shield
                    cfg_missChance = 50
                    sm_Shield = 0
                    shieldEnabled = False
                elif level == 5:
                    # Disable shield
                    cfg_missChance = 40
                    sm_Shield = 0
                    shieldEnabled = False
                elif level == 6:
                    cfg_missChance = 30
                    shieldEnabled = True
                elif level == 7:
                    cfg_missChance = 20
                    shieldEnabled = True
                elif level == 8:
                    cfg_missChance = 10
                    shieldEnabled = True
                
                discard = random.randint(1, 100)
                
                if discard < cfg_missChance:
                    # print("Input discarded!")
                    return ([], False, 0, False)
                else:
                    # print(input)
                    return (input, shieldActive, shieldLevel, shieldEnabled)
            else:
                # print(input)
                return (input, shieldActive, shieldLevel, True)
        
        elif level is not None and toggleOutput is False:
            # print("FF output is disabled")
            # Discard everything and return a fake config
            return ([], False, 0, False)
        else:
            raise ValueError("Fair Fight configuration error!")
    
    elif len(input) > 0 and ff_fatigueEnabled == True:
        # Define a fallback value just in case
        nuancedMissChance = 100.0
        discardChance = random.uniform(0.0, nuancedMissChance)
        if discardChance < fatigueSimOutput:
            ff_keyStack -= 2
            if ff_keyStack < 0:
                ff_keyStack = 0
            return ([], False, 0, False)
        else:
            return (input, shieldActive, shieldLevel, shieldEnabled)
    else:
        return ([], False, 0, False)

def sendKeys(input, shieldActive, shieldLevel, enable):
    #print("Prometeus hears:", input)
    global sm_Shield
    cwin = gw.getWindowsWithTitle(targetWin)
    if cwin is not None:
        isSafe = cwin[0].isActive
    # print(isSafe)
    # Only send the keystrokes to game window
    if isSafe == True:
        #print("Win focused")
        # Time to send the keys
        if len(input) > 0:
            #print("Prometeus hits:", input)
            pyautogui.press(input)
        # If it manages to build up enough combos, try to use it
        if shieldActive == True and shieldLevel == 2 and enable == True:
            sm_Shield += 1
            if sm_Shield > 8:
                pyautogui.press("s")
                pyautogui.press(Key.space)
                # Reset state machine to 0
                sm_Shield = 0
    #else:
        # print("WARN: Window not in focus! No keystrokes will be sent.")

def detectNotes(frame, min_size, max_size):
    global options
    global toggleOutput
    # Add small delay to lower CPU usage
    time.sleep(0.001)
    
    # Mask off areas
    frame = maskArea(frame)
    # This time please handle the ROI area calculation correctly
    frame = cv2.GaussianBlur(frame, (7, 7), 0)
    # Extract the dimensions of the frame
    image_y, image_x, _ = frame.shape
    
    # Define the region of interest (ROI) based on input coordinates
    areaSize = calcROIArea(noteROI[0], noteROI[1], noteROI[2], noteROI[3], options.get("width"), options.get("height"))
    # print(areaSize)
    # Crop the frame
    area = frame[areaSize[0]:areaSize[1], areaSize[2]:areaSize[3]]
    # Hack to convert "RGB" colors back to true colors as it is flipped in the source
    # frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    # Convert the frame to the HSV color space
    hsv = cv2.cvtColor(area, cv2.COLOR_BGR2HSV_FULL)
    
    # Generate color ranges
    colors = calcColorRange(noteColor[0], noteColorTol)
    
    # Define the lower and upper bounds of the blue color in HSV
    lower_blue = np.array([colors[0], noteSaturation[0], noteBrightness[0]])
    upper_blue = np.array([colors[1], noteSaturation[1], noteBrightness[1]])

    # Create a binary mask of the blue objects
    blue_mask = cv2.inRange(hsv, lower_blue, upper_blue)
    # Apply Gaussian blur so noisy elements are removed mostly
    blue_mask = cv2.GaussianBlur(blue_mask, (11, 11), 0)
    
    # Erode the result to remove small particles
    blue_mask = erodeFrame(blue_mask)
    # Apply adaptive thresholding
    #blue_mask = cv2.adaptiveThreshold(blue_mask, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, blockSize, constantOffset)
    # Apply further thresholding to remove noise
    vfdfg, blue_mask = cv2.threshold(blue_mask, -1, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
    
    # Find contours in the binary mask
    contours, _ = cv2.findContours(blue_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contoursList = []
    # Iterate through the contours
    for contour in contours:
        # Calculate the area of each contour
        area = int(cv2.contourArea(contour))
        # Check if the area is within the specified size range
        if min_size < area < max_size:
            # print("Area: ", area)
            # Get the bounding box coordinates
            x, y, w, h = map(int, cv2.boundingRect(contour))
            # Fix for the wrong offset
            x += noteROI[0]
            y += noteROI[1]
            # print(x, y, w, h)
            contoursList.append([x+w, y+h])
            if y >= beatLine[1]:
                rectColor = (0, 0, 255)
            else:
                rectColor = (0, 255, 0)
            # Draw a rectangle around the blue object
            cv2.rectangle(frame, (x, y), (x+w, y+h), rectColor, 2)
            text = str(x+w) + ", " + str(y+h)
            cv2.putText(frame, text, (x, y-10), font, 1, rectColor, 2)
            areatext = "A "+ str(area)
            cv2.putText(frame, areatext, (x, y-35), font, 1, rectColor, 2)
    
    smVal = isShieldActive(frame, shieldROI[0], shieldROI[1], shieldROI[2], shieldROI[3])
    
    shColor = shieldLvl0
    
    if smVal[0] == True:
        if smVal[1] == 1:
            shColor = shieldLvl1
        elif smVal[1] == 2:
            shColor = shieldLvl2
        else:
            shColor = shieldLvl0
            
    cv2.line(frame, (areaSize[2], areaSize[0]), (areaSize[3], areaSize[0]), (0, 0, 255), 4)
    cv2.line(frame, (areaSize[2], areaSize[1]), (areaSize[3], areaSize[1]), (255, 255, 0), 4)
    # [top, y2, left, x2]
    centerline = int((areaSize[2] + areaSize[3]) / 2)
    leftmostX1 = int(areaSize[2] - 30)
    leftLaneX1 = int(centerline - 295)
    rightLaneX1 = int(centerline + 295)
    rightmostX1 = int(areaSize[3] + 30)
    
    farLineX1 = int(centerline - 100)
    farLineX2 = int(centerline + 100)
    
    leftmostX2 = int(centerline - 95)
    leftLaneX2 = int(centerline - 55)
    rightLaneX2 = int(centerline + 55)
    rightmostX2 = int(centerline + 95)

    llm = [50, 380] 
    lm = [430, 570] 
    rm = [600, 790]
    rrm = [830, 1110]
    
    cv2.rectangle(frame, (llm[0], beatLine[1]), (llm[1], beatLine[1] + 70), color=(255,255,255), thickness=4)
    cv2.rectangle(frame, (lm[0], beatLine[1]), (lm[1], beatLine[1] + 70), color=(255,255,255), thickness=4)
    cv2.rectangle(frame, (rm[0], beatLine[1]), (rm[1], beatLine[1] + 70), color=(255,255,255), thickness=4)
    cv2.rectangle(frame, (rrm[0], beatLine[1]), (rrm[1], beatLine[1] + 70), color=(255,255,255), thickness=4)
    # Far line
    cv2.line(frame, (farLineX1, 150), (farLineX2, 150), (0, 0, 0), 4)
    # Leftmost lane
    cv2.line(frame, (leftmostX1, areaSize[1]), (farLineX1, 150), (255, 128, 0), 4)
    # Left lane
    cv2.line(frame, (leftLaneX1, areaSize[1]), (leftLaneX2, 150), (128, 0, 255), 4)
    # Center line
    cv2.line(frame, (centerline, 150), (centerline, areaSize[1]), (128, 128, 128), 4)
    # Right lane
    cv2.line(frame, (rightLaneX1, areaSize[1]), (rightLaneX2, 150), (128, 255, 0), 4)
    # Rightmost lane
    cv2.line(frame, (rightmostX1, areaSize[1]), (farLineX2, 150), (0, 255, 255), 4)
    
    # Limit line
    cv2.line(frame, (areaSize[2], beatLine[1]), (areaSize[3], beatLine[1]), (0, 128, 255), 4)
    
    cv2.rectangle(frame, (int(shieldROI[0]), int(shieldROI[1])), (int(shieldROI[0]+shieldROI[2]), int(shieldROI[1]+shieldROI[3])), color=shColor, thickness=4)
    
    levelTxtColor = (0, 255, 255)
    if toggleOutput == True:
        levelTxtColor = (0, 255, 255)
    elif toggleOutput == True and ff_fatigueEnabled == True:
        levelTxtColor = (255, 255, 0)
    elif toggleOutput == False:
        levelTxtColor = (128, 128, 128)
        
    cv2.putText(frame, str(ff_Level), (1200, 100), font, 3, levelTxtColor, 7)
    if ff_fatigueEnabled == True:
        fText = "C" + str(Decimal(ff_fatigueSpeed).quantize(Decimal("1.00")))
        fValue = "F" + str(Decimal(ff_fatigueLevel).quantize(Decimal("1.00")))
        cv2.putText(frame, fText, (1200, 150), font, 1.5, levelTxtColor, 4)
        cv2.putText(frame, fValue, (1200, 200), font, 1.5, levelTxtColor, 4)
    
    # Send keys if possible
    hammer = createKeys(buildKeyCombo(contoursList))
    # Run the output keys through Fair Fight governor
    ff_result = fairFightGovernor(hammer, smVal[0], smVal[1], ff_Level, toggleOutput)
    # print(ff_result)
    # Send the results to the keyboard
    sendKeys(ff_result[0], ff_result[1], ff_result[2], ff_result[3])
    # Display the resulting frame
    # cv2.imshow("IrisView-Blue", blue_mask)
    cv2.imshow("Thrym 2.0 - Odin's Eye", frame)

while True:
    # Get new frame
    frame = stream.read()
    # Kill thread if frame cannot be retrieved
    if frame is None:
	    raise RuntimeError("FRAME IS NULL! PLS CHECK VIDGEAR SETTINGS!")
    # Hack to convert "RGB" colors back to true colors as it is flipped in the source
    # Note that any image processing commands placed after this line will have corrupted color
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    # Call the function to detect blue objects and mark them with rectangles
    detectNotes(frame, noteSize[0], noteSize[1])
    key = cv2.waitKey(1) & 0xFF
    if key == ord("z"):
        break
    

listener.stop()
cv2.destroyAllWindows()
print(" ")
print("=====================================================")
print("We all make mistakes, and that's what makes us human.")
print("We shall fight again, brother. Farewell.")
print("=====================================================")
print(" ")
stream.stop()
