import tkinter as tk
import serial
import threading
import queue
import math
import time
import random
from collections import deque

SERIAL_PORT = "COM8"
BAUD_RATE = 9600

WINDOW_WIDTH = 1250
WINDOW_HEIGHT = 700

max_distance = 20.0
manual_mode = False

FRAME_MS = 20
TARGET_LIFETIME = 0.50
MAX_LOG_LINES = 24

BG = "#010302"
PANEL_BG = "#020805"

GREEN = "#00ff66"
GREEN_BRIGHT = "#7affb5"
GREEN_DARK = "#087a3c"
GREEN_FAINT = "#06351e"
GREEN_GRID = "#032315"

RED = "#ff2020"
RED_BRIGHT = "#ff5555"
RED_DARK = "#701313"

YELLOW = "#d8ff35"
CYAN = "#00ffd5"

WHITE = "#d9ffe8"

data_queue = queue.Queue(maxsize=500)

current_angle = 90.0
current_distance = -1.0

current_mode = "SCAN"
current_target_angle = None

last_detection = 0.0

targets = {}

live_logs = []

running = True

signal_history = deque([50] * 120, maxlen=120)
noise_history = deque([18] * 120, maxlen=120)
activity_history = deque([35] * 120, maxlen=120)
fake_start = time.time()

try:
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=0.03)
    CONNECTED = True
except Exception as e:
    print("Serial connection error:")
    print(e)
    ser = None
    CONNECTED = False

def send_command(cmd):
    if ser and ser.is_open:
        ser.write((cmd + "\n").encode())
        print(f"[DEBUG] Sent: {cmd}")
    else:
        print("[ERROR] Serial port not open!")

def serial_worker():
    while running:
        if ser is None:
            time.sleep(0.3)
            continue
        try:
            raw = ser.readline()
            if not raw:
                continue
            line = raw.decode("utf-8", errors="ignore").strip()
            if not line:
                continue

            mode = "SCAN"
            angle = None
            distance = None
            target_angle = None

            parts = line.split(",")
            for part in parts:
                if ":" not in part:
                    continue
                key, value = part.split(":", 1)
                key = key.strip().upper()
                value = value.strip()
                try:
                    if key == "MODE":
                        mode = value.upper()
                    elif key == "ANGLE":
                        angle = float(value)
                    elif key == "DIST":
                        distance = float(value)
                    elif key == "TARGET":
                        target_angle = float(value)
                except ValueError:
                    pass

            if angle is None or distance is None:
                continue

            item = (mode, angle, distance, target_angle)
            try:
                data_queue.put_nowait(item)
            except queue.Full:
                try:
                    data_queue.get_nowait()
                except queue.Empty:
                    pass
                try:
                    data_queue.put_nowait(item)
                except queue.Full:
                    pass

        except Exception:
            time.sleep(0.03)

threading.Thread(target=serial_worker, daemon=True).start()

root = tk.Tk()
root.title("PROJECT RADAR // TACTICAL HUD")
root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
root.resizable(False, False)
root.configure(bg=BG)

canvas = tk.Canvas(
    root,
    width=WINDOW_WIDTH,
    height=WINDOW_HEIGHT,
    bg=BG,
    highlightthickness=0
)
canvas.pack()

RADAR_CENTER_X = 410
RADAR_CENTER_Y = 625
RADAR_RADIUS = 435

def angle_position(angle, radius):
    rad = math.radians(angle)
    x = RADAR_CENTER_X - math.cos(rad) * radius
    y = RADAR_CENTER_Y - math.sin(rad) * radius
    return x, y

def radar_position(angle, distance):
    radius = (distance / max_distance) * RADAR_RADIUS
    return angle_position(angle, radius)

matrix_columns = []
for x in range(0, WINDOW_WIDTH, 18):
    matrix_columns.append({
        "x": x,
        "y": random.randint(-WINDOW_HEIGHT, WINDOW_HEIGHT),
        "speed": random.uniform(1, 4)
    })

