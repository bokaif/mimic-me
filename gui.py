import threading
import mouse
import keyboard
from tkinter import Tk, Canvas, Entry, Button, PhotoImage, filedialog, messagebox
import json
import time as _time

mouse_events = []
keyboard_events = []
recording = False


def get(path: str):
    return "assets/" + path


window = Tk()

window.geometry("700x406")
window.configure(bg="#FFFFFF")
window.title("Mimic Me")

canvas = Canvas(
    window,
    bg="#FFFFFF",
    height=406,
    width=700,
    bd=0,
    highlightthickness=0,
    relief="ridge"
)

canvas.place(x=0, y=0)
image_image_1 = PhotoImage(
    file=get("bg.png"))
image_1 = canvas.create_image(
    350.0,
    203.0,
    image=image_image_1
)

canvas.create_text(
    259.0,
    66.99999999999997,
    anchor="nw",
    text="MIMIC ME",
    fill="#FFFFFF",
    font=("NexaBold", 39 * -1)
)

canvas.create_text(
    106.0,
    117.99999999999997,
    anchor="nw",
    text="A tool that mimics your keyboard and mouse events",
    fill="#FFFFFF",
    font=("NexaLight", 20 * -1)
)

canvas.create_text(
    121.0,
    176.99999999999997,
    anchor="nw",
    text="Number of Loops",
    fill="#D2D1D2",
    font=("NexaLight", 16 * -1)
)

canvas.create_rectangle(
    97.0,
    203.99999999999997,
    288.0,
    238.99999999999997,
    fill="#A1A2A4",
    outline="")

n_loop_img = PhotoImage(
    file=get("n_loop.png"))
n_loop_bg = canvas.create_image(
    192.0,
    221.49999999999997,
    image=n_loop_img
)
n_loop = Entry(
    bd=0,
    bg="#A0A1A3",
    highlightthickness=0
)
n_loop.place(
    x=105.0,
    y=206.99999999999997,
    width=174.0,
    height=27.0
)

canvas.create_text(
    101.0,
    270.0,
    anchor="nw",
    text="Key to Stop Recording",
    fill="#D2D1D2",
    font=("NexaLight", 16 * -1)
)

canvas.create_rectangle(
    97.0,
    297.0,
    288.0,
    332.0,
    fill="#A1A2A4",
    outline="")

key_stoprec_img = PhotoImage(
    file=get("key_stoprec.png"))
key_stoprec_bg = canvas.create_image(
    192.0,
    314.5,
    image=key_stoprec_img
)
key_stoprec = Entry(
    bd=0,
    bg="#A1A2A4",
    highlightthickness=0
)
key_stoprec.place(
    x=105.0,
    y=299.0,
    width=174.0,
    height=29.0
)

record_img = PhotoImage(
    file=get("record_btn.png"))
record_btn = Button(
    image=record_img,
    borderwidth=0,
    highlightthickness=0,
    command=lambda: record(),
    relief="flat"
)
record_btn.place(
    x=346.0,
    y=203.99999999999997,
    width=112.622314453125,
    height=47.32142639160156
)

play_imag = PhotoImage(
    file=get("play_btn.png"))
play_btn = Button(
    image=play_imag,
    borderwidth=0,
    highlightthickness=0,
    command=lambda: play(),
    relief="flat"
)
play_btn.place(
    x=490.377685546875,
    y=203.99999999999997,
    width=112.622314453125,
    height=47.32142639160156
)

load_img = PhotoImage(
    file=get("load_btn.png"))
load_btn = Button(
    image=load_img,
    borderwidth=0,
    highlightthickness=0,
    command=lambda: load(),
    relief="flat"
)
load_btn.place(
    x=346.0,
    y=284.6785888671875,
    width=112.622314453125,
    height=47.321441650390625
)

save_img = PhotoImage(
    file=get("save_btn.png"))
save_btn = Button(
    image=save_img,
    borderwidth=0,
    highlightthickness=0,
    command=lambda: save(),
    relief="flat"
)
save_btn.place(
    x=490.377685546875,
    y=284.6785888671875,
    width=112.622314453125,
    height=47.321441650390625
)

record_btn['state'] = 'normal'
play_btn['state'] = 'disabled'
save_btn['state'] = 'disabled'
load_btn['state'] = 'normal'


def recheck():
    record_btn['cursor'] = "hand2" if str(record_btn['state']) != 'disabled' else "cross"
    play_btn['cursor'] = "hand2" if str(play_btn['state']) != 'disabled' else "cross"
    save_btn['cursor'] = "hand2" if str(save_btn['state']) != 'disabled' else "cross"
    load_btn['cursor'] = "hand2" if str(load_btn['state']) != 'disabled' else "cross"


recheck()

n_loop.insert(0, "1")
key_stoprec.insert(0, "esc")


# -- serialization --

def serialize_mouse_event(event):
    if isinstance(event, mouse.MoveEvent):
        return {"type": "move", "x": event.x, "y": event.y, "time": event.time}
    elif isinstance(event, mouse.ButtonEvent):
        return {"type": "button", "event_type": event.event_type,
                "button": event.button, "time": event.time}
    elif isinstance(event, mouse.WheelEvent):
        return {"type": "wheel", "delta": event.delta, "time": event.time}
    return {"type": "unknown", "data": list(event)}


