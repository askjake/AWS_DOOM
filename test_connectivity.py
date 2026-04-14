#!/usr/bin/env python3
"""Quick test script to verify AWS connectivity without running full app."""

import sys
from pathlib import Path

# Add current directory to path so we can import the library
sys.path.insert(0, str(Path(__file__).parent))

from aws_architecture_snapshot_lib_direct import run_aws_json, DEFAULT_REGION

def test_connectivity():
    """Test AWS CLI connectivity and permissions."""
    print("=" * 70)
    print("AWS CONNECTIVITY TEST")
    print("=" * 70)
    print()
    
    # Test 1: Get caller identity
    print("Test 1: Verifying AWS credentials...")
    try:
        result = run_aws_json("sts", "get-caller-identity", region=DEFAULT_REGION)
        print(f"✅ SUCCESS - Connected as:")
        print(f"   User ARN: {result.get('Arn')}")
        print(f"   Account: {result.get('Account')}")
        print(f"   User ID: {result.get('UserId')}")
    except Exception as e:
        print(f"❌ FAILED - {str(e)}")
        print("
Please run: aws configure")
        return False
    print()
    
    # Test 2: List VPCs
    print(f"Test 2: Listing VPCs in {DEFAULT_REGION}...")
    try:
        result = run_aws_json("ec2", "describe-vpcs", region=DEFAULT_REGION)
        vpcs = result.get("Vpcs", [])
        print(f"✅ SUCCESS - Found {len(vpcs)} VPC(s)")
        for vpc in vpcs[:3]:  # Show first 3
            vpc_id = vpc.get("VpcId")
            cidr = vpc.get("CidrBlock")
            print(f"   - {vpc_id} ({cidr})")
        if len(vpcs) > 3:
            print(f"   ... and {len(vpcs) - 3} more")
    except Exception as e:
        print(f"❌ FAILED - {str(e)}")
        return False
    print()
    
    # Test 3: List EKS clusters
    print(f"Test 3: Listing EKS clusters in {DEFAULT_REGION}...")
    try:
        result = run_aws_json("eks", "list-clusters", region=DEFAULT_REGION)
        clusters = result.get("clusters", [])
        print(f"✅ SUCCESS - Found {len(clusters)} EKS cluster(s)")
        for cluster in clusters:
            print(f"   - {cluster}")
    except Exception as e:
        print(f"⚠️  LIMITED ACCESS - {str(e)}")
        print("   (EKS permissions may not be available)")
    print()
    
    print("=" * 70)
    print("✅ CONNECTIVITY TEST COMPLETE")
    print("=" * 70)
    print()
    print("Ready to run:")
    print("  streamlit run aws_architecture_explorer_app_direct.py")
    return True

if __name__ == "__main__":
    success = test_connectivity()
    sys.exit(0 if success else 1)
