"""
test_cli.py
===========
Interactive Command-Line Interface (CLI) for testing SMS forwarding directly in Python.
Allows quick testing of:
1. SMTP credentials & connection verification
2. Sending a test verification email
3. Simulating an incoming SMS message and forwarding it to configured email(s)
"""

import sys
from forwarder import SMSForwarder


def main():
    forwarder = SMSForwarder()

    while True:
        print("\n" + "=" * 50)
        print("    MOBILE SMS FORWARDER (PYTHON CLI TESTER)")
        print("=" * 50)
        cfg = forwarder.config
        recipients = forwarder.get_recipients_list()

        print(f"  [1] View Current Configuration")
        print(f"  [2] Configure SMTP Settings & Recipients")
        print(f"  [3] Test SMTP Connection & Login")
        print(f"  [4] Send Test Email to Recipients")
        print(f"  [5] Simulate & Forward an Incoming SMS")
        print(f"  [6] Toggle Forwarding Status (Currently: {'ACTIVE' if cfg.get('is_active', True) else 'PAUSED'})")
        print(f"  [0] Exit")
        print("-" * 50)

        choice = input("Enter option (0-6): ").strip()

        if choice == "1":
            print("\n--- Current Settings ---")
            print(f"SMTP Server:     {cfg.get('smtp_server')}:{cfg.get('smtp_port')} (SSL={cfg.get('use_ssl')})")
            print(f"Sender Email:    {cfg.get('sender_email') or '<not set>'}")
            print(f"Password Set:    {'Yes' if cfg.get('sender_password') else 'No'}")
            print(f"Recipients:      {', '.join(recipients) if recipients else '<none>'}")
            print(f"Subject Prefix:  {cfg.get('subject_prefix')}")
            print(f"Device Name:     {cfg.get('device_name')}")
            print(f"Active:          {cfg.get('is_active')}")
            print(f"Config File:     {forwarder.config_path}")

        elif choice == "2":
            print("\n--- Configure SMTP & Recipients ---")
            print("Press ENTER to keep the current value in brackets.\n")

            cur_server = cfg.get("smtp_server", "smtp.gmail.com")
            server = input(f"SMTP Server [{cur_server}]: ").strip() or cur_server

            cur_port = str(cfg.get("smtp_port", 587))
            port_str = input(f"SMTP Port [{cur_port}]: ").strip() or cur_port
            try:
                port = int(port_str)
            except ValueError:
                port = 587

            use_ssl = (port == 465)

            cur_sender = cfg.get("sender_email", "")
            sender = input(f"Sender Email Address [{cur_sender}]: ").strip() or cur_sender

            cur_pass = cfg.get("sender_password", "")
            pass_prompt = "(keep current)" if cur_pass else "(empty)"
            password = input(f"Sender Password / App Password [{pass_prompt}]: ").strip() or cur_pass

            cur_recipients = ", ".join(recipients)
            recipients_input = input(f"Recipient Emails (comma-separated) [{cur_recipients}]: ").strip()
            if recipients_input:
                new_recipients = [r.strip() for r in recipients_input.replace(";", ",").split(",") if r.strip()]
            else:
                new_recipients = recipients

            cur_prefix = cfg.get("subject_prefix", "[SMS Forwarded]")
            prefix = input(f"Subject Prefix [{cur_prefix}]: ").strip() or cur_prefix

            new_cfg = {
                "smtp_server": server,
                "smtp_port": port,
                "use_ssl": use_ssl,
                "sender_email": sender,
                "sender_password": password,
                "recipient_emails": new_recipients,
                "subject_prefix": prefix,
            }
            if forwarder.save_config(new_cfg):
                print("\n[SUCCESS] Settings updated and saved successfully!")
            else:
                print("\n[ERROR] Failed to save settings.")

        elif choice == "3":
            print("\n--- Testing SMTP Connection ---")
            print("Connecting to SMTP server...")
            ok, msg = forwarder.test_connection()
            if ok:
                print(f"[SUCCESS] {msg}")
            else:
                print(f"[FAILED] {msg}")

        elif choice == "4":
            print("\n--- Sending Test Email ---")
            if not recipients:
                print("[ERROR] Please configure at least one recipient email address first (Option 2).")
                continue
            print(f"Sending test email to: {', '.join(recipients)}...")
            ok, msg = forwarder.send_test_email()
            if ok:
                print(f"[SUCCESS] {msg}")
            else:
                print(f"[FAILED] {msg}")

        elif choice == "5":
            print("\n--- Simulate Incoming SMS ---")
            if not recipients:
                print("[ERROR] Please configure recipient email addresses first (Option 2).")
                continue

            sender = input("Enter simulated Sender (e.g. +14155552671 or BANK-ALERT) [+14155552671]: ").strip()
            if not sender:
                sender = "+14155552671"

            body = input("Enter simulated SMS Body [Your login verification code is 591823. Valid for 10 minutes.]: ").strip()
            if not body:
                body = "Your login verification code is 591823. Valid for 10 minutes."

            print(f"\nForwarding simulated SMS from {sender}...")
            ok, msg = forwarder.forward_sms(sender_number=sender, message_body=body)
            if ok:
                print(f"[SUCCESS] {msg}")
            else:
                print(f"[FAILED] {msg}")

        elif choice == "6":
            new_state = not cfg.get("is_active", True)
            forwarder.config["is_active"] = new_state
            forwarder.save_config()
            print(f"\n[INFO] Forwarder service is now: {'ACTIVE' if new_state else 'PAUSED'}")

        elif choice == "0":
            print("\nExiting. Goodbye!")
            sys.exit(0)
        else:
            print("\n[INVALID] Please enter a valid number (0-6).")


if __name__ == "__main__":
    main()
