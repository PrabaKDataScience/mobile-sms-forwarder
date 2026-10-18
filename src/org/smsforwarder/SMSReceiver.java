package org.smsforwarder;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.os.Build;
import android.os.Bundle;
import android.telephony.SmsMessage;
import android.util.Log;

/**
 * SMSReceiver
 * -----------
 * Native Android BroadcastReceiver registered in AndroidManifest.xml.
 * Receives SMS broadcasts directly from the Android OS even if the Python UI is closed.
 */
public class SMSReceiver extends BroadcastReceiver {
    private static final String TAG = "SMSForwarderReceiver";

    @Override
    public void onReceive(Context context, Intent intent) {
        if (intent == null || intent.getAction() == null) {
            return;
        }

        if (intent.getAction().equals("android.provider.Telephony.SMS_RECEIVED")) {
            Bundle bundle = intent.getExtras();
            if (bundle != null) {
                try {
                    Object[] pdus = (Object[]) bundle.get("pdus");
                    String format = bundle.getString("format");

                    if (pdus != null && pdus.length > 0) {
                        String sender = "";
                        StringBuilder fullBody = new StringBuilder();

                        for (Object pdu : pdus) {
                            SmsMessage message;
                            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M && format != null) {
                                message = SmsMessage.createFromPdu((byte[]) pdu, format);
                            } else {
                                message = SmsMessage.createFromPdu((byte[]) pdu);
                            }

                            if (message != null) {
                                if (sender.isEmpty()) {
                                    sender = message.getDisplayOriginatingAddress();
                                }
                                String bodyChunk = message.getDisplayMessageBody();
                                if (bodyChunk != null) {
                                    fullBody.append(bodyChunk);
                                }
                            }
                        }

                        Log.i(TAG, "SMS Received from: " + sender + ", length: " + fullBody.length());

                        // Forward broadcast internally to the Python service
                        Intent serviceIntent = new Intent();
                        serviceIntent.setPackage(context.getPackageName());
                        serviceIntent.setAction("org.smsforwarder.ACTION_SMS_RECEIVED");
                        serviceIntent.putExtra("sender", sender);
                        serviceIntent.putExtra("body", fullBody.toString());
                        serviceIntent.putExtra("timestamp", System.currentTimeMillis());
                        context.sendBroadcast(serviceIntent);
                    }
                } catch (Exception e) {
                    Log.e(TAG, "Error processing incoming SMS broadcast: " + e.getMessage(), e);
                }
            }
        }
    }
}
