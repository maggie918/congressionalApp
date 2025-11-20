from roboflow import Roboflow
import cv2
import time
import math
import numpy as np

# Initialize Roboflow
rf = Roboflow(api_key="QgPuAFG1WvwzQ6fdfP8T")
project = rf.workspace("alertalertalert").project("my-first-project-aon9u")
model = project.version(1).model

# Open video file (or use 0 for webcam)
video_path = "/Users/maggielu/Desktop/school.mov"  # Replace with your video path
cap = cv2.VideoCapture(video_path)

output_path = "/Users/maggielu/Desktop/detectedImage.png"

gun_detected = False
target_fps = 15
frame_interval = 1 / target_fps
last_processed = 0

def distance(x1, y1, x2, y2):
    return math.hypot(x1 - x2, y1 - y2)

def center_wh_to_box(p):
    """Convert center-format (x,y,width,height) to (x_min,y_min,x_max,y_max)."""
    x, y, w, h = p['x'], p['y'], p['width'], p['height']
    x_min = int(x - w/2)
    y_min = int(y - h/2)
    x_max = int(x + w/2)
    y_max = int(y + h/2)
    return x_min, y_min, x_max, y_max

while cap.isOpened() and not gun_detected:
    ret, frame = cap.read()
    if not ret:
        break

    current_time = time.time()
    if current_time - last_processed < frame_interval:
        cv2.waitKey(1)
        continue
    last_processed = current_time

    # Prediction
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    result = model.predict(frame_rgb, confidence=40, overlap=30).json()
    preds = result.get('predictions', [])

    guns = [p for p in preds if 'gun' in p.get('class', '').lower()]
    persons = [p for p in preds if 'person' in p.get('class', '').lower()]

    if guns:
        gun_detected = True
        shooter_boxes = []

        if persons:
            # Find nearest person to each gun
            for gun in guns:
                gx, gy = gun['x'], gun['y']
                nearest = min(persons, key=lambda p: distance(gx, gy, p['x'], p['y']))
                shooter_boxes.append(center_wh_to_box(nearest))
        else:
            # If no person detected, fallback to gun box
            for gun in guns:
                shooter_boxes.append(center_wh_to_box(gun))

        # Combine multiple shooters into one tight bounding box
        x_min = min(b[0] for b in shooter_boxes)
        y_min = min(b[1] for b in shooter_boxes)
        x_max = max(b[2] for b in shooter_boxes)
        y_max = max(b[3] for b in shooter_boxes)

        # Add padding
        pad = 100
        h, w, _ = frame.shape
        x_min = max(60, x_min - pad)
        y_min = max(0, y_min - pad)
        x_max = min(w, x_max + pad)
        y_max = min(h, y_max + pad)

        # Shift crop to the right (automatically within frame bounds)
        shift_right = 120  # pixels to shift right
        if x_max + shift_right < w:
            x_min += shift_right
            x_max += shift_right

        # Crop around shooter
        cropped = frame[y_min:y_max, x_min:x_max]

        # Optional: upscale for clarity
        scale = 1.5
        cropped = cv2.resize(cropped, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)

        # Save final tight crop
        cv2.imwrite(output_path, cropped)
        print(f"✅ Shooter tightly cropped image saved at: {output_path}")

        # Draw red boxes on live feed only
        for box in shooter_boxes:
            sx1, sy1, sx2, sy2 = box
            cv2.rectangle(frame, (sx1, sy1), (sx2, sy2), (0, 0, 255), 6)

    # Show live feed
    #cv2.imshow("Gun Detection", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Show final crop briefly
if gun_detected:
    final_crop = cv2.imread(output_path)
    if final_crop is not None:
        #cv2.imshow("Final Shooter Crop", final_crop)
        #cv2.waitKey(3000)
        pass

#cap.release()
cv2.destroyAllWindows()
