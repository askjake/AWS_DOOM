# AWS DOOM - First-Person AWS Architecture Explorer

A DOOM-style first-person 3D game that transforms AWS infrastructure snapshots into an explorable dungeon.

## Features

- 3D Raycasting Engine - Classic DOOM-style rendering
- Real AWS Data - Visualizes actual AWS infrastructure
- Interactive Navigation - Walk through VPCs, subnets, security groups
- Hallway System - Connected rooms representing network topology
- Visual Enhancements - Textured walls, signs, directional arrows
- Web Interface - Play in browser via Flask + Socket.IO
- Key System - Collect authorization keys for secured resources

## Quick Start

Desktop Version:
  pip install pygame>=2.5.0
  ./run_aws_doom.sh

Web Version:
  pip install -r requirements_web.txt
  ./run_web_server.sh
  # Open browser to http://localhost:5000

## Controls

- W/S - Move forward/backward
- A/D - Rotate left/right
- E - Interact / Collect key
- M - Toggle minimap
- ESC - Quit

## Credits

- Concept: DOOM-style AWS infrastructure visualization
- Engine: Custom Python raycasting
- Inspired by: id Software DOOM (1993)
- Date: April 2026

Explore your AWS infrastructure like never before!
