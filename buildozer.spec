[app]

# (str) Title of your application
title = Cambodia Weather

# (str) Package name
package.name = cambodiaweather

# (str) Package domain
package.domain = org.test

# (str) Source code directory
source.dir = .

# (list) Source files to include
source.include_exts = py,png,jpg,kv,atlas

# (str) Application versioning
version = 0.1

# (list) Application requirements
requirements = python3,kivy,kivymd,requests

# (list) Supported orientations
orientation = portrait

# (bool) Indicate if application should be fullscreen
fullscreen = 0

# (list) Permissions
android.permissions = INTERNET

# (int) Target Android API
android.api = 33

# (int) Minimum API supported
android.minapi = 24

# (str) Android NDK version
android.ndk = 25b

# (int) Android NDK API
android.ndk_api = 24

# (list) Android archs
android.archs = arm64-v8a

# (bool) Auto accept SDK license
android.accept_sdk_license = True

# (bool) Enable auto backup
android.allow_backup = True

[buildozer]

# (int) Log level (0 = error only, 1 = info, 2 = debug)
log_level = 2

# (int) Display warning if buildozer is run as root
warn_on_root = 1
