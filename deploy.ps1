# AWS Architecture Explorer - Windows Deployment Script
# PowerShell Version

# Set error action preference
$ErrorActionPreference = "Stop"

Write-Host "======================================" -ForegroundColor Cyan
Write-Host "AWS Architecture Explorer Deployment" -ForegroundColor Cyan
Write-Host "Windows Edition" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""

# Function to check if a command exists
function Test-CommandExists {
    param($command)
    $null = Get-Command $command -ErrorAction SilentlyContinue
    return $?
}

# Check if AWS CLI is installed
Write-Host "Checking prerequisites..." -ForegroundColor Yellow
Write-Host ""

if (Test-CommandExists "aws") {
    Write-Host "[OK] AWS CLI is installed" -ForegroundColor Green
    $awsVersion = aws --version
    Write-Host "     Version: $awsVersion" -ForegroundColor Gray
} else {
    Write-Host "[ERROR] AWS CLI is not installed" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please install AWS CLI for Windows:" -ForegroundColor Yellow
    Write-Host "  https://aws.amazon.com/cli/" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Installation options:" -ForegroundColor Yellow
    Write-Host "  1. Download MSI installer from AWS website" -ForegroundColor Gray
    Write-Host "  2. Use Chocolatey: choco install awscli" -ForegroundColor Gray
    Write-Host "  3. Use Scoop: scoop install aws" -ForegroundColor Gray
    Write-Host ""
    exit 1
}

# Check if AWS credentials are configured
Write-Host ""
Write-Host "Checking AWS credentials..." -ForegroundColor Yellow
try {
    $identity = aws sts get-caller-identity 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[OK] AWS credentials are configured" -ForegroundColor Green
        Write-Host ""
        Write-Host "Current AWS Identity:" -ForegroundColor Cyan
        $identityJson = $identity | ConvertFrom-Json
        Write-Host "  Account: $($identityJson.Account)" -ForegroundColor Gray
        Write-Host "  User ARN: $($identityJson.Arn)" -ForegroundColor Gray
        Write-Host "  User ID: $($identityJson.UserId)" -ForegroundColor Gray
    } else {
        throw "AWS CLI returned error"
    }
} catch {
    Write-Host "[ERROR] AWS credentials are not configured" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please configure AWS credentials:" -ForegroundColor Yellow
    Write-Host "  aws configure" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "You will need:" -ForegroundColor Yellow
    Write-Host "  - AWS Access Key ID" -ForegroundColor Gray
    Write-Host "  - AWS Secret Access Key" -ForegroundColor Gray
    Write-Host "  - Default region (e.g., us-west-2)" -ForegroundColor Gray
    Write-Host ""
    exit 1
}

# Check Python installation
Write-Host ""
Write-Host "Checking Python installation..." -ForegroundColor Yellow

if (Test-CommandExists "python") {
    Write-Host "[OK] Python is installed" -ForegroundColor Green
    $pythonVersion = python --version
    Write-Host "     Version: $pythonVersion" -ForegroundColor Gray
    $pythonCmd = "python"
} elseif (Test-CommandExists "python3") {
    Write-Host "[OK] Python is installed" -ForegroundColor Green
    $pythonVersion = python3 --version
    Write-Host "     Version: $pythonVersion" -ForegroundColor Gray
    $pythonCmd = "python3"
} else {
    Write-Host "[ERROR] Python is not installed" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please install Python for Windows:" -ForegroundColor Yellow
    Write-Host "  https://www.python.org/downloads/" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Or use Windows Store:" -ForegroundColor Yellow
    Write-Host "  https://www.microsoft.com/store/productId/9PJPW5LDXLZ5" -ForegroundColor Cyan
    Write-Host ""
    exit 1
}

# Check pip
Write-Host ""
Write-Host "Checking pip installation..." -ForegroundColor Yellow
try {
    $pipVersion = & $pythonCmd -m pip --version
    Write-Host "[OK] pip is installed" -ForegroundColor Green
    Write-Host "     $pipVersion" -ForegroundColor Gray
} catch {
    Write-Host "[ERROR] pip is not installed" -ForegroundColor Red
    Write-Host ""
    Write-Host "Installing pip..." -ForegroundColor Yellow
    & $pythonCmd -m ensurepip --upgrade
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[ERROR] Failed to install pip" -ForegroundColor Red
        exit 1
    }
}

