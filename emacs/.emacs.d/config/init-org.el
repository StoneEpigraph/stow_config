;; org-bullets  -*- lexical-binding: t; -*-
;; 美化org的标题展示
;;; Code:
(use-package org-bullets)
(add-hook 'org-mode-hook 'org-bullets-mode)
;; org-agenda
;; (setq org-agenda-fies '("~/resource/nutStore/我的坚果云/todo.org"))
(setq org-agenda-files '("~/resource/dailyNotes/todolist.org" "~/resource/dailyNotes/daily/"))
;; orgmode truncate lines
(add-hook 'org-mode-hook
  (lambda () (setq truncate-lines nil)))
;; 修改日程状态字段。
;; 如果想在插入的时候插入时间及当前状态之前的状态需要添加!
;; 如果想在改变状态的时候输入说明需要添加@
;; 如果需要同时添加@和!需要在两个特殊字符之前添加/
(setq org-todo-keywords
      '((sequence "TODO(t)" "PROG(p)" "WAITING(w@/!)" "|"  "DONE(d!)")
	(sequence "MAYBE(m)" "BUG(b)" "|" "FIXED(f)" "CANCELED(c@/!)")))

(setq org-todo-keyword-faces
      '(("PROG" . (:foreground "yellow" :weight bold))))

(custom-set-variables
  '(org-agenda-files (quote ("~/resource/dailyNotes")))
  )
  ;; Customized view for the daily workflow. (Command: ", a n")
  (setq org-agenda-custom-commands
        '(("n" "My Weekly Agenda"
           ((agenda "" nil)
	    (todo "PROG" nil)
            (todo "TODO" nil))
           nil)))

(defun org-summary-todo (n-done n-not-done)
     "Switch entry to DONE when all subentries are done, to TODO otherwise."
   (let (org-log-done org-log-states)   ; turn off logging
	(org-todo (if (= n-not-done 0) "DONE" "TODO"))))
(add-hook 'org-after-todo-statistics-hook 'org-summary-todo)
(add-hook 'org-mode-hook (lambda () (setq truncate-lines t)))

;; org-download
(use-package org-download
  :ensure t
  :bind ("C-x y" . org-download-screenshot)
  :config
  (add-hook 'dired-mode-hook 'org-download-enable)
)

(setq-default org-download-image-dir "./img")

;; init org-indent-mode
;; emacs28.1之后无效,使用add-hook方式启动
;; (org-indent-mode t)
;; org-roam v2
(use-package org-roam
  :ensure t
  :custom
  (org-roam-directory (file-truename "/home/stone/resource/dailyNotes/"))
  :bind (("C-c n l" . org-roam-buffer-toggle)
	 ("C-c n f" . org-roam-node-find)
	 ("C-c n g" . org-roam-graph)
	 ("C-c n i" . org-roam-node-insert)
	 ("C-c n c" . org-roam-capture)
	 ;; Dailies
	 ("C-c n j" . org-roam-dailies-capture-today))
  :bind-keymap
  ("C-c n d" . org-roam-dailies-map)
  :config
  ;;  (org-roam-db-autosync-mode)
  ;; If using org-roam-protocol
  (require 'org-roam-protocol)
  (require 'org-roam-dailies)
  (org-roam-db-autosync-mode))
;; org-roam-ui
(setq org-roam-v2-ack t)
(use-package org-roam-ui)
(setq org-roam-directory "/home/stone/resource/dailyNotes/")
;;	(add-to-list 'load-path "~/.emacs.d/private/org-roam-ui")
;;	(load-library "org-roam-ui")
;; start or-roam-ui on start emacs
;;(org-roam-ui-mode t)
;;	(setq org-roam-ui-open-on-start nil)

;; (require 'org-roam-protocol)

;;添加一些快捷键
;; (add-hook
;;  'org-mode-hook
;;  (progn
;;    (global-set-key (kbd "C-c C-x h") 'org-toggle-item)))
;;; image paste
;;; (setq-default org-download-image-dir "~/Pictures/foo")

;; 启动缩进
(add-hook 'org-mode-hook 'org-indent-mode)
;; 更新org-mode的字体设置
;;	(let ((emacs-font-size 14)
;;	      (emacs-font-name "WenQuanYi Micro Hei Mono"))
;;	  (set-frame-font (format "%s-%s" (eval emacs-font-name) (eval emacs-font-size)))
;;	  (set-fontset-font (frame-parameter nil 'font) 'unicode (eval emacs-font-name)))
;;
;;        (with-eval-after-load 'org
;;	  (defun org-buffer-face-mode-variable ()
;;	    (interactive)
;;	    (make-face 'width-font-face)
;;	    (set-face-attribute 'width-font-face nil :font "等距更纱黑体 SC 15")
;;	    (setq buffer-face-mode-face 'width-font-face)
;;	    (buffer-face-mode))
;;	  (add-hook 'org-mode-hook 'org-buffer-face-mode-variable))
;;
;; 更新org-mode字体
;; set English font
;; use <s to generate code template
;; (use-package org-tempo)

;; org contrib
;;(use-package org-contrib
;;  :pin nongnu
;;  )

;; org-capture
(setq org-capture-templates
      '(("t" "TODO" entry (file+headline "~/resource/dailyNotes/ntodolist.org" "gtd")
	 "* TODO [#B] %? %i\n SCHEDULED: %T"
	 :empty-lines 1)))
(global-set-key (kbd "C-c r") 'org-capture)
;; config org-capture windows open position
(add-to-list 'display-buffer-alist
  '("Org Select"
    (display-buffer-in-side-window)
    (window-height . 0.4)
    (side . bottom))
  '("CAPTURE-*"
    (display-buffer-in-side-window)
    (window-width . 0.3)
    (side . right))
  '("Org Agenda"
    (display-buffer-in-direction)
    (window-width . 0.3)
    (direction . right)))
;; org-superstart-mode
;;(require 'org-superstar)
;; (add-hook 'org-mode-hook (lambda () (org-superstar-mode 1)))

;; 生成hugo头
;; #+HUGO_BASE_DIR: ~/resource/dailyNotes/hugo/stoneepigraph.github.io/
;; #+HUGO_SECTION: posts/
;; #+HUGO_CATEGORIES: "book" "read" "soft skills"
;; #+HUGO_TAGS: "book" "read" "soft skills"
;; #+DRAFT: false
;; #+DATE: 2022-11-25
;; #+title: 代码之外的生存指南
(defun gen_hugo_title ()
  "generate hugo title content"
  (interactive)
  (progn
    (goto-char (point-max))
    (insert "#+HUGO_BASE_DIR: ~/resource/dailyNotes/hugo/stoneepigraph.github.io/\n")
    (insert "#+HUGO_SECTION: posts/\n")
    (insert "#+HUGO_CATEGORIES: \n")
    (insert "#+HUGO_TAGS: \n")
    (insert "#+DRAFT: false\n")
    (insert "#+DATE: \n")
    (insert "#+TITLE: \n")
    ))

(defun new-org ()
  "generate new org file."
  (interactive)
  (org-id-get-create)
  (gen_hugo_title))
(provide 'init-org)
