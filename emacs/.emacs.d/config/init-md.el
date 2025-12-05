
;;; code
;; FLYMD
(use-package flymd
  :ensure t
  :commands (flymd-flyit flymd-browser-refresh)
  :config
  ;; 基本设置
  (setq flymd-browser-open-function 'browse-url-firefox)
  (setq flymd-http-port 9000)
  (setq flymd-output-directory temporary-file-directory)
  (setq flymd-close-buffer-delete-temp-files t)
  (setq flymd-delay 800)  ; 800ms 延迟，平衡响应和性能
  
  ;; 快捷键
  :bind (:map markdown-mode-map
         ("C-c p" . flymd-flyit)
         ("C-c r" . flymd-browser-refresh)))

;; 可选：自动为小型文件启动预览
(defun my/smart-flymd ()
  "智能启动 FLYMD：只在适当的时候启动"
  (when (and (derived-mode-p 'markdown-mode)
             (not (flymd-flyit))  ; 确保没有运行
             (< (buffer-size) 1000000))  ; 文件小于100KB
    (flymd-flyit)))

;; 取消注释以下行以启用智能自动启动
;; (add-hook 'markdown-mode-hook #'my/smart-flymd)


(provide 'init-md)
