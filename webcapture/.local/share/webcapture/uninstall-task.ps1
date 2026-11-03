#Requires -Version 5.1
<#
.SYNOPSIS
    卸载 webcapture 计划任务（对应 Linux 的 systemctl --user disable --now webcapture.timer）。

.DESCRIPTION
    只删计划任务，不删日志、状态和截图。要彻底清干净再手动删：
      %USERPROFILE%\webcapture\            状态 / 日志 / 基线
      %USERPROFILE%\public\webcapture\     成品截图
      %LOCALAPPDATA%\webcapture\           venv / profile / 临时目录

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File .\uninstall-task.ps1
#>
[CmdletBinding()]
param(
    [string]$TaskName = 'webcapture'
)

$ErrorActionPreference = 'Stop'

$task = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if (-not $task) {
    Write-Host "==> 没有名为 $TaskName 的计划任务，无需卸载" -ForegroundColor Yellow
    return
}

Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
Write-Host "==> 已卸载计划任务 $TaskName" -ForegroundColor Cyan
