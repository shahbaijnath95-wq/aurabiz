# AuraBiz - Download Embed Runtimes
# Run this to download Python + Node.js for bundling into EXE

$ErrorActionPreference = "Stop"
$resourcesDir = "$PSScriptRoot\resources"

# ─── Download Python Embedded ───
$pythonVersion = "3.11.9"
$pythonUrl = "https://www.python.org/ftp/python/$pythonVersion/python-$pythonVersion-embed-amd64.zip"
$pythonDir = "$resourcesDir\python-embed"
$pythonZip = "$resourcesDir\python-embed.zip"

if (!(Test-Path "$pythonDir\python.exe")) {
    Write-Host "Downloading Python $pythonVersion embedded..."
    Invoke-WebRequest -Uri $pythonUrl -OutFile $pythonZip -UseBasicParsing
    Expand-Archive -Path $pythonZip -DestinationPath $pythonDir -Force
    Remove-Item $pythonZip -Force

    # Enable pip + site-packages
    $pthFile = Get-ChildItem $pythonDir -Filter "python*._pth" | Select-Object -First 1
    if ($pthFile) {
        $content = Get-Content $pthFile.FullName -Raw
        $content = $content -replace "#import site", "import site"
        Set-Content $pthFile.FullName $content
        Write-Host "Enabled pip in embedded Python"
    }

    # Install pip
    $getPip = "$resourcesDir\get-pip.py"
    Invoke-WebRequest -Uri "https://bootstrap.pypa.io/get-pip.py" -OutFile $getPip -UseBasicParsing
    & "$pythonDir\python.exe" $getPip
    Remove-Item $getPip -Force

    # Install backend dependencies
    $backendReq = "$PSScriptRoot\..\backend\requirements.txt"
    if (Test-Path $backendReq) {
        Write-Host "Installing backend Python dependencies..."
        & "$pythonDir\python.exe" -m pip install -r $backendReq --quiet
    }

    Write-Host "Python embedded ready!"
} else {
    Write-Host "Python embedded already exists"
}

# ─── Download Node.js ───
$nodeVersion = "20.18.0"
$nodeUrl = "https://nodejs.org/dist/v$nodeVersion/node-v$nodeVersion-win-x64.zip"
$nodeDir = "$resourcesDir\node-embed"
$nodeZip = "$resourcesDir\node.zip"

if (!(Test-Path "$nodeDir\node.exe")) {
    Write-Host "Downloading Node.js v$nodeVersion..."
    Invoke-WebRequest -Uri $nodeUrl -OutFile $nodeZip -UseBasicParsing
    Expand-Archive -Path $nodeZip -DestinationPath $resourcesDir -Force
    # Move from subfolder to node-embed
    $extracted = Get-ChildItem $resourcesDir -Directory | Where-Object { $_.Name -like "node-v*" } | Select-Object -First 1
    if ($extracted) {
        Move-Item "$($extracted.FullName)\*" $nodeDir -Force
        Remove-Item $extracted.FullName -Force
    }
    Remove-Item $nodeZip -Force

    # Install bot dependencies
    $botPackage = "$PSScriptRoot\..\whatsapp-bot\package.json"
    if (Test-Path $botPackage) {
        Write-Host "Installing bot Node.js dependencies..."
        Push-Location "$PSScriptRoot\..\whatsapp-bot"
        & "$nodeDir\node.exe" "node_modules\npm\bin\npm-cli.js" install --production --quiet
        Pop-Location
    }

    Write-Host "Node.js embedded ready!"
} else {
    Write-Host "Node.js already exists"
}

Write-Host "`nAll runtimes ready! Now run: npm run dist"
