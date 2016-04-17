from setuptools import setup

with open("README.rst", "rb") as f:
    long_descr = f.read().decode('utf-8')

setup(
    name = "yanderelauncher",
    packages = ["yanderelauncher"],
    install_requires = [],
    entry_points = {
        "console_scripts": ['yanderelauncher = yanderelauncher.yanderelauncher:main']
        },
    version = "1.0.0",
    description = "Utilizes a checksum system to download and verify files for Yandere Simulator",
    long_description = long_descr,
    author = "Steven Smith",
    author_email = "stevensmith.ome@gmail.com",
    license = "MIT",
    url = "https://blha303.github.io/yanderelauncher/",
    classifiers = [
        "Development Status :: 4 - Beta",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3",
        "Intended Audience :: End Users/Desktop"
        ]
    )
