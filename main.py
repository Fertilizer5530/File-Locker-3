from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.label import Label
from kivy.uix.filechooser import FileChooserListView
from kivy.uix.popup import Popup
from kivy.uix.spinner import Spinner
import os, base64, hashlib
from android.permissions import request_permissions, Permission

HEADER = b"=== LOCKED BY FILE-HIDER ===\n"

def get_key(p):
    return hashlib.sha256(p.encode()).digest()

def lock_file(path, pwd):
    key = get_key(pwd)
    with open(path, "rb") as f: data = f.read()
    if data.startswith(HEADER): raise ValueError("already locked")
    enc = bytes(b ^ key[i % len(key)] for i, b in enumerate(data))
    with open(path, "wb") as f: f.write(HEADER + base64.b64encode(enc))

def unlock_file(path, pwd):
    key = get_key(pwd)
    with open(path, "rb") as f: data = f.read()
    if not data.startswith(HEADER): raise ValueError("not locked")
    enc = base64.b64decode(data[len(HEADER):])
    dec = bytes(b ^ key[i % len(key)] for i, b in enumerate(enc))
    with open(path, "wb") as f: f.write(dec)

def walk_files(folder):
    out = []
    for r, _, fs in os.walk(folder):
        for f in fs: out.append(os.path.join(r, f))
    return out

class FileLockerApp(App):
    def build(self):
        request_permissions([Permission.READ_EXTERNAL_STORAGE, Permission.WRITE_EXTERNAL_STORAGE])
        self.selected_path = ""
        self.is_folder = False
        root = BoxLayout(orientation="vertical", padding=20, spacing=10)

        root.add_widget(Label(text="File Locker", font_size=28, size_hint=(1, 0.15)))
        self.mode = Spinner(text="Single", values=("Single", "Folder"), size_hint=(1, 0.1))
        self.mode.bind(text=self.on_mode_change)
        root.add_widget(self.mode)

        self.path_label = Label(text="No path selected", size_hint=(1, 0.1))
        root.add_widget(self.path_label)
        root.add_widget(Button(text="Select File/Folder", size_hint=(1, 0.1), on_press=self.open_chooser))

        self.pwd = TextInput(hint_text="Password", password=True, multiline=False, size_hint=(1, 0.1))
        root.add_widget(self.pwd)

        self.action = Spinner(text="Lock", values=("Lock", "Unlock"), size_hint=(1, 0.1))
        root.add_widget(self.action)

        root.add_widget(Button(text="Start", size_hint=(1, 0.15), background_color=(0, 0.55, 1, 1), on_press=self.on_start))
        self.status = Label(text="", size_hint=(1, 0.1))
        root.add_widget(self.status)
        return root

    def on_mode_change(self, spinner, text):
        self.is_folder = (text == "Folder")

    def open_chooser(self):
        chooser = FileChooserListView(path="/storage/emulated/0", dirselect=self.is_folder)
        box = BoxLayout(orientation="vertical")
        box.add_widget(chooser)
        btn = Button(text="Select", size_hint=(1, 0.15))
        box.add_widget(btn)
        popup = Popup(title="Choose", content=box, size_hint=(0.9, 0.9))
        def select(_):
            if chooser.selection:
                self.selected_path = chooser.selection[0]
                self.path_label.text = self.selected_path
            popup.dismiss()
        btn.bind(on_press=select)
        popup.open()

    def on_start(self, _):
        pwd = self.pwd.text.strip()
        path = self.selected_path
        if not pwd or not path:
            self.status.text = "❌ Enter password & select path"
            return
        if self.is_folder:
            if not os.path.isdir(path):
                self.status.text = "❌ Not a folder"
                return
            files = walk_files(path)
        else:
            if not os.path.isfile(path):
                self.status.text = "❌ Not a file"
                return
            files = [path]
        ok = err = 0
        for i, fp in enumerate(files, 1):
            try:
                (lock_file if self.action.text == "Lock" else unlock_file)(fp, pwd)
                ok += 1
            except Exception:
                err += 1
            self.status.text = f"Working {i}/{len(files)}"
        self.status.text = f"✅ {ok} ok, ❌ {err} error"

if __name__ == "__main__":
    FileLockerApp().run()
