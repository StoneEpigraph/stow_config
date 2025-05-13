;;; Package --- summary  -*- lexical-binding: t; -*-
;;; Commentary;
;; set open file mode
;;; code:
(use-package web-mode)
(add-to-list 'auto-mode-alist '("\\.vue\\'" . web-mode))
(add-to-list 'auto-mode-alist '("\\.js\\'" . web-mode))
(setq web-mode-markup-indent-offset 2)
(setq web-mode-css-indent-offset 2)
(setq web-mode-code-indent-offset 2)
(setq server-mode t)
(global-reveal-mode t)
(use-package rust-mode)
(provide 'init-mode)
