;;; Package --- summary
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

(add-to-list 'load-path "/home/stone/.emacs.d/private/lsp-bridge")
(require 'yasnippet)
(yas-global-mode)
(require 'lsp-bridge)
(global-lsp-bridge-mode)


(provide 'init-lsp)
;;; init-lsp.el ends here
