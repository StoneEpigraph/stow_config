;;; hugo config

(use-package ox-hugo
  :ensure t
  :pin melpa
  :after ox)

(defun sm-create-org-file ()
  "create a org file generate template file header."
  (interactive)
  (org-id-get-create)
  (goto-char (point-max))
  (insert "#+HUGO_CATEGORIES: \n" )
  (insert "#+HUGO_BASE_DIR: ~/resource/dailyNote/hugo/stoneepigraph.github.io/\n" )
  (insert "#+DRAFT: false\n")
  (insert "#+DATE: " (format-time-string "%Y-%m-%d") "\n")
 (insert "#+TITLE: \n" )
 (previous-line)
 (end-of-line)
 )

(provide 'init-hugo)
;;; end file
