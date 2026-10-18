# Mobile SMS Forwarder (Python & Android APK)

A lightweight, automated mobile SMS-to-Email forwarder built with **Python**, **Kivy**, and **Android PyJNIus**. As soon as an incoming SMS arrives on the mobile device, it is instantly formatted and forwarded to your specified email address(es).

---

## 🌟 Key Features

- **Automated Instant Forwarding**: Intercepts incoming SMS and immediately emails the full message.
- **Multiple Recipients**: Forward to single or multiple comma-separated email addresses (`alert1@example.com, alert2@example.com`).
- **Rich HTML & Plaintext Templates**: Emails include the sender phone number, timestamp, device name, and the verbatim SMS text in a responsive card format.
- **Reliable Background Execution**: Native Android BroadcastReceiver (`SMSReceiver.java`) and background service ensure messages are captured even when the app is minimized.
- **Desktop Simulator & CLI**: Test your SMTP credentials and simulate incoming SMS messages directly from your PC before deploying to Android.
- **Zero-Setup Cloud APK Builder**: Includes a ready-to-run GitHub Actions workflow that compiles the Android APK for you in the cloud for free.

---

## 📁 Project Structure

```text
mobile_message_forwarder/
├── forwarder.py                   # Core SMTP engine & config manager
├── android_listener.py            # Android SMS broadcast listener & PyJNIus bridge
├── main.py                        # Kivy Graphical Interface (Desktop & Android)
├── service.py                     # Android background service daemon
├── test_cli.py                    # Interactive CLI tool for fast desktop testing
├── buildozer.spec                 # Buildozer packaging specification for Android APK
├── sms_forwarder_config.example.json # Safe configuration template for git commits
├── .env.example                   # Environment variable template
├── requirements.txt               # Python package dependencies
├── src/
│   └── org/smsforwarder/
│       └── SMSReceiver.java        # Native Android BroadcastReceiver
└── .github/
    └── workflows/
        └── build_apk.yml          # Cloud APK build workflow (GitHub Actions)
```

---

## 🚀 Quick Start: Testing on Desktop (Python)

You can test your email settings and simulate SMS forwarding on your computer before converting to an APK.

### 1. Run the Interactive CLI Tester
The CLI tester uses Python's standard library and requires **no external packages**:

```bash
python test_cli.py
```

From the CLI menu, you can:
1. Configure your SMTP settings (Server, Port, Sender Email, App Password, Recipients).
2. Test the connection and verify your credentials.
3. Send a test email.
4. Simulate an incoming SMS (e.g. from `+1987654321`) and inspect the forwarded email in your inbox.

### 2. Run the Full Graphical UI (Optional)
If you wish to run the desktop GUI:

```bash
pip install -r requirements.txt
python main.py
```

---

## 📧 Email Provider Setup (Important)

### For Gmail Users:
1. Enable **2-Step Verification** on your Google Account: [myaccount.google.com/security](https://myaccount.google.com/security).
2. Go to **App Passwords**: [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords).
3. Create a new App Password (e.g. named `SMS Forwarder`).
4. Copy the **16-character generated password**.
5. Use this App Password in the app (do **not** use your normal Google account password).
   - **SMTP Server**: `smtp.gmail.com`
   - **SMTP Port**: `587` (TLS) or `465` (SSL)

### For Outlook / Office 365:
- **SMTP Server**: `smtp-mail.outlook.com`
- **SMTP Port**: `587`
- Enable SMTP AUTH in your Microsoft account settings if required.

---

## 📱 How to Convert into an Android APK

There are two primary methods to convert this Python project into an installable Android APK:

### Method 1: Automated Cloud Build with GitHub Actions (Recommended)
This method requires **no local Linux or Android SDK installation** on your Windows PC.

1. Initialize a Git repository and commit the project:
   ```bash
   git init
   git add .
   git commit -m "Initial commit for SMS forwarder"
   ```
2. Create a repository on [GitHub](https://github.com/new) and push your code:
   ```bash
   git remote add origin https://github.com/<your-username>/<your-repo-name>.git
   git branch -M main
   git push -u origin main
   ```
3. Go to the **Actions** tab on your GitHub repository.
4. The workflow **"Build Android APK with Buildozer"** will run automatically.
5. Once completed (~8-10 minutes), download the ready-to-install `.apk` artifact under **Artifacts** (`SMSForwarder-debug-apk`).

---

### Method 2: Local Build using WSL (Windows Subsystem for Linux)
If you prefer building locally on Windows using WSL (Ubuntu):

1. Open WSL terminal (`wsl` in PowerShell).
2. Install dependencies:
   ```bash
   sudo apt update
   sudo apt install -y git zip unzip openjdk-17-jdk python3-pip autoconf libtool pkg-config zlib1g-dev libncurses5-dev libncursesw5-dev libtinfo5 cmake libffi-dev libssl-dev
   pip install --upgrade cython buildozer
   ```
3. Navigate to the project directory:
   ```bash
   cd /mnt/d/for_tamil_ai/mobile_message_forwarder
   ```
4. Build the APK:
   ```bash
   buildozer android debug
   ```
5. The compiled APK will be created in the `bin/` folder:
   `bin/smsforwarder-1.0.0-arm64-v8a_armeabi-v7a-debug.apk`

---

## ⚙️ Android Device Installation & Permissions

Once installed on your Android device:
1. **Grant SMS Permissions**:
   - Open the app.
   - Accept the prompt to allow reading and receiving SMS messages.
   - If prompted, allow notification permissions (Android 13+).
2. **Disable Battery Optimization (Crucial)**:
   - Android may put background services to sleep to save battery.
   - Go to **Settings** > **Apps** > **SMS Forwarder** > **Battery** > Set to **Unrestricted** / **Don't Optimize**.
3. **Configure & Test**:
   - Enter your SMTP details and recipient email(s).
   - Tap **Save Settings**.
   - Tap **Send Test Email** to confirm delivery.
   - Keep the service toggle set to **ACTIVE**.
