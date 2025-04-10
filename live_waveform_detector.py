import pyaudio
import numpy as np
import matplotlib.pyplot as plt
import keyboard
import time

# Audio settings
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
THRESHOLD = 500
MAX_DURATION = 30  # seconds

# Initialize audio stream
p = pyaudio.PyAudio()
stream = p.open(format=FORMAT,
                channels=CHANNELS,
                rate=RATE,
                input=True,
                frames_per_buffer=CHUNK)

# Set up the live plot
plt.ion()
fig, ax = plt.subplots()
x = np.arange(0, CHUNK)
line, = ax.plot(x, np.random.rand(CHUNK), '-', lw=2)
ax.set_ylim(-5000, 5000)
ax.set_xlim(0, CHUNK)
plt.title("Live Audio Waveform")
plt.xlabel("Samples")
plt.ylabel("Amplitude")

print("Listening... Press 'q' to stop.")
start_time = time.time()

try:
    while True:
        # Exit conditions
        if time.time() - start_time > MAX_DURATION:
            print("Time limit reached. Stopping.")
            break
        if keyboard.is_pressed('q'):
            print("Quit key pressed. Stopping.")
            break

        # Read audio data
        data = np.frombuffer(stream.read(CHUNK), dtype=np.int16)
        volume = np.linalg.norm(data)
        line.set_ydata(data)
        fig.canvas.draw()
        fig.canvas.flush_events()

        # Noise detection
        if volume > THRESHOLD:
            print("Unusual noise detected! Volume:", int(volume))

except Exception as e:
    print("Error:", e)

finally:
    stream.stop_stream()
    stream.close()
    p.terminate()
    plt.ioff()
    plt.close()
    print("Stream closed.")
