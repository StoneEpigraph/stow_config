#Requires -Version 5.1
<#
.SYNOPSIS
    webcapture 的 Windows 入口：跑一轮整页截图（对应 Linux 的 shot.sh）。

.DESCRIPTION
    由计划任务（install-task.ps1）每 15 分钟调用，也可以手动跑。
    - 用独占文件句柄做单实例互斥（对应 flock）
    - 先探测网络（对应 shot.sh 里的 nmcli 等待）
    - Python 的 stdout/stderr 合并后追加到 %USERPROFILE%\webcapture\run.out
    - RETENTION_DAYS>0 时清理过期截图

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File .\shot.ps1

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File .\shot.ps1 https://www.bjyouth.gov.cn/
#>
[CmdletBinding()]
param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$Urls
)

$ErrorActionPreference = 'Continue'

$AppDir   = $PSScriptRoot
$Source   = Join-Path $AppDir 'capture.py'
$StateDir = if ($env:WEBCAPTURE_HOME)     { $env:WEBCAPTURE_HOME }     else { Join-Path $env:USERPROFILE 'webcapture' }
$ImgOut   = if ($env:WEBCAPTURE_IMG_ROOT) { $env:WEBCAPTURE_IMG_ROOT } else { Join-Path $env:USERPROFILE 'public\webcapture' }
$CacheDir = if ($env:WEBCAPTURE_CACHE)    { $env:WEBCAPTURE_CACHE }    else { Join-Path $env:LOCALAPPDATA 'webcapture' }
$VenvRoot = if ($env:WEBCAPTURE_VENV) { $env:WEBCAPTURE_VENV } else { Join-Path $env:LOCALAPPDATA 'webcapture\venv' }
$VenvPy   = Join-Path $VenvRoot 'Scripts\python.exe'
$TmpDir   = Join-Path $CacheDir 'tmp'
$LogRun   = Join-Path $StateDir 'run.out'
$LockFile = Join-Path $StateDir '.lock'

New-Item -ItemType Directory -Force -Path $StateDir, $ImgOut, $TmpDir | Out-Null

# /tmp 在 Linux 上可能是小 tmpfs；Windows 上把 TEMP 挪到磁盘，顺便避免
# 计划任务在无控制台环境里用到不存在的用户临时目录。
$env:TEMP = $TmpDir
$env:TMP  = $TmpDir
# Python 默认按 locale 编码输出，报警文案里的 emoji 会让进程直接退出。
$env:PYTHONIOENCODING = 'utf-8'
$env:PYTHONUTF8 = '1'
try { [Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false) } catch { }

function Get-Timestamp { (Get-Date).ToString('yyyy-MM-dd HH:mm:ss') }

function Write-Run {
    param([string]$Message)
    try {
        Add-Content -LiteralPath $LogRun -Value ('[{0}] {1}' -f (Get-Timestamp), $Message) -Encoding UTF8
    } catch { }
}

function Select-Python {
    $cands = @()
    if ($env:WEBCAPTURE_PYTHON) { $cands += $env:WEBCAPTURE_PYTHON }
    $cands += $VenvPy
    $cands += (Join-Path $env:USERPROFILE '.workbuddy\binaries\python\envs\default\python.exe')
    foreach ($name in @('py', 'python', 'python3')) {
        $cmd = Get-Command $name -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($cmd) { $cands += $cmd.Source }
    }
    foreach ($c in $cands) {
        if (-not $c -or -not (Test-Path -LiteralPath $c)) { continue }
        & $c -c 'import playwright, PIL' 2>$null
        if ($LASTEXITCODE -eq 0) { return $c }
    }
    return $null
}

# user 会话里的网络就绪没有 systemd 那样的 target 可等，这里自己探。
# 开机补跑的那一轮常常还没连上网，不等就会四条一起超时误报。
function Wait-Network {
    for ($i = 0; $i -lt 20; $i++) {
        $client = New-Object System.Net.Sockets.TcpClient
        try {
            $task = $client.ConnectAsync('www.baidu.com', 443)
            if ($task.Wait(2000) -and $client.Connected) { return }
        } catch {
        } finally {
            $client.Dispose()
        }
        Start-Sleep -Seconds 3
    }
}

# 同一时间只跑一个实例。句柄留到进程结束，异常退出时由系统释放。
$lock = $null
try {
    $lock = [System.IO.File]::Open(
        $LockFile,
        [System.IO.FileMode]::OpenOrCreate,
        [System.IO.FileAccess]::ReadWrite,
        [System.IO.FileShare]::None)
} catch {
    Write-Run '已有实例在跑，跳过本轮'
    exit 0
}

$rc = 0
try {
    $py = Select-Python
    if (-not $py) {
        Write-Run ('缺少 playwright/pillow，请先运行 {0}' -f (Join-Path $AppDir 'setup.ps1'))
        exit 3
    }

    Wait-Network

    Write-Run ('---- run start ({0}) ----' -f $py)
    $captureArgs = @()
    if ($Urls) { $captureArgs = $Urls }

    $lines = @()
    try {
        $lines = & $py -u $Source @captureArgs 2>&1 | ForEach-Object { $_.ToString() }
        $rc = $LASTEXITCODE
    } catch {
        $lines = @('RUNNER 异常: ' + $_.Exception.Message)
        $rc = 1
    }
    if ($lines -and $lines.Count -gt 0) {
        try {
            Add-Content -LiteralPath $LogRun -Value $lines -Encoding UTF8
        } catch { }
    }

    # 保留策略：RETENTION_DAYS>0 时清理过期截图（默认关闭）
    $keepDays = 0
    if ($env:RETENTION_DAYS -and [int]::TryParse($env:RETENTION_DAYS, [ref]$keepDays) -and $keepDays -gt 0) {
        $cut = (Get-Date).AddDays(-$keepDays)
        Get-ChildItem -LiteralPath $StateDir, $ImgOut -Recurse -Filter '*.png' -File -ErrorAction SilentlyContinue |
            Where-Object { $_.LastWriteTime -lt $cut } |
            Remove-Item -Force -ErrorAction SilentlyContinue
    }
} finally {
    if ($lock) { $lock.Dispose() }
}

exit $rc
