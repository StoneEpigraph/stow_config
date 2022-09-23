	;; org-bullets
	;; 美化org的标题展示
	(use-package org-bullets)
	(add-hook 'org-mode-hook 'org-bullets-mode)
	;; org-agenda
	;; (setq org-agenda-fies '("~/resource/nutStore/我的坚果云/todo.org"))
	;; orgmode truncate lines
	(add-hook 'org-mode-hook
		  (lambda () (setq truncate-lines nil)))
	;; 修改日程状态字段。
	;; 如果想在插入的时候插入时间及当前状态之前的状态需要添加!
	;; 如果想在改变状态的时候输入说明需要添加@
	;; 如果需要同时添加@和!需要在两个特殊字符之前添加/
	(setq org-todo-keywords
	      '((sequence "TODO(t)" "BUG(b)" "WAITING(w@/!)" "|" "FIXED(f)")
		(sequence "MAYBE(m)" "|" "DONE(d!)" "CONTACT(l)" "CANCELED(c@/!)")))
	(custom-set-variables
	  '(org-agenda-files (quote ("~/resource/dailyNotes/todo.org")))
	)

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
	(setq-default org-download-image-dir "/home/stone/resource/dailyNotes/resources/pic/")

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
	  :config
	  (org-roam-db-autosync-mode)
	  ;; If using org-roam-protocol
	  (require 'org-roam-protocol))
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
	(use-package org-download
	  :ensure t
	  :config
	  ;; Drag and drop to Dired
	  (add-hook 'dired-mode-hook 'org-download-enable)
	  )

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
	(provide 'init-org)
