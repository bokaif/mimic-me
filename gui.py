import threading
import mouse
import keyboard
from tkinter import Tk, Canvas, Entry, Button, PhotoImage, filedialog, messagebox
import json
import time as _time
import sys
import os

mouse_events = []
keyboard_events = []
recording = False
playing = False
_lock = threading.Lock()

FILE_VERSION = 1


def get(path: str):
    base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, "assets", path)


window = Tk()
window.geometry("700x406")
window.configure(bg="#FFFFFF")
window.title("Mimic Me")

canvas = Canvas(
    window, bg="#FFFFFF", height=406, width=700,
    bd=0, highlightthickness=0, relief="ridge"
)
canvas.place(x=0, y=0)

image_image_1 = PhotoImage(file=get("bg.png"))
canvas.create_image(350.0, 203.0, image=image_image_1)

canvas.create_text(
    259.0, 67.0, anchor="nw", text="MIMIC ME",
    fill="#FFFFFF", font=("NexaBold", 39 * -1))

canvas.create_text(
    106.0, 118.0, anchor="nw",
    text="A tool that mimics your keyboard and mouse events",
    fill="#FFFFFF", font=("NexaLight", 20 * -1))

canvas.create_text(
    121.0, 177.0, anchor="nw", text="Number of Loops",
    fill="#D2D1D2", font=("NexaLight", 16 * -1))

canvas.create_rectangle(97.0, 204.0, 288.0, 239.0, fill="#A1A2A4", outline="")

n_loop_img = PhotoImage(file=get("n_loop.png"))
canvas.create_image(192.0, 221.5, image=n_loop_img)
n_loop = Entry(bd=0, bg="#A0A1A3", highlightthickness=0)
n_loop.place(x=105.0, y=207.0, width=174.0, height=27.0)

canvas.create_text(
    101.0, 270.0, anchor="nw", text="Key to Stop Recording",
    fill="#D2D1D2", font=("NexaLight", 16 * -1))

canvas.create_rectangle(97.0, 297.0, 288.0, 332.0, fill="#A1A2A4", outline="")

key_stoprec_img = PhotoImage(file=get("key_stoprec.png"))
canvas.create_image(192.0, 314.5, image=key_stoprec_img)
key_stoprec = Entry(bd=0, bg="#A1A2A4", highlightthickness=0)
key_stoprec.place(x=105.0, y=299.0, width=174.0, height=29.0)

# status label at the bottom of the left panel
status_text = canvas.create_text(
    192.0, 360.0, anchor="center", text="",
    fill="#FFFFFF", font=("NexaLight", 13 * -1))

record_img = PhotoImage(file=get("record_btn.png"))
record_btn = Button(
    image=record_img, borderwidth=0, highlightthickness=0,
    command=lambda: record(), relief="flat")
record_btn.place(x=346.0, y=204.0, width=112.62, height=47.32)

play_imag = PhotoImage(file=get("play_btn.png"))
play_btn = Button(
    image=play_imag, borderwidth=0, highlightthickness=0,
    command=lambda: play(), relief="flat")
play_btn.place(x=490.38, y=204.0, width=112.62, height=47.32)

load_img = PhotoImage(file=get("load_btn.png"))
load_btn = Button(
    image=load_img, borderwidth=0, highlightthickness=0,
    command=lambda: load(), relief="flat")
load_btn.place(x=346.0, y=284.68, width=112.62, height=47.32)

save_img = PhotoImage(file=get("save_btn.png"))
save_btn = Button(
    image=save_img, borderwidth=0, highlightthickness=0,
    command=lambda: save(), relief="flat")
save_btn.place(x=490.38, y=284.68, width=112.62, height=47.32)

record_btn['state'] = 'normal'
play_btn['state'] = 'disabled'
save_btn['state'] = 'disabled'
load_btn['state'] = 'normal'


def set_status(msg):
    canvas.itemconfig(status_text, text=msg)


def recheck():
    for btn in [record_btn, play_btn, save_btn, load_btn]:
        btn['cursor'] = "hand2" if str(btn['state']) != 'disabled' else "cross"


def set_all_buttons(state):
    for btn in [record_btn, play_btn, save_btn, load_btn]:
        btn['state'] = state
    recheck()


recheck()
n_loop.insert(0, "1")
key_stoprec.insert(0, "esc")


# -- serialization --

def serialize_mouse_event(event):
    if isinstance(event, mouse.MoveEvent):
        return {"t": "m", "x": event.x, "y": event.y, "ts": event.time}
    elif isinstance(event, mouse.ButtonEvent):
        return {"t": "b", "et": event.event_type, "btn": event.button, "ts": event.time}
    elif isinstance(event, mouse.WheelEvent):
        return {"t": "w", "d": event.delta, "ts": event.time}
    return {"t": "?", "raw": list(event)}


def deserialize_mouse_event(data):
    t = data.get("t") or data.get("type")
    if t in ("m", "move"):
        return mouse.MoveEvent(
            x=data.get("x"), y=data.get("y"),
            time=data.get("ts") or data.get("time"))
    elif t in ("b", "button"):
        return mouse.ButtonEvent(
            event_type=data.get("et") or data.get("event_type"),
            button=data.get("btn") or data.get("button"),
            time=data.get("ts") or data.get("time"))
    elif t in ("w", "wheel"):
        return mouse.WheelEvent(
            delta=data.get("d") or data.get("delta"),
            time=data.get("ts") or data.get("time"))
    raise ValueError(f"unknown mouse event: {data}")


# -- core --

