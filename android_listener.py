"""
android_listener.py
===================
Android SMS listener and permission manager.
Integrates with Android OS via PyJNIus when running on an Android device.
Provides mock/simulation mode when running on Desktop (Windows/Linux/macOS).
"""

import logging
import threading
from datetime import datetime
from typing import Callable, Optional

logger = logging.getLogger("SMSListener")

# Detect platform
IS_ANDROID = False
try:
    from kivy.utils import platform
    IS_ANDROID = (platform == "android")
except Exception:
    IS_ANDROID = False


class AndroidSMSListener:
    """
    Listens for incoming SMS messages on Android devices.
    Extracts sender, body, timestamp, and dispatches to a callback function.
    """

    def __init__(self, on_sms_received_callback: Callable[[str, str, str], None]):
        """
        :param on_sms_received_callback: Function called when SMS arrives:
                                         callback(sender_number, message_body, timestamp)
        """
        self.callback = on_sms_received_callback
        self.is_listening = False
        self._receiver = None
        self._wake_lock = None

    def request_permissions(self, on_complete: Optional[Callable[[bool], None]] = None):
        """Requests required Android permissions at runtime."""
        if not IS_ANDROID:
            logger.info("Desktop platform detected; skipping Android permission requests.")
            if on_complete:
                on_complete(True)
            return

        try:
            from android.permissions import Permission, request_permissions

            permissions_to_request = [
                Permission.RECEIVE_SMS,
                Permission.READ_SMS,
            ]

            # Optional extra permissions for modern Android (13+)
            try:
                if hasattr(Permission, "POST_NOTIFICATIONS"):
                    permissions_to_request.append(Permission.POST_NOTIFICATIONS)
            except Exception:
                pass

            def permission_callback(permissions, grant_results):
                all_granted = all(grant_results)
                logger.info(f"Permissions callback result: {permissions} -> {grant_results}")
                if on_complete:
                    on_complete(all_granted)

            request_permissions(permissions_to_request, permission_callback)
        except Exception as e:
            logger.error(f"Error requesting Android permissions: {e}")
            if on_complete:
                on_complete(False)

    def start_listening(self) -> bool:
        """Starts the SMS broadcast receiver."""
        if self.is_listening:
            return True

        if not IS_ANDROID:
            logger.info("Running on Desktop. SMS Listener started in simulation/test mode.")
            self.is_listening = True
            return True

        try:
            from jnius import autoclass
            from android.runnable import run_on_ui_thread

            PythonActivity = autoclass("org.kivy.android.PythonActivity")
            activity = PythonActivity.mActivity
            Context = autoclass("android.content.Context")
            IntentFilter = autoclass("android.content.IntentFilter")

            # Acquire partial WakeLock to keep CPU awake when SMS arrives
            try:
                PowerManager = autoclass("android.os.PowerManager")
                power_manager = activity.getSystemService(Context.POWER_SERVICE)
                self._wake_lock = power_manager.newWakeLock(
                    PowerManager.PARTIAL_WAKE_LOCK, "SMSForwarder::WakeLock"
                )
            except Exception as w_err:
                logger.warning(f"Could not acquire WakeLock: {w_err}")

            # Register dynamic receiver using PythonJavaClass or custom bridge
            self._register_android_receiver(activity, Context, IntentFilter)
            self.is_listening = True
            logger.info("Android SMS Receiver registered successfully.")
            return True
        except Exception as e:
            logger.error(f"Failed to start Android SMS listener: {e}")
            self.is_listening = False
            return False

    def stop_listening(self) -> bool:
        """Unregisters the receiver and releases any wake locks."""
        if not self.is_listening:
            return True

        if IS_ANDROID and self._receiver:
            try:
                from jnius import autoclass
                PythonActivity = autoclass("org.kivy.android.PythonActivity")
                activity = PythonActivity.mActivity
                activity.unregisterReceiver(self._receiver)
                self._receiver = None
            except Exception as e:
                logger.error(f"Error unregistering receiver: {e}")

        if self._wake_lock:
            try:
                if self._wake_lock.isHeld():
                    self._wake_lock.release()
            except Exception:
                pass
            self._wake_lock = None

        self.is_listening = False
        logger.info("SMS listener stopped.")
        return True

    def _register_android_receiver(self, activity, Context, IntentFilter):
        """Registers the BroadcastReceiver with Android OS using PyJNIus."""
        from jnius import PythonJavaClass, java_method

        parent_listener = self

        class DynamicSMSReceiver(PythonJavaClass):
            __javacontext__ = "app"
            __javainterfaces__ = ["android/content/BroadcastReceiver"]

            @java_method("(Landroid/content/Context;Landroid/content/Intent;)V")
            def onReceive(self, context, intent):
                action = intent.getAction()
                if action == "android.provider.Telephony.SMS_RECEIVED":
                    parent_listener._handle_incoming_sms_intent(intent)

        try:
            self._receiver = DynamicSMSReceiver()
            sms_filter = IntentFilter("android.provider.Telephony.SMS_RECEIVED")
            # Set high priority so we receive the SMS promptly
            sms_filter.setPriority(999)
            activity.registerReceiver(self._receiver, sms_filter)
        except Exception as e:
            logger.warning(f"Dynamic PythonJavaClass receiver registration failed: {e}. Relying on Java BroadcastReceiver.")

    def _handle_incoming_sms_intent(self, intent):
        """Extracts SMS message details from Android Intent."""
        try:
            from jnius import autoclass, cast

            bundle = intent.getExtras()
            if bundle is None:
                return

            pdus = bundle.get("pdus")
            if pdus is None:
                return

            format_type = bundle.getString("format")
            SmsMessage = autoclass("android.telephony.SmsMessage")
            BuildVersion = autoclass("android.os.Build$VERSION")

            sender = ""
            full_body = []
            timestamp_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # Iterate over all PDUs (multi-part SMS chunks)
            for i in range(len(pdus)):
                pdu_bytes = cast("java.lang.Object", pdus[i])
                if BuildVersion.SDK_INT >= 23 and format_type is not None:
                    sms = SmsMessage.createFromPdu(pdu_bytes, format_type)
                else:
                    sms = SmsMessage.createFromPdu(pdu_bytes)

                if sms is not None:
                    if not sender:
                        sender = str(sms.getDisplayOriginatingAddress())
                    body_chunk = sms.getDisplayMessageBody()
                    if body_chunk:
                        full_body.append(str(body_chunk))

            combined_body = "".join(full_body)

            if sender and combined_body:
                logger.info(f"Incoming SMS captured from {sender}: {combined_body[:30]}...")
                # Dispatch in a separate thread so we don't block the Android UI thread
                threading.Thread(
                    target=self.callback,
                    args=(sender, combined_body, timestamp_str),
                    daemon=True,
                ).start()
        except Exception as e:
            logger.error(f"Error parsing incoming SMS intent: {e}")

    def simulate_sms(self, sender: str, message: str):
        """Simulates an incoming SMS message for testing on desktop or without a real SIM."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        logger.info(f"[SIMULATED SMS] From: {sender} | Content: {message}")
        threading.Thread(
            target=self.callback,
            args=(sender, message, timestamp),
            daemon=True,
        ).start()
