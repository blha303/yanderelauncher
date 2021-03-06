#!/usr/bin/env python3
import requests
import sys
from json import loads
from hashlib import md5
from argparse import ArgumentParser
from zipfile import ZipFile
from traceback import format_exc
from shutil import rmtree
from tempfile import NamedTemporaryFile
from time import ctime
from tkinter import Canvas, Tk, PhotoImage, Toplevel, CENTER, NW
import base64
from subprocess import Popen
from glob import glob
from threading import Thread
from os import getcwd, sep, walk, makedirs, unlink, getenv
import os.path

__author__ = "blha303 <stevensmith.ome@gmail.com>"
__version__ = "0.1.2"

CDN = "https://yandere.b303.me/"
ROOT = getcwd()
DRYRUN = False
VERBOSE = False
GUI_LOGSTR = None

console_log = print

# Utils
def getcfg():
    if sys.platform[:3] == "win":
        return getenv("APPDATA") + sep + "YandereLauncher.cfg"
    elif sys.platform == "darwin":
        return getenv("PWD") + "/Library/YandereLauncher.cfg"
    else:
        return getenv("PWD") + "/.YandereLauncher.cfg"

def print(text, end=None, file=None):
    if GUI_LOGSTR:
        GUI_LOGSTR[0].itemconfig(GUI_LOGSTR[1], text=text)
    console_log(text, end=end, file=file)

def path_to(filename):
    """ Checks if YandereLauncher is running from a bundled package or source, and
        returns the path to the specified file """
    if getattr(sys, 'frozen', False):
        return os.path.join(sys._MEIPASS, filename)
    else:
        return os.path.join(ROOT, filename)

def download(url, dest, attempt=1, checksum=None):
    try:
        with open(os.path.join(ROOT, dest), "rb") as f:
            done = len(f.read())
        print("Resuming from byte " + str(done-1))
    except:
        done = 0
    try:
        r = requests.get(url, stream=True, headers={"Range": "bytes={}-".format(str(done))}, timeout=(10.0, 1.0))
        if r.status_code is 416:
            return
        if r.headers.get("Content-Range"):
            done = int(r.headers.get("Content-Range").split()[1].split("-")[0])
            total = int(r.headers.get("Content-Range").split("/")[1])
        elif r.headers.get("Content-Length"):
            total = int(r.headers.get("Content-Length"))
        else:
            total = 0
        mkdir(os.path.join(ROOT, dest))
        if not DRYRUN:
            with open(os.path.join(ROOT, dest), "ab+" if done else "wb") as f:
                for chunk in r.iter_content(chunk_size=1024):
                    if chunk:
                        f.write(chunk)
                    done += len(chunk)
                    if total:
                        print("{0:.2f}% ({1}) of {2}       ".format((done / total) * 100, sizeof_fmt(done), sizeof_fmt(total)), end="\r", file=sys.stderr)
                print()
        else:
            print("Would have downloaded {} ({}/{})".format(url, done, total), file=sys.stderr)
        if checksum and done == total:
            if checksum != md5sum(os.path.join(ROOT, dest)):
                if attempt >= 3:
                    print("Could not verify {}".format(dest))
                    return
                attempt += 1
                print("Could not verify {}, retrying (attempt {})".format(dest, attempt), file=sys.stderr)
                return download(url, dest, attempt=attempt, checksum=checksum)
    except requests.exceptions.ConnectionError as e:
        if VERBOSE:
            print(format_exc())
        if attempt >= 3:
            print("Could not download {}".format(dest))
            return
        attempt += 1
        print("Download failed, retrying (attempt {})".format(attempt), file=sys.stderr)
        return download(url, dest, attempt=attempt, checksum=checksum)

def mkdir(path):
    if DRYRUN:
        print("Would have made directories for path " + path, file=sys.stderr)
        return
    try:
        makedirs(os.path.dirname(path))
    except FileExistsError:
        if VERBOSE:
            print(format_exc())
        pass

def md5sum(filename):
    """ Opens a file and progressively generates an MD5 hash
        from its contents, avoiding loading the complete
        contents into ram at once
        http://stackoverflow.com/a/24847608 """
    hash = md5()
    try:
        with open(filename, "rb") as f:
            for chunk in iter(lambda: f.read(128 * hash.block_size), b""):
                hash.update(chunk)
        return hash.hexdigest()
    except FileNotFoundError:
        if VERBOSE:
            print(format_exc())
        return False