matrix_items = []
for column in matrix_columns:
    item = canvas.create_text(
        column["x"], column["y"],
        text=random.choice("01RADAR<>/\\[]{}#$%&"),
        fill=GREEN_GRID,
        font=("Consolas", 7)
    )
    matrix_items.append(item)

def update_matrix():
    for index, column in enumerate(matrix_columns):
        column["y"] += column["speed"]
        if column["y"] > WINDOW_HEIGHT + 20:
            column["y"] = random.randint(-150, -20)
        if random.random() < 0.04:
            char = random.choice("01RADAR<>/\\[]{}#$%&")
            canvas.itemconfig(matrix_items[index], text=char)
        canvas.coords(matrix_items[index], column["x"], column["y"])

ring_objects = []

def draw_static_radar():
    canvas.create_text(
        25, 20, anchor="nw",
        text="PROJECT // RADAR",
        fill=GREEN_BRIGHT,
        font=("Consolas", 22, "bold")
    )
    canvas.create_text(
        27, 51, anchor="nw",
        text="ADVANCED ULTRASONIC TRACKING INTERFACE",
        fill=GREEN_DARK,
        font=("Consolas", 9)
    )

    _draw_rings()

    for angle in range(0, 181, 15):
        x, y = angle_position(angle, RADAR_RADIUS)
        color = GREEN_DARK if angle % 30 == 0 else GREEN_GRID
        canvas.create_line(
            RADAR_CENTER_X, RADAR_CENTER_Y,
            x, y,
            fill=color, width=1
        )

    for angle in (0, 30, 60, 90, 120, 150, 180):
        x, y = angle_position(angle, RADAR_RADIUS + 18)
        canvas.create_text(
            x, y,
            text=f"{angle:03d}°",
            fill=GREEN_DARK,
            font=("Consolas", 8)
        )

    canvas.create_line(
        RADAR_CENTER_X - RADAR_RADIUS, RADAR_CENTER_Y,
        RADAR_CENTER_X + RADAR_RADIUS, RADAR_CENTER_Y,
        fill=GREEN_DARK, width=1
    )

    canvas.create_oval(
        RADAR_CENTER_X - 6, RADAR_CENTER_Y - 6,
        RADAR_CENTER_X + 6, RADAR_CENTER_Y + 6,
        fill=GREEN, outline=""
    )

def _draw_rings():
    global ring_objects
    for obj in ring_objects:
        canvas.delete(obj)
    ring_objects.clear()

    steps = [0.25, 0.50, 0.75, 1.0]
    for frac in steps:
        dist = frac * max_distance
        radius = (dist / max_distance) * RADAR_RADIUS
        ring = canvas.create_arc(
            RADAR_CENTER_X - radius,
            RADAR_CENTER_Y - radius,
            RADAR_CENTER_X + radius,
            RADAR_CENTER_Y + radius,
            start=0, extent=180,
            style=tk.ARC,
            outline=GREEN_FAINT,
            width=1
        )
        ring_objects.append(ring)

        x, y = radar_position(135, dist)
        label = canvas.create_text(
            x - 15, y,
            text=f"{dist:.0f}cm",
            fill=GREEN_DARK,
            font=("Consolas", 8)
        )
        ring_objects.append(label)

def update_radar_rings():
    _draw_rings()

draw_static_radar()

scan_glow = canvas.create_line(
    RADAR_CENTER_X, RADAR_CENTER_Y,
    RADAR_CENTER_X, RADAR_CENTER_Y - RADAR_RADIUS,
    fill="#063b20", width=10
)
scan_line = canvas.create_line(
    RADAR_CENTER_X, RADAR_CENTER_Y,
    RADAR_CENTER_X, RADAR_CENTER_Y - RADAR_RADIUS,
    fill=GREEN, width=2
)

target_items = {}

PANEL_X = 825
PANEL_Y = 15
PANEL_W = 395
PANEL_H = 660

canvas.create_rectangle(
    PANEL_X, PANEL_Y,
    PANEL_X + PANEL_W, PANEL_Y + PANEL_H,
    fill=PANEL_BG,
    outline=GREEN_GRID,
    width=1
)

