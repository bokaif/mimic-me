import customtkinter as ctk
import threading
import mouse
import keyboard
from tkinter import filedialog
from PIL import Image, ImageDraw
import json
import time as _time
import sys
import os
import ctypes

ctk.set_appearance_mode("dark")

# load inter font from assets
_base = os.path.dirname(os.path.abspath(__file__))
_FR_PRIVATE = 0x10
for _f in ("Inter-Regular.ttf", "Inter-Bold.ttf"):
    _fp = os.path.join(_base, "assets", _f)
    if os.path.exists(_fp):
        ctypes.windll.gdi32.AddFontResourceExW(_fp, _FR_PRIVATE, 0)
FONT = "Inter"

ACCENT = "#9b72cf"
ACCENT_H = "#b08de0"
DANGER = "#e05555"
DANGER_H = "#e87070"
SUCCESS = "#4ade80"
SUCCESS_H = "#22c55e"
SURFACE = "#111119"
CARD = "#1a1a2e"
CARD_BORDER = "#2a2a44"
INPUT_BG = "#252540"
MUTED = "#6c6c8a"
TITLEBAR_BG = "#0d0d15"
BORDER_COLOR = "#222238"
FILE_V = 2


def _icon(draw_fn, color="#e8e8f0", size=16):
    s = size * 4
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    draw_fn(d, s, color)
    out = img.resize((size, size), Image.LANCZOS)
    return ctk.CTkImage(light_image=out, dark_image=out, size=(size, size))


def _circle(d, s, c):
    p = int(s * 0.22)
    d.ellipse([p, p, s - p, s - p], fill=c)

