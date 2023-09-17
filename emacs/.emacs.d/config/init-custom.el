;; init-custom
;;; code
;; put current line to top of window
(defun line-to-top ()
  "move current line to top of window."
  (interactive)
  (recenter 0))

(global-set-key "\C-xt" 'line-to-top)

;; switch-to-buffer advice
(defadvice switch-to-buffer (before existing-buffer
				    activate compile)
  "when interactive, switch to existing buffers only, 
unless give a prefix argument."
  (interactive
   (list (read-buffer "Switch to buffer:"
		      (other-buffer)
		      (null current-prefix-arg)))))
;; reverse formatting text
(defun sm-re-formatting ()
  "reverse formatting"
  (interactive)
  (goto-char (point-min))
  (while (re-search-forward "[\n\t ]+")
    (replace-match " "))
  )

;; no backup file 
(setq make-backup-files nil)
;; 在输入内容后删除选中的内容
(delete-selection-mode t)

;; 在其它编辑器编辑文件后Emacs会自动更新
(global-auto-revert-mode 1)
;; 关闭自动产生的保存文件
(setq auto-save-default nil)
;; 关闭错误提示音
;; (setq ring-bell-function 'ignore)
;; 将yes替换成y
(fset 'gnus-yes-or-no-p 'y-or-n-p)

;; 不生产backup文件
(setq make-backup-files nil)

(provide 'init-custom)






