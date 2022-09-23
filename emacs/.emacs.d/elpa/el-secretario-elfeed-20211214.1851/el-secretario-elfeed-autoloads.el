;;; el-secretario-elfeed-autoloads.el --- automatically extracted autoloads
;;
;;; Code:

(add-to-list 'load-path (directory-file-name
                         (or (file-name-directory #$) (car load-path))))


;;;### (autoloads nil "el-secretario-elfeed" "el-secretario-elfeed.el"
;;;;;;  (0 0 0 0))
;;; Generated autoloads from el-secretario-elfeed.el

(autoload 'el-secretario-elfeed-make-source "el-secretario-elfeed" "\
Convenience macro for creating a source for elfeed.
QUERY is a normal elfeed query.
KEYMAP is a keymap to use during review of this source

\(fn &optional QUERY KEYMAP)" nil nil)

(if (fboundp 'register-definition-prefixes) (register-definition-prefixes "el-secretario-elfeed" '("el-secretario-elfeed-")))

;;;***

;; Local Variables:
;; version-control: never
;; no-byte-compile: t
;; no-update-autoloads: t
;; coding: utf-8
;; End:
;;; el-secretario-elfeed-autoloads.el ends here
