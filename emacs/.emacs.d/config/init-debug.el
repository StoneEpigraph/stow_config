;; init-debug  -*- lexical-binding: t; -*-
;; 开启全面调试
(setq debug-on-error t)
(setq warning-minimum-level :error)
(defun my/enable-full-debug ()
  "开启所有调试选项"
  (interactive)
  
  ;; 1. 开启错误调试
  (setq debug-on-error t)
  (setq debug-on-signal t)
  (setq debug-on-quit t)
  
  ;; 2. 开启 backtrace
  (setq backtrace-on-error t)
  (setq backtrace-on-error-noninteractive t)
  
  ;; 3. 开启详细日志
  (setq byte-compile-verbose t)
  (setq load-verbose t)
  (setq native-comp-verbose 3)
  
  ;; 4. 开启消息日志
  (setq message-log-max 10000)
  
  ;; 5. 开启特定包调试
  (when (featurep 'org)
    (setq org-log-note-clock-out t)
    (setq org-log-note-headings t))
  
  ;; 6. 开启 Emacs 内部调试
  (when (fboundp 'toggle-debug-on-event)
    (toggle-debug-on-event))
  
  (message "✅ 全面调试已开启"))

;; 运行此命令开始追踪
(defun my/trace-org-error ()
  "追踪 org-schedule 错误"
  (interactive)
  
  (my/enable-full-debug)
  
  ;; 记录当前状态
  (message "=== 开始错误追踪 ===")
  (message "时间: %s" (current-time-string))
  (message "文件: %s" (buffer-file-name))
  (message "行数: %d" (count-lines (point-min) (point-max)))
  (message "位置: 第 %d 行" (line-number-at-pos))
  
  ;; 检查当前行
  (save-excursion
    (beginning-of-line)
    (let ((line (buffer-substring (line-beginning-position) (line-end-position))))
      (message "当前行: %s" line)
      
      ;; 检查行属性
      (message "行属性: %S" (text-properties-at (point)))
      
      ;; 检查语法高亮
      (let ((faces (get-text-property (point) 'face)))
        (message "语法高亮: %S" faces))
      
      ;; 检查 org 元素
      (condition-case err
          (let ((element (org-element-at-point)))
            (message "Org 元素: %S" (org-element-type element))
            (message "元素属性: %S" element))
        (error
         (message "解析 Org 元素失败: %s" err)))))
  
  ;; 尝试触发错误
  (message "=== 尝试触发错误 ===")
  (condition-case err
      (call-interactively 'org-schedule)
    
    (args-out-of-range
     (message "❌ 捕获到错误: %S" err)
     (my/analyze-error err))
    
    (error
     (message "❌ 其他错误: %S" err))
    
    (:success
     (message "✅ 没有错误")))
  
  (message "=== 追踪结束 ==="))

(defun my/analyze-error (err)
  "分析错误对象"
  (let ((data (cdr err)))
    (message "错误数据: %S" data)
    
    ;; 检查是否是日期错误
    (when (and (consp data) (= (length data) 3))
      (message "看起来是日期错误: 年=%d, 月=%d, 日=%d"
               (nth 0 data) (nth 1 data) (nth 2 data))
      
      ;; 提供修复建议
      (cond
       ((> (nth 0 data) 2100)
        (message "年份过大，可能是时间戳解析错误"))
       ((< (nth 0 data) 1900)
        (message "年份过小，可能是基准时间错误"))
       ((or (< (nth 1 data) 1) (> (nth 1 data) 12))
        (message "月份无效: %d" (nth 1 data)))
       ((or (< (nth 2 data) 1) (> (nth 2 data) 31))
        (message "日期无效: %d" (nth 2 data)))))))
(provide 'init-debug)