canvas.create_text(
    PANEL_X + 18, PANEL_Y + 15,
    anchor="nw",
    text="TACTICAL // TELEMETRY",
    fill=GREEN_BRIGHT,
    font=("Consolas", 14, "bold")
)
canvas.create_text(
    PANEL_X + 18, PANEL_Y + 40,
    anchor="nw",
    text="LIVE SENSOR + SIMULATED ANALYTICS",
    fill=GREEN_DARK,
    font=("Consolas", 8)
)
canvas.create_line(
    PANEL_X + 15, PANEL_Y + 63,
    PANEL_X + PANEL_W - 15, PANEL_Y + 63,
    fill=GREEN_GRID
)

metric_labels = {}
metric_values = {}

def create_metric(name, x, y):
    metric_labels[name] = canvas.create_text(
        x, y, anchor="nw",
        text=name,
        fill=GREEN_DARK,
        font=("Consolas", 8)
    )
    metric_values[name] = canvas.create_text(
        x, y + 13, anchor="nw",
        text="--",
        fill=GREEN_BRIGHT,
        font=("Consolas", 11, "bold")
    )

create_metric("SIGNAL", PANEL_X + 18, PANEL_Y + 80)
create_metric("NOISE", PANEL_X + 150, PANEL_Y + 80)
create_metric("CONFIDENCE", PANEL_X + 280, PANEL_Y + 80)

create_metric("SYSTEM LOAD", PANEL_X + 18, PANEL_Y + 130)
create_metric("SCAN RATE", PANEL_X + 150, PANEL_Y + 130)
create_metric("TARGETS", PANEL_X + 280, PANEL_Y + 130)

create_metric("MAX RANGE", PANEL_X + 18, PANEL_Y + 180)

CHART_X = PANEL_X + 18
CHART_W = PANEL_W - 36

SIGNAL_CHART_Y = PANEL_Y + 230
SIGNAL_CHART_H = 80

ACTIVITY_CHART_Y = PANEL_Y + 330
ACTIVITY_CHART_H = 70

canvas.create_rectangle(
    CHART_X, SIGNAL_CHART_Y,
    CHART_X + CHART_W, SIGNAL_CHART_Y + SIGNAL_CHART_H,
    outline=GREEN_GRID
)
canvas.create_text(
    CHART_X + 8, SIGNAL_CHART_Y + 7,
    anchor="nw",
    text="SIGNAL ANALYSIS // SIMULATED",
    fill=GREEN_DARK,
    font=("Consolas", 8)
)

canvas.create_rectangle(
    CHART_X, ACTIVITY_CHART_Y,
    CHART_X + CHART_W, ACTIVITY_CHART_Y + ACTIVITY_CHART_H,
    outline=GREEN_GRID
)
canvas.create_text(
    CHART_X + 8, ACTIVITY_CHART_Y + 7,
    anchor="nw",
    text="SCAN ACTIVITY // SIMULATED",
    fill=GREEN_DARK,
    font=("Consolas", 8)
)

signal_chart = canvas.create_line(
    CHART_X + 5, SIGNAL_CHART_Y + SIGNAL_CHART_H // 2,
    CHART_X + 6, SIGNAL_CHART_Y + SIGNAL_CHART_H // 2,
    fill=GREEN, width=1
)
noise_chart = canvas.create_line(
    CHART_X + 5, SIGNAL_CHART_Y + SIGNAL_CHART_H // 2,
    CHART_X + 6, SIGNAL_CHART_Y + SIGNAL_CHART_H // 2,
    fill="#0c713c", width=1
)
activity_chart = canvas.create_line(
    CHART_X + 5, ACTIVITY_CHART_Y + ACTIVITY_CHART_H // 2,
    CHART_X + 6, ACTIVITY_CHART_Y + ACTIVITY_CHART_H // 2,
    fill=CYAN, width=1
)

STREAM_Y = PANEL_Y + 425

