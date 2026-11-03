param(
    [Parameter(Mandatory=$true)][ValidateSet('Install','Uninstall')][string]$Mode,
    [string]$ConfigDir,
    [string]$CliPath
)
$ErrorActionPreference = 'Stop'
$packRoot = Split-Path -Parent $PSScriptRoot
$utf8 = [Text.UTF8Encoding]::new($false)
function Hash-Bytes([byte[]]$bytes) {
    $sha = [Security.Cryptography.SHA256]::Create()
    try { return [BitConverter]::ToString($sha.ComputeHash($bytes)).Replace('-', '').ToLowerInvariant() }
    finally { $sha.Dispose() }
}
try {
    if (-not $CliPath) {
        $candidates = @($env:EFFECTCRAFT_CLI)
        foreach ($base in @($env:LOCALAPPDATA,$env:ProgramFiles,${env:ProgramFiles(x86)})) {
            if (-not $base) { continue }
            if ($base -eq $env:LOCALAPPDATA) { $base = Join-Path $base 'Programs' }
            $candidates += Join-Path $base 'ArtCraft\EffectCraft\effectcraft-cli.exe'
        }
        $CliPath = $candidates | Where-Object { $_ -and (Test-Path -LiteralPath $_ -PathType Leaf) } | Select-Object -First 1
    }
    if (-not $ConfigDir) {
        if ($env:EFFECTCRAFT_CONFIG_DIR) { $ConfigDir = $env:EFFECTCRAFT_CONFIG_DIR }
        elseif ($CliPath -and ((Test-Path -LiteralPath (Join-Path (Split-Path $CliPath) 'portable.txt')) -or (Test-Path -LiteralPath (Join-Path (Split-Path $CliPath) 'EffectCraft.portable')))) {
            $ConfigDir = Join-Path (Split-Path $CliPath) 'EffectCraftData'
        } else {
            if (-not $env:APPDATA) { throw 'APPDATA not found. Pass -ConfigDir with the application settings directory.' }
            $ConfigDir = Join-Path $env:APPDATA 'EffectCraft'
        }
    }
    if (-not [IO.Path]::IsPathRooted($ConfigDir)) { throw 'ConfigDir must be absolute.' }
    $ConfigDir = [IO.Path]::GetFullPath($ConfigDir).TrimEnd('\','/')
    $assets = Join-Path $ConfigDir 'IGPACK Motion Browser'
    $frames = Join-Path $assets 'Frames'
    $panel = Join-Path $ConfigDir 'Scripts\ScriptUI Panels\IGPACK\Motion Browser.jsx'
    $receiptPath = Join-Path $assets 'installed.json'
    if ($Mode -eq 'Uninstall') {
        if (-not (Test-Path -LiteralPath $receiptPath -PathType Leaf)) { throw "Installation receipt not found: $receiptPath" }
        $receipt = [IO.File]::ReadAllText($receiptPath,$utf8) | ConvertFrom-Json
        if ($receipt.product -ne 'IGPACK Motion Browser' -or $receipt.config -ne $ConfigDir) { throw 'Invalid installation receipt.' }
        foreach ($file in $receipt.files) {
            $full = [IO.Path]::GetFullPath($file.target)
            $validFrame = $full.StartsWith($frames+'\',[StringComparison]::OrdinalIgnoreCase) -and $full.Substring($frames.Length+1) -match '^\d{3}\\\d{2}\.png$'
            if (($full -ne $panel -and -not $validFrame) -or $full -ne $file.target -or $file.sha256 -notmatch '^[a-f0-9]{64}$') { throw 'Unsafe path or hash in installation receipt.' }
        }
        $remaining = @()
        foreach ($file in $receipt.files) {
            if (-not (Test-Path -LiteralPath $file.target)) { continue }
            $info = Get-Item -LiteralPath $file.target
            if ($info.PSIsContainer -or ($info.Attributes -band [IO.FileAttributes]::ReparsePoint)) { throw 'Refusing a linked or directory target.' }
            if ((Hash-Bytes ([IO.File]::ReadAllBytes($file.target))) -eq $file.sha256) { Remove-Item -LiteralPath $file.target }
            else { $remaining += $file; Write-Warning "Modified file preserved: $($file.target)" }
        }
        if ($remaining.Count) {
            $receipt.files = @($remaining)
            [IO.File]::WriteAllText($receiptPath,($receipt | ConvertTo-Json -Depth 8),$utf8)
            throw 'Modified or incomplete files were preserved. Move them elsewhere and run Uninstall again.'
        }
        Remove-Item -LiteralPath $receiptPath
        # Empty directories are harmless; never recursively delete a settings directory.
        Write-Host 'IGPACK Motion Browser removed. Other scripts, settings and customized files were preserved.'
        exit 0
    }
    if (-not $CliPath -or -not (Test-Path -LiteralPath $CliPath -PathType Leaf)) { throw 'EffectCraft CLI not found. Pass -CliPath or set EFFECTCRAFT_CLI.' }
    $version = (& $CliPath --version | Out-String).Trim()
    if ($LASTEXITCODE -ne 0 -or $version -ne 'effectcraft-cli 0.21.0') { throw "Requires EffectCraft 0.21.0. Found: $version" }
    if ((Test-Path -LiteralPath $assets) -and (@(Get-ChildItem -LiteralPath $assets -Force -Recurse -File).Count -gt 0)) { throw "Existing extension files found: $assets. Uninstall the previous version first." }
    if (Test-Path -LiteralPath $panel) { throw "An existing panel will not be overwritten: $panel" }
    $sourceRoot = Join-Path $packRoot 'Plugin'
    $manifest = [IO.File]::ReadAllText((Join-Path $sourceRoot 'manifest.json'),$utf8) | ConvertFrom-Json
    if ($manifest.version -ne '2.0.0' -or $manifest.engine -ne '0.21.0') { throw 'Invalid extension manifest.' }
    $plan = @()
    foreach ($property in $manifest.files.PSObject.Properties) {
        $relative = $property.Name
        if ($relative -ne 'IGPACK Motion Browser.jsx' -and $relative -notmatch '^Frames/\d{3}/\d{2}\.png$') { throw 'Invalid source path in manifest.' }
        $bytes = [IO.File]::ReadAllBytes((Join-Path $sourceRoot $relative))
        if ((Hash-Bytes $bytes) -ne $property.Value) { throw "Source checksum mismatch: $relative" }
        if ($relative -eq 'IGPACK Motion Browser.jsx') {
            $text = $utf8.GetString($bytes)
            if (-not $text.Contains('"__IGPACK_ASSET_ROOT__"')) { throw 'Missing asset path marker.' }
            $text = $text.Replace('"__IGPACK_ASSET_ROOT__"',($frames.Replace('\','/') | ConvertTo-Json -Compress))
            $bytes = $utf8.GetBytes($text)
            $target = $panel
        } else { $target = Join-Path $assets $relative }
        if (Test-Path -LiteralPath $target) { throw "Existing file will not be overwritten: $target" }
        $plan += [pscustomobject]@{target=$target;bytes=$bytes;sha256=(Hash-Bytes $bytes)}
    }
    if ($plan.Count -ne 1275) { throw 'Expected panel plus 1274 preview frames; no files copied.' }
    [IO.Directory]::CreateDirectory($assets) | Out-Null
    $receipt = [pscustomobject]@{product='IGPACK Motion Browser';version='2.0.0';config=$ConfigDir;files=@($plan | ForEach-Object { [pscustomobject]@{target=$_.target;sha256=$_.sha256} })}
    $stream = [IO.File]::Open($receiptPath,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::None)
    try {
        $receiptBytes = $utf8.GetBytes(($receipt | ConvertTo-Json -Depth 8))
        $stream.Write($receiptBytes,0,$receiptBytes.Length)
    } finally { $stream.Dispose() }
    foreach ($file in $plan) {
        [IO.Directory]::CreateDirectory((Split-Path -Parent $file.target)) | Out-Null
        $stream = [IO.File]::Open($file.target,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::None)
        try { $stream.Write($file.bytes,0,$file.bytes.Length) } finally { $stream.Dispose() }
    }
    Write-Host 'Installed IGPACK Motion Browser 2.0.0.'
    Write-Host 'In EffectCraft: Window > IGPACK > Motion Browser. If necessary, restart the application.'
    Write-Host "Settings directory: $ConfigDir"
    exit 0
} catch {
    Write-Error $_ -ErrorAction Continue
    exit 1
}
