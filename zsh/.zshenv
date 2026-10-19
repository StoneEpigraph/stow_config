if [ -f "$HOME/.cargo/env" ];then
    . "$HOME/.cargo/env"
fi
export FZF_DEFAULT_COMMAND="fd --exclude={.git,.idea,.sass-cache,node_modules,build} --type f"
alias sz="lrzsz-sz"
alias rz="lrzsz-rz"

# uv
export PATH="/home/stone/.local/bin:$PATH"

# ripgrep 只认这个变量，不会自动读 ~/.config/.ripgreprc
export RIPGREP_CONFIG_PATH="$HOME/.config/.ripgreprc"
