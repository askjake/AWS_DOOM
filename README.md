# AWS Architecture Explorer (Direct Access Version)

## Overview
This is a refactored version of the AWS Architecture Explorer that connects **directly** to AWS without requiring an SSH bastion host.

## What Changed?

### ❌ Removed
- SSH bastion dependency
- `DEFAULT_BASTION` configuration
- SSH command wrapping via `build_ssh_bash_cmd()`

### ✅ Added
- Direct AWS CLI execution from the local host
- AWS profile support (optional)
- Improved error messages
- Schema version 7 with `execution_mode: "direct"` metadata

## Installation

```bash
cd /tmp/dish_chat_agent/aws_arch_refactor
pip install -r requirements.txt
```

## Usage

### Run the Streamlit App
```bash
streamlit run aws_architecture_explorer_app_direct.py
```

### Required Setup
1. **AWS CLI must be installed** on your host
2. **AWS credentials must be configured** (via `~/.aws/credentials` or environment variables)
3. **Sufficient IAM permissions** to describe EC2, EKS, ELB, RDS, and S3 resources

### Using AWS Profiles
If you have multiple AWS profiles configured, you can specify which one to use in the sidebar:
- Leave blank to use the default profile
- Enter a profile name (e.g., "production", "dev") to use that profile

## Command Comparison

### Before (SSH Bastion):
```bash
ssh david-bastion -- bash -lc 'AWS_PAGER="" aws ec2 describe-vpcs --region us-west-2 --output json'
```

### After (Direct):
```bash
aws ec2 describe-vpcs --region us-west-2 --output json
```
*Executed locally with `AWS_PAGER=""` in the environment*

## Files

- **aws_architecture_snapshot_lib_direct.py** - Core library with AWS discovery functions
- **aws_architecture_explorer_app_direct.py** - Streamlit UI application
- **requirements.txt** - Python dependencies

## Compatibility

- Snapshot schema version: **7** (v6 used bastion, v7 is direct)
- Can load snapshots created by v6 (original) but will re-save as v7
- All visualization features remain identical

## Testing

To test that AWS CLI access works:
```bash
# Test basic connectivity
aws sts get-caller-identity

# Test EC2 access
aws ec2 describe-vpcs --region us-west-2

# Test with a specific profile
aws eks list-clusters --region us-west-2 --profile myprofile
```

## Troubleshooting

### "Unable to locate credentials"
Ensure AWS credentials are configured:
```bash
aws configure
# Or set environment variables:
export AWS_ACCESS_KEY_ID=your_key
export AWS_SECRET_ACCESS_KEY=your_secret
export AWS_DEFAULT_REGION=us-west-2
```

### "AccessDenied" errors
Verify your IAM user/role has permissions:
- `ec2:Describe*`
- `eks:List*`, `eks:Describe*`
- `elasticloadbalancing:Describe*`
- `rds:Describe*`
- `s3:ListAllMyBuckets`, `s3:GetBucketVersioning`

## Original Application

This is a refactored version. The original application can be found at:
`/home/montjac/AWS_Architecture_explorer/`
