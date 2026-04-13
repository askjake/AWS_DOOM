
from pathlib import Path

# Create PowerShell deployment script
powershell_script = '''# AWS Architecture Explorer - Windows Deployment Script
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
'''

ps1_path = Path("/tmp/dish_chat_agent/aws_arch_refactor/deploy.ps1")
ps1_path.write_text(powershell_script)
print(f"✅ Created PowerShell script: {ps1_path}")
print()

# Create batch file wrapper
batch_script = '''@echo off
REM AWS Architecture Explorer - Windows Deployment Script
REM Batch file wrapper for PowerShell script

echo ======================================
echo AWS Architecture Explorer Deployment
echo ======================================
echo.

REM Check if PowerShell is available
where powershell >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] PowerShell is not available
    echo Please install PowerShell or run deploy.ps1 manually
    pause
    exit /b 1
)

REM Run PowerShell script with execution policy bypass
echo Running deployment script...
echo.
powershell -ExecutionPolicy Bypass -File "%~dp0deploy.ps1"

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Deployment failed
    pause
    exit /b 1
)

echo.
echo Deployment completed successfully!
pause
'''

bat_path = Path("/tmp/dish_chat_agent/aws_arch_refactor/deploy.bat")
bat_path.write_text(batch_script)
print(f"✅ Created batch file: {bat_path}")
print()

# Create run application batch file
run_app_batch = '''@echo off
REM AWS Architecture Explorer - Run Application
REM Quick launch script for Windows

echo ======================================
echo AWS Architecture Explorer
echo ======================================
echo.

REM Check if Python is available
where python >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    set PYTHON_CMD=python
    goto :check_streamlit
)

where python3 >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    set PYTHON_CMD=python3
    goto :check_streamlit
)

echo [ERROR] Python is not installed or not in PATH
echo Please install Python: https://www.python.org/downloads/
pause
exit /b 1

:check_streamlit
REM Check if Streamlit is installed
%PYTHON_CMD% -c "import streamlit" >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Streamlit is not installed
    echo.
    echo Run deployment script first:
    echo   deploy.bat
    echo.
    pause
    exit /b 1
)

REM Check if app file exists
if not exist "aws_architecture_explorer_app_direct.py" (
    echo [ERROR] Application file not found
    echo   aws_architecture_explorer_app_direct.py
    echo.
    echo Make sure you are in the correct directory
    pause
    exit /b 1
)

REM Run the application
echo Starting Streamlit application...
echo.
echo The app will open in your default browser.
echo Press Ctrl+C to stop the application.
echo.

streamlit run aws_architecture_explorer_app_direct.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Failed to start application
    pause
    exit /b 1
)
'''

run_app_path = Path("/tmp/dish_chat_agent/aws_arch_refactor/run_app.bat")
run_app_path.write_text(run_app_batch)
print(f"✅ Created run application batch file: {run_app_path}")
print()

