#Requires -Version 5.1
<#
.SYNOPSIS
    注册计划任务：每 N 分钟跑一轮 webcapture（对应 Linux 的 webcapture.timer）。

.DESCRIPTION
    任务以当前用户身份运行（LogonType Interactive），所以：
      - 登录后自动开始，注销后停止 —— 与 Linux 的 systemd user timer + linger 关闭时一致
      - 锁屏 / 睡眠唤醒后继续；错过的触发点由 StartWhenAvailable 补跑一次
      - 不需要管理员权限

    参数按需改，默认 15 分钟一轮。

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File .\install-task.ps1

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File .\install-task.ps1 -IntervalMinutes 30 -TaskName webcapture-test
#>
[CmdletBinding()]
param(
    [string]$TaskName = 'webcapture',
    [int]$IntervalMinutes = 15,
    [int]$TimeLimitMinutes = 15,
    [string]$ShotScript
)

$ErrorActionPreference = 'Stop'

if (-not $ShotScript) { $ShotScript = Join-Path $PSScriptRoot 'shot.ps1' }
if (-not (Test-Path -LiteralPath $ShotScript)) { throw "找不到入口脚本：$ShotScript" }
$ShotScript = (Resolve-Path -LiteralPath $ShotScript).Path

if ($IntervalMinutes -lt 1) { throw 'IntervalMinutes 必须 >= 1' }

$argLine = '-NoProfile -NonInteractive -WindowStyle Hidden -ExecutionPolicy Bypass -File "{0}"' -f $ShotScript
$action = New-ScheduledTaskAction -Execute 'powershell.exe' -Argument $argLine

$me = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name

# 两个触发器：本用户登录时先跑一次，之后每 N 分钟一次（重复触发器从注册后 1 分钟开始）
$triggers = @(
    (New-ScheduledTaskTrigger -AtLogOn -User $me),
    (New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(1) `
        -RepetitionInterval (New-TimeSpan -Minutes $IntervalMinutes) `
        -RepetitionDuration (New-TimeSpan -Days 3650))
)

$settings = New-ScheduledTaskSettingsSet `
    -MultipleInstances IgnoreNew `
    -StartWhenAvailable `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -ExecutionTimeLimit (New-TimeSpan -Minutes $TimeLimitMinutes)

$principal = New-ScheduledTaskPrincipal -UserId $me -LogonType Interactive -RunLevel Limited

Register-ScheduledTask `
    -TaskName $TaskName `
    -Action $action `
    -Trigger $triggers `
    -Settings $settings `
    -Principal $principal `
    -Description 'webcapture: 每 N 分钟整页截图 + 时间水印（失败/恢复/变更推送到钉钉或企业微信）' `
    -Force | Out-Null

$task = Get-ScheduledTask -TaskName $TaskName
Write-Host "==> 已注册计划任务 $TaskName（每 $IntervalMinutes 分钟，用户 $me，登录后运行）" -ForegroundColor Cyan
Write-Host ("    状态: {0}" -f $task.State)
Write-Host "    立即跑一轮:  Start-ScheduledTask -TaskName $TaskName"
Write-Host "    看上次结果:  Get-ScheduledTaskInfo -TaskName $TaskName | Format-List"
Write-Host "    卸载:        .\uninstall-task.ps1 -TaskName $TaskName"
