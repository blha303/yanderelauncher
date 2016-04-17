YandereLauncher
===============

A program that utilizes a checksum system to download and verify files
for Yandere Simulator. This launcher is not created by or affiliated
with YandereDev.

Usage
-----

``setup.py`` is untested, I'm currently running the program from the
project directory with ``python3 -m yanderelauncher``, which creates a
directory called ``YandereSim`` in the same place and starts downloading
the files from there. It pulls the filelist from my web server where
I've extracted the files and produced a checksum file with `this script
I
wrote <https://gist.github.com/blha303/4c87ec7875edeea1c1398eb0c1cc09a5>`__.
You'll need ```requests`` <https://pypi.python.org/pypi/requests>`__.
