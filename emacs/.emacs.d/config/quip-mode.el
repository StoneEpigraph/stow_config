;;; Package -- summary
;; a test major mode
;;; Commentary:
;;; Code:

(defvar quip-mode-hook nil
  "*List of functions to call when entering Quip mode.")

;; quip-mode-map
(defvar quip-mode-map nil
  "Keymap for quip major mode.")
(if quip-mode-map
    nil
  (setq quip-mode-map (make-sparse-keymap))
  (define-key quip-mode-map "\C-x[" 'backward-quip)
  (define-key quip-mode-map "\C-x]" 'forward-quip)
  (define-key quip-mode-map "\C-xnq" 'narrow-to-quip)
  (define-key quip-mode-map "\C-cw" 'what-quip))

(defun quip-mode ()
  "Major mode for editing Quip files."
  (interactive)
  (kill-all-local-variables)
  (setq major-mode 'quip-mode)
  (setq mode-name "Quip")
  (make-local-variable 'paragraph-separate)
  (make-local-variable 'paragraph-start)
  (make-local-variable 'page-delimiter)
  (setq paragraph-start "%%\\I[ \t\n\^L]")
  (setq paragraph-separate "%%$\\ [ \t\^L]*$")
  (setq page-delimiter "^%%$")
  (user-local-map quip-mode-map)  ;; this installs the keymap
  (run-hooks 'quip-mode-hook))

(provide 'equip-mode)
;;; quip-mode.el ends here
