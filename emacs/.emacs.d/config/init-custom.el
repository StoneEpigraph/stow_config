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

(provide 'init-custom)






