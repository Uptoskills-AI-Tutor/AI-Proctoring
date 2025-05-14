import cv2
import mediapipe as mp
import numpy as np
import time
import os
import csv
from datetime import datetime
from plyer import notification
import winsound

# ========== Settings ==========
EXAM_DURATION_MIN = 60  # Set your exam time (in minutes)
TAKE_SNAPSHOTS = True  # Save snapshots when looking away
SNAPSHOTS_DIR = "snapshots"  # Directory to store snapshots

# Create snapshots directory if it doesn't exist
if TAKE_SNAPSHOTS and not os.path.exists(SNAPSHOTS_DIR):
    os.makedirs(SNAPSHOTS_DIR)

# ========== MediaPipe Setup ==========
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(refine_landmarks=True)
alert_triggered = False
log_data = []
snapshot_count = 0

FACE_POINTS_ID = {
    "nose_tip": 1,
    "chin": 152,
    "left_eye_outer": 33,
    "right_eye_outer": 263,
    "left_mouth": 61,
    "right_mouth": 291
}

# ========== Alert System ==========
def send_alert():
    global alert_triggered
    if not alert_triggered:
        alert_triggered = True
        winsound.Beep(1000, 400)
        notification.notify(
            title="Attention Alert!",
            message="You looked away from the screen!",
            timeout=2
        )
        time.sleep(1)
        alert_triggered = False

# ========== Logging ==========
def log_event(status, yaw, pitch, roll, snapshot_path=None):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    row = [timestamp, status, round(yaw, 2), round(pitch, 2), round(roll, 2), snapshot_path or ""]
    log_data.append(row)

def generate_report():
    filename = f"exam_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    with open(filename, "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["Timestamp", "Status", "Yaw", "Pitch", "Roll", "Snapshot"])
        writer.writerows(log_data)
    print(f"\n📄 Report saved to {filename}")

    # Summary
    total = len(log_data)
    distracted = sum(1 for row in log_data if row[1] == "Looking Away")
    focused = total - distracted
    print(f"\n🧠 Attention Summary:")
    print(f"Total Frames: {total}")
    print(f"Focused: {focused} ({round(focused / total * 100, 2)}%)")
    print(f"Looked Away: {distracted} ({round(distracted / total * 100, 2)}%)")

# ========== Video Capture ==========
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("❌ Error: Could not open camera")
    exit(1)

start_time = time.time()
end_time = start_time + (EXAM_DURATION_MIN * 60)
print(f"📚 Exam started. Duration: {EXAM_DURATION_MIN} minute(s)")

try:
    while cap.isOpened():
        current_time = time.time()
        if current_time >= end_time:
            print("\n✅ Exam time completed.")
            break

        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.flip(frame, 1)
        h, w, _ = frame.shape
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        results = face_mesh.process(rgb)

        status = "Unknown"
        snapshot_path = None

        if results.multi_face_landmarks:
            face_landmarks = results.multi_face_landmarks[0]
            landmarks = np.array([(lm.x * w, lm.y * h, lm.z * w) for lm in face_landmarks.landmark])

            image_points = np.array([
                landmarks[FACE_POINTS_ID["nose_tip"]][:2],
                landmarks[FACE_POINTS_ID["chin"]][:2],
                landmarks[FACE_POINTS_ID["left_eye_outer"]][:2],
                landmarks[FACE_POINTS_ID["right_eye_outer"]][:2],
                landmarks[FACE_POINTS_ID["left_mouth"]][:2],
                landmarks[FACE_POINTS_ID["right_mouth"]][:2]
            ], dtype="double")

            model_points = np.array([
                (0.0, 0.0, 0.0),
                (0.0, -63.6, -12.5),
                (-43.3, 32.7, -26.0),
                (43.3, 32.7, -26.0),
                (-28.9, -28.9, -24.1),
                (28.9, -28.9, -24.1)
            ])

            focal_length = w
            center = (w // 2, h // 2)
            camera_matrix = np.array([
                [focal_length, 0, center[0]],
                [0, focal_length, center[1]],
                [0, 0, 1]
            ], dtype="double")
            dist_coeffs = np.zeros((4, 1))

            success, rotation_vector, translation_vector = cv2.solvePnP(
                model_points, image_points, camera_matrix, dist_coeffs, flags=cv2.SOLVEPNP_ITERATIVE
            )

            if success:
                rmat, _ = cv2.Rodrigues(rotation_vector)
                pose_mat = cv2.hconcat((rmat, translation_vector))
                
                _, _, _, _, _, _, eulerAngles = cv2.decomposeProjectionMatrix(pose_mat)

                # ✅ Corrected order based on observed output
                yaw, pitch, roll = [angle[0] for angle in eulerAngles]

                if abs(yaw - 170) > 15 or abs(pitch) > 20:
                    status = "Looking Away"
                    color = (0, 0, 255)
                    send_alert()
                    if TAKE_SNAPSHOTS:
                        snapshot_path = os.path.join(SNAPSHOTS_DIR, f"snap_{datetime.now().strftime('%H%M%S')}.jpg")
                        cv2.imwrite(snapshot_path, frame)
                else:
                    status = "Looking Forward"
                    color = (0, 255, 0)

                cv2.putText(frame, f"{status} | Yaw: {int(yaw)}", (20, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
                log_event(status, yaw, pitch, roll, snapshot_path)

        time_left = int(end_time - current_time)
        minutes = time_left // 60
        seconds = time_left % 60
        timer_text = f"Time Left: {minutes:02}:{seconds:02}"
        cv2.putText(frame, timer_text, (20, h - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (200, 255, 200), 2)

        cv2.imshow("🧠 Exam Monitor", frame)

        if cv2.waitKey(1) & 0xFF == 27:  # ESC to exit
            print("\n❌ Manually exited.")
            break

except KeyboardInterrupt:
    print("\n🔴 Interrupted by user.")

finally:
    cap.release()
    cv2.destroyAllWindows()
    generate_report()
