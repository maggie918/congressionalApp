from roboflow import Roboflow
import cv2
import time

# Initialize Roboflow
rf = Roboflow(api_key="QgPuAFG1WvwzQ6fdfP8T")
project = rf.workspace().project("my-first-project-aon9u")
model = project.version("2").model

# Open video file (or use 0 for webcam)
video_path = "/Users/maggielu/gun_alert_app/test.mov"  # Replace with your video path
cap = cv2.VideoCapture(video_path)

gun_detected = False
target_fps = 15
frame_interval = 1 / target_fps  # time per frame in seconds
last_processed = 0  # timestamp of last processed frame

while cap.isOpened() and not gun_detected:
    ret, frame = cap.read()
    if not ret:
        break  # End of video

    # Control processing to ~15 FPS
    current_time = time.time()
    if current_time - last_processed < frame_interval:
        continue  # skip this frame
    last_processed = current_time

    # Convert frame from BGR to RGB (Roboflow likes RGB)
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # Run inference
    result = model.predict(frame_rgb, confidence=40, overlap=30).json()

    # Check results
    if result['predictions']:
        print("⚠️‼️GUN DETECTED")
        print(result)
        gun_detected = True  # stop the loop
    else:
        print("🥰 NO GUN DETECTED")

    # Draw predictions on the frame
    for pred in result['predictions']:
        x, y, w, h = pred['x'], pred['y'], pred['width'], pred['height']
        label = pred['class']
        confidence = pred['confidence']
        cv2.rectangle(frame, (int(x - w/2), int(y - h/2)), (int(x + w/2), int(y + h/2)), (0,0,255), 2)
        cv2.putText(frame, f"{label} {confidence:.2f}", (int(x - w/2), int(y - h/2 - 5)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,0,255), 2)

    # Show frame
    cv2.imshow("Gun Detection", frame)

    # Press 'q' to quit early
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()