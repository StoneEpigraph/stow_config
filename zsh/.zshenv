if [ -f "$HOME/.cargo/env" ];then
    . "$HOME/.cargo/env"
fi
export FZF_DEFAULT_COMMAND="fd --exclude={.git,.idea,.sass-cache,node_modules,build} --type f"
alias sz="lrzsz-sz"
alias rz="lrzsz-rz"
