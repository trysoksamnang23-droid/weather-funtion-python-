# 1. Purge broken tools
!pip uninstall -y buildozer python-for-android cython
!rm -rf ~/.buildozer/ .buildozer/

# 2. Install stable toolchain versions
!apt-get update && apt-get install -y build-essential ccache git libffi-dev libssl-dev python3-dev zip unzip zlib1g-dev openjdk-17-jdk
!pip install "cython<3.0.0" "setuptools<70.0.0" sh jinja2
!pip install git+https://github.com/kivy/buildozer.git
!pip install git+https://github.com/kivy/python-for-android.git

# 3. Trigger clean build
!buildozer -s android debug
