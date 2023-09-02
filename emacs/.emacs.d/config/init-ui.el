;;; display setting
;;; Code:
(tool-bar-mode -1)
(scroll-bar-mode -1)
(menu-bar-mode -1)
(global-hl-line-mode t)
(setq inhibit-splash-screen t)
(setq initial-scratch-message "\
;;   stone Mind scratch message.
;;   If you want to create a file press C - x C - f\n
")
;; show line number
(use-package emacs
  :config
  (setq display-line-numbers-type 'relative)
  (global-display-line-numbers-mode t))
(fset 'yes-or-no-p 'y-or-n-p)

;; cursor type
(setq-default cursor-type 'bar)

;; theme
(use-package mood-one-theme)
(load-theme 'mood-one t)
;; font setting
(global-set-key (kbd "C-=") 'text-scale-increase)
(global-set-key (kbd "C--") 'text-scale-decrease)
(global-set-key (kbd "C-0") 'text-scale-adjust)

;; 全屏
(add-to-list 'default-frame-alist '(fullscreen . maximized))
;; 指定启动大小
;; (add-to-list 'default-frame-alist '(width . 260))
;; (add-to-list 'default-frame-alist '(height . 60))
;; (add-to-list 'default-frame-alist '(top . 5))
;; (add-to-list 'default-frame-alist '(left . 5))
(set-frame-parameter (selected-frame) 'alpha '(95 80))


(provide 'init-ui)
;;; init-ui.el ends here
