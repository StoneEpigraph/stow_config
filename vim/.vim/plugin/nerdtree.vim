nnoremap <silent> <C-n> :NERDTreeToggle<Enter>
" Exit Vim if NERDTree is the only window remaining in the only tab.
autocmd BufEnter * if tabpagenr('$') == 1 && winnr('$') == 1 && exists('b:NERDTree') && b:NERDTree.isTabTree() | quit | endif

let NERDTreeMinimalUI = 1
let NERDTreeShowHidden = 1
