;;; Package --- summary  -*- lexical-binding: t; -*-
;;; Commentary:
;; set prefix for lsp-command-keymap (few alternatives - "C-l", "C-c l")
;;; code:
;; (use-package lsp-mode)
;; (use-package lsp-treemacs)
;;(use-package company-lsp
;;  :config
;;  (setq company-idle-delay 0)
;;  (setq company-minimum-prefix-length 1))
;; (use-package lsp-ui)
;; (use-package lsp-python-ms
;;  :ensure t
;;  :init (setq lsp-python-ms-auto-install-server t)
;;  :hook (python-mode . (lambda ()
;;                          (require 'lsp-python-ms)
;;                          (lsp))))  ; or lsp-deferred
;;
;; (lsp-treemacs-sync-mode 1)

;; lsp-bridge

;; (add-to-list 'load-path "/home/stone/.emacs.d/private/lsp-bridge")
;; (require 'yasnippet)
;; (yas-global-mode)
;; (require 'lsp-bridge)
;; (global-lsp-bridge-mode)

(require 'eglot)

(use-package treesit-auto
  :demand
  :init
  (progn
    (setq treesit-font-lock-level 4)
    )
  :config
  (global-treesit-auto-mode))

(use-package yasnippet
  :ensure t)
;; (use-package yasnippet
;;   :ensure t
;;   :hook ((prog-mode . yas-mirror-mode)
;; 	 (org-mode . yas-minor-mode))
;;   :init
;;   :config
;;   (progn
;;     (setq hippie-expand-try-functions-list
;; 	  '(yas/hippie-try-expand
;; 	    try-complete-file-name-partially
;; 	    try-expand-all-abbrevs
;; 	    try-expand-dabbrev
;; 	    try-expand-dabbrev-all-buffers
;; 	    try-expand-dabbrev-from-kill
;; 	    try-complete-lisp-symbol-partially
;; 	    try-complete-lisp-symbol))))

(use-package yasnippet-snippets
  :ensure t
  :after yasnippet)


(provide 'init-lsp)
;;; init-lsp.el ends here
