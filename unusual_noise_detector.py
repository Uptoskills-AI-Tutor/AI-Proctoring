import pyaudio
import numpy as np
import time
import keyboard  # Make sure to install it: pip install keyboard

# Audio settings
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
THRESHOLD = 500  # Adjust based on environment
MAX_DURATION = 30  # seconds (auto-stop after this time)

# Initialize PyAudio
p = pyaudio.PyAudio()

stream = p.open(format=FORMAT,
                channels=CHANNELS,
                rate=RATE,
                input=True,
                frames_per_buffer=CHUNK)

print("Listening for unusual noise... (press 'q' to quit)")
start_time = time.time()

try:
    while True:
        # Check if time exceeded or 'q' is pressed
        if time.time() - start_time > MAX_DURATION:
            print("Max duration reached. Stopping.")
            break
        if keyboard.is_pressed('q'):
            print("Quit key detected. Stopping.")
            break

        # Read and process audio
        data = np.frombuffer(stream.read(CHUNK), dtype=np.int16)
        volume = np.linalg.norm(data)
        
        if volume > THRESHOLD:
            print("Unusual noise detected! Volume:", int(volume))

except Exception as e:
    print("Error:", e)

finally:
    stream.stop_stream()
    stream.close()
    p.terminate()
    print("Audio stream closed.")
