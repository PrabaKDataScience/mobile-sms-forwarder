"""
main.py
=======
Graphical User Interface for SMS Forwarder (Kivy).
Runs on both Desktop (Windows/macOS/Linux) and Android.
Provides full configuration, SMTP testing, SMS simulation, and real-time activity log.
"""

import sys
import threading
from datetime import datetime

# Check Kivy availability
try:
    import kivy
    from kivy.app import App
    from kivy.clock import Clock
    from kivy.core.window import Window
    from kivy.graphics import Color, RoundedRectangle
    from kivy.metrics import dp
    from kivy.uix.boxlayout import BoxLayout
    from kivy.uix.button import Button
    from kivy.uix.gridlayout import GridLayout
    from kivy.uix.label import Label
    from kivy.uix.popup import Popup
    from kivy.uix.scrollview import ScrollView
    from kivy.uix.switch import Switch
    from kivy.uix.textinput import TextInput
except ImportError:
    print("\n[ERROR] Kivy is not installed.")
    print("To run the desktop GUI, please install kivy:")
    print("    pip install kivy\n")
    print("Alternatively, you can test SMS forwarding right now with the CLI:")
    print("    python test_cli.py\n")
    sys.exit(1)

from android_listener import AndroidSMSListener
from forwarder import SMSForwarder

# Preset SMTP configurations for popular email providers
SMTP_PRESETS = {
    "Gmail": {"server": "smtp.gmail.com", "port": 587, "ssl": False},
    "Outlook": {"server": "smtp-mail.outlook.com", "port": 587, "ssl": False},
    "Yahoo": {"server": "smtp.mail.yahoo.com", "port": 465, "ssl": True},
    "Custom": {"server": "", "port": 587, "ssl": False},
}


class ModernCard(BoxLayout):
    """A card container with subtle background and rounded corners."""
    def __init__(self, bg_color=(0.14, 0.17, 0.22, 1), **kwargs):
        super().__init__(**kwargs)
        self.bg_color = bg_color
        self.padding = dp(12)
        self.spacing = dp(8)
        self.orientation = "vertical"
        with self.canvas.before:
            Color(*self.bg_color)
            self.rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(10)])
        self.bind(pos=self._update_rect, size=self._update_rect)

    def _update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size


