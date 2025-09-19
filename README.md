# fsel
```fsel``` (stands for Folder Select) is a Text User Interface (TUI) program to easily navigate the folders of your project(s) in the terminal.

Conceptually, UI of ```fsel``` is similar to Mac's ```finder``` app: selected folders are shown next to each other.
![fsel navigation](https://raw.githubusercontent.com/semicontinuity/fsel/main/fsel.gif "Navigation")


* ```fsel``` is intended for navigation inside your project, it is not intended to navigate the entire file system.
* ```fsel``` auto-detects the root folder of your project: if there is a directory ```.git```, or ```.svn```, then it's the root of your project.
* ```fsel``` memorizes history of your navigation in the project; later it, suggests folders that you have recently visited.


## Installation
* Run ``` python3 setup.py install``` or ``` python3 setup.py install --user```.
* Run ```source key_bindings.bash``` to add key bindings.
* Put ```source /path/to/key_bindings.bash``` to your ```.bashrc``` to persist these key bindings.


## Key bindings for command-line

### Executables
* ```Ctrl-Alt-Space```: run selected executable
* ```Alt-Z```: run one of the recent executables
* ```Alt-Shift-Z```: insert the full path of one of the recent executables into command line
  
### Change directory
* ```Alt-X```: cd into the selected directory
* ```Alt-Shift-X```: cd into a recent directory
  
### Insert file path into command line
* ```Ctrl-]```: insert the relative file path into command line
* ```Alt-]```: insert the full file path into command line
* ```Alt-Shift-]```: insert the relative file path from the root into command line
* ```Ctrl-Alt-]```: insert the full path of  one of the recent files into command line

### Insert folder path into command line
* ```Ctrl-G```: insert the relative path to folder into command line
* ```Alt-G```: insert the full path to the folder into command line
* ```Alt-Shift-G```: insert the relative path to folder from root into command line
* ```Ctrl-Alt-G```: insert the full path of  one of the recent folders into command line

## Key reference
* ```Escape```: exit
* ```Enter```: navigate (cd) to the currently selected folder
* ```Up```, ```Down```: select another sub-folder in the selected folder
* ```Left```, ```Right```: select sub-folder or parent folder
* ```Home```, ```End```: select folder at the beginning or the end of the current path
* ```Tab```: navigate (cd) to the end of the current path
* ```Shift-Tab```: navigate (cd) to the root folder
* Type to search for a file or folder
* ```Alt-Up```, ```Alt-Down```: go to the previous/next search match

Type to search in the currently selected folder. If there are matches, then
* ```Alt+Up```: go to the previous match
* ```Alt+Down```: go to the next match
* ```Alt+PageUp```: go to the first match
* ```Alt+PageDown```: go to the last match
* ```Backspace```: erase last character of the search term
* ```Delete```: cancel search

## Configuration/history file
The file ```~/.fsel_history``` contains the list or project roots and keeps navigation history for the folder under these roots.

It has the following format:
```(json)
{
  "/path/to/root/of/project1": { ... },
  "/path/to/root/of/project2": { ... }
}
```
Add the roots of your projects to this file to keep navigation history for them.


# Extended folder attributes

* `user.description` - if set (`setfattr -n user.description -v "The description" .`), the description is displayed next to the folder name.
* `user.deleted` - if set (`setfattr -n user.deleted -v "true" .`), the folder is displayed with strike-thru font.
