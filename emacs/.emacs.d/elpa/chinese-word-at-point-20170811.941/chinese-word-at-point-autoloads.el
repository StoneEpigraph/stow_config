;;; chinese-word-at-point-autoloads.el --- automatically extracted autoloads (do not edit)   -*- lexical-binding: t -*-
;; Generated by the `loaddefs-generate' function.

;; This file is part of GNU Emacs.

;;; Code:

(add-to-list 'load-path (directory-file-name
                         (or (file-name-directory #$) (car load-path))))



;;; Generated autoloads from chinese-word-at-point.el

(autoload 'chinese-word-at-point "chinese-word-at-point" "\
Return the (most likely) Chinese word at point, or nil if none is found.")
(autoload 'chinese-or-other-word-at-point "chinese-word-at-point" "\
Return the Chinese or other language word at point, or nil if none is found.

Here's \"other\" denotes any language words that Emacs can understand,
i.e. (thing-at-point 'word) can get proper word.")
(register-definition-prefixes "chinese-word-at-point" '("chinese-"))

;;; End of scraped data

(provide 'chinese-word-at-point-autoloads)

;; Local Variables:
;; version-control: never
;; no-byte-compile: t
;; no-update-autoloads: t
;; no-native-compile: t
;; coding: utf-8-emacs-unix
;; End:

;;; chinese-word-at-point-autoloads.el ends here
