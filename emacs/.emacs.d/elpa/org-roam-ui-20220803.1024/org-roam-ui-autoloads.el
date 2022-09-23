;;; org-roam-ui-autoloads.el --- automatically extracted autoloads (do not edit)   -*- lexical-binding: t -*-
;; Generated by the `loaddefs-generate' function.

;; This file is part of GNU Emacs.

;;; Code:

(add-to-list 'load-path (directory-file-name
                         (or (file-name-directory #$) (car load-path))))



;;; Generated autoloads from org-roam-ui.el

(defvar org-roam-ui-mode nil "\
Non-nil if org-roam-ui mode is enabled.
See the `org-roam-ui-mode' command
for a description of this minor mode.
Setting this variable directly does not take effect;
either customize it (see the info node `Easy Customization')
or call the function `org-roam-ui-mode'.")
(custom-autoload 'org-roam-ui-mode "org-roam-ui" nil)
(autoload 'org-roam-ui-mode "org-roam-ui" "\
Enable org-roam-ui.

This serves the web-build and API over HTTP.

This is a global minor mode.  If called interactively, toggle the
`org-roam-ui mode' mode.  If the prefix argument is positive,
enable the mode, and if it is zero or negative, disable the mode.

If called from Lisp, toggle the mode if ARG is `toggle'.  Enable
the mode if ARG is nil, omitted, or is a positive number.
Disable the mode if ARG is a negative number.

To check whether the minor mode is enabled in the current buffer,
evaluate `(default-value \\='org-roam-ui-mode)'.

The mode's hook is called both when the mode is enabled and when
it is disabled.

(fn &optional ARG)" t)
(autoload 'org-roam-ui-open "org-roam-ui" "\
Ensure `org-roam-ui' is running, then open the `org-roam-ui' webpage." t)
(autoload 'org-roam-ui-node-zoom "org-roam-ui" "\
Move the view of the graph to current node.
or optionally a node of your choosing.
Optionally takes three arguments:
The ID of the node you want to travel to.
The SPEED in ms it takes to make the transition.
The PADDING around the nodes in the viewport.

(fn &optional ID SPEED PADDING)" t)
(autoload 'org-roam-ui-node-local "org-roam-ui" "\
Open the local graph view of the current node.
Optionally with ID (string), SPEED (number, ms) and PADDING (number, px).

(fn &optional ID SPEED PADDING)" t)
(autoload 'org-roam-ui-sync-theme "org-roam-ui" "\
Sync your current Emacs theme with org-roam-ui." t)
(defvar org-roam-ui-follow-mode nil "\
Non-nil if org-roam-ui-Follow mode is enabled.
See the `org-roam-ui-follow-mode' command
for a description of this minor mode.
Setting this variable directly does not take effect;
either customize it (see the info node `Easy Customization')
or call the function `org-roam-ui-follow-mode'.")
(custom-autoload 'org-roam-ui-follow-mode "org-roam-ui" nil)
(autoload 'org-roam-ui-follow-mode "org-roam-ui" "\
Set whether ORUI should follow your every move in Emacs.

This is a global minor mode.  If called interactively, toggle the
`org-roam-ui-Follow mode' mode.  If the prefix argument is
positive, enable the mode, and if it is zero or negative, disable
the mode.

If called from Lisp, toggle the mode if ARG is `toggle'.  Enable
the mode if ARG is nil, omitted, or is a positive number.
Disable the mode if ARG is a negative number.

To check whether the minor mode is enabled in the current buffer,
evaluate `(default-value \\='org-roam-ui-follow-mode)'.

The mode's hook is called both when the mode is enabled and when
it is disabled.

(fn &optional ARG)" t)
(register-definition-prefixes "org-roam-ui" '("img/:file" "node/:id" "org-roam-ui-"))

;;; End of scraped data

(provide 'org-roam-ui-autoloads)

;; Local Variables:
;; version-control: never
;; no-byte-compile: t
;; no-update-autoloads: t
;; no-native-compile: t
;; coding: utf-8-emacs-unix
;; End:

;;; org-roam-ui-autoloads.el ends here
