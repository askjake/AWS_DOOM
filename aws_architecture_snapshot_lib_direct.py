#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""AWS Architecture Snapshot Library - Direct Access Version

Refactored to work directly from the host without SSH bastion dependency.
All AWS CLI calls are executed locally using subprocess.
"""

from __future__ import annotations

import datetime as dt
import json
import os
import shlex
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

DEFAULT_REGION = os.environ.get("AWS_REGION", "us-west-2")
DEFAULT_SNAPSHOT_DIR = os.environ.get("AWS_SNAPSHOT_DIR", "snapshots")


def utc_now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _ensure_dir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)


def save_snapshot(snapshot: Dict[str, Any], out_path: Path) -> Path:
    out_path = Path(out_path)
    _ensure_dir(out_path.parent)
    tmp = out_path.with_suffix(out_path.suffix + ".tmp")
    tmp.write_text(json.dumps(snapshot, indent=2, default=str), encoding="utf-8")
    tmp.replace(out_path)
    return out_path


def load_snapshot(path: Path) -> Dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def list_snapshots(snapshot_dir: Path | str = DEFAULT_SNAPSHOT_DIR) -> List[Path]:
    d = Path(snapshot_dir)
    if not d.exists():
        return []
    return sorted(d.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)


# Back-compat alias
def list_snapshot_files(snapshot_dir: Path | str = DEFAULT_SNAPSHOT_DIR) -> List[Path]:
    return list_snapshots(snapshot_dir)


def default_snapshot_name(prefix: str = "aws_snapshot") -> str:
    ts = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{prefix}_{ts}.json"


def parse_json_loose(stdout: str) -> Any:
    """Try strict JSON first, then scan stdout for first JSON object/array.

    This recovers from MOTD/banner/profile noise.
    """
    s = (stdout or "").strip()
    if not s:
        return {}
    try:
        return json.loads(s)
    except Exception:
        pass

    dec = json.JSONDecoder()
    for i, ch in enumerate(s):
        if ch not in "{[":
            continue
        try:
            obj, _end = dec.raw_decode(s[i:])
            return obj
        except Exception:
            continue

    raise json.JSONDecodeError("No JSON found in output", s, 0)


def _run(cmd: List[str], timeout_s: int = 180, env: Optional[Dict[str, str]] = None) -> subprocess.CompletedProcess:
    """Execute command locally with optional environment variables."""
    import os
    
    # Merge with current environment
    full_env = os.environ.copy()
    if env:
        full_env.update(env)
    
    return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout_s, env=full_env)


def run_cmd_json(cmd: List[str], timeout_s: int = 180, env: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    """Execute command and parse JSON output."""
    p = _run(cmd, timeout_s=timeout_s, env=env)

    if p.returncode != 0:
        raise RuntimeError(
            "Command failed (rc=%s).\nCMD: %s\nSTDERR:\n%s\nSTDOUT:\n%s"
            % (p.returncode, " ".join(cmd), (p.stderr or ""), (p.stdout or ""))
        )

    out = (p.stdout or "")
    try:
        obj = parse_json_loose(out)
    except json.JSONDecodeError as e:
        raise RuntimeError(
            "Command did not return JSON.\nCMD: %s\nERR: %s\nRAW (first 4000 chars):\n%s"
            % (" ".join(cmd), str(e), out[:4000])
        )

    if isinstance(obj, dict):
        return obj
    return {"_list": obj}


def build_aws_cli_cmd(
    service: str,
    *args: str,
    region: Optional[str],
    output: str = "json",
    profile: Optional[str] = None,
) -> Tuple[List[str], Dict[str, str]]:
    """Build AWS CLI command and environment variables.
    
    Returns:
        Tuple of (command_list, environment_dict)
    """
    parts = ["aws", service] + list(args)
    if region:
        parts += ["--region", region]
    if output:
        parts += ["--output", output]
    if profile:
        parts += ["--profile", profile]
    
    # Set AWS_PAGER to empty to prevent paging
    env = {"AWS_PAGER": ""}
    
    return parts, env


def run_aws_json(
    service: str,
    *args: str,
    region: str,
    timeout_s: int = 180,
    profile: Optional[str] = None,
) -> Dict[str, Any]:
    """Execute AWS CLI command locally and return JSON result."""
    cmd, env = build_aws_cli_cmd(service, *args, region=region, output="json", profile=profile)
    return run_cmd_json(cmd, timeout_s=timeout_s, env=env)


def as_list_of_dicts(x: Any) -> List[Dict[str, Any]]:
    """Accept list[dict], dict[id->dict], or single dict; return list[dict]."""
    if x is None:
        return []
    if isinstance(x, list):
        return [i for i in x if isinstance(i, dict)]
    if isinstance(x, dict):
        vals = list(x.values())
        if vals and all(isinstance(v, dict) for v in vals):
            return vals
        return [x]
    return []


def discover_vpcs(region: str, profile: Optional[str] = None) -> Dict[str, Any]:
    """Discover VPCs, subnets, and security groups."""
    vpcs = run_aws_json("ec2", "describe-vpcs", region=region, profile=profile).get("Vpcs", [])
    subs = run_aws_json("ec2", "describe-subnets", region=region, profile=profile).get("Subnets", [])
    sgs = run_aws_json("ec2", "describe-security-groups", region=region, profile=profile).get("SecurityGroups", [])
    return {"vpcs": vpcs, "subnets": subs, "security_groups": sgs}


def discover_eks(region: str, include_node_instances: bool = False, profile: Optional[str] = None) -> Dict[str, Any]:
    """Discover EKS clusters, nodegroups, and optionally EC2 instances."""
    clusters = run_aws_json("eks", "list-clusters", region=region, profile=profile).get("clusters", [])
    out_clusters: List[Dict[str, Any]] = []

    for name in clusters:
        desc = run_aws_json("eks", "describe-cluster", "--name", name, region=region, profile=profile).get("cluster", {})
        nodegroups = run_aws_json("eks", "list-nodegroups", "--cluster-name", name, region=region, profile=profile).get("nodegroups", [])
        ng_descs: List[Dict[str, Any]] = []
        for ng in nodegroups:
            ngd = run_aws_json(
                "eks", "describe-nodegroup",
                "--cluster-name", name, "--nodegroup-name", ng,
                region=region, profile=profile
            ).get("nodegroup", {})
            ng_descs.append(ngd)

        desc["nodegroups"] = ng_descs
        out_clusters.append(desc)

    node_instances_raw: List[Dict[str, Any]] = []
    if include_node_instances:
        node_instances_raw = run_aws_json("ec2", "describe-instances", region=region, profile=profile).get("Reservations", [])

    return {"clusters": out_clusters, "node_instances_raw": node_instances_raw}


def discover_load_balancers(region: str, include_non_internet_lbs: bool = False, profile: Optional[str] = None) -> Dict[str, Any]:
    """Discover ELBv2 load balancers."""
    lbs = run_aws_json("elbv2", "describe-load-balancers", region=region, profile=profile).get("LoadBalancers", [])
    if not include_non_internet_lbs:
        lbs = [lb for lb in lbs if lb.get("Scheme") == "internet-facing"]
    return {"load_balancers": lbs}


def discover_rds(region: str, profile: Optional[str] = None) -> Dict[str, Any]:
    """Discover RDS database instances."""
    dbs = run_aws_json("rds", "describe-db-instances", region=region, profile=profile).get("DBInstances", [])
    return {"db_instances": dbs}


def _classify_s3_versioning_error(err: str) -> Tuple[str, str]:
    """Classify S3 API errors."""
    e = (err or "").lower()
    if "accessdenied" in e or "explicit deny" in e:
        return ("AccessDenied", err.strip())
    if "nosuchbucket" in e:
        return ("NoSuchBucket", err.strip())
    if "invalidbucketname" in e:
        return ("InvalidBucketName", err.strip())
    return ("Error", err.strip())


def discover_s3_versioning(region: str, bucket_limit: int = 200, profile: Optional[str] = None) -> Dict[str, Any]:
    """Discover S3 bucket versioning configuration."""
    buckets = run_aws_json("s3api", "list-buckets", region=region, profile=profile).get("Buckets", [])
    buckets = buckets[: max(0, int(bucket_limit))]

    rows: List[Dict[str, Any]] = []
    for b in buckets:
        name = b.get("Name")
        if not name:
            continue

        row = {
            "Bucket": name,
            "Versioning": "Unknown",
            "MFADelete": "Unknown",
            "Created": b.get("CreationDate"),
            "ErrorType": "",
            "ErrorDetail": "",
        }

        try:
            ver = run_aws_json("s3api", "get-bucket-versioning", "--bucket", name, region=region, profile=profile)
            row["Versioning"] = ver.get("Status") or "None"  # Enabled | Suspended | None
            row["MFADelete"] = ver.get("MFADelete") or "None"
        except Exception as e:
            status, detail = _classify_s3_versioning_error(str(e))
            row["Versioning"] = status
            row["MFADelete"] = status
            row["ErrorType"] = status
            row["ErrorDetail"] = detail[:2000]

        rows.append(row)

    return {"s3_versioning": rows}


def collect_arch_snapshot(
    *,
    region: str = DEFAULT_REGION,
    profile: Optional[str] = None,
    include_node_instances: bool = False,
    include_non_internet_lbs: bool = False,
    include_s3: bool = False,
    s3_bucket_limit: int = 200,
) -> Dict[str, Any]:
    """Collect complete AWS architecture snapshot.
    
    Args:
        region: AWS region to scan
        profile: AWS profile to use (optional)
        include_node_instances: Include EC2 instance details
        include_non_internet_lbs: Include internal load balancers
        include_s3: Include S3 versioning report
        s3_bucket_limit: Maximum number of S3 buckets to check
        
    Returns:
        Complete snapshot dictionary
    """
    base: Dict[str, Any] = {
        "schema_version": 7,  # Incremented for direct-access version
        "generated_at": utc_now_iso(),
        "region": region,
        "profile": profile or "default",
        "execution_mode": "direct",  # No bastion
        "options": {
            "include_node_instances": bool(include_node_instances),
            "include_non_internet_lbs": bool(include_non_internet_lbs),
            "include_s3": bool(include_s3),
            "s3_bucket_limit": int(s3_bucket_limit),
        },
    }

    base["vpc"] = discover_vpcs(region=region, profile=profile)
    base["eks"] = discover_eks(region=region, include_node_instances=include_node_instances, profile=profile)
    base["elbv2"] = discover_load_balancers(region=region, include_non_internet_lbs=include_non_internet_lbs, profile=profile)
    base["rds"] = discover_rds(region=region, profile=profile)

    if include_s3:
        base["s3"] = discover_s3_versioning(region=region, bucket_limit=s3_bucket_limit, profile=profile)
    else:
        base["s3"] = {"s3_versioning": []}

    return base
