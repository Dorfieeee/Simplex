# Simplex
Simplex is Python 3 command-line program for effortless processing of your data.

### Installation
Simplex requires [Python](https://www.python.org/downloads/) v3.8+ to run installed on your OS.
Older versions could not work as expected.

- 1. Install Python on your OS
- 2. Download this code repository by clicking on the green 'Code' button and selecting Zip file.
- 3. Unzip and save the folder somewhere you like.
- 4. Open your OS command line/terminal and go to Simplex directory.* [Help]
- 5. For the first time, run `$ python simplex.py build`, if this fails, install all dependencies manually listed bellow
- 6. Ready to go

### Usage
The easiest way is to open your terminal and go to Simplex directory.
```sh
$ python simplex.py [options] command
```
For all options and commands, type
```sh
$ python simplex.py --help
```

This program can convert your .ocw and .P00 files into .csv + graphs.
The only thing you need to tell the program is where your files are and what to do with them.
```sh
$ python simplex.py [what type? -f for file or -i for directory] [where? path] [what to do? command] 
```

Let's say I want to convert all files with .ocw extension in one directory, so I will use -i option for --input and type where the directory is and tell what to do with it by using jvc command(Current–voltage characteristic)
```sh
$ python simplex.py -i myFilesDirectory jvc 
```
Will tell the program to select all files with .ocw extension in myFilesDirectory and generate .csv + graps

You can also select one or multiple files to work with by using -f / --file option eg.
```sh
$ python simplex.py -f myFile.ocw jvc
```
or for multiple files
```sh
$ python simplex.py -f myFile.ocw -f mySecondFile.ocw jvc
```

### Dependencies

```sh
$ python -m pip install -U pip
```

* [Click] - Python CLI

```sh
$ python -m pip install click==7.1.2
```

* [Matplotlib] - Matplotlib is a comprehensive library for creating static,
                 animated, and interactive visualizations in Python.
```sh
$ python -m pip install matplotlib==3.3.2
```

### Other
If you find any problems running this program or you'd like the program to have other functionalities, please, do not hesitate and contact me.

License
----

MIT


**Free Software, Hell Yeah!**

[//]: # (These are reference links used in the body of this note and get stripped out when the markdown processor does its job. There is no need to format nicely because it shouldn't be seen. Thanks SO - http://stackoverflow.com/questions/4823468/store-comments-in-markdown-syntax)


   [Python 3]: <https://www.python.org>
   [Matplotlib]: <https://matplotlib.org/>
   [Click]: <https://palletsprojects.com/p/click/>
   [Help]: <https://linuxize.com/post/linux-cd-command/>
