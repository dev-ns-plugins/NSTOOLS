import tkinter as tk
from tkinter import ttk, messagebox
import pyautogui
import time
import threading
import keyboard
import random
import ctypes
import sys
import json
import os
import math
import webbrowser

def resource_path(relative_path: str) -> str:
    """Get absolute path to resource, works for dev and PyInstaller."""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = getattr(sys, '_MEIPASS')
    except Exception:
        # In dev: base is this file's directory; icon is at project root
        base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    return os.path.join(base_path, relative_path)

class ConquerClicker:
    def __init__(self):
        # Verificar privilégios de administrador
        # Quando empacotado (sys.frozen), o manifest UAC do executável já cuida da elevação
        if not getattr(sys, 'frozen', False):
            if not ctypes.windll.shell32.IsUserAnAdmin():
                ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
                sys.exit()
        
        self.root = tk.Tk()
        self.root.title("NS Clicker V1 - dsc.gg/nsplugins")
        self.root.geometry("220x75")
        self.root.configure(bg='#000000')
        # Set window icon if available
        try:
            self.root.iconbitmap(resource_path('icon.ico'))
        except Exception:
            pass
        try:
            self.root.overrideredirect(True)      
            self.root.wm_attributes("-toolwindow", True)
        except Exception:
            pass
        self.root.resizable(False, False)
        
        self.timers = {
            'left': False, 'right': False,
            'f1': False, 'f2': False, 'f3': False, 'f4': False, 'f5': False,
            'f6': False, 'f7': False, 'f8': False, 'f9': False, 'f10': False,
            'ctrl_hold': False
        }
        
        # Estado de pausa global
        self.paused = False
        
        self.timer_threads = {}
        # Auto Hunt (mouse circle)
        self.auto_hunt_active = False
        self._auto_hunt_thread = None
        self._auto_hunt_center = None
        
        # Gravação de movimentos
        self.recording = False
        self.recorded_actions = []
        self.recording_thread = None
        
        # Recursos removidos: gold/dragonball detection e hunt
        
        # Configurações
        self.root.attributes('-topmost', True)
        self.root.attributes('-alpha', 0.9)
        pyautogui.FAILSAFE = False
        pyautogui.PAUSE = 0.0
        
        self.setup_ui()
        self.setup_hotkeys()
        
    def setup_ui(self):
        # HUD Header (black bg, purple text)
        header = tk.Frame(self.root, bg='#000000', height=14)
        header.pack(fill='x', padx=1, pady=1)
        header.pack_propagate(False)

        # Status on the left
        self.status = tk.Label(header, text="Status: IDLE", fg='#8b5cf6', bg='#000000',
                               font=('Arial', 6, 'bold'))
        self.status.pack(side='left')

        # Options and Close on the right
        right_box = tk.Frame(header, bg='#000000')
        right_box.pack(side='right')
        self.opt_label = tk.Label(right_box, text='O', fg='#8b5cf6', bg='#000000', font=('Arial', 7, 'bold'), cursor='hand2')
        self.close_label = tk.Label(right_box, text='X', fg='#8b5cf6', bg='#000000', font=('Arial', 7, 'bold'), cursor='hand2')
        self.opt_label.pack(side='left', padx=4)
        self.close_label.pack(side='left', padx=2)
        # Use ButtonRelease to avoid conflict with drag start
        self.opt_label.bind('<ButtonRelease-1>', lambda e: self.open_settings())
        self.close_label.bind('<ButtonRelease-1>', lambda e: self.stop_all())
        # Permitir arrastar a HUD pelo header
        header.bind('<ButtonPress-1>', self._start_move)
        header.bind('<B1-Motion>', self._on_move)
        self.status.bind('<ButtonPress-1>', self._start_move)
        self.status.bind('<B1-Motion>', self._on_move)
        self.opt_label.bind('<ButtonPress-1>', self._start_move)
        self.opt_label.bind('<B1-Motion>', self._on_move)
        self.close_label.bind('<ButtonPress-1>', self._start_move)
        self.close_label.bind('<B1-Motion>', self._on_move)

        # HUD Body: row for Ctrl Left Right
        body = tk.Frame(self.root, bg='#000000')
        body.pack(fill='x', padx=2)

        self.ctrl_btn = tk.Label(body, text='Ctrl', fg='#8b5cf6', bg='#000000', font=('Arial', 7, 'bold'), cursor='hand2')
        self.left_btn = tk.Label(body, text='Left', fg='#8b5cf6', bg='#000000', font=('Arial', 7, 'bold'), cursor='hand2')
        self.right_btn = tk.Label(body, text='Right', fg='#8b5cf6', bg='#000000', font=('Arial', 7, 'bold'), cursor='hand2')
        self.ctrl_btn.grid(row=0, column=0, sticky='w')
        self.left_btn.grid(row=0, column=1)
        self.right_btn.grid(row=0, column=2, sticky='e')

        self.ctrl_btn.bind('<Button-1>', lambda e: self.toggle_ctrl_hold())
        self.left_btn.bind('<Button-1>', lambda e: self.toggle_left())
        self.right_btn.bind('<Button-1>', lambda e: self.toggle_right())

        # HUD F-keys row
        frow = tk.Frame(self.root, bg='#000000')
        frow.pack(fill='x', padx=2, pady=1)
        self.fkey_buttons = {}
        for i in range(1, 11):
            lbl = tk.Label(frow, text=f'F{i}', fg='#8b5cf6', bg='#000000', font=('Arial', 7, 'bold'), cursor='hand2')
            lbl.pack(side='left', padx=2)
            self.fkey_buttons[f'f{i}'] = lbl
            lbl.bind('<Button-1>', lambda e, x=f'f{i}': self.toggle_fkey(x))

        # Ensure settings vars exist and load settings
        self.build_settings_backend()
        try:
            self.load_settings()
            self.attach_settings_traces()
        except Exception as e:
            print(f"Erro ao carregar configurações: {e}")

    def set_active_style(self, widget, active: bool, label_text: str):
        # HUD style: keep same text, change shade of red when active
        try:
            # Purple palette
            color = '#c4b5fd' if active else '#8b5cf6'
            widget.config(fg=color, text=label_text)
        except Exception:
            pass

    def build_settings_backend(self):
        # Ensure settings variables are created if not using tabs
        if not hasattr(self, 'left_delay'):
            self.left_delay = tk.StringVar(value='100')
        if not hasattr(self, 'right_delay'):
            self.right_delay = tk.StringVar(value='100')
        if not hasattr(self, 'f_delay'):
            self.f_delay = tk.StringVar(value='100')
        if not hasattr(self, 'failsafe'):
            self.failsafe = tk.BooleanVar(value=False)
        if not hasattr(self, 'auto_save'):
            self.auto_save = tk.BooleanVar(value=True)
        if not hasattr(self, 'auto_hunt'):
            self.auto_hunt = tk.BooleanVar(value=False)
        if not hasattr(self, 'hunt_radius'):
            self.hunt_radius = tk.StringVar(value='50')  # pixels
        if not hasattr(self, 'hunt_speed_ms'):
            self.hunt_speed_ms = tk.StringVar(value='20')  # delay per step in ms
        if not hasattr(self, 'ui_alpha'):
            self.ui_alpha = tk.StringVar(value=str(int(self.root.attributes('-alpha') * 100)))
        pyautogui.FAILSAFE = bool(self.failsafe.get())

    def open_settings(self):
        # Options window similar to screenshot (simple, white theme)
        if hasattr(self, 'settings_win') and self.settings_win and tk.Toplevel.winfo_exists(self.settings_win):
            self.settings_win.lift()
            return
        win = tk.Toplevel(self.root)
        self.settings_win = win
        win.title('Options')
        # Compact dark theme matching HUD
        _bg = '#000000'
        _panel = '#000000'
        _text = '#e5e7eb'
        _muted = '#9ca3af'
        _entry_bg = '#0f0f10'
        _accent = '#8b5cf6'
        win.configure(bg=_bg)
        # Start with a moderate size; we'll auto-fit to content after building UI
        win.geometry('480x280')
        win.minsize(420, 240)
        win.resizable(True, True)
        # Borderless window (remove native title bar) and keep on top
        try:
            win.overrideredirect(True)
        except Exception:
            pass
        try:
            win.transient(self.root)
            win.lift()
            win.attributes('-topmost', True)
            # Apply current transparency to Options too
            try:
                current_alpha = max(0.5, min(1.0, float(self.ui_alpha.get())/100.0))
            except Exception:
                current_alpha = max(0.5, min(1.0, float(self.root.attributes('-alpha'))))
            win.attributes('-alpha', current_alpha)
        except Exception:
            pass
        # Position near current mouse to make it obvious
        try:
            mx, my = pyautogui.position()
            win.geometry(f"+{mx+12}+{my+12}")
        except Exception:
            pass

        # Custom header (for drag + close button)
        header = tk.Frame(win, bg=_panel, height=18)
        header.pack(fill='x', side='top')
        title = tk.Label(header, text='Options', bg=_panel, fg=_accent, font=('Arial', 7, 'bold'))
        title.pack(side='left', padx=4, pady=2)
        close_btn = tk.Button(header, text='✕', command=lambda: self._close_settings(),
                              bg=_panel, fg=_accent, activebackground=_panel, activeforeground='#c4b5fd',
                              bd=0, relief='flat', font=('Arial', 7, 'bold'), cursor='hand2')
        close_btn.pack(side='right', padx=4, pady=2)
        # Drag behavior for the borderless window
        _drag = {'x': 0, 'y': 0}
        def _start_move_opt(e):
            _drag['x'] = e.x
            _drag['y'] = e.y
        def _on_move_opt(e):
            try:
                x = e.x_root - _drag['x']
                y = e.y_root - _drag['y']
                win.geometry(f"+{x}+{y}")
            except Exception:
                pass
        header.bind('<ButtonPress-1>', _start_move_opt)
        header.bind('<B1-Motion>', _on_move_opt)
        title.bind('<ButtonPress-1>', _start_move_opt)
        title.bind('<B1-Motion>', _on_move_opt)
        # ESC to close
        win.bind('<Escape>', lambda e: self._close_settings())

        # Row: Save Settings, Transparency, Stay On Top
        row1 = tk.Frame(win, bg=_panel)
        row1.pack(fill='x', padx=8, pady=6)
        save_cb = tk.Checkbutton(row1, text='Save Settings', variable=self.auto_save, bg=_panel, fg=_text, selectcolor=_accent, activebackground=_panel, activeforeground=_text, font=('Arial', 7))
        save_cb.pack(side='left')
        tk.Label(row1, text='Transparency:', bg=_panel, fg=_text, font=('Arial', 7)).pack(side='left', padx=(4, 2))
        # Real-time transparency slider (50-100)
        alpha_scale = tk.Scale(row1, from_=50, to=100, orient='horizontal', length=160,
                               bg=_panel, fg=_text, highlightthickness=0, troughcolor='#2a2a2a', bd=0, font=('Arial', 7))
        try:
            alpha_scale.set(int(self.ui_alpha.get()))
        except Exception:
            alpha_scale.set(int(self.root.attributes('-alpha') * 100))
        alpha_scale.pack(side='left')
        def on_alpha_change(val):
            try:
                self.ui_alpha.set(str(int(float(val))))
            except Exception:
                pass
        alpha_scale.configure(command=on_alpha_change)
        stay_cb_var = tk.BooleanVar(value=bool(self.root.attributes('-topmost')))
        def toggle_stay():
            self.root.attributes('-topmost', stay_cb_var.get())
        tk.Checkbutton(row1, text='Stay On Top', variable=stay_cb_var, command=toggle_stay, bg=_panel, fg=_text, selectcolor=_accent, activebackground=_panel, activeforeground=_text, font=('Arial', 7)).pack(side='right')

        # Group: Timer speeds
        frame = tk.LabelFrame(win, text='Timer speeds', bg=_panel, fg=_accent, font=('Arial', 7, 'bold'), relief='ridge', bd=1, labelanchor='w')
        frame.pack(fill='x', padx=8, pady=4)
        for c in range(6):
            frame.grid_columnconfigure(c, weight=0)
        tk.Label(frame, text='Left:', bg=_panel, fg=_text, font=('Arial', 7)).grid(row=0, column=0, sticky='w', padx=(6,0), pady=4)
        tk.Entry(frame, textvariable=self.left_delay, width=6, bg=_entry_bg, fg=_text, insertbackground=_text, relief='flat').grid(row=0, column=1, padx=(4,8))
        tk.Label(frame, text='Right:', bg=_panel, fg=_text, font=('Arial', 7)).grid(row=0, column=2, sticky='w', padx=(6,0))
        tk.Entry(frame, textvariable=self.right_delay, width=6, bg=_entry_bg, fg=_text, insertbackground=_text, relief='flat').grid(row=0, column=3, padx=(4,8))
        tk.Label(frame, text='F Keys:', bg=_panel, fg=_text, font=('Arial', 7)).grid(row=0, column=4, sticky='w', padx=(6,0))
        tk.Entry(frame, textvariable=self.f_delay, width=6, bg=_entry_bg, fg=_text, insertbackground=_text, relief='flat').grid(row=0, column=5, padx=(4,8))

        # Group: Auto Hunt (circle)
        ah = tk.LabelFrame(win, text='Auto Hunt', bg=_panel, fg=_accent, font=('Arial', 7, 'bold'), relief='ridge', bd=1, labelanchor='w')
        ah.pack(fill='x', padx=8, pady=4)
        for c in range(5):
            ah.grid_columnconfigure(c, weight=0)
        tk.Checkbutton(ah, text='Enable', variable=self.auto_hunt, bg=_panel, fg=_text, selectcolor=_accent, activebackground=_panel, activeforeground=_text, font=('Arial', 7), command=self.toggle_auto_hunt).grid(row=0, column=0, sticky='w', padx=(6,8), pady=4)
        tk.Label(ah, text='Radius:', bg=_panel, fg=_text, font=('Arial', 7)).grid(row=0, column=1, padx=(6,0))
        tk.Entry(ah, textvariable=self.hunt_radius, width=6, bg=_entry_bg, fg=_text, insertbackground=_text, relief='flat').grid(row=0, column=2, padx=(4,8))
        tk.Label(ah, text='Speed (ms):', bg=_panel, fg=_text, font=('Arial', 7)).grid(row=0, column=3, padx=(6,0))
        tk.Entry(ah, textvariable=self.hunt_speed_ms, width=6, bg=_entry_bg, fg=_text, insertbackground=_text, relief='flat').grid(row=0, column=4, padx=(4,8))
        # Hotkeys section removed (see HOTKEYS.txt for usage)

        # Save/Load buttons
        actions = tk.Frame(win, bg=_panel)
        actions.pack(fill='x', padx=8, pady=6)
        def _open_discord():
            try:
                webbrowser.open('https://dsc.gg/nsplugins')
            except Exception:
                pass
        tk.Button(actions, text='Save', command=self.save_settings, bg=_entry_bg, fg=_text, activebackground=_panel, activeforeground=_text, relief='flat', font=('Arial', 7, 'bold')).pack(side='left')
        tk.Button(actions, text='Load', command=self.load_settings, bg=_entry_bg, fg=_text, activebackground=_panel, activeforeground=_text, relief='flat', font=('Arial', 7, 'bold')).pack(side='left', padx=6)
        tk.Button(actions, text='Discord', command=_open_discord, bg=_entry_bg, fg=_accent, activebackground=_panel, activeforeground='#c4b5fd', relief='flat', font=('Arial', 7, 'bold'), cursor='hand2').pack(side='right')

        # Auto-fit size to content to remove empty space
        try:
            win.update_idletasks()
            req_w = max(win.winfo_reqwidth() + 8, 420)
            req_h = max(win.winfo_reqheight() + 8, 220)
            # Keep within a reasonable max
            req_w = min(req_w, 600)
            req_h = min(req_h, 400)
            win.minsize(req_w, req_h)
            win.geometry(f"{req_w}x{req_h}")
        except Exception:
            pass

    def toggle_auto_hunt(self):
        if bool(self.auto_hunt.get()):
            self.start_auto_hunt()
        else:
            self.stop_auto_hunt()

    def toggle_auto_hunt_hotkey(self):
        try:
            self.auto_hunt.set(not bool(self.auto_hunt.get()))
        except Exception:
            pass

    def start_auto_hunt(self):
        if self.auto_hunt_active:
            return
        # Set center at current mouse position
        try:
            cx, cy = pyautogui.position()
            self._auto_hunt_center = (cx, cy)
        except Exception:
            self._auto_hunt_center = None
        self.auto_hunt_active = True

        def loop():
            theta = 0.0
            while self.auto_hunt_active:
                try:
                    if self.paused:
                        time.sleep(0.05)
                        continue
                    r = max(5, int(self.hunt_radius.get()))
                    delay = max(5, int(self.hunt_speed_ms.get())) / 1000.0
                    if self._auto_hunt_center is None:
                        cx, cy = pyautogui.position()
                        self._auto_hunt_center = (cx, cy)
                    cx, cy = self._auto_hunt_center
                    x = int(cx + r * math.cos(theta))
                    y = int(cy + r * math.sin(theta))
                    pyautogui.moveTo(x, y, duration=0)
                    theta += 0.25  # step angle
                    time.sleep(delay)
                except Exception:
                    break

        self._auto_hunt_thread = threading.Thread(target=loop, daemon=True)
        self._auto_hunt_thread.start()

    def stop_auto_hunt(self):
        self.auto_hunt_active = False
        try:
            self.auto_hunt.set(False)
        except Exception:
            pass

    def setup_hotkeys(self):
        # Reset and register global hotkeys to match HUD behavior
        try:
            keyboard.unhook_all()
        except Exception:
            pass
        try:
            # Pause/Resume
            keyboard.add_hotkey('pause', self.toggle_pause_resume, trigger_on_release=False)
        except Exception as e:
            print('Hotkey error (pause):', e)
        # Toggles
        for combo, func in [
            ('insert', self.toggle_ctrl_hold),
            ('home', self.toggle_left),
            ('page up', self.toggle_right),
        ]:
            try:
                keyboard.add_hotkey(combo, func, trigger_on_release=False)
            except Exception as e:
                print(f'Hotkey error ({combo}):', e)
        # F keys mapped to skill keys (press actual F1..F10)
        fkeys = ['f1','f2','f3','f4','f5','f6','f7','f8','f9','f10']
        for fk in fkeys:
            try:
                keyboard.add_hotkey(fk, lambda fk=fk: self.toggle_fkey(fk), trigger_on_release=False)
            except Exception as e:
                print(f'Hotkey error ({fk}):', e)
        # Backup hotkey to toggle CTRL hold if needed (no CTRL involved)
        try:
            keyboard.add_hotkey('alt+c', self.toggle_ctrl_hold, trigger_on_release=False)
        except Exception as e:
            print('Hotkey error (alt+c):', e)
        # Stop and exit
        for combo in ('alt+s','ctrl+alt+s'):
            try:
                keyboard.add_hotkey(combo, self.stop_all, trigger_on_release=False)
            except Exception as e:
                print(f'Hotkey error ({combo}):', e)
        # Open options
        try:
            keyboard.add_hotkey('alt+o', self.open_settings, trigger_on_release=False)
        except Exception as e:
            print('Hotkey error (alt+o):', e)
        # Auto Hunt toggle (End key)
        try:
            keyboard.add_hotkey('end', self.toggle_auto_hunt_hotkey, trigger_on_release=False)
        except Exception as e:
            print('Hotkey error (end):', e)
    
    def setup_hunt_tab(self):
        # Legacy stub (removed UI)
        return
        
        # Mouse Recording
        recording_frame = tk.LabelFrame(self.hunt_tab, text="MOUSE RECORDING", fg='#8b5cf6', bg='#1a1a1a', 
                                      font=('Arial', 10, 'bold'))
        recording_frame.pack(fill='x', pady=5, padx=10)
        
        # Recording controls
        controls_frame = tk.Frame(recording_frame, bg='#1a1a1a')
        controls_frame.pack(fill='x', pady=5)
        
        self.record_btn = self.create_button(controls_frame, "RECORD", self.toggle_recording, 0, 0)
        self.play_btn = self.create_button(controls_frame, "PLAY", self.play_recording, 0, 1)
        self.save_btn = self.create_button(controls_frame, "SAVE", self.save_recording, 0, 2)
        self.load_btn = self.create_button(controls_frame, "LOAD", self.load_recording, 0, 3)
        self.clear_btn = self.create_button(controls_frame, "CLEAR", self.clear_recording, 0, 4)
        
        # Recording info
        info_frame = tk.Frame(recording_frame, bg='#1a1a1a')
        info_frame.pack(fill='x', pady=5)
        
        self.recording_info = tk.Label(info_frame, text="No recording", fg='#888888', bg='#1a1a1a', 
                                     font=('Arial', 8))
        self.recording_info.pack(anchor='w')
        
        # Recording list
        list_frame = tk.Frame(recording_frame, bg='#1a1a1a')
        list_frame.pack(fill='both', expand=True, pady=5)
        
        tk.Label(list_frame, text="Recorded Actions:", fg='white', bg='#1a1a1a', font=('Arial', 9, 'bold')).pack(anchor='w')
        
        # Listbox para mostrar ações gravadas
        self.actions_listbox = tk.Listbox(list_frame, bg='#2d2d2d', fg='white', height=6, 
                                        font=('Arial', 8))
        self.actions_listbox.pack(fill='both', expand=True, pady=2)
    
    def setup_gold_tab(self):
        # Gold settings
        gold_frame = tk.LabelFrame(self.gold_tab, text="GOLD COLLECTOR CONFIGURATION", fg='#8b5cf6', bg='#1a1a1a', 
                                 font=('Arial', 10, 'bold'))
        gold_frame.pack(fill='x', pady=5, padx=10)
        
        # Detection mode
        mode_frame = tk.Frame(gold_frame, bg='#1a1a1a')
        mode_frame.pack(fill='x', pady=5)
        
        tk.Label(mode_frame, text="Detection Mode:", fg='white', bg='#1a1a1a', font=('Arial', 9, 'bold')).pack(anchor='w')
        
        self.gold_detection_mode = tk.StringVar(value="dragonball")
        tk.Radiobutton(mode_frame, text="DragonBall Detection", variable=self.gold_detection_mode, value="dragonball", 
                      fg='white', bg='#1a1a1a', selectcolor='#8b5cf6').pack(side='left', padx=5)
        tk.Radiobutton(mode_frame, text="GoldBar Detection", variable=self.gold_detection_mode, value="goldbar", 
                      fg='white', bg='#1a1a1a', selectcolor='#8b5cf6').pack(side='left', padx=5)
        tk.Radiobutton(mode_frame, text="Manual Area", variable=self.gold_detection_mode, value="manual", 
                      fg='white', bg='#1a1a1a', selectcolor='#8b5cf6').pack(side='left', padx=5)
        
        # Auto detection controls
        auto_frame = tk.Frame(gold_frame, bg='#1a1a1a')
        auto_frame.pack(fill='x', pady=5)
        
        self.capture_btn = self.create_button(auto_frame, "CAPTURE ITEM", self.capture_item, 0, 0)
        self.detect_btn = self.create_button(auto_frame, "START DETECTION", self.toggle_item_detection, 0, 1)
        self.track_btn = self.create_button(auto_frame, "TRACK POSITIONS", self.toggle_position_tracking, 0, 2)
        
        # Detection settings
        detect_frame = tk.Frame(gold_frame, bg='#1a1a1a')
        detect_frame.pack(fill='x', pady=5)
        
        tk.Label(detect_frame, text="Detection Threshold:", fg='white', bg='#1a1a1a').pack(side='left')
        self.gold_threshold = tk.StringVar(value="0.8")
        tk.Entry(detect_frame, textvariable=self.gold_threshold, width=8, bg='#2d2d2d', fg='white').pack(side='left', padx=5)
        
        tk.Label(detect_frame, text="Detection Delay (ms):", fg='white', bg='#1a1a1a').pack(side='left', padx=(10, 0))
        self.gold_detection_delay = tk.StringVar(value="500")
        tk.Entry(detect_frame, textvariable=self.gold_detection_delay, width=8, bg='#2d2d2d', fg='white').pack(side='left', padx=5)
        
        # Manual area selection
        area_frame = tk.Frame(gold_frame, bg='#1a1a1a')
        area_frame.pack(fill='x', pady=5)
        
        tk.Label(area_frame, text="Manual Click Area:", fg='white', bg='#1a1a1a', font=('Arial', 9, 'bold')).pack(anchor='w')
        
        coords_frame = tk.Frame(area_frame, bg='#1a1a1a')
        coords_frame.pack(fill='x', pady=2)
        
        tk.Label(coords_frame, text="X1:", fg='white', bg='#1a1a1a').pack(side='left')
        self.gold_x1 = tk.StringVar(value="100")
        tk.Entry(coords_frame, textvariable=self.gold_x1, width=6, bg='#2d2d2d', fg='white').pack(side='left', padx=2)
        
        tk.Label(coords_frame, text="Y1:", fg='white', bg='#1a1a1a').pack(side='left', padx=(5, 0))
        self.gold_y1 = tk.StringVar(value="100")
        tk.Entry(coords_frame, textvariable=self.gold_y1, width=6, bg='#2d2d2d', fg='white').pack(side='left', padx=2)
        
        tk.Label(coords_frame, text="X2:", fg='white', bg='#1a1a1a').pack(side='left', padx=(5, 0))
        self.gold_x2 = tk.StringVar(value="800")
        tk.Entry(coords_frame, textvariable=self.gold_x2, width=6, bg='#2d2d2d', fg='white').pack(side='left', padx=2)
        
        tk.Label(coords_frame, text="Y2:", fg='white', bg='#1a1a1a').pack(side='left', padx=(5, 0))
        self.gold_y2 = tk.StringVar(value="600")
        tk.Entry(coords_frame, textvariable=self.gold_y2, width=6, bg='#2d2d2d', fg='white').pack(side='left', padx=2)
        
        # Gold settings
        settings_frame = tk.Frame(gold_frame, bg='#1a1a1a')
        settings_frame.pack(fill='x', pady=5)
        
        tk.Label(settings_frame, text="Click Delay (ms):", fg='white', bg='#1a1a1a').pack(side='left')
        self.gold_delay = tk.StringVar(value="100")
        tk.Entry(settings_frame, textvariable=self.gold_delay, width=8, bg='#2d2d2d', fg='white').pack(side='left', padx=5)
        
        tk.Label(settings_frame, text="Random Area:", fg='white', bg='#1a1a1a').pack(side='left', padx=(10, 0))
        self.gold_random = tk.BooleanVar(value=True)
        tk.Checkbutton(settings_frame, variable=self.gold_random, fg='white', bg='#1a1a1a', 
                      selectcolor='#8b5cf6').pack(side='left')
        
        # Gold status
        status_frame = tk.Frame(gold_frame, bg='#1a1a1a')
        status_frame.pack(fill='x', pady=5)
        
        self.gold_status = tk.Label(status_frame, text="Gold Detection: Inactive", fg='#888888', bg='#1a1a1a', 
                                   font=('Arial', 8))
        self.gold_status.pack(anchor='w')
    
    def setup_macro_tab(self):
        # Macro settings
        macro_frame = tk.LabelFrame(self.macro_tab, text="MACRO CONFIGURATION", fg='#8b5cf6', bg='#1a1a1a', 
                                  font=('Arial', 10, 'bold'))
        macro_frame.pack(fill='x', pady=5, padx=10)
        
        # Macro sequence
        sequence_frame = tk.Frame(macro_frame, bg='#1a1a1a')
        sequence_frame.pack(fill='x', pady=5)
        
        tk.Label(sequence_frame, text="Macro Sequence:", fg='white', bg='#1a1a1a', font=('Arial', 9, 'bold')).pack(anchor='w')
        
        self.macro_sequence = []
        for i in range(8):
            var = tk.StringVar(value=f"F{i+1}" if i < 5 else "")
            self.macro_sequence.append(var)
            tk.Entry(sequence_frame, textvariable=var, width=8, bg='#2d2d2d', fg='white').pack(side='left', padx=2, pady=2)
        
        # Macro delays
        delay_frame = tk.Frame(macro_frame, bg='#1a1a1a')
        delay_frame.pack(fill='x', pady=5)
        
        tk.Label(delay_frame, text="Key Delay (ms):", fg='white', bg='#1a1a1a').pack(side='left')
        self.macro_key_delay = tk.StringVar(value="500")
        tk.Entry(delay_frame, textvariable=self.macro_key_delay, width=8, bg='#2d2d2d', fg='white').pack(side='left', padx=5)
        
        tk.Label(delay_frame, text="Loop Delay (ms):", fg='white', bg='#1a1a1a').pack(side='left', padx=(10, 0))
        self.macro_loop_delay = tk.StringVar(value="100")
        tk.Entry(delay_frame, textvariable=self.macro_loop_delay, width=8, bg='#2d2d2d', fg='white').pack(side='left', padx=5)
        
        # Macro options
        options_frame = tk.Frame(macro_frame, bg='#1a1a1a')
        options_frame.pack(fill='x', pady=5)
        
        self.macro_loop = tk.BooleanVar(value=True)
        tk.Checkbutton(options_frame, text="Loop Macro", variable=self.macro_loop, fg='white', bg='#1a1a1a', 
                      selectcolor='#8b5cf6').pack(side='left')
        
        self.macro_random = tk.BooleanVar(value=False)
        tk.Checkbutton(options_frame, text="Random Order", variable=self.macro_random, fg='white', bg='#1a1a1a', 
                      selectcolor='#8b5cf6').pack(side='left', padx=(10, 0))
    
    def setup_settings_tab(self):
        # General settings (tema dark compacto)
        general_frame = tk.LabelFrame(self.settings_tab, text="SETTINGS", fg='#8b5cf6', bg='#0e0e10', 
                                    font=('Arial', 7, 'bold'))
        general_frame.pack(fill='x', pady=1, padx=3)
        
        # Delays
        delay_frame = tk.Frame(general_frame, bg='#0e0e10')
        delay_frame.pack(fill='x', pady=1)
        
        tk.Label(delay_frame, text="Left (ms):", fg='white', bg='#0e0e10', font=('Arial', 6)).pack(side='left')
        self.left_delay = tk.StringVar(value="100")
        tk.Entry(delay_frame, textvariable=self.left_delay, width=4, bg='#2d2d2d', fg='white').pack(side='left', padx=2)
        
        tk.Label(delay_frame, text="Right (ms):", fg='white', bg='#0e0e10', font=('Arial', 6)).pack(side='left', padx=(4, 0))
        self.right_delay = tk.StringVar(value="100")
        tk.Entry(delay_frame, textvariable=self.right_delay, width=4, bg='#2d2d2d', fg='white').pack(side='left', padx=2)
        
        tk.Label(delay_frame, text="F Keys (ms):", fg='white', bg='#0e0e10', font=('Arial', 6)).pack(side='left', padx=(4, 0))
        self.f_delay = tk.StringVar(value="100")
        tk.Entry(delay_frame, textvariable=self.f_delay, width=4, bg='#2d2d2d', fg='white').pack(side='left', padx=2)
        
        # Advanced settings
        advanced_frame = tk.LabelFrame(self.settings_tab, text="ADVANCED", fg='#8b5cf6', bg='#0e0e10', 
                                     font=('Arial', 7, 'bold'))
        advanced_frame.pack(fill='x', pady=1, padx=3)
        
        # Failsafe
        failsafe_frame = tk.Frame(advanced_frame, bg='#0e0e10')
        failsafe_frame.pack(fill='x', pady=1)
        
        self.failsafe = tk.BooleanVar(value=False)
        tk.Checkbutton(failsafe_frame, text="Enable Failsafe (move mouse to corner)", 
                      variable=self.failsafe, fg='white', bg='#0e0e10', selectcolor='#8b5cf6').pack(anchor='w')
        
        # Save/Load controls
        actions_frame = tk.Frame(self.settings_tab, bg='#0e0e10')
        actions_frame.pack(fill='x', pady=1, padx=3)
        
        self.auto_save = tk.BooleanVar(value=True)
        tk.Checkbutton(actions_frame, text="Auto-save", 
                      variable=self.auto_save, fg='white', bg='#0e0e10', selectcolor='#8b5cf6').pack(side='left')
        
        tk.Button(actions_frame, text="Save", command=self.save_settings, bg='#2d2d2d', fg='white', font=('Arial', 6, 'bold'), bd=1).pack(side='left', padx=2)
        tk.Button(actions_frame, text="Load", command=self.load_settings, bg='#2d2d2d', fg='white', font=('Arial', 6, 'bold'), bd=1).pack(side='left', padx=2)

    # ===== Settings persistence =====
    def settings_file_path(self):
        return os.path.join(os.getcwd(), 'settings.json')

    def collect_settings(self):
        return {
            'left_delay': self.left_delay.get(),
            'right_delay': self.right_delay.get(),
            'f_delay': self.f_delay.get(),
            'failsafe': bool(self.failsafe.get()),
            'auto_save': bool(self.auto_save.get()),
            'auto_hunt': bool(self.auto_hunt.get()),
            'hunt_radius': self.hunt_radius.get(),
            'hunt_speed_ms': self.hunt_speed_ms.get(),
            'ui_alpha': self.ui_alpha.get(),
        }

    def apply_settings(self, data):
        if not isinstance(data, dict):
            return
        if 'left_delay' in data:
            self.left_delay.set(str(data['left_delay']))
        if 'right_delay' in data:
            self.right_delay.set(str(data['right_delay']))
        if 'f_delay' in data:
            self.f_delay.set(str(data['f_delay']))
        if 'failsafe' in data:
            self.failsafe.set(bool(data['failsafe']))
            pyautogui.FAILSAFE = bool(data['failsafe'])
        if 'auto_save' in data:
            self.auto_save.set(bool(data['auto_save']))
        if 'auto_hunt' in data:
            self.auto_hunt.set(bool(data['auto_hunt']))
        if 'hunt_radius' in data:
            self.hunt_radius.set(str(data['hunt_radius']))
        if 'hunt_speed_ms' in data:
            self.hunt_speed_ms.set(str(data['hunt_speed_ms']))
        if 'ui_alpha' in data:
            self.ui_alpha.set(str(data['ui_alpha']))
            try:
                self.root.attributes('-alpha', max(0.5, min(1.0, float(self.ui_alpha.get())/100.0)))
            except Exception:
                pass

    def save_settings(self):
        try:
            data = self.collect_settings()
            with open(self.settings_file_path(), 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"Erro ao salvar configurações: {e}")
            return False

    def load_settings(self):
        try:
            path = self.settings_file_path()
            if os.path.exists(path):
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self.apply_settings(data)
            else:
                # Salva defaults na primeira execução
                self.save_settings()
        except Exception as e:
            print(f"Erro ao carregar configurações: {e}")

    def attach_settings_traces(self):
        def on_change(*_):
            try:
                pyautogui.FAILSAFE = bool(self.failsafe.get())
                if bool(self.auto_save.get()):
                    self.save_settings()
            except Exception as e:
                print(f"Erro ao aplicar alterações: {e}")
        for var in (self.left_delay, self.right_delay, self.f_delay, self.failsafe, self.auto_save, self.hunt_radius, self.hunt_speed_ms, self.ui_alpha):
            try:
                var.trace_add('write', lambda *_: on_change())
            except Exception:
                # Fallback para versões antigas de tkinter
                var.trace('w', lambda *_: on_change())
        # extra: update alpha in real-time
        try:
            self.ui_alpha.trace_add('write', lambda *_: self._apply_alpha())
        except Exception:
            self.ui_alpha.trace('w', lambda *_: self._apply_alpha())
        # auto_hunt check toggles behavior
        try:
            self.auto_hunt.trace_add('write', lambda *_: self.toggle_auto_hunt())
        except Exception:
            self.auto_hunt.trace('w', lambda *_: self.toggle_auto_hunt())

    def _apply_alpha(self):
        try:
            val = max(50, min(100, int(self.ui_alpha.get())))
            alpha = val/100.0
            self.root.attributes('-alpha', alpha)
            try:
                if hasattr(self, 'settings_win') and self.settings_win and tk.Toplevel.winfo_exists(self.settings_win):
                    self.settings_win.attributes('-alpha', alpha)
            except Exception:
                pass
            if bool(self.auto_save.get()):
                self.save_settings()
        except Exception:
            pass
    
    def _close_settings(self):
        try:
            if hasattr(self, 'settings_win') and self.settings_win:
                self.settings_win.destroy()
        except Exception:
            pass
        finally:
            self.settings_win = None
    
    def _sleep_responsive(self, timer_key: str, total_ms: int):
        """Sleep in small steps while checking flags so stop is instant."""
        end_time = time.time() + max(0, total_ms) / 100.0
        step = 0.01  # 10ms steps
        while time.time() < end_time:
            if not self.timers.get(timer_key, False) or self.paused:
                break
            remaining = end_time - time.time()
            time.sleep(step if remaining > step else max(0, remaining))
    
    def create_button(self, parent, text, command, row, col):
        btn = tk.Button(parent, text=text, command=command, 
                       bg='#2d2d2d', fg='white', font=('Arial', 6, 'bold'),
                       relief='raised', bd=1, width=4)
        btn.grid(row=row, column=col, padx=1, pady=1, sticky='ew')
        parent.grid_columnconfigure(col, weight=1)
        return btn
    
    def setup_hotkeys_legacy(self):
        # Legacy stub to avoid overriding HUD hotkeys
        return
    
    def update_status(self, text):
        self.status.config(text=text)
    
    def refresh_status(self):
        # Atualiza o status global com base nos timers e no estado pausado
        if self.paused:
            self.status.config(text="Status: PAUSED")
            return
        active = []
        for key, val in self.timers.items():
            if val:
                active.append(key.upper())
        if active:
            # Mostra até 3 itens ativos para manter curto
            display = ", ".join(active[:3]) + ("..." if len(active) > 3 else "")
            self.status.config(text=f"Status: ACTIVE ({display})")
        else:
            self.status.config(text="Status: IDLE")

    def toggle_pause_resume(self):
        self.paused = not self.paused
        if self.paused:
            self.update_status("Status: PAUSED")
        else:
            self.update_status("Status: RESUMED")

    # Drag helpers (para HUD sem barra de título)
    def _start_move(self, event):
        try:
            self._drag_x = event.x
            self._drag_y = event.y
        except Exception:
            self._drag_x = self._drag_y = 0

    def _on_move(self, event):
        try:
            x = event.x_root - getattr(self, '_drag_x', 0)
            y = event.y_root - getattr(self, '_drag_y', 0)
            self.root.geometry(f"+{x}+{y}")
        except Exception:
            pass
    
    def toggle_ctrl_hold(self):
        self.timers['ctrl_hold'] = not self.timers['ctrl_hold']
        if self.timers['ctrl_hold']:
            self.start_ctrl_hold()
            self.set_active_style(self.ctrl_btn, True, 'Ctrl')
            self.refresh_status()
        else:
            self.stop_ctrl_hold()
            self.set_active_style(self.ctrl_btn, False, 'Ctrl')
            self.refresh_status()
    
    def start_ctrl_hold(self):
        # Press and hold CTRL using keyboard module for reliable modifier behavior
        try:
            keyboard.press('ctrl')
        except Exception:
            try:
                pyautogui.keyDown('ctrl')
            except Exception:
                pass

        def ctrl_hold_loop():
            while self.timers['ctrl_hold']:
                try:
                    if self.paused:
                        # Release while paused
                        try:
                            keyboard.release('ctrl')
                        except Exception:
                            try:
                                pyautogui.keyUp('ctrl')
                            except Exception:
                                pass
                        # small responsive wait
                        time.sleep(0.05)
                    else:
                        # ensure it's pressed if not paused
                        if not keyboard.is_pressed('ctrl'):
                            try:
                                keyboard.press('ctrl')
                            except Exception:
                                try:
                                    pyautogui.keyDown('ctrl')
                                except Exception:
                                    pass
                        time.sleep(0.02)
                except Exception:
                    break
            # On exit ensure release
            try:
                keyboard.release('ctrl')
            except Exception:
                try:
                    pyautogui.keyUp('ctrl')
                except Exception:
                    pass
        self.timer_threads['ctrl_hold'] = threading.Thread(target=ctrl_hold_loop, daemon=True)
        self.timer_threads['ctrl_hold'].start()
    
    def stop_ctrl_hold(self):
        self.timers['ctrl_hold'] = False
        if 'ctrl_hold' in self.timer_threads:
            del self.timer_threads['ctrl_hold']
        # Ensure release via both backends
        try:
            keyboard.release('ctrl')
        except Exception:
            pass
        try:
            pyautogui.keyUp('ctrl')
        except Exception:
            pass
    
    def toggle_left(self):
        self.timers['left'] = not self.timers['left']
        if self.timers['left']:
            self.start_timer('left')
            self.set_active_style(self.left_btn, True, 'Left')
        else:
            self.stop_timer('left')
            self.set_active_style(self.left_btn, False, 'Left')
    
    def toggle_right(self):
        self.timers['right'] = not self.timers['right']
        if self.timers['right']:
            self.start_timer('right')
            self.set_active_style(self.right_btn, True, 'Right')
        else:
            self.stop_timer('right')
            self.set_active_style(self.right_btn, False, 'Right')
    
    def toggle_fkey(self, fkey):
        self.timers[fkey] = not self.timers[fkey]
        if self.timers[fkey]:
            self.start_timer(fkey)
            self.set_active_style(self.fkey_buttons[fkey], True, fkey.upper())
        else:
            self.stop_timer(fkey)
            self.set_active_style(self.fkey_buttons[fkey], False, fkey.upper())
    
    def toggle_hunt(self):
        self.timers['hunt'] = not self.timers['hunt']
        if self.timers['hunt']:
            self.start_hunt()
            self.hunt_btn.config(fg='#8b5cf6', text="HUNT ✓")
        else:
            self.stop_hunt()
            self.hunt_btn.config(fg='white', text="HUNT")
    
    def toggle_gold(self):
        self.timers['gold'] = not self.timers['gold']
        if self.timers['gold']:
            self.start_gold()
            self.gold_btn.config(fg='#8b5cf6', text="GOLD ✓")
        else:
            self.stop_gold()
            self.gold_btn.config(fg='white', text="GOLD")
    
    def start_timer(self, timer_type):
        if timer_type in self.timer_threads:
            return
        
        def timer_loop():
            while self.timers.get(timer_type, False):
                try:
                    if self.paused:
                        time.sleep(0.1)
                        continue
                        
                    if timer_type == 'left':
                        pyautogui.click(button='left')
                        delay = int(self.left_delay.get())
                    elif timer_type == 'right':
                        pyautogui.click(button='right')
                        delay = int(self.right_delay.get())
                    elif timer_type.startswith('f'):
                        # Use skills: press the F-key with a short hold for reliability
                        key_name = timer_type
                        try:
                            keyboard.press(key_name)
                            time.sleep(0.03)
                            keyboard.release(key_name)
                        except Exception:
                            # Fallback
                            pyautogui.press(timer_type.upper())
                        delay = int(self.f_delay.get())
                    
                    self._sleep_responsive(timer_type, delay)
                except:
                    break
        
        self.timer_threads[timer_type] = threading.Thread(target=timer_loop, daemon=True)
        self.timer_threads[timer_type].start()
        self.refresh_status()
    
    def stop_timer(self, timer_type):
        self.timers[timer_type] = False
        if timer_type in self.timer_threads:
            del self.timer_threads[timer_type]
        self.refresh_status()
    
    def start_hunt(self):
        # Legacy stub (removed feature)
        return
    
    def stop_hunt(self):
        # Legacy stub (removed feature)
        return
    
    def start_gold(self):
        self.timers['gold'] = True
        self.update_status("GOLD ACTIVE")
        
        def gold_loop():
            while self.timers['gold']:
                try:
                    if self.paused:
                        time.sleep(0.1)
                        continue
                    
                    # Usar configurações da aba Gold
                    x1 = int(self.gold_x1.get())
                    y1 = int(self.gold_y1.get())
                    x2 = int(self.gold_x2.get())
                    y2 = int(self.gold_y2.get())
                    delay = int(self.gold_delay.get())
                    random_area = self.gold_random.get()
                    
                    if random_area:
                        click_x = random.randint(x1, x2)
                        click_y = random.randint(y1, y2)
                    else:
                        click_x = (x1 + x2) // 2
                        click_y = (y1 + y2) // 2
                    
                    pyautogui.click(click_x, click_y)
                    time.sleep(delay / 100.0)
                except:
                    break
        
        self.timer_threads['gold'] = threading.Thread(target=gold_loop, daemon=True)
        self.timer_threads['gold'].start()
    
    def stop_gold(self):
        self.timers['gold'] = False
        if 'gold' in self.timer_threads:
            del self.timer_threads['gold']
        self.gold_detection_active = False
        self.gold_status.config(text="Gold Detection: Inactive", fg='#888888')
        self.refresh_status()
    
    # Funções para gravação de movimentos
    def toggle_recording(self):
        if not self.recording:
            self.start_recording()
        else:
            self.stop_recording()
    
    def start_recording(self):
        self.recording = True
        self.recorded_actions = []
        self.record_btn.config(fg='#8b5cf6', text="STOP REC")
        self.recording_info.config(text="Recording... Click, move mouse, and press keys", fg='#ff6b6b')
        
        # Limpar listbox
        self.actions_listbox.delete(0, tk.END)
        
        # Configurar listeners de teclado
        self.setup_recording_hotkeys()
        
        def record_loop():
            last_time = time.time()
            last_click_time = 0
            
            while self.recording:
                try:
                    current_time = time.time()
                    x, y = pyautogui.position()
                    
                    # Detectar cliques com debounce
                    if pyautogui.mouseDown(button='left') and current_time - last_click_time > 0.2:
                        action = {
                            'type': 'left_click',
                            'x': x, 'y': y,
                            'time': current_time - last_time
                        }
                        self.recorded_actions.append(action)
                        self.actions_listbox.insert(tk.END, f"Left Click at ({x}, {y})")
                        self.actions_listbox.see(tk.END)
                        last_time = current_time
                        last_click_time = current_time
                        time.sleep(0.1)
                    
                    elif pyautogui.mouseDown(button='right') and current_time - last_click_time > 0.2:
                        action = {
                            'type': 'right_click',
                            'x': x, 'y': y,
                            'time': current_time - last_time
                        }
                        self.recorded_actions.append(action)
                        self.actions_listbox.insert(tk.END, f"Right Click at ({x}, {y})")
                        self.actions_listbox.see(tk.END)
                        last_time = current_time
                        last_click_time = current_time
                        time.sleep(0.1)
                    
                    time.sleep(0.01)
                except Exception as e:
                    print(f"Erro na gravação: {e}")
                    break
        
        self.recording_thread = threading.Thread(target=record_loop, daemon=True)
        self.recording_thread.start()
    
    def setup_recording_hotkeys(self):
        # Hotkeys para gravação de teclas - usando shift para evitar conflitos
        try:
            keyboard.add_hotkey('shift+f1', lambda: self.record_key('F1'))
            keyboard.add_hotkey('shift+f2', lambda: self.record_key('F2'))
            keyboard.add_hotkey('shift+f3', lambda: self.record_key('F3'))
            keyboard.add_hotkey('shift+f4', lambda: self.record_key('F4'))
            keyboard.add_hotkey('shift+f5', lambda: self.record_key('F5'))
            keyboard.add_hotkey('shift+f6', lambda: self.record_key('F6'))
            keyboard.add_hotkey('shift+f7', lambda: self.record_key('F7'))
            keyboard.add_hotkey('shift+f8', lambda: self.record_key('F8'))
            keyboard.add_hotkey('shift+f9', lambda: self.record_key('F9'))
            keyboard.add_hotkey('shift+f10', lambda: self.record_key('F10'))
            keyboard.add_hotkey('space', lambda: self.record_key('SPACE'))
            keyboard.add_hotkey('enter', lambda: self.record_key('ENTER'))
            keyboard.add_hotkey('tab', lambda: self.record_key('TAB'))
            keyboard.add_hotkey('shift', lambda: self.record_key('SHIFT'))
            keyboard.add_hotkey('ctrl', lambda: self.record_key('CTRL'))
            keyboard.add_hotkey('alt', lambda: self.record_key('ALT'))
        except:
            pass
    
    def record_key(self, key):
        if self.recording:
            action = {
                'type': 'key_press',
                'key': key,
                'time': 0  # Será calculado no play
            }
            self.recorded_actions.append(action)
            self.actions_listbox.insert(tk.END, f"Key Press: {key}")
    
    def stop_recording(self):
        self.recording = False
        self.record_btn.config(fg='white', text="RECORD")
        
        # Remover hotkeys de gravação
        try:
            keyboard.unhook_all()
            self.setup_hotkeys()  # Reconfigurar hotkeys principais
        except:
            pass
        
        if len(self.recorded_actions) > 0:
            self.recording_info.config(text=f"Recorded {len(self.recorded_actions)} actions", fg='#00ff00')
        else:
            self.recording_info.config(text="No actions recorded", fg='#ff6b6b')
    
    def play_recording(self):
        if not self.recorded_actions:
            messagebox.showwarning("Warning", "No recording to play!")
            return
        
        def play_loop():
            self.recording_info.config(text="Playing recording...", fg='#8b5cf6')
            
            for i, action in enumerate(self.recorded_actions):
                if not self.recording:  # Se não estiver gravando, pode parar
                    break
                
                # Usar delay real da gravação ou delay padrão
                if 'time' in action and action['time'] > 0:
                    delay = action['time']
                else:
                    delay = 0.5  # Delay padrão
                
                if delay > 0:
                    time.sleep(delay)
                
                try:
                    if action['type'] == 'left_click':
                        pyautogui.click(action['x'], action['y'], button='left')
                    elif action['type'] == 'right_click':
                        pyautogui.click(action['x'], action['y'], button='right')
                    elif action['type'] == 'key_press':
                        pyautogui.press(action['key'])
                except Exception as e:
                    print(f"Erro ao executar ação: {e}")
            
            self.recording_info.config(text=f"Playback completed - {len(self.recorded_actions)} actions", fg='#00ff00')
        
        threading.Thread(target=play_loop, daemon=True).start()
    
    def save_recording(self):
        if not self.recorded_actions:
            messagebox.showwarning("Warning", "No recording to save!")
            return
        
        filename = f"recording_{int(time.time())}.json"
        with open(filename, 'w') as f:
            json.dump(self.recorded_actions, f)
        messagebox.showinfo("Success", f"Recording saved as {filename}")
    
    def load_recording(self):
        filename = tk.filedialog.askopenfilename(
            title="Load Recording",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if filename:
            try:
                with open(filename, 'r') as f:
                    self.recorded_actions = json.load(f)
                self.actions_listbox.delete(0, tk.END)
                for action in self.recorded_actions:
                    self.actions_listbox.insert(tk.END, f"{action['type']} at ({action['x']}, {action['y']})")
                self.recording_info.config(text=f"Loaded {len(self.recorded_actions)} actions", fg='#00ff00')
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load recording: {e}")
    
    def clear_recording(self):
        self.recorded_actions = []
        self.actions_listbox.delete(0, tk.END)
        self.recording_info.config(text="No recording", fg='#888888')
    
    # Funções para detecção de GoldBars
    def capture_goldbar(self):
        messagebox.showinfo("Capture GoldBar", "Position your mouse over a GoldBar and press Enter")
        
        def capture_loop():
            time.sleep(2)  # Dar tempo para posicionar
            x, y = pyautogui.position()
            
            # Capturar área ao redor do mouse
            screenshot = pyautogui.screenshot(region=(x-25, y-25, 50, 50))
            self.gold_template = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
            
            # Salvar template
            cv2.imwrite('goldbar_template.png', self.gold_template)
            messagebox.showinfo("Success", "GoldBar template captured!")
        
        threading.Thread(target=capture_loop, daemon=True).start()
    
    def toggle_gold_detection(self):
        if not self.gold_detection_active:
            self.start_gold_detection()
        else:
            self.stop_gold_detection()
    
    def start_gold_detection(self):
        if self.gold_template is None:
            messagebox.showwarning("Warning", "Please capture a GoldBar template first!")
            return
        
        self.gold_detection_active = True
        self.detect_btn.config(fg='#8b5cf6', text="STOP DETECTION")
        self.gold_status.config(text="Gold Detection: Active", fg='#00ff00')
        
        def detection_loop():
            while self.gold_detection_active and not self.paused:
                try:
                    # Capturar screenshot da tela
                    screenshot = pyautogui.screenshot()
                    screen = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
                    
                    # Procurar GoldBars
                    result = cv2.matchTemplate(screen, self.gold_template, cv2.TM_CCOEFF_NORMED)
                    threshold = float(self.gold_threshold.get())
                    locations = np.where(result >= threshold)
                    
                    if len(locations[0]) > 0:
                        # Pegar o primeiro GoldBar encontrado
                        y, x = locations[0][0], locations[1][0]
                        pyautogui.click(x + 25, y + 25)  # Centro do template
                        
                        delay = int(self.gold_detection_delay.get())
                        time.sleep(delay / 100.0)
                    else:
                        time.sleep(0.1)
                        
                except Exception as e:
                    print(f"Erro na detecção: {e}")
                    break
        
        self.timer_threads['gold_detection'] = threading.Thread(target=detection_loop, daemon=True)
        self.timer_threads['gold_detection'].start()
    
    def stop_gold_detection(self):
        self.gold_detection_active = False
        self.detect_btn.config(fg='white', text="START DETECTION")
        self.gold_status.config(text="Gold Detection: Inactive", fg='#888888')
        if 'gold_detection' in self.timer_threads:
            del self.timer_threads['gold_detection']
    
    # Funções para detecção de DragonBalls
    def capture_item(self):
        mode = self.gold_detection_mode.get()
        if mode == "dragonball":
            self.capture_dragonball()
        else:
            self.capture_goldbar()
    
    def capture_dragonball(self):
        messagebox.showinfo("Capture DragonBall", "Position your mouse over a DragonBall and press Enter")
        
        def capture_loop():
            time.sleep(2)  # Dar tempo para posicionar
            x, y = pyautogui.position()
            
            # Capturar área ao redor do mouse
            screenshot = pyautogui.screenshot(region=(x-30, y-30, 60, 60))
            template = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
            
            # Salvar template
            cv2.imwrite('dragonball_template.png', template)
            self.dragonball_templates['dragonball'] = template
            messagebox.showinfo("Success", "DragonBall template captured!")
        
        threading.Thread(target=capture_loop, daemon=True).start()
    
    def toggle_item_detection(self):
        if not self.gold_detection_active:
            self.start_item_detection()
        else:
            self.stop_item_detection()
    
    def start_item_detection(self):
        mode = self.gold_detection_mode.get()
        
        if mode == "dragonball" and 'dragonball' not in self.dragonball_templates:
            messagebox.showwarning("Warning", "Please capture a DragonBall template first!")
            return
        elif mode == "goldbar" and self.gold_template is None:
            messagebox.showwarning("Warning", "Please capture a GoldBar template first!")
            return
        
        self.gold_detection_active = True
        self.detect_btn.config(fg='#8b5cf6', text="STOP DETECTION")
        self.gold_status.config(text=f"{mode.title()} Detection: Active", fg='#00ff00')
        
        def detection_loop():
            while self.gold_detection_active and not self.paused:
                try:
                    # Capturar screenshot da tela
                    screenshot = pyautogui.screenshot()
                    screen = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
                    
                    if mode == "dragonball":
                        self.detect_dragonballs(screen)
                    elif mode == "goldbar":
                        self.detect_goldbars(screen)
                    elif mode == "manual":
                        self.manual_click()
                    
                    delay = int(self.gold_detection_delay.get())
                    time.sleep(delay / 100.0)
                        
                except Exception as e:
                    print(f"Erro na detecção: {e}")
                    break
        
        self.timer_threads['item_detection'] = threading.Thread(target=detection_loop, daemon=True)
        self.timer_threads['item_detection'].start()
    
    def detect_dragonballs(self, screen):
        template = self.dragonball_templates.get('dragonball')
        if template is None:
            return
        
        # Procurar DragonBalls
        result = cv2.matchTemplate(screen, template, cv2.TM_CCOEFF_NORMED)
        threshold = float(self.gold_threshold.get())
        locations = np.where(result >= threshold)
        
        if len(locations[0]) > 0:
            # Pegar o primeiro DragonBall encontrado
            y, x = locations[0][0], locations[1][0]
            click_x = x + 30  # Centro do template
            click_y = y + 30
            
            # Verificar se já clicou nesta posição recentemente
            if not self.is_recent_position(click_x, click_y):
                pyautogui.click(click_x, click_y)
                self.add_position(click_x, click_y)
    
    def detect_goldbars(self, screen):
        if self.gold_template is None:
            return
        
        # Procurar GoldBars
        result = cv2.matchTemplate(screen, self.gold_template, cv2.TM_CCOEFF_NORMED)
        threshold = float(self.gold_threshold.get())
        locations = np.where(result >= threshold)
        
        if len(locations[0]) > 0:
            # Pegar o primeiro GoldBar encontrado
            y, x = locations[0][0], locations[1][0]
            click_x = x + 25  # Centro do template
            click_y = y + 25
            
            # Verificar se já clicou nesta posição recentemente
            if not self.is_recent_position(click_x, click_y):
                pyautogui.click(click_x, click_y)
                self.add_position(click_x, click_y)
    
    def manual_click(self):
        x1 = int(self.gold_x1.get())
        y1 = int(self.gold_y1.get())
        x2 = int(self.gold_x2.get())
        y2 = int(self.gold_y2.get())
        random_area = self.gold_random.get()
        
        if random_area:
            click_x = random.randint(x1, x2)
            click_y = random.randint(y1, y2)
        else:
            click_x = (x1 + x2) // 2
            click_y = (y1 + y2) // 2
        
        pyautogui.click(click_x, click_y)
    
    def is_recent_position(self, x, y):
        # Verificar se clicou nesta posição nos últimos 2 segundos
        current_time = time.time()
        for pos in self.item_positions:
            if (abs(pos['x'] - x) < 50 and abs(pos['y'] - y) < 50 and 
                current_time - pos['time'] < 2.0):
                return True
        return False
    
    def add_position(self, x, y):
        # Adicionar posição clicada
        self.item_positions.append({
            'x': x, 'y': y, 'time': time.time()
        })
        
        # Limpar posições antigas (mais de 5 segundos)
        current_time = time.time()
        self.item_positions = [pos for pos in self.item_positions 
                              if current_time - pos['time'] < 5.0]
    
    def toggle_position_tracking(self):
        # Legacy stub (removed feature)
        return
    
    def stop_item_detection(self):
        # Legacy stub (removed feature)
        return
    
    def stop_all(self):
        # Desativa todos os timers e recursos
        for timer_type in list(self.timers.keys()):
            self.timers[timer_type] = False

        # Para recursos específicos com limpeza adequada
        try:
            self.stop_ctrl_hold()
        except:
            pass
        try:
            self.stop_auto_hunt()
        except:
            pass

        # Limpa referências de threads
        self.timer_threads.clear()

        # Reset HUD labels
        try:
            self.set_active_style(self.left_btn, False, 'Left')
            self.set_active_style(self.right_btn, False, 'Right')
            self.set_active_style(self.ctrl_btn, False, 'Ctrl')
        except Exception:
            pass
        for i in range(1, 11):
            try:
                self.set_active_style(self.fkey_buttons[f'f{i}'], False, f"F{i}")
            except Exception:
                pass
        
        self.refresh_status()
        # Fecha o aplicativo após garantir que tudo foi parado
        try:
            self.root.after(50, self.root.destroy)
        except:
            pass
    
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = ConquerClicker()
    app.run()
