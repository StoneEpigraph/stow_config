
;; setting source
(require 'package)
 (setq package-archives '(("gnu"   . "http://mirrors.tuna.tsinghua.edu.cn/elpa/gnu/")
                          ("melpa" . "http://mirrors.tuna.tsinghua.edu.cn/elpa/melpa/")
 			 ("org"   . "http://mirrors.tuna.tsinghua.edu.cn/elpa/org/")))
;;(setq package-archives '(("gnu" . "http://elpa.emacs-china.org/gnu/")
;;			("melpa" . "http://elpa.emacs-china.org/melpa/")
;;			("melpa-stable" . "http://elpa.emacs-china.org/melpa-stable/")
;;			("org" . "http://elpa.emacs-china.org/org/")))
(setq package-load-list '(all))
(package-initialize) ;; You might already have this line
(setq package-enable-at-startup nil)
(unless (package-installed-p 'use-package)
  (package-refresh-contents)
  (package-install 'use-package))
(eval-when-compile
  (require 'use-package))
(setq use-package-always-ensure t)

;; set major mode


(provide 'init-melpa)
