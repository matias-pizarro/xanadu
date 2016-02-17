# If not running interactively, don't do anything
case $- in
    *i*) ;;
      *) return;;
esac

# don't put duplicate lines or lines starting with space in the history.
# See bash(1) for more options
export HISTCONTROL=ignoreboth

# append to the history file, don't overwrite it
shopt -s histappend

# for setting history length see HISTSIZE and HISTFILESIZE in bash(1)
export HISTSIZE=9999
export HISTFILESIZE=9999

if [ `uname -o` = 'FreeBSD' ]; then
    work_os='FreeBSD';
else
    work_os='GNU/Linux';
fi

if [ "${work_os}" = 'FreeBSD' ]; then
    if [ -f ~/.bsd_bash_aliases ]; then
        . ~/.bsd_bash_aliases
    fi
else
    if [ -f ~/.gnu_bash_aliases ]; then
        . ~/.gnu_bash_aliases
    fi
fi

if [ -d ~/.bash_aliases ]; then
    . ~/.bash_aliases/*
fi

# check the window size after each command and, if necessary,
# update the values of LINES and COLUMNS.
shopt -s checkwinsize

# If set, the pattern "**" used in a pathname expansion context will
# match all files and zero or more directories and subdirectories.
#shopt -s globstar

# A righteous umask
umask 0002

export PATH=/sbin:/bin:/usr/sbin:/usr/bin:/usr/games:/usr/local/sbin:/usr/local/bin:$HOME/bin:/usr/local/mysql/bin
# set path = (/sbin /bin /usr/sbin /usr/bin /usr/games /usr/local/sbin /usr/local/bin $HOME/bin /usr/local/mysql/bin  $HOME/scripts)
bind '"\e[A"':history-search-backward # Use up and down arrow to search
bind '"\e[B"':history-search-forward  # the history. Invaluable!
bind 'C-b':backward-word
bind 'C-f':forward-word
set completion-ignore-case On
set completion-query-items 999
set show-all-if-ambiguous On

export PS1="\u@\h:\w \\$ "
export CLICOLOR=1                     # Use colors (if possible)
export LSCOLORS=Exfxcxdxbxegedabageced

if [ -f ~/git-completion.bash ]; then
    source ~/git-completion.bash
fi

if [ -f ~/.bashrc_local ]; then
    source ~/.bashrc_local
fi
