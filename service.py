"""
service.py
==========
Android Background Service for SMS Forwarder.
Runs as a persistent background service on Android to process incoming SMS
even when the main UI application is minimized or closed.
"""

import time
import logging
from forwarder import SMSForwarder
from android_listener import AndroidSMSListener

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("SMSBackgroundService")


def on_sms_received(sender: str, body: str, timestamp: str):
    logger.info(f"[BACKGROUND SERVICE] SMS from {sender}: {body[:20]}...")
    forwarder = SMSForwarder()
    ok, msg = forwarder.forward_sms(
        sender_number=sender,
        message_body=body,
        received_timestamp=timestamp,
    )
    logger.info(f"[BACKGROUND SERVICE] Forward result: ok={ok}, msg={msg}")


def main():
    logger.info("SMS Forwarder Background Service starting...")
    forwarder = SMSForwarder()

    if not forwarder.config.get("is_active", True):
        logger.info("Service is inactive per user configuration.")

    listener = AndroidSMSListener(on_sms_received_callback=on_sms_received)
    listener.start_listening()
    logger.info("SMS Listener running in background service loop.")

    # Keep service alive
    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        listener.stop_listening()
        logger.info("Background service stopped.")


if __name__ == "__main__":
    main()
