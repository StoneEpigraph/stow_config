;; -*- lexical-binding: t; -*-

;; setting source
(require 'package)
(setq package-archives '(
			 ;; ("gnu"   . "http://mirrors.tuna.tsinghua.edu.cn/elpa/gnu/")
                          ("melpa" . "https://melpa.org/packages/")
 			  ;; ("org"   . "http://mirrors.tuna.tsinghua.edu.cn/elpa/)
			  ))
;;(setq package-archives '(("gnu" . "http://elpa.emacs-china.org/gnu/")
;;			("melpa" . "http://elpa.emacs-china.org/melpa/")
;;			("melpa-stable" . "http://elpa.emacs-china.org/melpa-stable/")
;;			("org" . "http://elpa.emacs-china.org/org/")))
;; (add-to-list 'package-archives
;;              '("melpa" . "https://melpa.org/packages/") t)

(setq package-load-list '(all))
(package-initialize) ;; You might already have this line
(package-refresh-contents)
(setq package-enable-at-startup nil)
(unless (package-installed-p 'use-package)
  (package-refresh-contents)
  (package-install 'use-package))
(eval-when-compile
  (require 'use-package))
(setq use-package-always-ensure t)

;; set major mode


(provide 'init-melpa)
