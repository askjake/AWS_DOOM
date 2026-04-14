# AWS Architecture Explorer - Windows Installation Guide

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
cd C:\path	ows_arch_refactor

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
cd C:\path	ows_arch_refactor

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
C:\path	ows_arch_refactorun_app.bat

REM Or with full paths:
cd /d D:\MyDocuments
D:\Downloadsws_arch_refactorun_app.bat
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
aws_arch_refactor├── deploy.bat                              # Windows deployment (double-click this)
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
