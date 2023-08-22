#!/bin/bash

__fsel_cat__() {
  local file
  file=$(python3 -m fsel.app -r -f "$@") && printf "${PAGER:-less} $file"
}

__fsel_edit__() {
  local file
  file=$(python3 -m fsel.app -r -f "$@") && printf "${EDITOR:-nano} $file"
}

__fsel_cd__() {
  local args=("$@")
  while true; do
    local dir
    local res
    dir=$(python3 -m fsel.app "${args[@]}")
    res=$?

    # On Alt+Enter, continue with the link target
    [[ $res == 80 ]] && args=($(realpath "$dir")) && continue
    # On Alt+Home, continue with the parent of the returned root folder
    [[ $res == 95 ]] && args=($(dirname "$dir")) && continue

    [[ $res == 14 ]] && printf 'rm -rf %q' "$dir"
    [[ $res == 0 ]] && printf 'cd %q' "$dir"
    break
  done
}

__fsel_run__() {
  local file
  file=$(python3 -m fsel.app -f -x "$@") && printf '%q' "$file"
}

__fsel_widget__() {
  local selected
  selected=$(python3 -m fsel.app "$@")
  READLINE_LINE="${READLINE_LINE:0:$READLINE_POINT}$selected${READLINE_LINE:$READLINE_POINT}"
  READLINE_POINT=$(( READLINE_POINT + ${#selected} ))
}


# Alt+Q: view selected file
bind '"\eq": "$(__fsel_cat__)\e\C-e\C-m"'

# Ctrl+Q: view selected file (including dot-files)
bind '"\C-Q": "$(__fsel_cat__ -a)\e\C-e\C-m"'

# Alt+Shift+Q: edit selected file
bind '"\eQ": "$(__fsel_edit__)\e\C-e\C-m"'

# Ctrl+Alt+Shift+Q: edit selected file (including dot-files)
bind '"\e\C-Q": "$(__fsel_edit__ -a)\e\C-e\C-m"'


# CTRL-ALT-Space: run selected executable
bind '"\e\C- ": "$(__fsel_run__)\e\C-e\C-m"'

# ALT-Z: run one of the recent executables
bind '"\ez": "$(__fsel_run__ -e)\e\C-e\C-m"'

# ALT-SHIFT-Z: insert the full path of one of the recent executables into command line
bind -x '"\eZ": "__fsel_widget__ -e -f -x"'


# ALT-X or Alt+End: cd into the selected directory
#bind '"\ex": "$(__fsel_cd__)\C-x\C-x\C-e\C-x\C-r\C-m\C-w"'
bind '"\ex": "$(__fsel_cd__)\e\C-e\C-m"'
bind '"\e[1;3F": "$(__fsel_cd__)\e\C-e\C-m"'

# ALT-SHIFT-X or Alt+Home: cd into one of the recent directories
bind '"\eX": "$(__fsel_cd__ -e)\e\C-e\C-m"'
bind '"\e[1;3H": "$(__fsel_cd__ -e)\e\C-e\C-m"'

# CTRL-]: insert the relative file path into command line
bind -x '"\C-]": "__fsel_widget__ -r -f"'

# ALT-]: insert the full file path into command line
bind -x '"\e]": "__fsel_widget__ -f"'

# ALT-SHIFT-]: insert the relative file path from root into command line
bind -x '"\e}": "__fsel_widget__ -R -f"'

# CTRL-ALT-]: insert the full path of one of the recent files into command line
bind -x '"\e\C-]": "__fsel_widget__ -e -f"'


# CTRL-G: insert the relative path to folder into command line
bind -x '"\C-g": "__fsel_widget__ -r"'

# ALT-G: insert the full path to folder into command line
bind -x '"\eg": "__fsel_widget__"'

# ALT-SHIFT-G: insert the relative path to folder from root into command line
bind -x '"\eG": "__fsel_widget__ -R"'

# CTRL-ALT-G: insert the full path of one of the recent folders into command line
bind -x '"\e\C-G": "__fsel_widget__ -e"'