# Create a Windows-specific README
windows_readme = '''# AWS Architecture Explorer - Windows Installation Guide

## Quick Start (Easy Mode)

1. **Download all files** from the project
2. **Double-click `deploy.bat`** - It will check everything and install dependencies
3. **Double-click `run_app.bat`** - Launches the application
4. **Browser will open** automatically with the Streamlit app

## Prerequisites

### 1. Install AWS CLI for Windows

**Option A: MSI Installer (Recommended)**
- Download: https://aws.amazon.com/cli/
- Run the installer and follow prompts
- Verify: Open Command Prompt and run `aws --version`

**Option B: Chocolatey**
```powershell
choco install awscli
```

**Option C: Scoop**
```powershell
scoop install aws
```

### 2. Install Python

**Option A: Official Installer (Recommended)**
- Download: https://www.python.org/downloads/
- Check "Add Python to PATH" during installation
- Verify: `python --version`

**Option B: Windows Store**
- Search for "Python 3.12" in Microsoft Store
- Click Install

**Option C: Chocolatey**
```powershell
choco install python
```

### 3. Configure AWS Credentials

Open Command Prompt or PowerShell:
```cmd
aws configure
```

You'll need:
- AWS Access Key ID
- AWS Secret Access Key  
- Default region (e.g., `us-west-2`)
- Output format: `json`

Test it works:
```cmd
aws sts get-caller-identity
```

## Manual Installation

If the batch files don't work, follow these steps:

### Step 1: Open PowerShell as Administrator
```powershell
# Navigate to the project directory
cd C:\path\to\aws_arch_refactor

# Allow script execution (if needed)
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Step 2: Run Deployment Script
```powershell
.\deploy.ps1
```

### Step 3: Run the Application
```powershell
streamlit run aws_architecture_explorer_app_direct.py
```

## Alternative: Command Prompt Installation

```cmd
REM Navigate to project directory
cd C:\path\to\aws_arch_refactor

REM Install dependencies
python -m pip install -r requirements.txt

REM Create snapshots directory
mkdir snapshots

REM Test connectivity
python test_connectivity.py

REM Run application
streamlit run aws_architecture_explorer_app_direct.py
```

## Troubleshooting

### "PowerShell script cannot be loaded"

**Error:**
```
deploy.ps1 cannot be loaded because running scripts is disabled on this system
```

**Solution:**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Or use the batch file:
```cmd
deploy.bat
```

### "aws is not recognized"

**Error:**
```
'aws' is not recognized as an internal or external command
```

**Solution:**
1. Reinstall AWS CLI
2. Add to PATH manually:
   - Search "Environment Variables" in Windows
   - Edit "Path" variable
   - Add: `C:\Program Files\Amazon\AWSCLIV2`
   - Restart Command Prompt

### "python is not recognized"

**Error:**
```
'python' is not recognized as an internal or external command
```

**Solution:**
1. Reinstall Python with "Add to PATH" checked
2. Or use `py` command instead:
   ```cmd
   py -m pip install -r requirements.txt
   py test_connectivity.py
   streamlit run aws_architecture_explorer_app_direct.py
   ```

### "Unable to locate credentials"

**Error:**
```
Unable to locate credentials. You can configure credentials by running "aws configure"
```

**Solution:**
```cmd
aws configure
```

Enter your AWS credentials when prompted.

### Streamlit opens blank page

**Solution:**
1. Check firewall isn't blocking port 8501
2. Try accessing: http://localhost:8501
3. Stop other Streamlit instances:
   ```cmd
   taskkill /IM streamlit.exe /F
   ```

### "Access Denied" errors in app

**Solution:**
Your AWS IAM user/role needs these permissions:
- `ec2:Describe*`
- `eks:List*`, `eks:Describe*`
- `elasticloadbalancing:Describe*`
- `rds:Describe*`
- `s3:ListAllMyBuckets`, `s3:GetBucketVersioning`

Contact your AWS administrator to grant these.

## Running from Different Directories

The batch files work from any location:

```cmd
REM From any directory:
C:\path\to\aws_arch_refactor\run_app.bat

REM Or with full paths:
cd /d D:\MyDocuments
D:\Downloads\aws_arch_refactor\run_app.bat
```

## Using AWS Profiles

If you have multiple AWS accounts configured:

1. Check your profiles:
   ```cmd
   aws configure list-profiles
   ```

2. In the Streamlit app sidebar:
   - Enter the profile name in "AWS Profile" field
   - Leave blank for default profile

3. Or set environment variable:
   ```cmd
   set AWS_PROFILE=myprofile
   run_app.bat
   ```

## Performance Tips

### Speed up snapshot collection:
1. Uncheck "Include EC2 node instances" (heavy operation)
2. Reduce "S3 bucket limit" if you have many buckets
3. Use a specific region instead of scanning multiple regions

### If the app is slow:
1. Close other applications
2. Use "VPC-centered" view (lightest)
3. Reduce "Graph density" slider
4. Set "Detail level" to 0 or 1

## File Structure

```
aws_arch_refactor\
├── deploy.bat                              # Windows deployment (double-click this)
├── deploy.ps1                              # PowerShell deployment script
├── run_app.bat                             # Launch application (double-click this)
├── aws_architecture_explorer_app_direct.py # Main Streamlit app
├── aws_architecture_snapshot_lib_direct.py # Core library
├── test_connectivity.py                    # Connectivity test
├── requirements.txt                        # Python dependencies
├── README.md                               # Main documentation
├── WINDOWS_README.md                       # This file
├── COMPARISON.md                           # Code changes documentation
├── SUMMARY.md                              # Project summary
└── snapshots\                              # Saved snapshots (created automatically)
```

## Uninstall

To remove:
1. Delete the `aws_arch_refactor` folder
2. (Optional) Uninstall Python packages:
   ```cmd
   pip uninstall streamlit streamlit-agraph -y
   ```

## Support

### Test basic connectivity:
```cmd
REM 1. Check AWS CLI
aws --version

REM 2. Check credentials
aws sts get-caller-identity

REM 3. Check Python
python --version

REM 4. Test AWS access
python test_connectivity.py

REM 5. Check Streamlit
streamlit --version
```

### Get help:
```cmd
REM AWS CLI help
aws help

REM Streamlit help
streamlit --help

REM Python help
python --help
```

## Next Steps

1. ✅ Run `deploy.bat` to set up everything
2. ✅ Run `run_app.bat` to launch the app
3. ✅ In the app, click "Collect snapshot now" in sidebar
4. ✅ Explore the architecture visualization
5. ✅ Check "Outside-in security review" tab for findings

---

**Pro Tip:** Create a desktop shortcut to `run_app.bat` for quick access!

**Note:** This application runs locally on your machine. Your AWS credentials never leave your computer.
'''