# Upgrade pip
Write-Host ""
Write-Host "Upgrading pip..." -ForegroundColor Yellow
& $pythonCmd -m pip install --upgrade pip --quiet
if ($LASTEXITCODE -eq 0) {
    Write-Host "[OK] pip upgraded" -ForegroundColor Green
} else {
    Write-Host "[WARNING] Failed to upgrade pip (continuing anyway)" -ForegroundColor Yellow
}

# Install Python dependencies
Write-Host ""
Write-Host "Installing Python dependencies..." -ForegroundColor Yellow

if (Test-Path "requirements.txt") {
    & $pythonCmd -m pip install -r requirements.txt --quiet
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[OK] Dependencies installed" -ForegroundColor Green
    } else {
        Write-Host "[ERROR] Failed to install dependencies" -ForegroundColor Red
        Write-Host ""
        Write-Host "Try manually:" -ForegroundColor Yellow
        Write-Host "  $pythonCmd -m pip install streamlit streamlit-agraph" -ForegroundColor Cyan
        Write-Host ""
        exit 1
    }
} else {
    Write-Host "[WARNING] requirements.txt not found" -ForegroundColor Yellow
    Write-Host "Installing core dependencies..." -ForegroundColor Yellow
    & $pythonCmd -m pip install streamlit streamlit-agraph --quiet
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[OK] Core dependencies installed" -ForegroundColor Green
    } else {
        Write-Host "[ERROR] Failed to install dependencies" -ForegroundColor Red
        exit 1
    }
}

# Create snapshots directory
Write-Host ""
Write-Host "Creating snapshots directory..." -ForegroundColor Yellow
if (-not (Test-Path "snapshots")) {
    New-Item -ItemType Directory -Path "snapshots" -Force | Out-Null
    Write-Host "[OK] Snapshots directory created: .\snapshots" -ForegroundColor Green
} else {
    Write-Host "[OK] Snapshots directory exists: .\snapshots" -ForegroundColor Green
}

# Test AWS connectivity
Write-Host ""
Write-Host "Testing AWS connectivity..." -ForegroundColor Yellow
Write-Host ""

try {
    Write-Host "  Testing VPC access..." -ForegroundColor Gray
    $vpcs = aws ec2 describe-vpcs --region us-west-2 --output json 2>&1
    if ($LASTEXITCODE -eq 0) {
        $vpcsJson = $vpcs | ConvertFrom-Json
        $vpcCount = $vpcsJson.Vpcs.Count
        Write-Host "  [OK] Found $vpcCount VPC(s) in us-west-2" -ForegroundColor Green
    } else {
        Write-Host "  [WARNING] Limited VPC access (may need permissions)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "  [WARNING] Could not test VPC access" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "======================================" -ForegroundColor Cyan
Write-Host "[SUCCESS] Deployment complete!" -ForegroundColor Green
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""

# Display usage instructions
Write-Host "To run the application:" -ForegroundColor Yellow
Write-Host ""
Write-Host "  streamlit run aws_architecture_explorer_app_direct.py" -ForegroundColor Cyan
Write-Host ""
Write-Host "Or use the provided batch file:" -ForegroundColor Yellow
Write-Host ""
Write-Host "  run_app.bat" -ForegroundColor Cyan
Write-Host ""

Write-Host "To test connectivity:" -ForegroundColor Yellow
Write-Host ""
Write-Host "  $pythonCmd test_connectivity.py" -ForegroundColor Cyan
Write-Host ""

Write-Host "Documentation:" -ForegroundColor Yellow
Write-Host "  README.md       - User guide" -ForegroundColor Gray
Write-Host "  COMPARISON.md   - Code changes" -ForegroundColor Gray
Write-Host "  SUMMARY.md      - Project overview" -ForegroundColor Gray
Write-Host ""

# Offer to run the app
Write-Host "Would you like to run the application now? (Y/N): " -ForegroundColor Cyan -NoNewline
$response = Read-Host
if ($response -eq "Y" -or $response -eq "y") {
    Write-Host ""
    Write-Host "Starting Streamlit application..." -ForegroundColor Green
    Write-Host ""
    streamlit run aws_architecture_explorer_app_direct.py
} else {
    Write-Host ""
    Write-Host "You can run it later with: streamlit run aws_architecture_explorer_app_direct.py" -ForegroundColor Gray
}
