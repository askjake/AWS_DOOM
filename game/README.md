# AWS DOOM - First-Person AWS Architecture Explorer

## Overview

AWS DOOM is a DOOM-style first-person 3D game that transforms your AWS infrastructure snapshots into an explorable dungeon. Navigate through VPCs, subnets, security groups, EKS clusters, load balancers, and RDS instances as if they were rooms and hallways in a classic FPS game.

## Features

### Core Gameplay
- 3D Raycasting Engine: Classic DOOM-style rendering with distance shading
- Real AWS Architecture: Maps are generated from actual AWS snapshot data
- Interactive Exploration: Walk through your infrastructure like a dungeon
- Security Visualization: Locked rooms represent security groups and private resources
- Key Collection System: Collect "keys" (authorizations) to access restricted areas

### Visualization
- Resource Metadata: View detailed AWS resource information as you explore
- Minimap: Toggle a 2D overhead map to see your location
- Color-Coded Resources:
  - Blue = VPCs (Virtual Private Clouds)
  - Cyan = Subnets
  - Orange = Security Groups (require keys)
  - Purple = EKS Clusters
  - Green = Load Balancers
  - Red = RDS Databases (may require keys)
  - Yellow = S3 Buckets

## Architecture Design

The game generates a spatial representation of your AWS architecture:

1. VPCs are large container rooms (main areas)
2. Subnets are rooms within VPCs (subdivisions)
3. Security Groups are locked areas requiring authorization (access control)
4. EKS Clusters are major zones/areas (compute environments)
5. Load Balancers serve as entry points (internet-facing = unlocked)
6. RDS Instances are data vaults (private = locked, public = unlocked)
7. Hallways connect related resources (network paths)

This design accurately depicts the hierarchical and security structure of AWS.

## Installation

### Prerequisites

- Python 3.10 or higher
- AWS snapshot file (from AWS Architecture Explorer)

### Setup

```bash
cd ~/AWS_Architecture_explorer/AWS_DOOM/game
pip install -r requirements.txt
```

## Usage

### Quick Start (Linux/Mac)

```bash
cd ~/AWS_Architecture_explorer/AWS_DOOM/game
./run_aws_doom.sh
```

### Quick Start (Windows)

```bash
cd ~/AWS_Architecture_explorer/AWS_DOOM/game
run_aws_doom.bat
```

### Manual Launch

```bash
python3 aws_doom.py
```

This will automatically load the most recent snapshot from:
~/AWS_Architecture_explorer/snapshots/

### Specify Custom Snapshot

```bash
python3 aws_doom.py /path/to/your/snapshot.json
```

## Controls

| Key | Action |
|-----|--------|
| W | Move forward |
| S | Move backward |
| A | Rotate left |
| D | Rotate right |
| E | Interact / Collect key |
| M | Toggle minimap |
| ESC | Quit game |

## Gameplay Guide

### Objective

Explore your AWS infrastructure and collect "keys" (security authorizations) to access locked resources. Each room represents a real AWS resource with actual metadata from your environment.

### Starting Position

You spawn at:
1. The first internet-facing load balancer (if available), OR
2. The first VPC entry point

This represents the public entry point to your infrastructure.

### Locked Rooms (Red Overlay)

Some rooms are locked and require a "key":

- Security Groups: Represent access control policies
- Private RDS Instances: Require authorization to access
- Internal Load Balancers: Not publicly accessible

To unlock: Walk into a locked room and press E to collect its key.

### HUD Information

The bottom HUD displays:

- Location: Current resource type (VPC, Subnet, etc.)
- Resource Name: AWS resource identifier/CIDR/name
- Metadata: Resource details (CIDR blocks, AZ, status, etc.)
- Access Status: AUTHORIZED (green) or LOCKED (red)
- Keys Collected: Number of authorization keys obtained
- Position: Your X/Y coordinates on the map

### Minimap

Press M to toggle the overhead minimap (top-right corner).

The minimap shows:
- Green dot: Your current position
- Green line: Your viewing direction
- Colored lines: Walls representing AWS resources

## Technical Details

### Map Generation Algorithm

The game parses your AWS snapshot JSON and generates a spatial map:

1. Parse snapshot: Read VPCs, subnets, security groups, EKS clusters, load balancers, RDS, and S3
2. Create rooms: Generate rooms for each AWS resource with appropriate dimensions
3. Position resources: Place resources in a hierarchical layout
4. Generate walls: Create wall boundaries for each room
5. Apply security: Mark resources as locked/unlocked based on AWS accessibility
6. Set colors: Assign colors based on resource type
7. Connect resources: Add hallways to represent network connections

### Rendering Engine

- Technique: Raycasting (2.5D rendering like original DOOM)
- Field of View: 60 degrees
- Ray count: 120 rays per frame for smooth wall rendering
- Distance shading: Walls appear darker with distance
- Collision detection: Prevents walking through walls
- Locked door visualization: Red transparent overlay on inaccessible resources

### Performance

- Target FPS: 60 frames per second
- Optimized for: Snapshots with 10-50 resources
- Resource limits applied to prevent performance issues

## Troubleshooting

### "No snapshot files found"

Run the AWS Architecture Explorer snapshot collector:

```bash
cd ~/AWS_Architecture_explorer
python collect_snapshot.py --region us-west-2 --out snapshots/my_snapshot.json
```

### "Module pygame not found"

Install pygame:

```bash
pip install pygame>=2.5.0
```

## Architecture Accuracy

The game accurately represents:

- Hierarchical structure: VPCs contain subnets
- Access control: Security groups as locked areas
- Public vs private: Internet-facing resources are unlocked
- Resource metadata: Real AWS data displayed in HUD
- Connectivity: Hallways represent network paths
- Scale: Room size proportional to resource importance

The game is engaging and fun while always being architecturally accurate.

## Use Cases

1. Security Review: Visually explore which resources are locked vs accessible
2. Training: Teach new engineers about AWS architecture in an interactive way
3. Documentation: Generate engaging architecture walkthroughs
4. Presentations: Demonstrate AWS infrastructure in a unique format
5. Discovery: Find misconfigured or unexpected resources

## Credits

- Concept: DOOM-style visualization of AWS cloud infrastructure
- Engine: Custom Python raycasting engine using pygame
- Data Source: AWS Architecture Explorer snapshot library
- Inspired by: id Software's DOOM (1993)

---

Explore your AWS infrastructure like never before!