class SMSForwarderApp(App):
    """Main application class for Mobile SMS Forwarder."""

    def build(self):
        self.title = "SMS Forwarder"
        Window.clearcolor = (0.09, 0.11, 0.14, 1.0)  # Dark sleek background

        # Core forwarder and listener
        self.forwarder = SMSForwarder()
        self.listener = AndroidSMSListener(on_sms_received_callback=self.on_sms_received)

        # Root layout
        root = BoxLayout(orientation="vertical", padding=dp(12), spacing=dp(10))

        # 1. Header Bar
        header = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(10))
        title_label = Label(
            text="[b]SMS Forwarder[/b]",
            markup=True,
            font_size="20sp",
            color=(1, 1, 1, 1),
            size_hint_x=0.6,
            halign="left",
            valign="middle",
        )
        title_label.bind(size=title_label.setter("text_size"))
        header.add_widget(title_label)

        self.status_badge = Label(
            text="[b]ACTIVE[/b]",
            markup=True,
            font_size="13sp",
            color=(0.2, 0.9, 0.4, 1),
            size_hint_x=0.4,
            halign="right",
            valign="middle",
        )
        self.status_badge.bind(size=self.status_badge.setter("text_size"))
        header.add_widget(self.status_badge)
        root.add_widget(header)

        # 2. Main Scrollable Container for Settings and Simulator
        scroll_view = ScrollView(size_hint=(1, 1), do_scroll_x=False)
        content_box = BoxLayout(orientation="vertical", spacing=dp(12), size_hint_y=None)
        content_box.bind(minimum_height=content_box.setter("height"))

        # --- Card 1: Service Toggle & Quick Presets ---
        service_card = ModernCard(size_hint_y=None)
        service_card.height = dp(115)

        toggle_row = BoxLayout(size_hint_y=None, height=dp(36), spacing=dp(8))
        toggle_label = Label(
            text="Forwarding Service Status:",
            color=(0.9, 0.9, 0.9, 1),
            halign="left",
            valign="middle",
            size_hint_x=0.7,
        )
        toggle_label.bind(size=toggle_label.setter("text_size"))
        self.service_switch = Switch(
            active=self.forwarder.config.get("is_active", True),
            size_hint_x=0.3,
        )
        self.service_switch.bind(active=self.on_toggle_service)
        toggle_row.add_widget(toggle_label)
        toggle_row.add_widget(self.service_switch)
        service_card.add_widget(toggle_row)

        presets_row = BoxLayout(size_hint_y=None, height=dp(36), spacing=dp(6))
        preset_lbl = Label(
            text="Presets:",
            color=(0.7, 0.75, 0.85, 1),
            size_hint_x=0.25,
            font_size="12sp",
        )
        presets_row.add_widget(preset_lbl)
        for preset_name in ["Gmail", "Outlook", "Yahoo", "Custom"]:
            btn = Button(
                text=preset_name,
                font_size="12sp",
                background_color=(0.2, 0.4, 0.7, 1),
                background_normal="",
            )
            btn.bind(on_release=lambda instance, p=preset_name: self.apply_preset(p))
            presets_row.add_widget(btn)
        service_card.add_widget(presets_row)
        content_box.add_widget(service_card)

        # --- Card 2: SMTP Configuration ---
        config_card = ModernCard(size_hint_y=None)
        config_card.height = dp(330)

        config_title = Label(
            text="[b]SMTP Email Settings[/b]",
            markup=True,
            font_size="15sp",
            color=(0.4, 0.75, 1, 1),
            size_hint_y=None,
            height=dp(24),
            halign="left",
        )
        config_title.bind(size=config_title.setter("text_size"))
        config_card.add_widget(config_title)

        grid = GridLayout(cols=2, spacing=dp(6), size_hint_y=None, height=dp(210))

        # Helper to create styled inputs
        def add_field(label_text, value="", is_password=False):
            lbl = Label(
                text=label_text,
                color=(0.8, 0.85, 0.9, 1),
                size_hint_x=0.38,
                font_size="13sp",
                halign="left",
                valign="middle",
            )
            lbl.bind(size=lbl.setter("text_size"))
            ti = TextInput(
                text=str(value),
                multiline=False,
                password=is_password,
                background_color=(0.1, 0.12, 0.16, 1),
                foreground_color=(1, 1, 1, 1),
                font_size="13sp",
                padding=[dp(8), dp(6)],
            )
            grid.add_widget(lbl)
            grid.add_widget(ti)
            return ti

        self.input_smtp_server = add_field("SMTP Server:", self.forwarder.config.get("smtp_server", "smtp.gmail.com"))
        self.input_smtp_port = add_field("SMTP Port:", str(self.forwarder.config.get("smtp_port", 587)))
        self.input_sender_email = add_field("Sender Email:", self.forwarder.config.get("sender_email", ""))
        self.input_sender_pass = add_field("App Password:", self.forwarder.config.get("sender_password", ""), is_password=True)
        self.input_recipients = add_field("Forward To:", ", ".join(self.forwarder.get_recipients_list()))
        self.input_prefix = add_field("Subject Prefix:", self.forwarder.config.get("subject_prefix", "[SMS Forwarded]"))

        config_card.add_widget(grid)

        # Action buttons for config
        cfg_btns = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(10))
        self.btn_save = Button(
            text="Save Settings",
            background_color=(0.18, 0.65, 0.35, 1),
            background_normal="",
            font_size="13sp",
        )
        self.btn_save.bind(on_release=self.on_save_settings)
        cfg_btns.add_widget(self.btn_save)

        self.btn_test = Button(
            text="Send Test Email",
            background_color=(0.25, 0.5, 0.85, 1),
            background_normal="",
            font_size="13sp",
        )
        self.btn_test.bind(on_release=self.on_send_test_email)
        cfg_btns.add_widget(self.btn_test)
        config_card.add_widget(cfg_btns)
        content_box.add_widget(config_card)

        # --- Card 3: SMS Simulator (Quick Desktop Testing) ---
        sim_card = ModernCard(size_hint_y=None)
        sim_card.height = dp(175)

        sim_title = Label(
            text="[b]SMS Test Simulator (Desktop / Verification)[/b]",
            markup=True,
            font_size="15sp",
            color=(0.95, 0.75, 0.25, 1),
            size_hint_y=None,
            height=dp(24),
            halign="left",
        )
        sim_title.bind(size=sim_title.setter("text_size"))
        sim_card.add_widget(sim_title)

        sim_grid = GridLayout(cols=2, spacing=dp(6), size_hint_y=None, height=dp(80))
        sim_lbl1 = Label(text="Sender Phone:", color=(0.8, 0.85, 0.9, 1), size_hint_x=0.35, font_size="13sp")
        self.input_sim_sender = TextInput(
            text="+1987654321",
            multiline=False,
            background_color=(0.1, 0.12, 0.16, 1),
            foreground_color=(1, 1, 1, 1),
            font_size="13sp",
        )
        sim_grid.add_widget(sim_lbl1)
        sim_grid.add_widget(self.input_sim_sender)

        sim_lbl2 = Label(text="SMS Content:", color=(0.8, 0.85, 0.9, 1), size_hint_x=0.35, font_size="13sp")
        self.input_sim_body = TextInput(
            text="Verification code is 849201. Do not share this code.",
            multiline=False,
            background_color=(0.1, 0.12, 0.16, 1),
            foreground_color=(1, 1, 1, 1),
            font_size="13sp",
        )
        sim_grid.add_widget(sim_lbl2)
        sim_grid.add_widget(self.input_sim_body)
        sim_card.add_widget(sim_grid)

        self.btn_sim_send = Button(
            text="Simulate & Forward SMS",
            background_color=(0.7, 0.35, 0.8, 1),
            background_normal="",
            size_hint_y=None,
            height=dp(36),
            font_size="13sp",
        )
        self.btn_sim_send.bind(on_release=self.on_simulate_sms)
        sim_card.add_widget(self.btn_sim_send)
        content_box.add_widget(sim_card)

        # --- Card 4: Activity Log ---
        log_card = ModernCard(size_hint_y=None)
        log_card.height = dp(200)

        log_header = BoxLayout(size_hint_y=None, height=dp(26))
        log_title = Label(
            text="[b]Forwarding Activity Log[/b]",
            markup=True,
            font_size="14sp",
            color=(0.8, 0.85, 0.9, 1),
            halign="left",
        )
        log_title.bind(size=log_title.setter("text_size"))
        log_header.add_widget(log_title)

        btn_clear = Button(
            text="Clear",
            size_hint_x=None,
            width=dp(60),
            background_color=(0.3, 0.35, 0.4, 1),
            background_normal="",
            font_size="11sp",
        )
        btn_clear.bind(on_release=self.clear_log)
        log_header.add_widget(btn_clear)
        log_card.add_widget(log_header)

        self.log_scroll = ScrollView(size_hint=(1, 1))
        self.log_label = Label(
            text="[color=888888]Ready. Waiting for incoming SMS messages...[/color]\n",
            markup=True,
            font_size="12sp",
            size_hint_y=None,
            valign="top",
            halign="left",
        )
        self.log_label.bind(
            width=lambda *x: self.log_label.setter("text_size")(self.log_label, (self.log_label.width, None)),
            texture_size=lambda *x: self.log_label.setter("height")(self.log_label, self.log_label.texture_size[1]),
        )
        self.log_scroll.add_widget(self.log_label)
        log_card.add_widget(self.log_scroll)
        content_box.add_widget(log_card)

        scroll_view.add_widget(content_box)
        root.add_widget(scroll_view)

        # Start SMS listening service
        self.start_listener_service()

        return root

    def append_log(self, text: str, level: str = "INFO"):
        """Thread-safe UI log updater."""
        color = "88c0d0" if level == "INFO" else ("a3be8c" if level == "SUCCESS" else "bf616a")
        now = datetime.now().strftime("%H:%M:%S")
        entry = f"[{now}] [color={color}]{text}[/color]\n"

        def _update(dt):
            self.log_label.text = entry + self.log_label.text
        Clock.schedule_once(_update)

    def clear_log(self, *args):
        self.log_label.text = "[color=888888]Log cleared.[/color]\n"

    def apply_preset(self, preset_name: str):
        """Fills SMTP host and port based on selected preset."""
        preset = SMTP_PRESETS.get(preset_name)
        if preset:
            if preset["server"]:
                self.input_smtp_server.text = preset["server"]
            self.input_smtp_port.text = str(preset["port"])
            self.append_log(f"Applied preset: {preset_name}", "INFO")

    def on_toggle_service(self, switch, value):
        """Enables or disables forwarding."""
        self.forwarder.config["is_active"] = value
        self.forwarder.save_config()
        if value:
            self.status_badge.text = "[b]ACTIVE[/b]"
            self.status_badge.color = (0.2, 0.9, 0.4, 1)
            self.append_log("Forwarder service resumed.", "SUCCESS")
        else:
            self.status_badge.text = "[b]PAUSED[/b]"
            self.status_badge.color = (0.9, 0.3, 0.3, 1)
            self.append_log("Forwarder service paused.", "WARN")

    def on_save_settings(self, *args):
        """Reads inputs and saves to JSON."""
        try:
            port = int(self.input_smtp_port.text.strip())
        except ValueError:
            port = 587

        recipients_str = self.input_recipients.text.strip()
        recipients = [r.strip() for r in recipients_str.replace(";", ",").split(",") if r.strip()]

        new_config = {
            "smtp_server": self.input_smtp_server.text.strip(),
            "smtp_port": port,
            "use_ssl": (port == 465),
            "sender_email": self.input_sender_email.text.strip(),
            "sender_password": self.input_sender_pass.text.strip(),
            "recipient_emails": recipients,
            "subject_prefix": self.input_prefix.text.strip(),
        }

        if self.forwarder.save_config(new_config):
            self.show_popup("Success", "Settings saved successfully!")
            self.append_log("Configuration saved.", "SUCCESS")
        else:
            self.show_popup("Error", "Could not save settings file.")

    def on_send_test_email(self, *args):
        """Sends test email in a background thread."""
        self.on_save_settings()
        self.append_log("Sending test email...", "INFO")

        def _run():
            ok, msg = self.forwarder.send_test_email()
            def _post(dt):
                if ok:
                    self.show_popup("Test Email Success", msg)
                    self.append_log(f"Test email delivered: {msg}", "SUCCESS")
                else:
                    self.show_popup("Test Email Failed", msg)
                    self.append_log(f"Test email failed: {msg}", "ERROR")
            Clock.schedule_once(_post)

        threading.Thread(target=_run, daemon=True).start()

    def on_simulate_sms(self, *args):
        """Simulates incoming SMS using input fields."""
        sender = self.input_sim_sender.text.strip() or "MockSender"
        body = self.input_sim_body.text.strip() or "Sample test SMS message"
        self.append_log(f"Simulating incoming SMS from {sender}...", "INFO")
        self.listener.simulate_sms(sender, body)

    def on_sms_received(self, sender: str, body: str, timestamp: str):
        """Triggered whenever a real or simulated SMS arrives."""
        self.append_log(f"Incoming SMS from {sender}: {body[:25]}...", "INFO")
        ok, msg = self.forwarder.forward_sms(
            sender_number=sender,
            message_body=body,
            received_timestamp=timestamp,
        )
        if ok:
            self.append_log(f"SMS forwarded successfully -> {msg}", "SUCCESS")
        else:
            self.append_log(f"Forwarding failed: {msg}", "ERROR")

    def start_listener_service(self):
        """Requests Android permissions and starts SMS listener."""
        def _on_permissions(granted):
            if granted:
                self.listener.start_listening()
                self.append_log("SMS Receiver listener active.", "SUCCESS")
            else:
                self.append_log("SMS permissions were not granted.", "ERROR")

        self.listener.request_permissions(on_complete=_on_permissions)

    def show_popup(self, title: str, text: str):
        """Displays a simple modal alert dialog."""
        layout = BoxLayout(orientation="vertical", padding=dp(10), spacing=dp(10))
        lbl = Label(text=text, halign="center", valign="middle")
        lbl.bind(size=lbl.setter("text_size"))
        btn = Button(
            text="OK",
            size_hint_y=None,
            height=dp(40),
            background_color=(0.25, 0.5, 0.85, 1),
            background_normal="",
        )
        layout.add_widget(lbl)
        layout.add_widget(btn)

        popup = Popup(
            title=title,
            content=layout,
            size_hint=(0.85, 0.4),
            auto_dismiss=False,
        )
        btn.bind(on_release=popup.dismiss)
        popup.open()


if __name__ == "__main__":
    SMSForwarderApp().run()