canvas.create_text(
    CHART_X, STREAM_Y,
    anchor="nw",
    text="LIVE DATA STREAM",
    fill=GREEN_BRIGHT,
    font=("Consolas", 10, "bold")
)
canvas.create_text(
    CHART_X, STREAM_Y + 21,
    anchor="nw",
    text=">> RAW TELEMETRY",
    fill=GREEN_DARK,
    font=("Consolas", 8)
)

stream_start = STREAM_Y + 43
stream_items = []
for i in range(MAX_LOG_LINES):
    item = canvas.create_text(
        CHART_X, stream_start + i * 19,
        anchor="nw",
        text="",
        fill=GREEN_DARK,
        font=("Consolas", 8)
    )
    stream_items.append(item)

def update_fake_analytics():
    global max_distance
    elapsed = time.time() - fake_start

    signal = 65 + math.sin(elapsed * 2.1) * 12 + math.sin(elapsed * 5.4) * 4
    noise = 18 + math.sin(elapsed * 3.7) * 5 + math.sin(elapsed * 8.1) * 2
    confidence = 88 + math.sin(elapsed * 1.4) * 7
    load = 34 + math.sin(elapsed * 1.9) * 11 + random.random() * 4
    scan_rate = 42 + math.sin(elapsed * 2.8) * 5
    target_count = len(targets)

    signal = max(0, min(100, signal))
    noise = max(0, min(100, noise))
    confidence = max(0, min(100, confidence))
    load = max(0, min(100, load))

    signal_history.append(signal)
    noise_history.append(noise)
    activity = 50 + math.sin(elapsed * 3.2) * 25 + random.random() * 8
    activity_history.append(activity)

    canvas.itemconfig(metric_values["SIGNAL"], text=f"{signal:05.1f}%")
    canvas.itemconfig(metric_values["NOISE"], text=f"{noise:05.1f}%")
    canvas.itemconfig(metric_values["CONFIDENCE"], text=f"{confidence:05.1f}%")
    canvas.itemconfig(metric_values["SYSTEM LOAD"], text=f"{load:05.1f}%")
    canvas.itemconfig(metric_values["SCAN RATE"], text=f"{scan_rate:05.1f} Hz")
    canvas.itemconfig(metric_values["TARGETS"], text=f"{target_count:02d}")
    canvas.itemconfig(metric_values["MAX RANGE"], text=f"{max_distance:04.0f} cm")

def make_chart_points(values, x, y, width, height):
    values_list = list(values)
    if not values_list:
        return []
    minimum = min(values_list)
    maximum = max(values_list)
    if maximum - minimum < 1:
        maximum = minimum + 1
    points = []
    for i, value in enumerate(values_list):
        px = x + (i / (len(values_list) - 1)) * width
        normalized = (value - minimum) / (maximum - minimum)
        py = y + height - normalized * height
        points.extend([px, py])
    return points

def update_charts():
    signal_points = make_chart_points(
        signal_history,
        CHART_X + 5, SIGNAL_CHART_Y + 22,
        CHART_W - 10, SIGNAL_CHART_H - 28
    )
    noise_points = make_chart_points(
        noise_history,
        CHART_X + 5, SIGNAL_CHART_Y + 22,
        CHART_W - 10, SIGNAL_CHART_H - 28
    )
    activity_points = make_chart_points(
        activity_history,
        CHART_X + 5, ACTIVITY_CHART_Y + 22,
        CHART_W - 10, ACTIVITY_CHART_H - 28
    )

    canvas.coords(signal_chart, *signal_points)
    canvas.coords(noise_chart, *noise_points)
    canvas.coords(activity_chart, *activity_points)

status_text = canvas.create_text(
    780, 30,
    anchor="e",
    text="● SCANNING",
    fill=GREEN_BRIGHT,
    font=("Consolas", 16, "bold")
)

angle_hud = canvas.create_text(
    25, WINDOW_HEIGHT - 63,
    anchor="w",
    text="ANGLE 090.0°",
    fill=GREEN_BRIGHT,
    font=("Consolas", 14, "bold")
)
distance_hud = canvas.create_text(
    25, WINDOW_HEIGHT - 35,
    anchor="w",
    text="DIST  ------",
    fill=GREEN_BRIGHT,
    font=("Consolas", 14, "bold")
)

