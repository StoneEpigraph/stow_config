;;; package --- Commentary
;;; Commentary:
;;; Code:
;; org config
(global-set-key (kbd "C-c a") 'org-agenda)
;; org-downloaded
;; (global-set-key (kbd "C-x p") 'org-download-clipboard)
;; compare
(global-set-key (kbd "C-c c") 'compare-windows)
;; find
(global-set-key (kbd "C-h C-f") 'find-function)
(global-set-key (kbd "C-h C-v") 'find-variable)
(global-set-key (kbd "C-h C-k") 'find-function-on-key)
;; 全局搜索文本
(global-set-key (kbd "C-c C-s") 'consult-ripgrep)

(provide 'init-kbd)
;;; init-kbd ends here