def record():
    global mouse_events, keyboard_events, recording

    with _lock:
        if recording or playing:
            return
        recording = True

    mouse_events = []
    keyboard_events = []
    stop_key = key_stoprec.get().strip() or "esc"

    set_all_buttons('disabled')
    set_status(f"recording... press [{stop_key}] to stop")

    def on_key_event(event):
        global recording
        keyboard_events.append(event)
        if event.name == stop_key and event.event_type == keyboard.KEY_DOWN:
            with _lock:
                recording = False

    # stable ref so unhook can find it
    mouse_handler = mouse_events.append

    keyboard.hook(on_key_event)
    mouse.hook(mouse_handler)

    try:
        while True:
            with _lock:
                if not recording:
                    break
            window.update()
            _time.sleep(0.01)
    except Exception:
        pass
    finally:
        try:
            keyboard.unhook(on_key_event)
        except Exception:
            pass
        try:
            mouse.unhook(mouse_handler)
        except Exception:
            pass

        with _lock:
            recording = False

    # strip stop key so it doesn't replay
    while keyboard_events and keyboard_events[-1].name == stop_key:
        keyboard_events.pop()

    has_events = bool(mouse_events or keyboard_events)

    record_btn['state'] = 'normal'
    load_btn['state'] = 'normal'
    play_btn['state'] = 'normal' if has_events else 'disabled'
    save_btn['state'] = 'normal' if has_events else 'disabled'
    recheck()

    if has_events:
        set_status(f"recorded {len(mouse_events)}m + {len(keyboard_events)}k events")
    else:
        set_status("nothing recorded")


def play():
    global playing

    with _lock:
        if recording or playing:
            return
        playing = True

    if not mouse_events and not keyboard_events:
        with _lock:
            playing = False
        return

    try:
        loops = int(n_loop.get())
    except ValueError:
        messagebox.showerror("error", "loop count must be an integer.")
        with _lock:
            playing = False
        return

    if loops < 1:
        messagebox.showerror("error", "loop count must be at least 1.")
        with _lock:
            playing = False
        return

    set_all_buttons('disabled')
    set_status(f"playing {loops} loop(s)...")

    def run_playback():
        global playing
        try:
            for i in range(loops):
                with _lock:
                    if not playing:
                        break

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

                if i < loops - 1:
                    _time.sleep(0.3)
        except Exception:
            pass
        finally:
            with _lock:
                playing = False
            window.after(0, _after_play)

    def _after_play():
        record_btn['state'] = 'normal'
        play_btn['state'] = 'normal'
        save_btn['state'] = 'normal'
        load_btn['state'] = 'normal'
        recheck()
        set_status("playback done")

    threading.Thread(target=run_playback, daemon=True).start()


def save():
    if not mouse_events and not keyboard_events:
        messagebox.showinfo("save", "nothing to save.")
        return

    save_file = filedialog.asksaveasfilename(
        defaultextension=".mimic",
        filetypes=[("mimic files", "*.mimic"), ("json files", "*.json")])
    if not save_file:
        return

    data = {
        "version": FILE_VERSION,
        "mouse_events": [serialize_mouse_event(e) for e in mouse_events],
        "keyboard_events": [
            {"name": e.name, "sc": e.scan_code,
             "ts": e.time, "et": e.event_type}
            for e in keyboard_events
        ]
    }

    try:
        with open(save_file, 'w') as f:
            json.dump(data, f)
        set_status(f"saved to {os.path.basename(save_file)}")
    except Exception as e:
        messagebox.showerror("save error", str(e))


def load():
    global mouse_events, keyboard_events

    load_file = filedialog.askopenfilename(
        filetypes=[("mimic files", "*.mimic"), ("json files", "*.json")])
    if not load_file:
        return

    try:
        with open(load_file, 'r') as f:
            data = json.load(f)

        if not isinstance(data, dict):
            raise ValueError("invalid file format")

        mouse_events = [
            deserialize_mouse_event(e)
            for e in data.get("mouse_events", [])
        ]

        keyboard_events = []
        for e in data.get("keyboard_events", []):
            # handle both old (name, scan_code, time) and new dict format
            if isinstance(e, list):
                name, scan_code, ts = e[0], e[1], e[2]
                et = keyboard.KEY_DOWN
            elif isinstance(e, dict):
                name = e.get("name")
                scan_code = e.get("sc") or e.get("scan_code")
                ts = e.get("ts") or e.get("time")
                et = e.get("et") or e.get("event_type", keyboard.KEY_DOWN)
            else:
                raise ValueError(f"bad keyboard event: {e}")

            keyboard_events.append(
                keyboard.KeyboardEvent(
                    name=name, scan_code=scan_code,
                    time=ts, event_type=et))

        play_btn['state'] = 'normal'
        save_btn['state'] = 'normal'
        recheck()
        set_status(
            f"loaded {len(mouse_events)}m + {len(keyboard_events)}k from {os.path.basename(load_file)}")

    except json.JSONDecodeError:
        messagebox.showerror("load error", "file is not valid json.")
        mouse_events, keyboard_events = [], []
    except Exception as e:
        messagebox.showerror("load error", str(e))
        mouse_events, keyboard_events = [], []


def on_close():
    global recording, playing
    with _lock:
        recording = False
        playing = False
    try:
        keyboard.unhook_all()
        mouse.unhook_all()
    except Exception:
        pass
    window.destroy()
    sys.exit(0)


window.protocol("WM_DELETE_WINDOW", on_close)
window.resizable(0, 0)
window.mainloop()