def process_serial():
    global current_angle, current_distance, current_mode
    global current_target_angle, last_detection

    items = []
    while True:
        try:
            item = data_queue.get_nowait()
            items.append(item)
        except queue.Empty:
            break

    if not items:
        return

    for mode, angle, distance, target_angle in items:
        if not manual_mode:
            current_angle = max(0, min(180, angle))
        current_distance = distance
        current_mode = mode
        current_target_angle = target_angle

        now = time.time()
        timestamp = time.strftime("%H:%M:%S")
        milliseconds = int((time.time() % 1) * 1000)

        if distance > 0:
            dist_text = f"{distance:5.1f}cm"
            state = "TARGET" if mode in ("LOCK", "SEARCH") or distance <= max_distance else mode
        else:
            dist_text = "------"
            state = mode

        log_line = f"{timestamp}.{milliseconds:03d} {state:<6} A:{angle:03.0f}° D:{dist_text}"
        live_logs.append((log_line, state))
        if len(live_logs) > MAX_LOG_LINES:
            del live_logs[:-MAX_LOG_LINES]

        if distance > 0 and distance <= max_distance:
            key = int(round(angle))
            targets[key] = {"angle": angle, "distance": distance, "time": now}
            last_detection = now

def update_stream():
    for item in stream_items:
        canvas.itemconfig(item, text="")

    visible = live_logs[-MAX_LOG_LINES:]
    for i, (text, state) in enumerate(visible):
        if state in ("TARGET", "LOCK"):
            color = RED_BRIGHT
        elif state == "SEARCH":
            color = YELLOW
        else:
            color = GREEN_DARK
        canvas.itemconfig(stream_items[i], text=text, fill=color)

def update_scan_line():
    x, y = angle_position(current_angle, RADAR_RADIUS)
    canvas.coords(scan_glow, RADAR_CENTER_X, RADAR_CENTER_Y, x, y)
    canvas.coords(scan_line, RADAR_CENTER_X, RADAR_CENTER_Y, x, y)

def update_targets():
    now = time.time()
    active = set()

    for key, target in list(targets.items()):
        age = now - target["time"]
        if age > TARGET_LIFETIME:
            targets.pop(key, None)
            if key in target_items:
                for item in target_items[key]:
                    canvas.delete(item)
                del target_items[key]
            continue

        active.add(key)
        angle = target["angle"]
        distance = target["distance"]
        x, y = radar_position(angle, distance)

        pulse = (math.sin(now * 12) + 1) / 2
        outer = 9 + pulse * 9

        if key not in target_items:
            glow = canvas.create_oval(0, 0, 0, 0, outline=RED_DARK, width=2)
            ring = canvas.create_oval(0, 0, 0, 0, outline=RED_BRIGHT, width=1)
            core = canvas.create_oval(0, 0, 0, 0, fill=RED, outline="")
            h1 = canvas.create_line(0, 0, 0, 0, fill=RED, width=1)
            h2 = canvas.create_line(0, 0, 0, 0, fill=RED, width=1)
            v1 = canvas.create_line(0, 0, 0, 0, fill=RED, width=1)
            v2 = canvas.create_line(0, 0, 0, 0, fill=RED, width=1)
            label = canvas.create_text(0, 0, anchor="w", fill=RED_BRIGHT, font=("Consolas", 8, "bold"))
            target_items[key] = (glow, ring, core, h1, h2, v1, v2, label)

        glow, ring, core, h1, h2, v1, v2, label = target_items[key]

        canvas.coords(glow, x - outer, y - outer, x + outer, y + outer)
        canvas.coords(ring, x - 8, y - 8, x + 8, y + 8)
        canvas.coords(core, x - 4, y - 4, x + 4, y + 4)
        canvas.coords(h1, x - 17, y, x - 7, y)
        canvas.coords(h2, x + 7, y, x + 17, y)
        canvas.coords(v1, x, y - 17, x, y - 7)
        canvas.coords(v2, x, y + 7, x, y + 17)
        canvas.coords(label, x + 22, y - 5)
        canvas.itemconfig(label, text=f"{angle:.0f}° {distance:.1f}cm")

    for key in list(target_items.keys()):
        if key not in active:
            for item in target_items[key]:
                canvas.delete(item)
            del target_items[key]

