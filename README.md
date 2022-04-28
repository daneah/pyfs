# pyfs

A toy, in-memory file system in Python. See the [contribution guidelines](./.github/CONTRIBUTING.md) for more about running and testing the code.

## Installation

This project is an installable Python package.

1. Ensure you have Python 3.10 installed on your system, and a virtual environment when you're comfortable installing packages.
1. Clone this repository using your favorite method:
   ```shell
   $ git clone https://github.com/daneah/pyfs
   $ git clone git@github.com/daneah/pyfs
   $ gh repo clone daneah/pyfs
   ```
1. With your virtual environment active, install the package using the following command:
   ```shell
   (my-3.10-env) $ python -m pip install -e pyfs
   ```
1. Ensure the installation has worked properly. The following should complete without error:

```shell
(my-3.10-env) $ python
>>> from pyfs import FileSystem
>>> fs = FileSystem()
```

## Usage

pyfs provides many of the same commands a Unix file system would. The following example shows most of the options:

```pycon
>>> from pyfs import FileSystem
>>> fs = FileSystem()
>>> fs.cwd()
'/'
>>> fs.ls()
[]
>>> fs.write_file("test.txt", "hello, world!")
>>> fs.ls()
['test.txt']
>>> fs.ls(show_details=True)
['{"name": "test.txt", "ctime": "Feb 21 2022 23:16:34", "mtime": "Feb 21 2022 23:16:34", "atime": "Feb 21 2022 23:16:34", "links": 1}']
>>> fs.read_file("test.txt")
'hello, world!'
>>> fs.mkdir("cat-pictures")
>>> fs.ls()
['test.txt', 'cat-pictures']
>>> fs.cd("cat-pictures")
>>> fs.cwd()
'/cat-pictures'
>>> fs.cd("..")
>>> fs.rm("test.txt")
>>> fs.ls()
['cat-pictures']
>>> fs.mv("cat-pictures", "cat-memes")
>>> fs.ls()
['cat-memes']
>>> fs.ln("cat-memes", "best-memes")
>>> fs.ls()
['cat-memes', 'best-memes']
>>> fs.rm('cat-memes', recursive=True)
>>> fs.ls()
['best-memes']
```
