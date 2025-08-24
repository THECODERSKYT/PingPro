#!/usr/bin/env python3

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib
import requests
import threading
import time
from datetime import datetime

# असुरक्षित HTTPS अनुरोधों के लिए चेतावनी को अक्षम करें (verify=False के लिए)
try:
    from requests.packages.urllib3.exceptions import InsecureRequestWarning
    requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
except ImportError:
    pass

def ping_website(url):
    """बैकग्राउंड थ्रेड में वेबसाइट को पिंग करता है और (status, message) लौटाता है"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    try:
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        response = requests.get(url, headers=headers, timeout=15, verify=False)
        if 200 <= response.status_code < 400:
            return ("ONLINE", f"HTTP {response.status_code}")
        else:
            return ("OFFLINE", f"HTTP {response.status_code}")
    except requests.exceptions.RequestException as e:
        return ("ERROR", "Connection Error or Invalid Host")

class PingerProWindow(Gtk.Window):
    def __init__(self):
        super().__init__(title="PingerPro")
        self.set_default_size(500, 350)
        self.set_border_width(12)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.set_icon_name("network-transmit-receive")

        self.is_pinging = False
        self.ping_thread = None

        # --- UI एलिमेंट्स का निर्माण ---
        
        # मुख्य लेआउट के लिए ग्रिड
        grid = Gtk.Grid()
        grid.set_column_spacing(10)
        grid.set_row_spacing(10)
        self.add(grid)

        # URL इनपुट
        url_label = Gtk.Label(label="Website URL:")
        url_label.set_halign(Gtk.Align.END)
        self.url_entry = Gtk.Entry()
        self.url_entry.set_placeholder_text("example.com")
        self.url_entry.set_hexpand(True)

        # समय अंतराल के लिए नियंत्रण
        interval_label = Gtk.Label(label="Interval:")
        interval_label.set_halign(Gtk.Align.END)
        self.interval_entry = Gtk.Entry()
        self.interval_entry.set_text("30")
        self.interval_entry.set_width_chars(5)
        
        self.unit_combo = Gtk.ComboBoxText()
        self.unit_combo.append_text("Seconds")
        self.unit_combo.append_text("Minutes")
        self.unit_combo.set_active(0)

        interval_box = Gtk.Box(spacing=6)
        interval_box.pack_start(self.interval_entry, True, True, 0)
        interval_box.pack_start(self.unit_combo, False, False, 0)

        # Start/Stop बटन्स
        self.start_button = Gtk.Button(label="Start Pinging")
        self.stop_button = Gtk.Button(label="Stop Pinging")
        self.stop_button.set_sensitive(False)

        button_box = Gtk.Box(spacing=6)
        button_box.set_halign(Gtk.Align.CENTER)
        button_box.pack_start(self.start_button, True, True, 0)
        button_box.pack_start(self.stop_button, True, True, 0)

        # परिणाम दिखाने के लिए स्क्रॉल करने योग्य विंडो और लेबल
        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.set_hexpand(True)
        scrolled_window.set_vexpand(True)
        self.result_label = Gtk.Label(label="Status will be displayed here.")
        self.result_label.set_selectable(True)
        self.result_label.set_line_wrap(True)
        self.result_label.set_justify(Gtk.Justification.CENTER)
        scrolled_window.add(self.result_label)

        # स्टेटस बार और स्पिनर
        self.spinner = Gtk.Spinner()
        self.statusbar = Gtk.Statusbar()
        self.statusbar_context_id = self.statusbar.get_context_id("status")
        self.statusbar.push(self.statusbar_context_id, "Status: Idle")

        # --- ग्रिड में एलिमेंट्स को जोड़ना ---
        grid.attach(url_label, 0, 0, 1, 1)
        grid.attach(self.url_entry, 1, 0, 1, 1)
        grid.attach(interval_label, 0, 1, 1, 1)
        grid.attach(interval_box, 1, 1, 1, 1)
        grid.attach(button_box, 0, 2, 2, 1)
        grid.attach(scrolled_window, 0, 3, 2, 1)
        grid.attach(self.spinner, 0, 4, 1, 1)
        grid.attach(self.statusbar, 1, 4, 1, 1)

        # --- सिग्नल्स को फंक्शन्स से जोड़ना ---
        self.connect("destroy", self.on_destroy)
        self.start_button.connect("clicked", self.on_start_clicked)
        self.stop_button.connect("clicked", self.on_stop_clicked)

    def show_error_dialog(self, primary_text, secondary_text):
        """एक सरल त्रुटि संवाद प्रदर्शित करता है"""
        dialog = Gtk.MessageDialog(
            transient_for=self,
            flags=0,
            message_type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.OK,
            text=primary_text,
        )
        dialog.format_secondary_text(secondary_text)
        dialog.run()
        dialog.destroy()

    def on_start_clicked(self, widget):
        """'Start' बटन दबाने पर इनपुट की जाँच करता है और पिंगिंग शुरू करता है"""
        url = self.url_entry.get_text().strip()
        if not url:
            self.show_error_dialog("Invalid Input", "URL field cannot be empty.")
            return

        try:
            interval_val = int(self.interval_entry.get_text())
            if interval_val < 3:
                self.show_error_dialog("Invalid Input", "Interval must be at least 3 seconds.")
                return
        except ValueError:
            self.show_error_dialog("Invalid Input", "Interval must be a whole number.")
            return

        self.is_pinging = True
        self.toggle_controls(False)
        self.statusbar.push(self.statusbar_context_id, f"Pinging {url}...")
        
        self.ping_thread = threading.Thread(target=self.ping_worker, args=(url, interval_val))
        self.ping_thread.daemon = True
        self.ping_thread.start()

    def on_stop_clicked(self, widget):
        """'Stop' बटन दबाने पर पिंगिंग को रोकता है"""
        if self.is_pinging:
            self.is_pinging = False
            self.toggle_controls(True)
            self.statusbar.push(self.statusbar_context_id, "Status: Stopped by user.")
            self.result_label.set_markup("<i>Pinging stopped.</i>")

    def on_destroy(self, widget):
        """विंडो बंद होने पर एप्लिकेशन को बंद करता है"""
        self.is_pinging = False
        Gtk.main_quit()

    def toggle_controls(self, is_active):
        """पिंगिंग के दौरान नियंत्रणों को अक्षम/सक्षम करता है"""
        self.url_entry.set_sensitive(is_active)
        self.interval_entry.set_sensitive(is_active)
        self.unit_combo.set_sensitive(is_active)
        self.start_button.set_sensitive(is_active)
        self.stop_button.set_sensitive(not is_active)

    def update_ui(self, status, message, url):
        """UI को मुख्य थ्रेड से सुरक्षित रूप से अपडेट करता है"""
        self.spinner.stop()
        now = datetime.now().strftime('%H:%M:%S')
        markup = f"<big><b>Last Check at {now}</b></big>\n"
        if status == "ONLINE":
            markup += f"<span foreground='green'><b>{status}</b></span> - {url}\n<small>{message}</small>"
        else:
            markup += f"<span foreground='red'><b>{status}</b></span> - {url}\n<small>{message}</small>"
        self.result_label.set_markup(markup)
        return False # GLib को बताएं कि इसे दोबारा न चलाएं

    def ping_worker(self, url, interval_val):
        """यह फंक्शन बैकग्राउंड थ्रेड में लगातार चलता है"""
        unit = self.unit_combo.get_active_text()
        interval_seconds = interval_val * 60 if unit == "Minutes" else interval_val
            
        while self.is_pinging:
            GLib.idle_add(self.spinner.start) # मुख्य थ्रेड में स्पिनर शुरू करें
            status, message = ping_website(url)
            if self.is_pinging:
                GLib.idle_add(self.update_ui, status, message, url)
            
            # अंतराल के लिए प्रतीक्षा करें
            for _ in range(interval_seconds):
                if not self.is_pinging:
                    break
                time.sleep(1)
        
        GLib.idle_add(self.spinner.stop)


# --- एप्लिकेशन शुरू करें ---
if __name__ == "__main__":
    win = PingerProWindow()
    win.show_all()
    Gtk.main()