def _tri(d, s, c):
    p = int(s * 0.22)
    d.polygon([(p + 2, p), (s - p, s // 2), (p + 2, s - p)], fill=c)

def _sq(d, s, c):
    p = int(s * 0.28)
    d.rectangle([p, p, s - p, s - p], fill=c)

def _arrow_down(d, s, c):
    w = max(2, int(s * 0.09))
    cx = s // 2
    d.line([(cx, int(s*0.15)), (cx, int(s*0.55))], fill=c, width=w)
    aw = int(s * 0.18)
    d.polygon([(cx-aw, int(s*0.45)), (cx+aw, int(s*0.45)), (cx, int(s*0.65))], fill=c)
    tp = int(s * 0.2)
    by = int(s * 0.82)
    d.line([(tp, int(s*0.65)), (tp, by)], fill=c, width=w)
    d.line([(tp, by), (s-tp, by)], fill=c, width=w)
    d.line([(s-tp, by), (s-tp, int(s*0.65))], fill=c, width=w)

def _folder(d, s, c):
    w = max(2, int(s * 0.09))
    p = int(s * 0.18)
    d.rectangle([p, int(s*0.35), s-p, s-p], outline=c, width=w)
    d.line([(p, int(s*0.35)), (p, int(s*0.2))], fill=c, width=w)
    d.line([(p, int(s*0.2)), (p+int(s*0.3), int(s*0.2))], fill=c, width=w)
    d.line([(p+int(s*0.3), int(s*0.2)), (p+int(s*0.35), int(s*0.35))], fill=c, width=w)

def _xmark(d, s, c):
    w = max(2, int(s * 0.1))
    p = int(s * 0.28)
    d.line([(p, p), (s-p, s-p)], fill=c, width=w)
    d.line([(s-p, p), (p, s-p)], fill=c, width=w)

def _minus(d, s, c):
    w = max(2, int(s * 0.1))
    p = int(s * 0.28)
    d.line([(p, s//2), (s-p, s//2)], fill=c, width=w)


class MimicMe(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.overrideredirect(True)
        self.configure(fg_color=BORDER_COLOR)
        self.geometry("460x600")

        self.mouse_events = []
        self.keyboard_events = []
        self.recording = False
        self.playing = False
        self._lock = threading.Lock()
        self._capturing_key = False
        self._stop_key = "esc"
        self._drag_x = 0
        self._drag_y = 0

        self._icons = {
            "record": _icon(_circle, "#ffffff", 16),
            "record_disabled": _icon(_circle, "#888899", 16),
            "play": _icon(_tri, "#111111", 16),
            "play_disabled": _icon(_tri, "#888899", 16),
            "stop": _icon(_sq, "#ffffff", 16),
            "stop_disabled": _icon(_sq, "#888899", 16),
            "save": _icon(_arrow_down, "#e8e8f0", 16),
            "save_disabled": _icon(_arrow_down, "#888899", 16),
            "load": _icon(_folder, "#e8e8f0", 16),
            "load_disabled": _icon(_folder, "#888899", 16),
            "close": _icon(_xmark, "#888899", 14),
            "close_hover": _icon(_xmark, "#ffffff", 14),
            "min": _icon(_minus, "#888899", 14),
        }

        self._build()
        self._bind_keys()
        self._center()
        self._setup_taskbar()
        self.bind_all("<Button-1>", self._steal_focus, add="+")

    def _build_titlebar(self):
        tb = ctk.CTkFrame(self, fg_color=TITLEBAR_BG, height=38, corner_radius=0)
        tb.pack(fill="x", padx=1, pady=(1, 0))
        tb.pack_propagate(False)

        try:
            self.iconbitmap(os.path.join(_base, "assets", "mimic-me.png"))
        except Exception:
            pass

        title_img = ctk.CTkImage(Image.open(os.path.join(_base, "assets", "mimic-me.png")), size=(14, 14))
        title = ctk.CTkLabel(
            tb, text=" mimic me", image=title_img, compound="left",
            font=ctk.CTkFont(family=FONT, size=12, weight="bold"),
            text_color=MUTED, anchor="w")
        title.pack(side="left", fill="x", expand=True, padx=(8, 4))

        close_btn = ctk.CTkButton(
            tb, text="", image=self._icons["close"],
            width=38, height=38, corner_radius=0,
            fg_color="transparent", hover_color=DANGER,
            command=self._quit)
        close_btn.pack(side="right")
        close_btn.bind("<Enter>", lambda e: close_btn.configure(image=self._icons["close_hover"]))
        close_btn.bind("<Leave>", lambda e: close_btn.configure(image=self._icons["close"]))

        min_btn = ctk.CTkButton(
            tb, text="", image=self._icons["min"],
            width=38, height=38, corner_radius=0,
            fg_color="transparent", hover_color="#2a2a44",
            command=self._minimize)
        min_btn.pack(side="right")

        for w in [tb, title]:
            w.bind("<Button-1>", self._start_drag)
            w.bind("<B1-Motion>", self._on_drag)

    def _start_drag(self, e):
        self._drag_x = e.x
        self._drag_y = e.y

    def _on_drag(self, e):
        self.geometry(f"+{self.winfo_x() + e.x - self._drag_x}+{self.winfo_y() + e.y - self._drag_y}")

    def _setup_taskbar(self):
        # make borderless window show in taskbar
        self.update_idletasks()
        hwnd = ctypes.windll.user32.GetParent(self.winfo_id())
        GWL_EXSTYLE = -20
        style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
        style = (style & ~0x00000080) | 0x00040000  # ~TOOLWINDOW | APPWINDOW
        ctypes.windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, style)
        self.withdraw()
        self.after(10, self.deiconify)

    def _minimize(self):
        hwnd = ctypes.windll.user32.GetParent(self.winfo_id())
        ctypes.windll.user32.ShowWindow(hwnd, 6)  # SW_MINIMIZE

    def _center(self):
        self.update_idletasks()
        self.geometry(f"+{(self.winfo_screenwidth()-self.winfo_width())//2}+{(self.winfo_screenheight()-self.winfo_height())//2}")

    def _build(self):
        self._build_titlebar()
        c = ctk.CTkFrame(self, fg_color=SURFACE, corner_radius=0)
        c.pack(fill="both", expand=True, padx=1, pady=(0, 1))

        ctk.CTkLabel(c, text="MIMIC ME", font=ctk.CTkFont(family=FONT, size=30, weight="bold"), text_color="#fff").pack(pady=(22, 0))
        ctk.CTkLabel(c, text="keyboard & mouse automation", font=ctk.CTkFont(family=FONT, size=12), text_color=MUTED).pack(pady=(2, 0))

        actions = ctk.CTkFrame(c, fg_color=CARD, corner_radius=0, border_width=1, border_color=CARD_BORDER)
        actions.pack(fill="x", padx=28, pady=(18, 0))
        row = ctk.CTkFrame(actions, fg_color="transparent")
        row.pack(padx=14, pady=14)
        row.grid_columnconfigure((0, 1, 2), weight=1, uniform="a")

        self.record_btn = ctk.CTkButton(row, text="record", image=self._icons["record"], compound="left", width=120, height=40, corner_radius=0, fg_color=DANGER, hover_color=DANGER_H, font=ctk.CTkFont(family=FONT, size=13, weight="bold"), command=self.record)
        self.record_btn._icon_name = "record"
        self.record_btn.grid(row=0, column=0, padx=4)

        self.play_btn = ctk.CTkButton(row, text="play", image=self._icons["play"], compound="left", width=120, height=40, corner_radius=0, fg_color=SUCCESS, hover_color=SUCCESS_H, text_color="#111", font=ctk.CTkFont(family=FONT, size=13, weight="bold"), command=self.play)
        self.play_btn._icon_name = "play"
        self._set_btn_state(self.play_btn, "disabled")
        self.play_btn.grid(row=0, column=1, padx=4)

        self.stop_btn = ctk.CTkButton(row, text="stop", image=self._icons["stop"], compound="left", width=120, height=40, corner_radius=0, fg_color=ACCENT, hover_color=ACCENT_H, font=ctk.CTkFont(family=FONT, size=13, weight="bold"), command=self.stop)
        self.stop_btn._icon_name = "stop"
        self._set_btn_state(self.stop_btn, "disabled")
        self.stop_btn.grid(row=0, column=2, padx=4)

        settings = ctk.CTkFrame(c, fg_color=CARD, corner_radius=0, border_width=1, border_color=CARD_BORDER)
        settings.pack(fill="x", padx=28, pady=(12, 0))
        inner = ctk.CTkFrame(settings, fg_color="transparent")
        inner.pack(fill="x", padx=18, pady=16)

        for label, widget_fn in self._setting_rows(inner):
            r = ctk.CTkFrame(inner, fg_color="transparent")
            r.pack(fill="x", pady=(0, 10))
            ctk.CTkLabel(r, text=label, text_color=MUTED, font=ctk.CTkFont(family=FONT, size=12)).pack(side="left")
            widget_fn(r)

        r4 = ctk.CTkFrame(inner, fg_color="transparent")
        r4.pack(fill="x", pady=(4, 0))
        self.rec_mouse = ctk.BooleanVar(value=True)
        self.rec_kb = ctk.BooleanVar(value=True)
        ctk.CTkSwitch(r4, text="mouse", variable=self.rec_mouse, font=ctk.CTkFont(family=FONT, size=12), text_color=MUTED, progress_color=ACCENT, button_color="#fff", button_hover_color="#ddd", height=20, switch_width=36, switch_height=18).pack(side="left", padx=(0, 20))
        ctk.CTkSwitch(r4, text="keyboard", variable=self.rec_kb, font=ctk.CTkFont(family=FONT, size=12), text_color=MUTED, progress_color=ACCENT, button_color="#fff", button_hover_color="#ddd", height=20, switch_width=36, switch_height=18).pack(side="left")

        frow = ctk.CTkFrame(c, fg_color="transparent")
        frow.pack(fill="x", padx=28, pady=(12, 0))
        frow.grid_columnconfigure((0, 1), weight=1, uniform="f")

        self.save_btn = ctk.CTkButton(frow, text="save config", image=self._icons["save"], compound="left", height=38, corner_radius=0, fg_color=CARD, hover_color="#252540", border_width=1, border_color=CARD_BORDER, font=ctk.CTkFont(family=FONT, size=12), command=self.save)
        self.save_btn._icon_name = "save"
        self._set_btn_state(self.save_btn, "disabled")
        self.save_btn.grid(row=0, column=0, padx=(0, 5), sticky="ew")

        self.load_btn = ctk.CTkButton(frow, text="load config", image=self._icons["load"], compound="left", height=38, corner_radius=0, fg_color=CARD, hover_color="#252540", border_width=1, border_color=CARD_BORDER, font=ctk.CTkFont(family=FONT, size=12), command=self.load)
        self.load_btn._icon_name = "load"
        self.load_btn.grid(row=0, column=1, padx=(5, 0), sticky="ew")

        sbar = ctk.CTkFrame(c, fg_color=CARD, corner_radius=0, border_width=1, border_color=CARD_BORDER, height=44)
        sbar.pack(fill="x", padx=28, pady=(12, 0))
        sbar.pack_propagate(False)
        self.status = ctk.CTkLabel(sbar, text="idle", font=ctk.CTkFont(family=FONT, size=12), text_color=MUTED)
        self.status.pack(expand=True)

        ctk.CTkLabel(c, text="ctrl+r record  ·  ctrl+p play  ·  ctrl+s save  ·  ctrl+l load", font=ctk.CTkFont(family=FONT, size=10), text_color="#5c5c78").pack(pady=(10, 16))

    def _setting_rows(self, parent):
        def loops(r):
            self.loops_entry = ctk.CTkEntry(r, width=64, height=30, corner_radius=0, justify="center", fg_color=INPUT_BG, border_width=0, font=ctk.CTkFont(family=FONT, size=12))
            self.loops_entry.pack(side="right")
            self.loops_entry.insert(0, "1")

        def speed(r):
            self.speed_sl = ctk.CTkSlider(r, from_=0.25, to=4.0, number_of_steps=15, width=170, height=16, button_color=ACCENT, button_hover_color=ACCENT_H, progress_color=ACCENT, command=lambda v: (self.speed_lbl.configure(text=f"{v:.2f}x"), setattr(self.speed_lbl, '_custom_value', None)))
            self.speed_sl.pack(side="right")
            self.speed_sl.set(1.0)
            self.speed_lbl = ctk.CTkLabel(r, text="1.00x", font=ctk.CTkFont(family=FONT, size=12), width=48, cursor="hand2")
            self.speed_lbl.pack(side="right", padx=(0, 8))
            self.speed_lbl.bind("<Button-1>", lambda e: self._inline_edit(self.speed_lbl, self.speed_sl, 0.25, 4.0, "x"))

        def delay(r):
            self.delay_sl = ctk.CTkSlider(r, from_=0, to=5.0, number_of_steps=50, width=170, height=16, button_color=ACCENT, button_hover_color=ACCENT_H, progress_color=ACCENT, command=lambda v: (self.delay_lbl.configure(text=f"{v:.2f}s"), setattr(self.delay_lbl, '_custom_value', None)))
            self.delay_sl.pack(side="right")
            self.delay_sl.set(0.3)
            self.delay_lbl = ctk.CTkLabel(r, text="0.30s", font=ctk.CTkFont(family=FONT, size=12), width=48, cursor="hand2")
            self.delay_lbl.pack(side="right", padx=(0, 8))
            self.delay_lbl.bind("<Button-1>", lambda e: self._inline_edit(self.delay_lbl, self.delay_sl, 0.0, 5.0, "s"))

        def stopkey(r):
            self.stopkey_btn = ctk.CTkButton(r, text="esc", width=90, height=30, corner_radius=0, fg_color=INPUT_BG, hover_color="#333350", border_width=1, border_color=CARD_BORDER, font=ctk.CTkFont(family=FONT, size=12), command=self._capture_stop_key)
            self.stopkey_btn.pack(side="right")

        return [("loops", loops), ("speed", speed), ("loop delay", delay), ("stop key", stopkey)]

    def _inline_edit(self, lbl, slider, vmin, vmax, suffix):
        lbl.pack_forget()
        parent = lbl.master
        entry = ctk.CTkEntry(parent, width=50, height=24, corner_radius=0, justify="center",
                             fg_color=INPUT_BG, border_width=1, border_color=ACCENT,
                             font=ctk.CTkFont(family=FONT, size=12))
        entry.pack(side="right")
        entry.insert(0, f"{getattr(lbl, '_custom_value', None) or slider.get():.2f}")
        entry.select_range(0, "end")
        entry.focus_set()
        def commit(e=None):
            try:
                v = float(entry.get())
                if v < 0:
                    v = 0
            except ValueError:
                v = slider.get()
            slider.set(max(vmin, min(vmax, v)))
            lbl.configure(text=f"{v:.2f}{suffix}")
            lbl._custom_value = v
            entry.destroy()
            lbl.pack(side="right")
        entry.bind("<Return>", commit)
        entry.bind("<FocusOut>", commit)

    def _capture_stop_key(self):
        if self._capturing_key:
            return
        self._capturing_key = True
        self._capture_held = []
        self.stopkey_btn.configure(text="press keys...", fg_color=ACCENT)
        def on_press(event):
            if event.event_type == keyboard.KEY_DOWN:
                if event.name not in self._capture_held:
                    self._capture_held.append(event.name)
                display = "+".join(self._capture_held)
                self.stopkey_btn.configure(text=display)
            elif event.event_type == keyboard.KEY_UP:
                if self._capture_held:
                    combo = "+".join(self._capture_held)
                    self._stop_key = combo
                    self.stopkey_btn.configure(text=combo, fg_color=INPUT_BG)
                    self._capture_held = []
                    self._capturing_key = False
                    keyboard.unhook(on_press)
        keyboard.hook(on_press)

    def _steal_focus(self, event):
        w = event.widget
        if not isinstance(w, (ctk.CTkEntry,)):
            self.focus_set()

    def _bind_keys(self):
        def _guarded(fn):
            def wrapper(e=None):
                if self._capturing_key or self.recording or self.playing:
                    return "break"
                fn()
            return wrapper
        self.bind("<Control-r>", _guarded(self.record))
        self.bind("<Control-p>", _guarded(self.play))
        self.bind("<Control-s>", _guarded(self.save))
        self.bind("<Control-l>", _guarded(self.load))

    def _set_status(self, msg):
        self.status.configure(text=msg)

    def _set_btn_state(self, btn, state):
        if not hasattr(btn, "_orig_fg"):
            btn._orig_fg = btn.cget("fg_color")
            btn._orig_hover = btn.cget("hover_color")
            btn._orig_text = btn.cget("text_color")
        
        if state == "disabled":
            btn.configure(state="disabled", fg_color="#44445a", hover_color="#44445a", text_color="#888899")
            if hasattr(btn, "_icon_name"):
                btn.configure(image=self._icons.get(f"{btn._icon_name}_disabled", btn.cget("image")))
        else:
            btn.configure(state="normal", fg_color=btn._orig_fg, hover_color=btn._orig_hover, text_color=btn._orig_text)
            if hasattr(btn, "_icon_name"):
                btn.configure(image=self._icons.get(btn._icon_name, btn.cget("image")))

    def _lock_ui(self):
        for b in [self.record_btn, self.play_btn, self.save_btn, self.load_btn]:
            self._set_btn_state(b, "disabled")
        self._set_btn_state(self.stop_btn, "normal")

    def _unlock_ui(self, has=True):
        self._set_btn_state(self.record_btn, "normal")
        self._set_btn_state(self.play_btn, "normal" if has else "disabled")
        self._set_btn_state(self.save_btn, "normal" if has else "disabled")
        self._set_btn_state(self.load_btn, "normal")
        self._set_btn_state(self.stop_btn, "disabled")

    def stop(self):
        with self._lock:
            self.recording = False
            self.playing = False

    def record(self):
        with self._lock:
            if self.recording or self.playing:
                return
            self.recording = True
        self.mouse_events = []
        self.keyboard_events = []
        sk = self._stop_key
        wm, wk = self.rec_mouse.get(), self.rec_kb.get()
        if not wm and not wk:
            self._set_status("turn on at least one input")
            with self._lock:
                self.recording = False
            return
        self._lock_ui()
        self._set_status(f"recording... press [{sk}] to stop")
        stop_parts = set(sk.split("+"))
        def on_key(ev):
            self.keyboard_events.append(ev)
            if ev.event_type == keyboard.KEY_DOWN and ev.name in stop_parts:
                if all(k == ev.name or keyboard.is_pressed(k) for k in stop_parts):
                    with self._lock:
                        self.recording = False
        mcb = self.mouse_events.append
        if wk: keyboard.hook(on_key)
        if wm: mouse.hook(mcb)
        try:
            while True:
                with self._lock:
                    if not self.recording: break
                self.update()
                _time.sleep(0.01)
        except: pass
        finally:
            if wk:
                try: keyboard.unhook(on_key)
                except: pass
            if wm:
                try: mouse.unhook(mcb)
                except: pass
            with self._lock:
                self.recording = False
        while self.keyboard_events and self.keyboard_events[-1].name in stop_parts:
            self.keyboard_events.pop()
        has = bool(self.mouse_events or self.keyboard_events)
        self._unlock_ui(has)
        self._set_status(f"recorded {len(self.mouse_events)}m + {len(self.keyboard_events)}k events" if has else "nothing recorded")

    def play(self):
        with self._lock:
            if self.recording or self.playing: return
            self.playing = True
        if not self.mouse_events and not self.keyboard_events:
            with self._lock: self.playing = False
            return
        try: loops = int(self.loops_entry.get())
        except ValueError:
            self._set_status("loop count must be a number")
            with self._lock: self.playing = False
            return
        if loops < 1:
            self._set_status("loop count must be at least 1")
            with self._lock: self.playing = False
            return
        spd = getattr(self.speed_lbl, '_custom_value', None) or self.speed_sl.get()
        dly = getattr(self.delay_lbl, '_custom_value', None) or self.delay_sl.get()
        self._lock_ui()
        self._set_status(f"playing {loops} loop(s) @ {spd:.1f}x...")
        def run():
            try:
                for i in range(loops):
                    with self._lock:
                        if not self.playing: break
                    ts = []
                    if self.keyboard_events:
                        ts.append(threading.Thread(target=lambda: keyboard.play(self.keyboard_events, speed_factor=spd), daemon=True))
                    if self.mouse_events:
                        ts.append(threading.Thread(target=lambda: mouse.play(self.mouse_events, speed_factor=spd), daemon=True))
                    for t in ts: t.start()
                    for t in ts: t.join()
                    if i < loops - 1: _time.sleep(dly)
            except: pass
            finally:
                with self._lock: self.playing = False
                self.after(0, lambda: (self._unlock_ui(True), self._set_status("playback done")))
        threading.Thread(target=run, daemon=True).start()

    @staticmethod
    def _ser_mouse(e):
        if isinstance(e, mouse.MoveEvent): return {"t":"m","x":e.x,"y":e.y,"ts":e.time}
        if isinstance(e, mouse.ButtonEvent): return {"t":"b","et":e.event_type,"btn":e.button,"ts":e.time}
        if isinstance(e, mouse.WheelEvent): return {"t":"w","d":e.delta,"ts":e.time}
        return {"t":"?","raw":list(e)}

    @staticmethod
    def _deser_mouse(d):
        t = d.get("t") or d.get("type")
        if t in ("m","move"): return mouse.MoveEvent(x=d.get("x"),y=d.get("y"),time=d.get("ts") or d.get("time"))
        if t in ("b","button"): return mouse.ButtonEvent(event_type=d.get("et") or d.get("event_type"),button=d.get("btn") or d.get("button"),time=d.get("ts") or d.get("time"))
        if t in ("w","wheel"): return mouse.WheelEvent(delta=d.get("d") or d.get("delta"),time=d.get("ts") or d.get("time"))
        raise ValueError(f"unknown event: {d}")

    def save(self):
        if not self.mouse_events and not self.keyboard_events:
            self._set_status("nothing to save"); return
        path = filedialog.asksaveasfilename(defaultextension=".mimic", filetypes=[("mimic files","*.mimic"),("json files","*.json")])
        if not path: return
        data = {"version":FILE_V,"settings":{"loops":self.loops_entry.get(),"speed":self.speed_sl.get(),"delay":self.delay_sl.get(),"stop_key":self._stop_key,"rec_mouse":self.rec_mouse.get(),"rec_keyboard":self.rec_kb.get()},"mouse_events":[self._ser_mouse(e) for e in self.mouse_events],"keyboard_events":[{"n":e.name,"sc":e.scan_code,"ts":e.time,"et":e.event_type} for e in self.keyboard_events]}
        try:
            with open(path,'w') as f: json.dump(data,f)
            self._set_status(f"saved → {os.path.basename(path)}")
        except Exception as ex: self._set_status(f"save failed: {ex}")

    def load(self):
        path = filedialog.askopenfilename(filetypes=[("mimic files","*.mimic"),("json files","*.json")])
        if not path: return
        try:
            with open(path,'r') as f: data = json.load(f)
            if not isinstance(data,dict): raise ValueError("invalid format")
            s = data.get("settings",{})
            if s:
                self.loops_entry.delete(0,"end"); self.loops_entry.insert(0,str(s.get("loops","1")))
                self.speed_sl.set(float(s.get("speed",1.0))); self.speed_lbl.configure(text=f"{self.speed_sl.get():.2f}x")
                self.delay_sl.set(float(s.get("delay",0.3))); self.delay_lbl.configure(text=f"{self.delay_sl.get():.2f}s")
                if "stop_key" in s: self._stop_key=s["stop_key"]; self.stopkey_btn.configure(text=self._stop_key)
                if "rec_mouse" in s: self.rec_mouse.set(s["rec_mouse"])
                if "rec_keyboard" in s: self.rec_kb.set(s["rec_keyboard"])
            self.mouse_events = [self._deser_mouse(e) for e in data.get("mouse_events",[])]
            self.keyboard_events = []
            for e in data.get("keyboard_events",[]):
                if isinstance(e,list): n,sc,ts,et=e[0],e[1],e[2],keyboard.KEY_DOWN
                elif isinstance(e,dict): n=e.get("n") or e.get("name"); sc=e.get("sc") or e.get("scan_code"); ts=e.get("ts") or e.get("time"); et=e.get("et") or e.get("event_type",keyboard.KEY_DOWN)
                else: raise ValueError(f"bad event: {e}")
                self.keyboard_events.append(keyboard.KeyboardEvent(name=n,scan_code=sc,time=ts,event_type=et))
            self._unlock_ui(bool(self.mouse_events or self.keyboard_events))
            self._set_status(f"loaded {len(self.mouse_events)}m + {len(self.keyboard_events)}k ← {os.path.basename(path)}")
        except json.JSONDecodeError: self._set_status("file is not valid json")
        except Exception as ex: self._set_status(f"load failed: {ex}"); self.mouse_events,self.keyboard_events=[],[]

    def _quit(self):
        with self._lock: self.recording=False; self.playing=False
        try: keyboard.unhook_all(); mouse.unhook_all()
        except: pass
        self.destroy(); sys.exit(0)

if __name__ == "__main__":
    MimicMe().mainloop()