def update_hud():
    canvas.itemconfig(angle_hud, text=f"ANGLE {current_angle:06.1f}°")
    if current_distance > 0:
        canvas.itemconfig(distance_hud, text=f"DIST  {current_distance:06.1f} cm")
    else:
        canvas.itemconfig(distance_hud, text="DIST  ------")

    if manual_mode:
        canvas.itemconfig(status_text, text="● MANUAL CONTROL", fill=CYAN)
    elif current_mode == "LOCK":
        canvas.itemconfig(status_text, text="● TARGET LOCK", fill=RED_BRIGHT)
    elif current_mode == "SEARCH":
        canvas.itemconfig(status_text, text="● SEARCHING", fill=YELLOW)
    elif time.time() - last_detection < 0.35:
        canvas.itemconfig(status_text, text="● TARGET DETECTED", fill=RED_BRIGHT)
    else:
        blink = int(time.time() * 2) % 2
        canvas.itemconfig(
            status_text,
            text="● SCANNING" if blink else "◉ SCANNING",
            fill=GREEN_BRIGHT
        )

corner_lines = []

def create_corner(x, y, direction_x, direction_y):
    length = 18
    line1 = canvas.create_line(x, y, x + direction_x * length, y, fill=GREEN_DARK, width=1)
    line2 = canvas.create_line(x, y, x, y + direction_y * length, fill=GREEN_DARK, width=1)
    corner_lines.extend([line1, line2])

create_corner(12, 12, 1, 1)
create_corner(WINDOW_WIDTH - 12, 12, -1, 1)
create_corner(12, WINDOW_HEIGHT - 12, 1, -1)
create_corner(WINDOW_WIDTH - 12, WINDOW_HEIGHT - 12, -1, -1)

decor_texts = []
for i in range(9):
    x = random.randint(20, 800)
    y = random.randint(90, 550)
    item = canvas.create_text(x, y, text="", anchor="nw", fill=GREEN_GRID, font=("Consolas", 7))
    decor_texts.append(item)

def update_decor():
    elapsed = time.time()
    for i, item in enumerate(decor_texts):
        if random.random() < 0.02:
            value = random.choice(["SYNC", "SCAN", "CORE", "ARRAY", "NODE", "TRACK", "LINK", "UPLINK", "VECTOR"])
            number = random.randint(10, 9999)
            canvas.itemconfig(item, text=f"{value} // {number}")

def on_key_press(event):
    global manual_mode, current_angle, max_distance

    key = event.keysym
    print(f"[DEBUG] Key pressed: {key}")

    if key.lower() == 'm':
        manual_mode = not manual_mode
        send_command("M")
        return

    if manual_mode:
        if key == 'Left':
            current_angle = max(0, current_angle - 1)
            send_command(f"A:{int(current_angle)}")
        elif key == 'Right':
            current_angle = min(180, current_angle + 1)
            send_command(f"A:{int(current_angle)}")

    if key == 'Up':
        new_max = min(100, max_distance + 5)
        if new_max != max_distance:
            max_distance = new_max
            send_command(f"D:{max_distance:.1f}")
            update_radar_rings()
    elif key == 'Down':
        new_max = max(10, max_distance - 5)
        if new_max != max_distance:
            max_distance = new_max
            send_command(f"D:{max_distance:.1f}")
            update_radar_rings()

root.bind_all('<Key>', on_key_press)

def update():
    if not running:
        return

    process_serial()

    update_scan_line()
    update_targets()

    update_hud()

    update_stream()

    update_fake_analytics()
    update_charts()

    update_matrix()
    update_decor()

    root.after(FRAME_MS, update)

def close_app():
    global running
    running = False
    try:
        if ser:
            ser.close()
    except Exception:
        pass
    root.destroy()

root.protocol("WM_DELETE_WINDOW", close_app)

update()
root.mainloop()