[app]

# (str) Title of your application
title = SMS Forwarder

# (str) Package name
package.name = smsforwarder

# (str) Package domain (needed for android/ios packaging)
package.domain = org.smsforwarder

# (str) Source code where the main.py lives
source.dir = .

# (str) Icon of the application
icon.filename = %(source.dir)s/icon.png

# (list) Source files to include (let empty to include all the files)
source.include_exts = py,png,jpg,kv,atlas,json,txt,java

# (list) List of inclusions using pattern matching
#source.include_patterns = assets/*,images/*.png

# (list) Source files to exclude (let empty to not exclude anything)
source.exclude_dirs = tests, bin, .git, .github

# (list) List of exclusions using pattern matching
#source.exclude_patterns = license,data/audio/*.wav

# (str) Application versioning (method 1)
version = 1.0.0

# (list) Application requirements
# comma separated e.g. requirements = sqlite3,kivy
requirements = python3,kivy,pyjnius,charset-normalizer==2.1.1

# (str) Supported orientation (one of landscape, sensorLandscape, portrait or all)
orientation = portrait

# (bool) Indicate if the application should be fullscreen or not
fullscreen = 0

#
# Android specific
#

# (list) Permissions
android.permissions = RECEIVE_SMS, READ_SMS, INTERNET, ACCESS_NETWORK_STATE, WAKE_LOCK, FOREGROUND_SERVICE, POST_NOTIFICATIONS

# (int) Target Android API, should be as high as possible.
android.api = 33

# (int) Minimum API your APK will support.
android.minapi = 24

# (int) Android NDK API to use.
android.ndk_api = 24

# (bool) Use --private data storage (True) or --dir public storage (False)
android.private_storage = True

# (bool) Automatically accept Android SDK licenses
android.accept_sdk_license = True

# (list) The Android architectures to build for.
android.archs = arm64-v8a

# (str) python-for-android branch to use
p4a.branch = develop

# (list) Java source folders to add
android.add_src = src

# (list) Android services to declare
# Format: <service_name>:<service_entrypoint.py>
services = forwarder:service.py

# (bool) Android logcat filters to use
android.logcat_filters = *:S python:D SMSForwarder:D SMSListener:D SMSForwarderReceiver:D

# (str) Android entry point (leave commented to use default SDL2 PythonActivity)
# android.entrypoint = org.kivy.android.PythonActivity

[buildozer]

# (int) Log level (0 = error only, 1 = info, 2 = debug with command output)
log_level = 2

# (int) Display warning if buildozer is run as root (0 = False, 1 = True)
warn_on_root = 1
