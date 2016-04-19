#!/usr/bin/env python3
import requests
from json import loads
from hashlib import md5
from sys import exit, stderr, stdout
from argparse import ArgumentParser
from zipfile import ZipFile
from traceback import format_exc
from shutil import rmtree
from tempfile import NamedTemporaryFile
from time import ctime
from os import getcwd, sep, walk, makedirs, unlink
import os.path

__author__ = "blha303 <stevensmith.ome@gmail.com>"
__version__ = "0.0.8"

CDN = "https://yandere.b303.me/"
ROOT = getcwd()
DRYRUN = False
VERBOSE = False
LOG = None

# Utils
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
                        print("{0:.2f}% ({1}) of {2}       ".format((done / total) * 100, sizeof_fmt(done), sizeof_fmt(total)), end="\r", file=stderr)
                print()
        else:
            print("Would have downloaded {} ({}/{})".format(url, done, total), file=stderr)
        if checksum and done == total:
            if checksum != md5sum(os.path.join(ROOT, dest)):
                if attempt >= 3:
                    print("Could not verify {}".format(dest))
                    return
                attempt += 1
                print("Could not verify {}, retrying (attempt {})".format(dest, attempt), file=stderr)
                return download(url, dest, attempt=attempt, checksum=checksum)
    except requests.exceptions.ConnectionError as e:
        if VERBOSE:
            print(format_exc())
        if attempt >= 3:
            print("Could not download {}".format(dest))
            return
        attempt += 1
        print("Download failed, retrying (attempt {})".format(attempt), file=stderr)
        return download(url, dest, attempt=attempt, checksum=checksum)

def mkdir(path):
    if DRYRUN:
        print("Would have made directories for path " + path, file=stderr)
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
            print("Package did not download successfully", file=stderr)
            return False
        if extract:
            if DRYRUN:
                print("Would have extracted the zip", file=stderr)
            else:
                with ZipFile(filename, "r") as z:
                    print("Extracting files, please be patient", file=stderr)
                    z.extractall(ROOT)
                latest = requests.get(CDN + "latest").text.strip()
                checksums = requests.get(CDN + latest + "checksums.json").json()
                for fn, chk in checksums.items():
                    if chk != md5sum(os.path.join(ROOT, latest, fn)):
                        if DRYRUN:
                            print("{} could not be verified, not redownloading".format(fn), file=stderr)
                            continue
                        print("{} could not be verified, redownloading".format(fn), file=stderr)
                        unlink(os.path.join(ROOT, latest, fn))
                        download(CDN + latest + fn, os.path.join(latest, fn), attempt=2, checksum=chk)
    except KeyboardInterrupt:
        if VERBOSE:
            print(format_exc())
        return False
    else:
        return True

def check_files():
    latest = requests.get(CDN + "latest").text.strip()
    with open(os.path.join(ROOT, latest, latest[:-1] + ".exe")) as f:
        pass

def main():
    parser = ArgumentParser(prog="YandereLauncher")
    parser.add_argument("-d", "--dryrun", help="Don't change anything on the filesystem, just print what's going on", action="store_true")
    parser.add_argument("-s", "--cdn", help="Specify a different server URL, with trailing slash")
    parser.add_argument("-e", "--skip-extract", help="Skip extraction of zip", action="store_false")
    parser.add_argument("-v", "--verbose", help="Print full traceback for all exceptions", action="store_true")
    parser.add_argument("--redownload", help="Redownload game files (DELETES ALL DIRECTORIES AND ZIPS MATCHING YandereSim* IN CURRENT DIR)", action="store_true")
    parser.add_argument("--gui", help="Show GUI", action="store_true")
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
    if args.gui:
        from tkinter import Canvas, Tk, PhotoImage, Toplevel, Label
        import base64
        from subprocess import Popen
        # init tkinter
        root = Tk()
        # debug
        root.bind("<Motion>", lambda event: print("{}, {}".format(event.x, event.y)))
        root.title("YandereLauncher")
        # background image
        with open(os.path.join("img", "YandereLauncher.gif"), "rb") as f:
            photo = PhotoImage(data=base64.encodestring(f.read()))
        cv = Canvas(width=635, height=355)
        cv.pack(side='top', fill='both', expand='yes')
        cv.create_image(0, 0, image=photo, anchor='nw')
        # play button
        def start_game(event):
            # temp
            tl = Toplevel()
            label = Label(tl, text="And this is where I would launch \nmy game. IF I HAD ONE", height=10, width=30)
            label.pack()
#            root.destroy()
        play = cv.create_rectangle(88, 260, 244, 323, fill="", outline="")
        cv.tag_bind(play, "<ButtonPress-1>", start_game)
#        close = tk.Button(window, command=lambda: root.destroy())
#        close.pack(
        root.mainloop()
    else:
        if get_latest_zip(extract=args.skip_extract):
            print("Download was successful")
            return 0
        else:
            print("Download was unsuccessful")
            return 1

if __name__ == "__main__":
    exit(main())