windows_readme_path = Path("/tmp/dish_chat_agent/aws_arch_refactor/WINDOWS_README.md")
windows_readme_path.write_text(windows_readme)
print(f"✅ Created Windows README: {windows_readme_path}")
print()

# Create a desktop shortcut creator script
shortcut_script = '''# Create Desktop Shortcut for AWS Architecture Explorer
# PowerShell script

$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$batPath = Join-Path $scriptPath "run_app.bat"

if (-not (Test-Path $batPath)) {
    Write-Host "[ERROR] run_app.bat not found in current directory" -ForegroundColor Red
    Write-Host "Please run this script from the aws_arch_refactor directory" -ForegroundColor Yellow
    pause
    exit 1
}

$desktopPath = [Environment]::GetFolderPath("Desktop")
$shortcutPath = Join-Path $desktopPath "AWS Architecture Explorer.lnk"

Write-Host "Creating desktop shortcut..." -ForegroundColor Yellow
Write-Host "  Target: $batPath" -ForegroundColor Gray
Write-Host "  Desktop: $desktopPath" -ForegroundColor Gray

try {
    $shell = New-Object -ComObject WScript.Shell
    $shortcut = $shell.CreateShortcut($shortcutPath)
    $shortcut.TargetPath = $batPath
    $shortcut.WorkingDirectory = $scriptPath
    $shortcut.Description = "AWS Architecture Explorer - Direct Access"
    $shortcut.IconLocation = "C:\Windows\System32\shell32.dll,13"  # Cloud icon
    $shortcut.Save()
    
    Write-Host ""
    Write-Host "[SUCCESS] Shortcut created on desktop!" -ForegroundColor Green
    Write-Host ""
    Write-Host "You can now double-click the shortcut to launch the app" -ForegroundColor Cyan
    
} catch {
    Write-Host ""
    Write-Host "[ERROR] Failed to create shortcut" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
}

Write-Host ""
pause
'''

