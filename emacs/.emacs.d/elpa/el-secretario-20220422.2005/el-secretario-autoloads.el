;;; el-secretario-autoloads.el --- automatically extracted autoloads  -*- lexical-binding: t -*-
;;
;;; Code:

(add-to-list 'load-path (directory-file-name
                         (or (file-name-directory #$) (car load-path))))


;;;### (autoloads nil "el-secretario" "el-secretario.el" (0 0 0 0))
;;; Generated autoloads from el-secretario.el

(autoload 'el-secretario-start-session "el-secretario" "\
Start session specified by SOURCE-LIST.

SOURCE-LIST should be a list of newly instantiated sources, or
SOURCE-LIST is a function that returns a list of newly instantiated sources.

\(fn SOURCE-LIST)" nil nil)

(register-definition-prefixes "el-secretario" '("el-secretario-" "hercules--"))

;;;***

;;;### (autoloads nil "el-secretario-function" "el-secretario-function.el"
;;;;;;  (0 0 0 0))
;;; Generated autoloads from el-secretario-function.el

(eieio-defclass-autoload 'el-secretario-function-source '(el-secretario-source) "el-secretario-function" nil)

;;;***

;;;### (autoloads nil "el-secretario-message" "el-secretario-message.el"
;;;;;;  (0 0 0 0))
;;; Generated autoloads from el-secretario-message.el

(autoload 'el-secretario-message-display-message-prompt "el-secretario-message" "\
Display MESSAGE in a dedicated buffer.
If KEYMAP is nil, use `el-secretario-message-message-keymap'.

If KEYMAP is non-nil, use that as prompt.  Keep in mind that it
should probably have one keybinding that calls
`el-secretario-message--back-to-pre-message'

\(fn MESSAGE &optional KEYMAP)" nil nil)

(register-definition-prefixes "el-secretario-message" '("el-secretario-message-"))

;;;***

;;;### (autoloads nil "el-secretario-source" "el-secretario-source.el"
;;;;;;  (0 0 0 0))
;;; Generated autoloads from el-secretario-source.el

(register-definition-prefixes "el-secretario-source" '("el-secretario-source"))

;;;***

;;;### (autoloads nil nil ("el-secretario-pkg.el") (0 0 0 0))

;;;***

;; Local Variables:
;; version-control: never
;; no-byte-compile: t
;; no-update-autoloads: t
;; coding: utf-8
;; End:
;;; el-secretario-autoloads.el ends here