def sizeof_fmt(num, suffix='B'):
    for unit in ['','K','M','G']:
        if abs(num) < 1024.0:
            return "%3.1f%s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f%s%s" % (num, 'T', suffix)
# End utils

def get_latest_zip(extract=True):
    """ Downloads the latest Yandere Simulator zip from the server and,
        if the option is enabled, extracts it to the current directory
        and checksums the files using the checksums.json from the server """
    try:
        checksum, filename = requests.get(CDN + "latest-checksum").text.strip().split(maxsplit=1)
        download(CDN + filename, filename)
        if checksum != md5sum(filename):
            print("Package did not download successfully", file=sys.stderr)
            return False
        if extract:
            if DRYRUN:
                print("Would have extracted the zip", file=sys.stderr)
            else:
                with ZipFile(filename, "r") as z:
                    print("Extracting files, please be patient", file=sys.stderr)
                    z.extractall(ROOT)
                latest = requests.get(CDN + "latest").text.strip()
                checksums = requests.get(CDN + latest + "checksums.json").json()
                for fn, chk in checksums.items():
                    if chk != md5sum(os.path.join(ROOT, latest, fn)):
                        if DRYRUN:
                            print("{} could not be verified, not redownloading".format(fn), file=sys.stderr)
                            continue
                        print("{} could not be verified, redownloading".format(fn), file=sys.stderr)
                        unlink(os.path.join(ROOT, latest, fn))
                        download(CDN + latest + fn, os.path.join(latest, fn), attempt=2, checksum=chk)
                with open(getcfg(), "w") as f:
                    exe = glob(os.path.join(ROOT, latest, "*.exe"))[0]
                    f.write(exe)
    except KeyboardInterrupt:
        if VERBOSE:
            print(format_exc())
        return False
    else:
        return True

def main():
    parser = ArgumentParser(prog="YandereLauncher")
    parser.add_argument("-d", "--dryrun", help="Don't change anything on the filesystem, just print what's going on", action="store_true")
    parser.add_argument("-s", "--cdn", help="Specify a different server URL, with trailing slash")
    parser.add_argument("-e", "--skip-extract", help="Skip extraction of zip", action="store_false")
    parser.add_argument("-v", "--verbose", help="Print full traceback for all exceptions", action="store_true")
    parser.add_argument("--redownload", help="Redownload game files (DELETES ALL DIRECTORIES AND ZIPS MATCHING YandereSim* IN CURRENT DIR)", action="store_true")
    parser.add_argument("--gui", help="Show GUI (defaults to true if frozen)", action="store_true")
    args = parser.parse_args()
    if args.cdn:
        global CDN
        CDN = args.cdn
    if args.dryrun:
        global DRYRUN
        DRYRUN = True
    if args.verbose:
        global VERBOSE
        VERBOSE = True
    if args.redownload:
        from glob import glob
        for a in glob(os.path.join(ROOT, "YandereSim*")):
            if os.path.isdir(a):
                rmtree(a)
            elif a[-4:] == ".zip":
                unlink(a)
    if getattr(sys, 'frozen', False) or args.gui:
        # init tkinter
        root = Tk()
        root.title("YandereLauncher")
        # background image

        with open(path_to("YandereLauncher.gif"), "rb") as f:
            photo = PhotoImage(data=base64.encodestring(f.read()))
        cv = Canvas(width=635, height=355)
        cv.pack(side='top', fill='both', expand='yes')
        cv.create_image(0, 0, image=photo, anchor=NW)
        def start_game(event):
            try:
                with open(getcfg()) as f:
                    Popen(["start", f.read()])
            except:
                print("You need to run an update")

        play = cv.create_rectangle(88, 260, 244, 323, fill="", outline="")
        cv.tag_bind(play, "<ButtonPress-1>", start_game)

        update = cv.create_rectangle(400, 260, 555, 323, fill="", outline="")
        cv.tag_bind(update, "<ButtonPress-1>", lambda event: Thread(target=get_latest_zip))

        global GUI_LOGSTR
        GUI_LOGSTR = (cv, cv.create_text(166, 199, text="Ready to update...", width=311, justify=CENTER, anchor=NW))

#        close = cv.create_rectangle(622, 5, 640, 22, fill="", outline="")
#        cv.tag_bind(close, "<ButtonPress-1>", lambda root=root:root.destroy())

        root.mainloop()
    else:
        if get_latest_zip(extract=args.skip_extract):
            print("Download was successful")
            return 0
        else:
            print("Download was unsuccessful")
            return 1

if __name__ == "__main__":
    sys.exit(main())
