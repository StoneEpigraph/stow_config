;;; package: --- Summary
;;; commentary:
;;; init-package.el this is my installed package config
;;; Code:
;; swiper
(use-package swiper
  :config
  (progn
    (global-set-key (kbd "C-s") 'swiper)))
; (use-package counsel)

;; package magit
;;(use-package magit			;
;;  :config
;;  (progn
;;    (global-set-key (kbd "C-x g") 'magit-status)))
;; package counsel-web
;; (global-set-key (kbd "M-x") 'counsel-M-x)

;; window change
(use-package window-numbering)
(window-numbering-mode 1)


;; company
(use-package company
  :config
  (add-hook 'after-init-hook 'global-company-mode)
  (setq company-minimum-prefix-length 1)
  (setq company-idle-delay 0))

;; flycheck
(use-package flycheck
  :init
  (global-flycheck-mode 1))

;; magit


;; treemacs
(use-package treemacs
  :ensure t
  :defer t
  :init
  (with-eval-after-load 'winum
    (define-key winum-keymap (kbd "M-0") #'treemacs-select-window))
  :config
  (progn
    (setq treemacs-collapse-dirs                 (if treemacs-python-executable 3 0)
          treemacs-deferred-git-apply-delay      0.5
          treemacs-directory-name-transformer    #'identity
          treemacs-display-in-side-window        t
          treemacs-eldoc-display                 t
          treemacs-file-event-delay              5000
          treemacs-file-extension-regex          treemacs-last-period-regex-value
          treemacs-file-follow-delay             0.2
          treemacs-file-name-transformer         #'identity
          treemacs-follow-after-init             t
          treemacs-git-command-pipe              ""
          treemacs-goto-tag-strategy             'refetch-index
          treemacs-indentation                   2
          treemacs-indentation-string            " "
          treemacs-is-never-other-window         nil
          treemacs-max-git-entries               5000
          treemacs-missing-project-action        'ask
          treemacs-move-forward-on-expand        nil
          treemacs-no-png-images                 nil
          treemacs-no-delete-other-windows       t
          treemacs-project-follow-cleanup        nil
          treemacs-persist-file                  (expand-file-name ".cache/treemacs-persist" user-emacs-directory)
          treemacs-position                      'left
          treemacs-recenter-distance             0.1
          treemacs-recenter-after-file-follow    nil
          treemacs-recenter-after-tag-follow     nil
          treemacs-recenter-after-project-jump   'always
          treemacs-recenter-after-project-expand 'on-distance
          treemacs-show-cursor                   nil
          treemacs-show-hidden-files             t
          treemacs-silent-filewatch              nil
          treemacs-silent-refresh                nil
          treemacs-sorting                       'alphabetic-asc
          treemacs-space-between-root-nodes      t
          treemacs-tag-follow-cleanup            t
          treemacs-tag-follow-delay              1.5
          treemacs-user-mode-line-format         nil
          treemacs-user-header-line-format       nil
          treemacs-width                         35
          treemacs-workspace-switch-cleanup      nil)

    ;; The default width and height of the icons is 22 pixels. If you are
    ;; using a Hi-DPI display, uncomment this to double the icon size.
    ;;(treemacs-resize-icons 44)

    (treemacs-follow-mode t)
    (treemacs-filewatch-mode t)
    (treemacs-fringe-indicator-mode t)
    (pcase (cons (not (null (executable-find "git")))
                 (not (null treemacs-python-executable)))
      (`(t . t)
       (treemacs-git-mode 'deferred))
      (`(t . _)
       (treemacs-git-mode 'simple))))
  :bind
  (:map global-map
        ("M-0"       . treemacs-select-window)
        ("C-x t 1"   . treemacs-delete-other-windows)
        ("C-x t t"   . treemacs)
        ("C-x t B"   . treemacs-bookmark)
        ("C-x t C-t" . treemacs-find-file)
        ("C-x t M-t" . treemacs-find-tag)))

(use-package treemacs-projectile
  :after treemacs projectile
  :ensure t)

(use-package treemacs-icons-dired
  :after treemacs dired
  :ensure t
  :config (treemacs-icons-dired-mode))

;;(use-package treemacs-magit
;;  :after treemacs magit
;;  :ensure t)

(use-package treemacs-persp ;;treemacs-persective if you use perspective.el vs. persp-mode
  :after treemacs persp-mode ;;or perspective vs. persp-mode
  :ensure t
  :config (treemacs-set-scope-type 'Perspectives))
(treemacs)

;; recentf
(recentf-mode 1)
(global-set-key (kbd "C-x C-r") 'recentf-open-files)

;; ace-window
(use-package ace-window
  :config
  (global-set-key (kbd "M-o") 'ace-window))

;;  smartparents
(use-package smartparens
  :defer nil
  :config
  (smartparens-mode t))
(add-hook 'prog-mode-hook #'smartparens-mode)
(smartparens-global-mode t)

;; rainbow
(use-package rainbow-delimiters
  :defer nil
  :config
  (rainbow-delimiters-mode t))
;;   (add-hook 'prog-mode-hook #'rainbow-delimiters-mode)
(add-hook 'prog-mode-hook #'rainbow-delimiters-mode)

;; ident-guide
(use-package indent-guide
  :config
  (indent-guide-global-mode t))

;; optional if you want which-key integration
(use-package which-key
  :defer nil
  :config
  (which-key-mode 1))

;; multiple cursor
(use-package multiple-cursors
  :config
  (global-set-key (kbd "C-S-c C-S-c") 'mc/edit-lines)
  (global-set-key (kbd "C->") 'mc/mark-next-like-this)
  (global-set-key (kbd "C-<") 'mc/mark-previous-like-this)
  (global-set-key (kbd "C-c C-<") 'mc/mark-all-like-this))

;; dict
(use-package youdao-dictionary
  :config
  (setq url-automatic-caching t)
  (global-set-key (kbd "C-c y") 'youdao-dictionary-search-at-point+))

;; multiple-cursors
(use-package multiple-cursors
  :bind (("C->" . mc/mark-next-like-this)
	 ("C-<" . mc/mark-previous-like-this)
	 ("C-M-<" . mc/skip-to-next-like-this)
	 ("C-M-<" . mc/skip-to-previous-like-this)
	 ("C-c C-<" . mc/mark-all-like-this)
	 ("C-S-<mouse-1>" . mc/add-cursor-on-click)
	 :map mc/keymap
	 ("C-|" . mc/vertical-align-with-space))
  :config
  (setq mc/insert-numbers-default 1))

;;
(use-package simple-httpd)
(use-package websocket)

;; keyfreq
(use-package keyfreq)
(keyfreq-mode 1)
(keyfreq-autosave-mode 1)

;;; projectile
(use-package projectile
  :ensure t
  :config
  (define-key projectile-mode-map (kbd "s-p") 'projectile-command-map)
  (define-key projectile-mode-map (kbd "C-c p") 'projectile-command-map)
  (projectile-mode +1))
;; show key
(use-package keycast)
;; command company
(use-package vertico
  :config
  )
(vertico-mode t)
;; 
(use-package orderless
  :config
  (setq completion-styles '(orderless)))
;; show comment
(use-package marginalia
  :init
  (marginalia-mode t))
;; act on function
(use-package embark
  :config
  (global-set-key (kbd "C-;") 'embark-act))
;;
(setq prefix-help-command 'embark-prefix-help-command)
;; file search
(use-package consult
  :config
  (global-set-key (kbd "C-s") 'consult-line)
  ;;显示可切换的buffer和最近打开的文件
  (global-set-key (kbd "C-x b") 'consult-buffer))

;; awesome-tab
(use-package awesome-tab
  :load-path "~/.emacs.d/private/awesome-tab"
  :config
  (awesome-tab-mode t))
(defun awesome-tab-buffer-groups ()
  "`awesome-tab-buffer-groups' control buffers' group rules.

Group awesome-tab with mode if buffer is derived from `eshell-mode' `emacs-lisp-mode' `dired-mode' `org-mode' `magit-mode'.
All buffer name start with * will group to \"Emacs\".
Other buffer group by `awesome-tab-get-group-name' with project name."
  (list
   (cond
    ((or (string-equal "*" (substring (buffer-name) 0 1))
;;         (memq major-mode '(magit-process-mode
;;                            magit-status-mode
;;                            magit-diff-mode
;;                            magit-log-mode
;;                            magit-file-mode
;;                            magit-blob-mode
;;                            magit-blame-mode
;;                            ))
	 )
     "Emacs")
    ((derived-mode-p 'eshell-mode)
     "EShell")
    ((derived-mode-p 'emacs-lisp-mode)
     "Elisp")
    ((derived-mode-p 'dired-mode)
     "Dired")
    ((memq major-mode '(org-mode org-agenda-mode diary-mode))
     "OrgMode")
    (t
     (awesome-tab-get-group-name (current-buffer))))))
;; search
(use-package embark-consult)
(use-package wgrep
  :config
  (setq wgrep-auto-save-buffer t))
;; elfeed
(use-package elfeed)
;; 代码块
(require 'org-tempo)

(provide 'init-package)
;;; init-package.el ends here

