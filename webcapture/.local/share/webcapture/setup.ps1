#Requires -Version 5.1
<#
.SYNOPSIS
    webcapture 的 Windows 环境准备（对应 Linux 的 setup.sh）。

.DESCRIPTION
    建独立 venv、装 playwright + pillow、检查系统浏览器、生成 notify.conf。
    脚本就地运行，不改动仓库里的 Python 源码；依赖装在
    %LOCALAPPDATA%\webcapture\venv，重复运行是安全的。

    浏览器优先级：Chrome → Edge → Chromium → Playwright 自带 Chromium。
    机器上没有 Chrome/Edge 时加 -InstallBrowser 让 Playwright 下一个（约 150MB）。

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File .\setup.ps1

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File .\setup.ps1 -InstallBrowser -RegisterTask
#>
[CmdletBinding()]
param(
    [string]$VenvDir = (Join-Path $env:LOCALAPPDATA 'webcapture\venv'),
    [string]$StateDir = (Join-Path $env:USERPROFILE 'webcapture'),
    [switch]$InstallBrowser,
    [switch]$RegisterTask
)

$ErrorActionPreference = 'Continue'

$AppDir   = $PSScriptRoot
$CacheDir = Join-Path $env:LOCALAPPDATA 'webcapture'
$TmpDir   = Join-Path $CacheDir 'tmp'
$VenvPy   = Join-Path $VenvDir 'Scripts\python.exe'

function Write-Step { param([string]$Message) Write-Host "==> $Message" -ForegroundColor Cyan }
function Write-Info { param([string]$Message) Write-Host "    $Message" }
function Fail { param([string]$Message) Write-Host $Message -ForegroundColor Red; exit 1 }

New-Item -ItemType Directory -Force -Path $CacheDir, $TmpDir, $StateDir | Out-Null

# /tmp 在某些机器上是小容量 tmpfs；Windows 上同样把 pip 的临时目录挪到磁盘
$env:TEMP = $TmpDir
$env:TMP  = $TmpDir
$env:PYTHONIOENCODING = 'utf-8'
$env:PYTHONUTF8 = '1'
$env:PIP_DISABLE_PIP_VERSION_CHECK = '1'
try { [Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false) } catch { }

Push-Location $AppDir
try {
    # ---- 1) 找一个 Python 3.9+ -------------------------------------------------
    Write-Step '查找 Python 3.9+'
    $python = $null
    foreach ($name in @('py', 'python', 'python3')) {
        $cmd = Get-Command $name -ErrorAction SilentlyContinue | Select-Object -First 1
        if (-not $cmd) { continue }
        $probe = & $cmd.Source -c 'import sys; print(sys.version_info >= (3, 9)); print(sys.executable)' 2>$null
        if ($LASTEXITCODE -eq 0 -and $probe -and $probe.Count -ge 2 -and $probe[0] -eq 'True') {
            $python = $probe[1].Trim()
            break
        }
    }
    if (-not $python) {
        Fail '未找到 Python 3.9+。装一个：winget install Python.Python.3.12（或从 python.org 下载）'
    }
    Write-Info "python -> $python"

    # ---- 2) venv --------------------------------------------------------------
    Write-Step "venv: $VenvDir"
    if (-not (Test-Path -LiteralPath $VenvPy)) {
        & $python -m venv $VenvDir
        if ($LASTEXITCODE -ne 0 -or -not (Test-Path -LiteralPath $VenvPy)) {
            Fail "创建 venv 失败（$VenvDir）"
        }
    } else {
        Write-Info '已存在，跳过创建'
    }

    # ---- 3) playwright + pillow ----------------------------------------------
    Write-Step '安装 playwright + pillow'
    & $VenvPy -m pip install -q --upgrade pip
    & $VenvPy -m pip install -q playwright pillow
    if ($LASTEXITCODE -ne 0) { Fail 'pip install 失败，检查网络或 pip 镜像配置' }
    & $VenvPy -c "import playwright, PIL; print('    deps ok, pillow', PIL.__version__)"

    $defaultVenv = Join-Path $env:LOCALAPPDATA 'webcapture\venv'
    if ($VenvDir -ne $defaultVenv) {
        Write-Info "注意：用的不是默认 venv 目录，跑 shot.ps1 前需要设 WEBCAPTURE_VENV=$VenvDir"
    }
    $defaultState = Join-Path $env:USERPROFILE 'webcapture'
    if ($StateDir -ne $defaultState) {
        Write-Info "注意：状态目录非默认，跑 shot.ps1 前需要设 WEBCAPTURE_HOME=$StateDir"
    }

    # ---- 4) 浏览器 ------------------------------------------------------------
    Write-Step '检查浏览器（不默认下载 Playwright 自带 Chromium）'
    $browser = @(& $VenvPy -c "import paths; print(paths.find_browser() or '')" 2>$null) |
        Where-Object { $_ } | Select-Object -First 1
    if ($browser) { $browser = $browser.Trim() } else { $browser = '' }
    if ($browser) {
        Write-Info "system browser -> $browser"
    } elseif ($InstallBrowser) {
        Write-Info '未找到 Chrome/Edge，下载 Playwright 自带 Chromium'
        & $VenvPy -m playwright install chromium
        if ($LASTEXITCODE -ne 0) { Fail 'playwright install chromium 失败' }
    } else {
        Write-Host '    未找到 Chrome / Edge / Chromium。' -ForegroundColor Yellow
        Write-Host '    装 Chrome/Edge，或重跑本脚本并加 -InstallBrowser' -ForegroundColor Yellow
    }

    # ---- 5) notify.conf -------------------------------------------------------
    New-Item -ItemType Directory -Force -Path $StateDir | Out-Null
    $conf = Join-Path $StateDir 'notify.conf'
    $example = Join-Path $AppDir 'notify.conf.example'
    if (-not (Test-Path -LiteralPath $conf) -and (Test-Path -LiteralPath $example)) {
        Copy-Item -LiteralPath $example -Destination $conf
        # 含 webhook 密钥，只给当前用户读写
        try {
            $me = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
            & icacls.exe $conf /inheritance:r /grant:r "${me}:(R,W)" | Out-Null
            if ($LASTEXITCODE -ne 0) {
                Write-Host "    $conf 权限未收紧（icacls 退出码 $LASTEXITCODE），它里面有 webhook 密钥" -ForegroundColor Yellow
            }
        } catch {
            Write-Host "    收紧 $conf 权限失败：$($_.Exception.Message)" -ForegroundColor Yellow
        }
        Write-Info "已生成 $conf（填 webhook 才会发报警）"
    } elseif (Test-Path -LiteralPath $conf) {
        Write-Info "已存在 $conf"
    }

    # ---- 6) 可选：注册计划任务 ------------------------------------------------
    if ($RegisterTask) {
        Write-Step '注册计划任务'
        & (Join-Path $AppDir 'install-task.ps1')
    }
} finally {
    Pop-Location
}

Write-Host ''
Write-Step '完成'
Write-Info "试跑一轮： powershell -ExecutionPolicy Bypass -File `"$(Join-Path $AppDir 'shot.ps1')`""
Write-Info "报警自检： `"$VenvPy`" `"$(Join-Path $AppDir 'notify.py')`" --test"
if (-not $RegisterTask) {
    Write-Info '每 15 分钟自动跑： powershell -ExecutionPolicy Bypass -File .\install-task.ps1'
}
