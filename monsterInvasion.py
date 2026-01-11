import easyocr
import cv2
import numpy as np
import os
import pandas as pd
from src.utils import downscaleImage, fuse_rects, group_by_rows, processTop3, loadJsonFile, writeCSV
from argparse import ArgumentParser

def createImageMask(image):
    """
    Creats a binary mask isolating the red-ish background of the MI leaderboard. Uses HSV color space in case of lighting variations in different devices.
    
    :param image: Image of the MI leaderboard
    :return: Mask isolating the red-ish background
    """
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

    lower = np.array([160, 40, 40])
    upper = np.array([180, 255, 255])

    mask = cv2.inRange(hsv, lower, upper)
    mask = cv2.erode(mask, None, iterations=1)

    return mask

def main(args):
    MI_SCORES = {}
    NAME_CORRECTION = loadJsonFile("nameCorrection.json")

    reader = easyocr.Reader(['en'])

    rootPath = args.path
    debug = args.debug
    
    for i, imageName in enumerate(os.listdir(rootPath)):
        DEBUG_SCORES = {}
        top3Flag = False
        if i == 0 or debug == True:
            top3Flag = True

        image = cv2.imread(os.path.join(rootPath, imageName))
        # Downscale image for faster processing
        image = downscaleImage(image, max_height=1024)

        mask = createImageMask(image)

        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # Use debug flag to see if there are areas with nothing there that are being processed and tune this value if necessary. It's the minimum area of a region to be considered.   
        MIN_AREA = 800 

        # Sort contour areas by size and filter out the small ones 
        filteredContours = sorted(
            (cnt for cnt in contours if cv2.contourArea(cnt) >= MIN_AREA),
            key=cv2.contourArea,
            reverse=True
        )

        # Sort the areas top to bottom then left to right in order to get the top3 area first
        filteredContours.sort(key=lambda c: (cv2.boundingRect(c)[1], cv2.boundingRect(c)[0]))

        # Fuse the rectangles extracted from the contours that are of similar height.
        # This helps in cases where player icons or weapons split the contour into smaller areas
        fusedRects = fuse_rects([cv2.boundingRect(c) for c in filteredContours])
        # Fusing countours of similar height
        filteredContours = [np.array([
            [[x, y]],
            [[x + w, y]],
            [[x + w, y + h]],
            [[x, y + h]]
        ], dtype=np.int32) for x, y, w, h in fusedRects]

        # Disregarding x axis
        rows = group_by_rows([cv2.boundingRect(c) for c in filteredContours])

        # Convert each rectangle to a contour
        fusedContours = []
        for row in rows:
            # Find min/max x and y for the whole row
            x_min = min(r[0] for r in row)
            y_min = min(r[1] for r in row)
            x_max = max(r[0] + r[2] for r in row)
            y_max = max(r[1] + r[3] for r in row)

            # Create a contour for the whole row
            fusedContours.append(
                np.array([
                    [[x_min, y_min]],
                    [[x_max, y_min]],
                    [[x_max, y_max]],
                    [[x_min, y_max]]
                ], dtype=np.int32)
            )

        debug_img = image.copy()

        bboxes = [cv2.boundingRect(cnt) for cnt in fusedContours]

        # Pop first box as it belong to the top3 scores area
        top3 = bboxes.pop(0)

        ocrOutput = []
        # Only process the top3 area on the first image to save processing time when dealing with many images.
        if top3Flag:
            top3bboxes = processTop3(top3)
            for box in top3bboxes:
                x, y, w, h = box
                x1, y1, x2, y2 = x, y, x + w, y + h
                cv2.rectangle(
                    debug_img,
                    (x1, y1),
                    (x2, y2),
                    (0,0,255),  # red box
                    2
                )
                reader_results = reader.readtext(image[y1:y2, x1:x2], detail = 0)
                ocrOutput.append(reader_results)

        for i, box in enumerate(bboxes):
            x, y, w, h = box
            x1, y1, x2, y2 = x, y, x + w, y + h
            x1 = int(x1+(x2-x1)*0.3)
            if i == len(bboxes) - 1:
                color = (255,0,0)  # blue box for smallest
            else:  
                color = (0,255,0)
            cv2.rectangle(
                debug_img,
                (x1, y1),
                (x2, y2),
                color,  # green box
                2
            )
            reader_results = reader.readtext(image[y1:y2, x1:x2], detail = 0)
            ocrOutput.append(reader_results)

        # Create pairs of name and score from the rest of the leaderboard area. Needed when areas include multiple players
        pairs = []
        for sublist in ocrOutput:
            # If sublist has more than 2 items and length is even, split into consecutive pairs
            if len(sublist) > 2 and len(sublist) % 2 == 0:
                for i in range(0, len(sublist), 2):
                    pairs.append([sublist[i], sublist[i+1]])
            elif len(sublist) == 2:
                pairs.append(sublist)

        # Create ouput dictionary and correct names
        for pair in pairs:
            # Replace any O in the score with a 0
            value = pair[1].replace('O', '0')
            # Make sure the value excluding the M/B/T is a valid float
            try:
                float(value[:-1])
                if value[-1] == '8':
                    value = value[:-1] + 'B'
                elif value[-1] == '1' or value[-1] == '7' or value[-1] == 't':
                    value = value[:-1] + 'T'
                
                # Get corrected name if it doesn't exist default back to what OCR read
                correctedName = NAME_CORRECTION.get(pair[0], pair[0])
                MI_SCORES[correctedName] = value
                DEBUG_SCORES[correctedName] = value
            except ValueError:
                continue

        if debug:
            for name, score in DEBUG_SCORES.items():
                print(f"{name} — {score}")

            print(f"Total hits recorded: {len(DEBUG_SCORES)}")

            cv2.imshow(f'{imageName.split(".")[0]}', downscaleImage(image, max_height=1024))
            cv2.imshow(f'Debug {imageName.split(".")[0]}', downscaleImage(debug_img, max_height=1024))
            cv2.imshow(f'Mask {imageName.split(".")[0]}', mask)
            cv2.waitKey(0)
            cv2.destroyAllWindows()
            
    MI_SCORES = dict(sorted(MI_SCORES.items(), key=lambda x: x[0].lower()))
    for name, score in MI_SCORES.items():
        print(f"{name} — {score}")

    print(f"Total hits recorded: {len(MI_SCORES)}")

    writeCSV(MI_SCORES, args.fileName)

if __name__ == "__main__":
    parser = ArgumentParser(add_help=False)
    parser.add_argument("-h", "--help", action="help", help="Script to automatically extract Monster Invasion scores from Archero2 screenshots using OCR.")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode with detailed output and images.")
    parser.add_argument("--path", type=str, required=True, help="Path to the folder containing images.")
    parser.add_argument("--fileName", type=str, default="monster_invasion_scores.csv", help="Output CSV file name.")
    args = parser.parse_args()
    main(args)