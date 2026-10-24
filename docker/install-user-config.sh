#!/usr/bin/env bash
set -euo pipefail
mkdir -p "$HOME/.tmux/plugins" "$HOME/.vim/bundle"
while read -r repo revision; do
    case "$repo" in
        tmux-plugins/*|nordtheme/*) destination="$HOME/.tmux/plugins/${repo##*/}" ;;
        *) destination="$HOME/.vim/bundle/${repo##*/}" ;;
    esac
    git init -q "$destination"
    git -C "$destination" remote add origin "https://github.com/$repo.git"
    git -C "$destination" fetch -q --depth 1 origin "$revision"
    git -C "$destination" checkout -q --detach FETCH_HEAD
done < /etc/px4-plugins.lock
# Command-T 7.x is the Ruby-powered Vim-compatible release.
command_t_extension="$HOME/.vim/bundle/command-t/ruby/command-t/ext/command-t"
(cd "$command_t_extension" && ruby extconf.rb && make)
tmux -L plugin-check new-session -d -s check
tmux -L plugin-check source-file "$HOME/.tmux.conf"
test -f "$HOME/.tmux/plugins/tmux/nord.tmux"
test -f "$HOME/.tmux/plugins/tmux-sensible/sensible.tmux"
tmux -L plugin-check kill-server
vim -Nu "$HOME/.vimrc" -n -es -c 'qall!'
# Load the native matcher explicitly: a plugin directory alone is not enough.
vim -Nu "$HOME/.vimrc" -n -es -c 'ruby require File.expand_path("~/.vim/bundle/command-t/ruby/command-t/ext/command-t/ext")' -c 'qall!'
