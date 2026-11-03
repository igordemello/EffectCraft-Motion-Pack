param(
    [Parameter(Mandatory=$true)][ValidateSet('Install','Uninstall')][string]$Mode,
    [string]$PresetsDir,
    [string]$CliPath
)
$ErrorActionPreference = 'Stop'
$packRoot = Split-Path -Parent $PSScriptRoot
$manifestName = '.effectcraft-motion-pack-1.0.json'

function File-Hash([string]$path) {
    $sha = [Security.Cryptography.SHA256]::Create()
    $stream = [IO.File]::OpenRead($path)
    try { return [BitConverter]::ToString($sha.ComputeHash($stream)).Replace('-', '') }
    finally { $stream.Dispose(); $sha.Dispose() }
}

function Save-Receipt($receipt, $path) {
    $text = $receipt | ConvertTo-Json -Depth 8
    $temp = $path + '.' + [guid]::NewGuid().ToString('N') + '.tmp'
    try {
        [IO.File]::WriteAllText($temp, $text, [Text.UTF8Encoding]::new($false))
        [IO.File]::Replace($temp, $path, [NullString]::Value)
    } finally {
        if (Test-Path -LiteralPath $temp) { Remove-Item -LiteralPath $temp }
    }
}

try {
    if (-not $PresetsDir) {
        if (Test-Path Env:EC_PRESETS_DIR) {
            if (-not $env:EC_PRESETS_DIR) { throw 'EC_PRESETS_DIR is empty.' }
            $PresetsDir = $env:EC_PRESETS_DIR
        } else {
            $profileRoot = $env:HOME
            if (-not $profileRoot) { $profileRoot = $env:USERPROFILE }
            if (-not $profileRoot) { throw 'Cannot resolve HOME or USERPROFILE.' }
            # The 0.21.0 app uses literal Documents, not Windows KnownFolder redirection.
            $PresetsDir = Join-Path $profileRoot 'Documents\EffectCraft\Presets'
        }
    }
    if (-not [IO.Path]::IsPathRooted($PresetsDir)) { throw 'Preset directory must be an absolute path.' }
    $PresetsDir = [IO.Path]::GetFullPath($PresetsDir)
    $receiptPath = Join-Path $PresetsDir $manifestName

    if ($Mode -eq 'Uninstall') {
        if (-not (Test-Path -LiteralPath $receiptPath -PathType Leaf)) { throw "Pack receipt not found: $receiptPath" }
        $receipt = Get-Content -LiteralPath $receiptPath -Raw | ConvertFrom-Json
        if ($receipt.pack -ne 'EffectCraft Motion Pack 1.0' -or $receipt.target -ne $PresetsDir) { throw 'Invalid pack receipt.' }
        $remaining = @()
        # Validate the entire receipt before deleting any file. Never follow paths from a receipt.
        foreach ($item in $receipt.files) {
            if ($item.name -ne [IO.Path]::GetFileName($item.name) -or $item.name -notlike 'ECMP *.ecpreset' -or $item.sha256 -notmatch '^[a-fA-F0-9]{64}$') {
                throw 'Unsafe filename or checksum in receipt.'
            }
        }
        foreach ($item in $receipt.files) {
            $target = Join-Path $PresetsDir $item.name
            if (-not (Test-Path -LiteralPath $target)) { continue }
            $info = Get-Item -LiteralPath $target
            if (($info.Attributes -band [IO.FileAttributes]::ReparsePoint) -or $info.PSIsContainer) { throw "Refusing linked/directory target: $target" }
            if ((File-Hash $target) -eq $item.sha256) {
                Remove-Item -LiteralPath $target
            } else {
                Write-Warning "Modified file preserved: $($item.name)"
                $remaining += $item
            }
        }
        if ($remaining.Count) {
            $receipt.files = @($remaining)
            Save-Receipt $receipt $receiptPath
            throw "$($remaining.Count) modified files were preserved; receipt retained. Move them elsewhere and run uninstall again."
        }
        Remove-Item -LiteralPath $receiptPath
        Write-Host "Uninstalled pack files. Other files and the preset directory were preserved."
        exit 0
    }

    if (-not $CliPath) {
        $candidates = @($env:EFFECTCRAFT_CLI)
        foreach ($base in @($env:LOCALAPPDATA, $env:ProgramFiles, ${env:ProgramFiles(x86)})) {
            if (-not $base) { continue }
            if ($base -eq $env:LOCALAPPDATA) { $base = Join-Path $base 'Programs' }
            $candidates += Join-Path $base 'ArtCraft\EffectCraft\effectcraft-cli.exe'
        }
        $CliPath = $candidates | Where-Object { $_ -and (Test-Path -LiteralPath $_ -PathType Leaf) } | Select-Object -First 1
    }
    if (-not $CliPath -or -not (Test-Path -LiteralPath $CliPath -PathType Leaf)) { throw 'EffectCraft CLI not found. Pass -CliPath or set EFFECTCRAFT_CLI.' }
    $version = (& $CliPath --version | Out-String).Trim()
    if ($LASTEXITCODE -ne 0 -or $version -ne 'effectcraft-cli 0.21.0') { throw "Requires EffectCraft 0.21.0. Found: $version" }
    if (Test-Path -LiteralPath $receiptPath) { throw 'Pack already installed or previous installation incomplete. Uninstall it first.' }
    $catalog = Get-Content -LiteralPath (Join-Path $packRoot 'Documentation\catalog.json') -Raw | ConvertFrom-Json
    $checksums = Get-Content -LiteralPath (Join-Path $packRoot 'Documentation\preset_hashes.json') -Raw | ConvertFrom-Json
    $plan = @()
    foreach ($entry in $catalog) {
        if (-not $entry.implemented) { continue }
        $source = [IO.Path]::GetFullPath((Join-Path $packRoot $entry.path))
        if (-not $source.StartsWith($packRoot + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) { throw 'Source escaped pack directory.' }
        $name = 'ECMP ' + $entry.category + ' - ' + ('{0:000}' -f $entry.id) + ' ' + $entry.name + '.ecpreset'
        $target = Join-Path $PresetsDir $name
        if (Test-Path -LiteralPath $target) { throw "Existing file will not be overwritten: $target" }
        $hash = File-Hash $source
        if ($hash -ne $checksums.($entry.path)) { throw "Source checksum mismatch: $source" }
        $plan += [pscustomobject]@{source=$source;target=$target;name=$name;sha256=$hash}
    }
    if ($plan.Count -ne 98) { throw 'Expected 98 presets; no files copied.' }
    [IO.Directory]::CreateDirectory($PresetsDir) | Out-Null
    $receipt = [pscustomobject]@{pack='EffectCraft Motion Pack 1.0';version='0.21.0';target=$PresetsDir;files=@()}
    # Claim a unique receipt before copying; an existing installation is never overwritten.
    $claim = [IO.File]::Open($receiptPath,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::None)
    $claim.Dispose()
    Save-Receipt $receipt $receiptPath
    try {
        foreach ($item in $plan) {
            $inputStream = [IO.File]::OpenRead($item.source)
            try {
                $outputStream = [IO.File]::Open($item.target,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::None)
                try {
                    $receipt.files += [pscustomobject]@{name=$item.name;sha256=$item.sha256}
                    Save-Receipt $receipt $receiptPath
                    $inputStream.CopyTo($outputStream)
                } finally { $outputStream.Dispose() }
            } finally { $inputStream.Dispose() }
            if ((File-Hash $item.target) -ne $item.sha256) { throw "Copied file checksum mismatch: $($item.name)" }
        }
    } catch {
        # Retain the receipt so an interrupted copy can be safely removed with Uninstall.
        throw "Installation stopped: $($_.Exception.Message). Receipt retained at $receiptPath; run Uninstall before retrying."
    }
    Write-Host "Installed $($receipt.files.Count) presets to $PresetsDir"
    Write-Host 'In Effects & Presets, refresh Animation Presets or restart EffectCraft. Search ECMP.'
    exit 0
} catch {
    Write-Error $_ -ErrorAction Continue
    exit 1
}