shortcut_path = Path("/tmp/dish_chat_agent/aws_arch_refactor/create_shortcut.ps1")
shortcut_path.write_text(shortcut_script)
print(f"✅ Created shortcut creator: {shortcut_path}")
print()

# Create quick reference card
quick_ref = '''╔═══════════════════════════════════════════════════════════════════╗
║          AWS ARCHITECTURE EXPLORER - WINDOWS QUICK REFERENCE      ║
╚═══════════════════════════════════════════════════════════════════╝

📦 INSTALLATION (First Time Only)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. Double-click: deploy.bat
   (Installs everything automatically)

🚀 RUNNING THE APP
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. Double-click: run_app.bat
   (Opens in your browser automatically)

🔧 MANUAL COMMANDS (If batch files don't work)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Deploy:     powershell -ExecutionPolicy Bypass -File deploy.ps1
Test:       python test_connectivity.py
Run App:    streamlit run aws_architecture_explorer_app_direct.py

⚙️ PREREQUISITES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✓ AWS CLI    https://aws.amazon.com/cli/
✓ Python     https://www.python.org/downloads/
✓ Configure: aws configure

🧪 TESTING
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Check AWS CLI:      aws --version
Check credentials:  aws sts get-caller-identity
Test connectivity:  python test_connectivity.py

📁 KEY FILES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
deploy.bat          → Install & setup (run once)
run_app.bat         → Launch application (run anytime)
WINDOWS_README.md   → Full Windows documentation
SUMMARY.md          → Project overview

🛠️ TROUBLESHOOTING
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"aws not recognized"
  → Add to PATH or reinstall AWS CLI

"python not recognized"  
  → Add to PATH or use: py -m pip install -r requirements.txt

"Unable to locate credentials"
  → Run: aws configure

"Cannot load PowerShell script"
  → Use deploy.bat instead, or run:
    Set-ExecutionPolicy RemoteSigned -Scope CurrentUser

"Access Denied" in app
  → IAM permissions needed: ec2:Describe*, eks:*, rds:*, s3:*

📱 DESKTOP SHORTCUT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Create:  powershell -ExecutionPolicy Bypass -File create_shortcut.ps1

🌐 APP USAGE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. Sidebar → Configure Region & Options
2. Click "Collect snapshot now"
3. View architecture graph
4. Check "Outside-in security review" tab
5. Download snapshot JSON for later

💡 TIPS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• Use AWS_PROFILE env var for multi-account: set AWS_PROFILE=prod
• Snapshots saved in: .\snapshots\
• Press Ctrl+C in terminal to stop app
• Browser: http://localhost:8501

📧 SUPPORT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Read WINDOWS_README.md for detailed troubleshooting

╔═══════════════════════════════════════════════════════════════════╗
║  Quick Start: deploy.bat → run_app.bat → Collect snapshot        ║
╚═══════════════════════════════════════════════════════════════════╝
'''

quick_ref_path = Path("/tmp/dish_chat_agent/aws_arch_refactor/QUICK_START_WINDOWS.txt")
quick_ref_path.write_text(quick_ref)
print(f"✅ Created quick reference: {quick_ref_path}")
print()

print("=" * 70)
print("WINDOWS DEPLOYMENT SCRIPTS CREATED")
print("=" * 70)
print()
print("Created files:")
print("  1. deploy.ps1           - PowerShell deployment script (full featured)")
print("  2. deploy.bat           - Batch wrapper (double-click friendly)")
print("  3. run_app.bat          - Quick launch script")
print("  4. WINDOWS_README.md    - Complete Windows guide")
print("  5. create_shortcut.ps1  - Desktop shortcut creator")
print("  6. QUICK_START_WINDOWS.txt - Quick reference card")
print()
print("=" * 70)
print("QUICK START FOR WINDOWS USERS")
print("=" * 70)
print()
print("1. Download all files from the project")
print("2. Double-click: deploy.bat")
print("3. Double-click: run_app.bat")
print("4. Browser opens automatically!")
print()
print("That's it! 🎉")
