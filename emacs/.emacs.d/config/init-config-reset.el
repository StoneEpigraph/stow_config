;; ===========================================
;; 重置 Emacs 时间系统配置
;; ===========================================

(defun my/reset-emacs-time-system ()
  "重置 Emacs 时间系统到默认状态"
  (interactive)
  
  ;; 1. 重置环境变量
  (setenv "TZ" "UTC-8")  ; 中国标准时间
  
  ;; 2. 重置 Emacs 时间变量
  (setq system-time-locale "C")
  (setq calendar-locale "C")
  (setq calendar-time-display-form 
        '(year "-" month "-" day " " hour ":" minute ":" second))
  
  ;; 3. 重置日历变量
  (setq calendar-absolute-time nil)
  (setq calendar-current-date nil)
  (setq calendar-mark-ring nil)
  
  ;; 4. 重置时间戳格式
  (setq org-time-stamp-formats '("<%Y-%m-%d %a>" . "<%Y-%m-%d %a %H:%M>"))
  (setq org-display-custom-times t)
  
  ;; 5. 重置日期读取
  (setq org-read-date-prefer-future 'time)
  (setq org-read-date-force-compatible-dates nil)
  
  ;; 6. 强制时间系统重新初始化
  (current-time)  ; 触发时间系统
  
  ;; 7. 测试时间系统
  (let ((test-time (current-time)))
    (message "时间系统已重置")
    (message "当前时间: %s" (current-time-string))
    (message "时间戳: %S" test-time)
    
    ;; 验证年份范围
    (let* ((decoded (decode-time test-time))
           (year (nth 5 decoded)))
      (if (and (>= year 1900) (<= year 2100))
          (message "✅ 年份 %d 在正常范围内" year)
        (message "⚠️ 警告: 年份 %d 超出正常范围" year))))
  
  t)

;; 在 Emacs 启动时重置时间系统
(add-hook 'emacs-startup-hook 'my/reset-emacs-time-system)

(provide 'init-config-reset)
