#!/usr/bin/env python
from __future__ import print_function
from requests import get
from json import loads
from hashlib import md5
from sys import exit, stderr, stdout
from argparse import ArgumentParser
from os import getcwd, sep, walk, makedirs
import os.path

def mkdir(path):
    try:
        makedirs(os.path.dirname(path))
    except FileExistsError:
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
        return False

def sizeof_fmt(num, suffix='B'):
    for unit in ['','K','M','G','T','P','E','Z']:
        if abs(num) < 1024.0:
            return "%3.1f%s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f%s%s" % (num, 'Y', suffix)

CDN = "https://yandere.b303.me/"
ROOT = getcwd() + sep + "YandereSim" + sep
mkdir(ROOT)

def get_checksums():
    """ Downloads the latest checksum file and returns a dict of its contents,
        and the root url to prepend to the filenames
        >>> get_checksums()
        ("https://yandere.b303.me/YandereSimApril15th/",
         {"YandereSimApril15th_Data/StreamingAssets/Portraits/Student_37.png":
           "1c443f9823b1398b0e39b68bc47398a8",
          ...}
        ) """
    latest = get(CDN + "latest").text.strip()
    return (CDN + latest, loads(get(CDN + latest + "checksums.json").text))

def redownload(filename, webroot, checksums):
    """ Redownload file from the given CDN and verify checksum
        Returns True if file verifies, False if not """
    print("Downloading {}".format(filename))
    r = get(webroot + filename, stream=True)
    done = 0
    mkdir(os.path.join(ROOT, filename))
    with open(os.path.join(ROOT, filename), 'wb') as f:
        for chunk in r.iter_content(chunk_size=1024):
            done += len(chunk)
            if chunk:
                f.write(chunk)
            tot = int(r.headers.get("content-length"))
            print("{0:.2f}% ({1}) of {2}       ".format((done / tot) * 100, sizeof_fmt(done), sizeof_fmt(tot)), end="\r")
    return checksums[filename] == md5sum(os.path.join(ROOT, filename))

def get_files(webroot, checksums, dryrun=False):
    """ Searches the YandereSim directory for files that are missing or invalid
        compared to the provided checksum dict, and redownloads them from the
        given CDN """
    ERROR = False
    for filename, checksum in checksums.items():
        if filename == "checksums.json":
            # Shouldn't happen, but a catch for if it does
            continue
        if checksum != md5sum(os.path.join(ROOT, filename)):
            if dryrun:
                print("File not verified: {}".format(filename))
            elif not redownload(filename, webroot, checksums):
                print("Error downloading {}".format(filename))
                ERROR = True
            else:
                print("Downloaded {}".format(filename))
        else:
            print("File exists and is verified: {}".format(filename))
    else:
        print("Unknown file: {}".format(filename))
    return not ERROR

def main():
    parser = ArgumentParser(prog="YandereLauncher")
    parser.add_argument("--cdn", help="Supply alternate CDN, with trailing slash")
    parser.add_argument("--dryrun", help="Test functionality without doing anything to the filesystem", action="store_true")
    args = parser.parse_args()
    if args.cdn:
        global CDN
        CDN = args.cdn
    if get_files(*get_checksums(), dryrun=args.dryrun):
        return 0
    else:
        return 1

if __name__ == "__main__":
    exit(main())