def deserialize_mouse_event(data):
    t = data.get("type")
    if t == "move":
        return mouse.MoveEvent(x=data["x"], y=data["y"], time=data["time"])
    elif t == "button":
        return mouse.ButtonEvent(event_type=data["event_type"],
                                 button=data["button"], time=data["time"])
    elif t == "wheel":
        return mouse.WheelEvent(delta=data["delta"], time=data["time"])
    raise ValueError(f"unknown mouse event type: {data}")


# -- core functions --

def record():
    global mouse_events, keyboard_events, recording
    mouse_events = []
    keyboard_events = []
    recording = True

    stop_key = key_stoprec.get().strip()

    # lock everything while recording
    record_btn['state'] = 'disabled'
    play_btn['state'] = 'disabled'
    save_btn['state'] = 'disabled'
    load_btn['state'] = 'disabled'
    recheck()

    def on_key_event(event):
        global recording
        keyboard_events.append(event)
        if event.name == stop_key and event.event_type == keyboard.KEY_DOWN:
            recording = False

    # need to hold a stable reference so unhook can find it
    mouse_handler = mouse_events.append

    keyboard.hook(on_key_event)
    mouse.hook(mouse_handler)

    while recording:
        window.update()

    keyboard.unhook(on_key_event)
    mouse.unhook(mouse_handler)

    # strip the stop key presses so they don't replay
    while keyboard_events and keyboard_events[-1].name == stop_key:
        keyboard_events.pop()

    record_btn['state'] = 'normal'
    load_btn['state'] = 'normal'

    if mouse_events or keyboard_events:
        play_btn['state'] = 'normal'
        save_btn['state'] = 'normal'
    else:
        play_btn['state'] = 'disabled'
        save_btn['state'] = 'disabled'

    recheck()


def play():
    global mouse_events, keyboard_events

    if not mouse_events and not keyboard_events:
        return

    try:
        loops = int(n_loop.get())
    except ValueError:
        messagebox.showerror("error", "loop count must be an integer.")
        return

    if loops < 1:
        messagebox.showerror("error", "loop count must be at least 1.")
        return

    record_btn['state'] = 'disabled'
    play_btn['state'] = 'disabled'
    save_btn['state'] = 'disabled'
    load_btn['state'] = 'disabled'
    recheck()

    def run_playback():
        for i in range(loops):
            threads = []

            if keyboard_events:
                t = threading.Thread(
                    target=lambda: keyboard.play(keyboard_events, speed_factor=1),
                    daemon=True)
                threads.append(t)

            if mouse_events:
                t = threading.Thread(
                    target=lambda: mouse.play(mouse_events, speed_factor=1),
                    daemon=True)
                threads.append(t)

            for t in threads:
                t.start()
            for t in threads:
                t.join()

            # small gap between loops
            if i < loops - 1:
                _time.sleep(0.3)

        window.after(0, restore_buttons)

    def restore_buttons():
        record_btn['state'] = 'normal'
        play_btn['state'] = 'normal'
        save_btn['state'] = 'normal'
        load_btn['state'] = 'normal'
        recheck()

    playback_thread = threading.Thread(target=run_playback, daemon=True)
    playback_thread.start()


def save():
    global mouse_events, keyboard_events
    if not mouse_events and not keyboard_events:
        messagebox.showinfo("save", "nothing to save.")
        return

    save_file = filedialog.asksaveasfilename(
        defaultextension=".json",
        filetypes=[("mimic files", "*.mimic"), ("json files", "*.json")])
    if not save_file:
        return

    data = {
        "mouse_events": [serialize_mouse_event(e) for e in mouse_events],
        "keyboard_events": [
            {
                "name": e.name,
                "scan_code": e.scan_code,
                "time": e.time,
                "event_type": e.event_type
            }
            for e in keyboard_events
        ]
    }

    try:
        with open(save_file, 'w') as file:
            json.dump(data, file, indent=2)
        messagebox.showinfo("save", "saved.")
    except Exception as e:
        messagebox.showerror("save error", str(e))


def load():
    global mouse_events, keyboard_events

    load_file = filedialog.askopenfilename(
        filetypes=[("mimic files", "*.mimic"), ("json files", "*.json")])
    if not load_file:
        return

    try:
        with open(load_file, 'r') as file:
            data = json.load(file)

        mouse_events = [
            deserialize_mouse_event(e)
            for e in data.get("mouse_events", [])
        ]

        keyboard_events = []
        for e in data.get("keyboard_events", []):
            keyboard_events.append(
                keyboard.KeyboardEvent(
                    name=e["name"],
                    scan_code=e["scan_code"],
                    time=e["time"],
                    event_type=e.get("event_type", keyboard.KEY_DOWN)
                )
            )

        play_btn['state'] = 'normal'
        save_btn['state'] = 'normal'
        recheck()

        messagebox.showinfo(
            "load",
            f"loaded {len(mouse_events)} mouse + {len(keyboard_events)} keyboard events.")
    except Exception as e:
        messagebox.showerror("load error", str(e))
        mouse_events, keyboard_events = [], []


window.resizable(0, 0)
window.mainloop()
