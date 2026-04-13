#!/bin/bash
# Deployment script for AWS Architecture Explorer (Direct Access)

set -e

echo "======================================"
echo "AWS Architecture Explorer Deployment"
echo "======================================"
echo

# Check if AWS CLI is available
if ! command -v aws &> /dev/null; then
    echo "❌ ERROR: AWS CLI is not installed"
    echo "   Install it first: https://aws.amazon.com/cli/"
    exit 1
fi
echo "✅ AWS CLI is installed"

# Check if AWS credentials are configured
if ! aws sts get-caller-identity &> /dev/null; then
    echo "❌ ERROR: AWS credentials are not configured"
    echo "   Run 'aws configure' to set up your credentials"
    exit 1
fi
echo "✅ AWS credentials are configured"

# Get current AWS identity
echo
echo "Current AWS Identity:"
aws sts get-caller-identity
echo

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ ERROR: Python 3 is not installed"
    exit 1
fi
echo "✅ Python 3 is installed"

# Install dependencies
echo
echo "Installing Python dependencies..."
pip install -q -r requirements.txt
echo "✅ Dependencies installed"

# Create snapshots directory
mkdir -p snapshots
echo "✅ Snapshots directory ready: ./snapshots"

echo
echo "======================================"
echo "✅ Deployment complete!"
echo "======================================"
echo
echo "To run the application:"
echo "  streamlit run aws_architecture_explorer_app_direct.py"
echo
echo "To test AWS connectivity:"
echo "  python3 -c 'from aws_architecture_snapshot_lib_direct import run_aws_json; print(run_aws_json("sts", "get-caller-identity", region="us-west-2"))'"
echo
