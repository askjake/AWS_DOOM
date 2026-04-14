#!/usr/bin/env python3
"""
AWS DOOM - First-Person AWS Architecture Explorer
A DOOM-style 3D game that visualizes AWS infrastructure as a dungeon to navigate.
FIXED VERSION - Handles both flat and nested snapshot structures
"""

import pygame
import math
import json
import sys
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass, field
from enum import Enum


# Spacing and Layout Constants
ROOM_SIZE_SMALL = 120
ROOM_SIZE_MEDIUM = 180
ROOM_SIZE_LARGE = 240
ROOM_SIZE_XLARGE = 300
HALLWAY_WIDTH = 60
DOORWAY_SIZE = 80
ROOM_SPACING = 100
VPC_SPACING = 400

# Grid-based layout system for clean, organized maps
GRID_SIZE       = 400   # Size of each grid cell (pixels)
GRID_MARGIN     = 50    # Margin between grid cells
LB_COLUMN       = 0     # Load Balancers in column 0
VPC_COLUMN      = 2     # VPCs in column 2
SUBNET_COLUMN   = 4     # Subnets in column 4


# Initialize Pygame
pygame.init()

# Constants
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
FOV = math.pi / 3  # 60 degrees
HALF_FOV = FOV / 2
NUM_RAYS = 120
MAX_DEPTH = 800
DELTA_ANGLE = FOV / NUM_RAYS

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (100, 100, 100)
DARK_GRAY = (50, 50, 50)
RED = (200, 50, 50)
GREEN = (50, 200, 50)
BLUE = (50, 100, 200)
YELLOW = (200, 200, 50)
ORANGE = (255, 140, 0)
PURPLE = (150, 50, 200)
CYAN = (50, 200, 200)
FLOOR_COLOR = (30, 30, 30)
CEILING_COLOR = (60, 60, 80)

# AWS Resource Colors
# AWS-Themed Color Palette (from agentpi003 refactor)
AWS_ORANGE      = (255, 153, 0)   # Primary AWS brand
EC2_BLUE        = (35, 142, 214)  # Compute services
LAMBDA_GREEN    = (82, 196, 26)   # Serverless
S3_TEAL         = (100, 181, 246) # Storage
ALARM_RED       = (255, 69, 58)   # Danger/alerts
RDS_PURPLE      = (146, 43, 140)  # Databases
CEILING_TOP     = (8, 18, 32)     # Deep black
CEILING_BOTTOM  = (20, 40, 70)    # Dim blue ambient
FLOOR_TOP       = (25, 20, 15)    # Warm concrete
FLOOR_BOTTOM    = (10, 8, 6)      # Deep shadow

COLORS = {
    'vpc': EC2_BLUE,           # VPC walls use EC2 blue
    'subnet': S3_TEAL,         # Subnet walls use S3 teal
    'security_group': ALARM_RED, # Security groups are red (restricted)
    'eks_cluster': RDS_PURPLE, # EKS clusters purple
    'load_balancer': LAMBDA_GREEN, # Load balancers green
    'rds': RDS_PURPLE,         # RDS purple
    'hallway': (70, 70, 70),   # Hallways dark gray
    'default': AWS_ORANGE,     # Default AWS orange
    'floor': FLOOR_BOTTOM,
    'ceiling': CEILING_TOP,
}



# Movement
MOVE_SPEED = 5
ROTATE_SPEED = 0.05


class ResourceType(Enum):
    VPC = "vpc"
    SUBNET = "subnet"
    SECURITY_GROUP = "security_group"
    EKS_CLUSTER = "eks_cluster"
    LOAD_BALANCER = "load_balancer"
    RDS = "rds"
    S3 = "s3"
    HALLWAY = "hallway"


def lerp_color(c1: tuple, c2: tuple, t: float) -> tuple:
    """Linear interpolate between two RGB colors."""
    return tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))


def apply_distance_fog(color: tuple, distance: float, max_depth: float = MAX_DEPTH) -> tuple:
    """Apply exponential distance fog - dims color toward near-black."""
    fog_factor = 1.0 - min(1.0, (distance / max_depth) * 1.2)
    return tuple(int(c * fog_factor) for c in color)


def apply_scanline_texture(base_color: tuple, y: int, wall_height: int) -> tuple:
    """Simulate horizontal scanline texture banding for wall detail."""
    if wall_height == 0:
        return base_color
    # Alternate light/dark bands every ~6px
    band = int((y / max(wall_height, 1)) * wall_height / 6) % 2
    if band == 0:
        return tuple(min(255, int(c * 1.08)) for c in base_color)
    else:
        return tuple(int(c * 0.92) for c in base_color)


@dataclass
class Wall:
    x1: float
    y1: float
    x2: float
    y2: float
    color: Tuple[int, int, int]
    resource_type: ResourceType
    resource_name: str = ""
    resource_id: str = ""
    sign_text: str = ""  # Text to display on wall as sign
    direction_to: str = ""  # Direction indicator (e.g., "→ VPC-Main")
    texture_pattern: int = 0  # 0=solid, 1=striped, 2=dotted, 3=grid

    requires_key: bool = False
    
    
@dataclass
class Room:
    x: float
    y: float
    width: float
    height: float
    resource_type: ResourceType
    resource_name: str
    resource_id: str
    walls: List[Wall] = field(default_factory=list)
    requires_key: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    
@dataclass
class Player:
    x: float
    y: float
    angle: float
    keys: List[str] = field(default_factory=list)



def grid_to_world(row: int, col: int) -> tuple:
    """Convert grid coordinates to world pixel coordinates"""
    x = 100 + (col * (GRID_SIZE + GRID_MARGIN))
    y = 100 + (row * (GRID_SIZE + GRID_MARGIN))
    return (x, y)

class AWSMap:
    """Generate a DOOM-style map from AWS snapshot data"""
    
    def __init__(self, snapshot_path: str):
        self.snapshot = self._load_snapshot(snapshot_path)
        self.rooms: List[Room] = []
        self.walls: List[Wall] = []
        self.spawn_x = 100
        self.spawn_y = 100
        self._generate_map()
        
    def _load_snapshot(self, path: str) -> Dict[str, Any]:
        with open(path, 'r') as f:
            return json.load(f)
            
    def _generate_map(self):
        """Generate grid-based map with logical routing from AWS snapshot"""
        
        # Handle both nested and flat snapshot structures
        vpcs = []
        if 'vpc' in self.snapshot and isinstance(self.snapshot['vpc'], dict):
            vpcs = self.snapshot['vpc'].get('vpcs', [])
        elif 'vpcs' in self.snapshot:
            vpcs = self.snapshot.get('vpcs', [])
        
        subnets_all = []
        if 'vpc' in self.snapshot and isinstance(self.snapshot['vpc'], dict):
            subnets_all = self.snapshot['vpc'].get('subnets', [])
        elif 'subnets' in self.snapshot:
            subnets_all = self.snapshot.get('subnets', [])
        
        load_balancers = []
        if 'elbv2' in self.snapshot:
            load_balancers = self.snapshot['elbv2'].get('load_balancers', [])
        
        security_groups = []
        if 'ec2' in self.snapshot:
            security_groups = self.snapshot['ec2'].get('security_groups', [])
        
        # === GRID LAYOUT PLAN ===
        # Column 0: Load Balancers (entry points)
        # Column 1: Hallway connections
        # Column 2: VPCs (main containers)
        # Column 3: Hallway connections
        # Column 4: Subnets (network segments)
        # Column 5: Security Groups & Resources
        
        lb_row = 0
        vpc_row = 0
        
        # Track what we've created for connections
        lb_positions = {}
        vpc_positions = {}
        subnet_positions = {}
        
        # 1. CREATE LOAD BALANCERS (Entry points in column 0)
        for lb_idx, lb in enumerate(load_balancers[:5]):  # Limit to 5 LBs
            lb_name = lb.get('LoadBalancerName', f'LB-{lb_idx}')
            lb_arn = lb.get('LoadBalancerArn', f'arn-lb-{lb_idx}')
            vpc_id = lb.get('VpcId', None)
            
            # Place in grid
            lb_x, lb_y = grid_to_world(lb_row, LB_COLUMN)
            
            lb_room = self._create_room(
                lb_x, lb_y, ROOM_SIZE_MEDIUM, ROOM_SIZE_MEDIUM,
                ResourceType.LOAD_BALANCER, f"LB {lb_name[:15]}", lb_arn,
                sign_text=f"LB {lb_name[:15]}",
                direction_to=f"→ VPC {vpc_id[:8] if vpc_id else 'N/A'}"
            )
            self.rooms.append(lb_room)
            lb_positions[lb_arn] = (lb_row, LB_COLUMN, vpc_id)
            
            # Set spawn point at first Load Balancer
            if lb_idx == 0:
                self.spawn_x = lb_x + ROOM_SIZE_MEDIUM // 2
                self.spawn_y = lb_y + ROOM_SIZE_MEDIUM // 2
            
            lb_row += 1
        
        # 2. CREATE VPCs (Main containers in column 2)
        for vpc_idx, vpc in enumerate(vpcs[:8]):  # Limit to 8 VPCs
            vpc_id = vpc.get('VpcId', f'vpc-{vpc_idx}')
            vpc_cidr = vpc.get('CidrBlock', '0.0.0.0/0')
            
            # Place in grid
            vpc_x, vpc_y = grid_to_world(vpc_row, VPC_COLUMN)
            
            vpc_room = self._create_room(
                vpc_x, vpc_y, ROOM_SIZE_LARGE, ROOM_SIZE_LARGE,
                ResourceType.VPC, f"VPC {vpc_cidr}", vpc_id,
                sign_text=f"VPC {vpc_cidr}",
                direction_to="→ Subnets",
                metadata={'cidr': vpc_cidr, 'vpc_id': vpc_id}
            )
            self.rooms.append(vpc_room)
            vpc_positions[vpc_id] = (vpc_row, VPC_COLUMN)
            
            # 3. CREATE SUBNETS for this VPC (in column 4, aligned with VPC row)
            vpc_subnets = [s for s in subnets_all if s.get('VpcId') == vpc_id]
            
            for sub_idx, subnet in enumerate(vpc_subnets[:4]):  # Max 4 subnets per VPC
                subnet_id = subnet.get('SubnetId', f'subnet-{sub_idx}')
                subnet_cidr = subnet.get('CidrBlock', '0.0.0.0/0')
                az = subnet.get('AvailabilityZone', 'N/A')
                
                # Place subnet in same row as VPC, but in subnet column
                # If multiple subnets, stack them vertically
                subnet_row = vpc_row + (sub_idx * 0.6)  # Slight offset
                subnet_x, subnet_y = grid_to_world(int(subnet_row), SUBNET_COLUMN)
                
                subnet_room = self._create_room(
                    subnet_x, subnet_y, ROOM_SIZE_MEDIUM, ROOM_SIZE_SMALL,
                    ResourceType.SUBNET, f"Subnet {subnet_cidr}", subnet_id,
                    sign_text=f"Subnet {subnet_cidr}",
                    direction_to=f"AZ: {az[-2:]}",
                    metadata={'cidr': subnet_cidr, 'vpc_id': vpc_id, 'az': az}
                )
                self.rooms.append(subnet_room)
                subnet_positions[subnet_id] = (subnet_row, SUBNET_COLUMN, vpc_id)
            
            vpc_row += 2  # Space out VPCs vertically
        
        # 4. CREATE HALLWAY CONNECTIONS (Logical routing)
        
        # Connect Load Balancers to their VPCs
        for lb_arn, (lb_row, lb_col, vpc_id) in lb_positions.items():
            if vpc_id and vpc_id in vpc_positions:
                lb_x, lb_y = grid_to_world(lb_row, lb_col)
                vpc_row_pos, vpc_col = vpc_positions[vpc_id]
                vpc_x, vpc_y = grid_to_world(vpc_row_pos, vpc_col)
                
                # Horizontal hallway from LB to VPC
                self._add_hallway(lb_x + ROOM_SIZE_MEDIUM, lb_y + ROOM_SIZE_MEDIUM // 2, vpc_x, vpc_y + ROOM_SIZE_LARGE // 2, HALLWAY_WIDTH)
        
        # Connect VPCs to their Subnets
        for vpc_id, (vpc_row_pos, vpc_col) in vpc_positions.items():
            vpc_subnets = [(sid, pos) for sid, pos in subnet_positions.items() 
                          if pos[2] == vpc_id]
            
            if vpc_subnets:
                vpc_x, vpc_y = grid_to_world(vpc_row_pos, vpc_col)
                
                for subnet_id, (subnet_row, subnet_col, _) in vpc_subnets:
                    subnet_x, subnet_y = grid_to_world(int(subnet_row), subnet_col)
                    
                    # Horizontal hallway from VPC to Subnet
                    self._add_hallway(vpc_x + ROOM_SIZE_LARGE, vpc_y + ROOM_SIZE_LARGE // 2, subnet_x, subnet_y + ROOM_SIZE_SMALL // 2, HALLWAY_WIDTH)
        
        # 5. ADD SECURITY GROUPS as locked rooms near subnets
        for sg_idx, sg in enumerate(security_groups[:6]):
            sg_id = sg.get('GroupId', f'sg-{sg_idx}')
            sg_name = sg.get('GroupName', f'SG-{sg_idx}')
            vpc_id = sg.get('VpcId', None)
            
            if vpc_id and vpc_id in vpc_positions:
                # Place near the VPC it belongs to
                vpc_row_pos, _ = vpc_positions[vpc_id]
                sg_x, sg_y = grid_to_world(vpc_row_pos + sg_idx, SUBNET_COLUMN + 1)
                
                sg_room = self._create_room(
                    sg_x, sg_y, ROOM_SIZE_SMALL, ROOM_SIZE_SMALL,
                    ResourceType.SECURITY_GROUP, f"SG {sg_name[:12]}", sg_id,
                    sign_text=f"SG {sg_name[:12]}",
                    direction_to="🔒 Restricted",
                    requires_key=True
                )
                self.rooms.append(sg_room)
    
    def _create_room(self, x: float, y: float, width: float, height: float,
                     resource_type: ResourceType, resource_name: str, resource_id: str,
                     sign_text: str = None, direction_to: str = None,
                     requires_key: bool = False, metadata: Dict[str, Any] = None):
        """Create a room with walls and optional signage"""
        if metadata is None:
            metadata = {}
        
        # Add sign/direction to metadata if provided
        if sign_text:
            metadata['sign_text'] = sign_text
        if direction_to:
            metadata['direction_to'] = direction_to
        
        room = Room(
            x=x, y=y, width=width, height=height,
            resource_type=resource_type,
            resource_name=resource_name,
            resource_id=resource_id,
            requires_key=requires_key,
            metadata=metadata
        )
        
        # Create walls with proper signature
        color = COLORS.get(resource_type.value, COLORS['default'])
        
        # Top wall - only top wall gets the sign
        top_wall = Wall(
            x1=x, y1=y, x2=x + width, y2=y,
            color=color,
            resource_type=resource_type,
            resource_name=resource_name,
            resource_id=resource_id,
            sign_text=sign_text or "",
            direction_to=direction_to or ""
        )
        # Right wall
        right_wall = Wall(
            x1=x + width, y1=y, x2=x + width, y2=y + height,
            color=color,
            resource_type=resource_type,
            resource_name=resource_name,
            resource_id=resource_id
        )
        # Bottom wall
        bottom_wall = Wall(
            x1=x, y1=y + height, x2=x + width, y2=y + height,
            color=color,
            resource_type=resource_type,
            resource_name=resource_name,
            resource_id=resource_id
        )
        # Left wall
        left_wall = Wall(
            x1=x, y1=y, x2=x, y2=y + height,
            color=color,
            resource_type=resource_type,
            resource_name=resource_name,
            resource_id=resource_id
        )
        
        room.walls = [top_wall, right_wall, bottom_wall, left_wall]
        self.walls.extend(room.walls)
        
        return room

    def _add_hallway(self, x1: float, y1: float, x2: float, y2: float, 
                     width: float = 40):
        """Add a hallway connecting two points with openings in walls"""
        color = DARK_GRAY
        
        # Calculate hallway direction
        dx = x2 - x1
        dy = y2 - y1
        distance = math.sqrt(dx * dx + dy * dy)
        
        if distance < 10:
            return  # Too close, no hallway needed
        
        # Normalize direction
        dx_norm = dx / distance
        dy_norm = dy / distance
        
        # Perpendicular direction for width
        perp_x = -dy_norm
        perp_y = dx_norm
        
        # Create hallway walls on both sides
        half_width = width / 2
        
        # Left wall of hallway
        wall1_x1 = x1 + perp_x * half_width
        wall1_y1 = y1 + perp_y * half_width
        wall1_x2 = x2 + perp_x * half_width
        wall1_y2 = y2 + perp_y * half_width
        
        # Right wall of hallway
        wall2_x1 = x1 - perp_x * half_width
        wall2_y1 = y1 - perp_y * half_width
        wall2_x2 = x2 - perp_x * half_width
        wall2_y2 = y2 - perp_y * half_width
        
        # Add hallway walls with directional signs
        # Calculate direction for signs
        angle = math.atan2(dy_norm, dx_norm)
        if abs(angle) < math.pi/4:
            direction = "→ East"
        elif abs(angle) > 3*math.pi/4:
            direction = "← West"
        elif angle > 0:
            direction = "↓ South"
        else:
            direction = "↑ North"
        
        self.walls.append(
            Wall(wall1_x1, wall1_y1, wall1_x2, wall1_y2, 
                 color, ResourceType.HALLWAY, "Hallway", "hallway", False,
                 "CORRIDOR", direction, 0)
        )
        self.walls.append(
            Wall(wall2_x1, wall2_y1, wall2_x2, wall2_y2, 
                 color, ResourceType.HALLWAY, "Hallway", "hallway", False,
                 "CORRIDOR", direction, 0)
        )
    

    def cast_ray(self, player: Player, ray_angle: float) -> Tuple[Optional[Wall], float]:
        """Cast a single ray and return the wall hit and distance"""
        sin_a = math.sin(ray_angle)
        cos_a = math.cos(ray_angle)
        
        min_dist = MAX_DEPTH
        hit_wall = None
        
        for wall in self.aws_map.walls:
            # Line-line intersection
            x1, y1 = wall.x1, wall.y1
            x2, y2 = wall.x2, wall.y2
            
            # Wall direction
            wall_dx = x2 - x1
            wall_dy = y2 - y1
            
            # Ray direction
            ray_dx = cos_a
            ray_dy = sin_a
            
            # Solve for intersection
            denominator = ray_dx * wall_dy - ray_dy * wall_dx
            
            if abs(denominator) < 0.0001:
                continue
                
            t = ((x1 - player.x) * wall_dy - (y1 - player.y) * wall_dx) / denominator
            u = ((x1 - player.x) * ray_dy - (y1 - player.y) * ray_dx) / denominator
            
            if t > 0 and 0 <= u <= 1:
                dist = t
                if dist < min_dist:
                    min_dist = dist
                    hit_wall = wall
                    
        return hit_wall, min_dist
    
    def render_3d_view(self, player: Player):
        """Render the 3D first-person view"""
        # Draw ceiling and floor
        pygame.draw.rect(self.screen, CEILING_COLOR, (0, 0, SCREEN_WIDTH, SCREEN_HEIGHT // 2))
        pygame.draw.rect(self.screen, FLOOR_COLOR, (0, SCREEN_HEIGHT // 2, SCREEN_WIDTH, SCREEN_HEIGHT // 2))
        
        # Cast rays
        ray_angle = player.angle - HALF_FOV
        
        for ray in range(NUM_RAYS):
            wall, dist = self.cast_ray(player, ray_angle)
            
            if wall:
                # Fix fish-eye effect
                dist = dist * math.cos(player.angle - ray_angle)
                
                # Calculate wall height
                wall_height = min(40000 / (dist + 0.0001), SCREEN_HEIGHT)
                
                # Calculate color with distance shading
                shade = max(0.2, 1 - dist / MAX_DEPTH)
                color = tuple(int(c * shade) for c in wall.color)
                
                # Draw wall slice
                slice_width = SCREEN_WIDTH / NUM_RAYS
                x = ray * slice_width
                y = (SCREEN_HEIGHT - wall_height) / 2
                
                # Get base color (with AWS service-specific colors)
                base_color = wall.color
                
                # Apply distance fog
                fogged_color = apply_distance_fog(base_color, dist)
                
                # Apply shading based on distance
                fogged_color = tuple(int(c * shade) for c in fogged_color)
                
                # Render wall column with scanline texture
                for scan_y in range(int(y), int(y + wall_height)):
                    if 0 <= scan_y < SCREEN_HEIGHT:
                        scan_color = apply_scanline_texture(fogged_color, scan_y - int(y), int(wall_height))
                        pixel_surf = pygame.Surface((slice_width + 1, 1))
                        pixel_surf.fill(scan_color)
                        self.screen.blit(pixel_surf, (x, scan_y))
                
                # Render sign if close enough and wall is roughly center-facing
                # Only render on the actual wall's center, not scattered
                if dist < 250 and abs(ray - NUM_RAYS//2) < 5 and wall.sign_text:
                    self.render_wall_sign(x, y, wall_height, slice_width + 1,
                                         wall.sign_text, wall.direction_to)
                
                # Render arrow separately if direction exists
                if dist < 200 and abs(ray - NUM_RAYS//2) < 8 and wall.direction_to:
                    self.render_directional_arrow(x, y, wall_height, 
                                                  wall.direction_to, (100, 255, 100))
                
                # Draw red overlay if door is locked
                if wall.requires_key and wall.resource_id not in player.keys:
                    lock_color = (200, 0, 0, 100)
                    s = pygame.Surface((slice_width + 1, wall_height), pygame.SRCALPHA)
                    s.fill(lock_color)
                    self.screen.blit(s, (x, y))
            
            ray_angle += DELTA_ANGLE
    
    def render_2d_map(self, player: Player, x_offset: int, y_offset: int, scale: float = 0.15):
        """Render minimap"""
        map_surface = pygame.Surface((300, 300), pygame.SRCALPHA)
        map_surface.fill((0, 0, 0, 180))
        
        # Draw walls
        for wall in self.aws_map.walls:
            x1 = int((wall.x1 - x_offset) * scale)
            y1 = int((wall.y1 - y_offset) * scale)
            x2 = int((wall.x2 - x_offset) * scale)
            y2 = int((wall.y2 - y_offset) * scale)
            
            if -50 <= x1 < 350 and -50 <= y1 < 350:
                pygame.draw.line(map_surface, wall.color, (x1, y1), (x2, y2), 2)
        
        # Draw player
        player_x = int((player.x - x_offset) * scale)
        player_y = int((player.y - y_offset) * scale)
        
        if 0 <= player_x < 300 and 0 <= player_y < 300:
            pygame.draw.circle(map_surface, GREEN, (player_x, player_y), 5)
            
            # Draw direction indicator
            dir_x = player_x + int(math.cos(player.angle) * 15)
            dir_y = player_y + int(math.sin(player.angle) * 15)
            pygame.draw.line(map_surface, GREEN, (player_x, player_y), (dir_x, dir_y), 2)
        
        self.screen.blit(map_surface, (SCREEN_WIDTH - 320, 20))
    
    def render_hud(self, player: Player, current_room: Optional[Room]):
        """Render HUD with AWS resource information"""
        # Draw HUD background
        hud_surface = pygame.Surface((SCREEN_WIDTH, 150), pygame.SRCALPHA)
        hud_surface.fill((0, 0, 0, 200))
        self.screen.blit(hud_surface, (0, SCREEN_HEIGHT - 150))
        
        # Current location
        y_pos = SCREEN_HEIGHT - 140
        
        if current_room:
            # Resource type and name
            type_text = self.font.render(f"Location: {current_room.resource_type.value.upper()}", 
                                        True, WHITE)
            self.screen.blit(type_text, (20, y_pos))
            y_pos += 30
            
            name_text = self.small_font.render(f"{current_room.resource_name}", 
                                              True, YELLOW)
            self.screen.blit(name_text, (20, y_pos))
            y_pos += 25
            
            # Metadata
            if current_room.metadata:
                meta_items = list(current_room.metadata.items())[:3]
                meta_str = " | ".join([f"{k}: {str(v)[:30]}" for k, v in meta_items])
                meta_text = self.small_font.render(meta_str, True, CYAN)
                self.screen.blit(meta_text, (20, y_pos))
            
            # Access status
            if current_room.requires_key:
                access_color = GREEN if current_room.resource_id in player.keys else RED
                access_text = "AUTHORIZED" if current_room.resource_id in player.keys else "LOCKED"
                lock_render = self.font.render(f"Access: {access_text}", True, access_color)
                self.screen.blit(lock_render, (SCREEN_WIDTH - 250, y_pos - 55))
        
        # Keys collected
        keys_text = self.small_font.render(f"Keys: {len(player.keys)}", True, YELLOW)
        self.screen.blit(keys_text, (SCREEN_WIDTH - 250, SCREEN_HEIGHT - 140))
        
        # Position
        pos_text = self.small_font.render(
            f"Position: ({int(player.x)}, {int(player.y)})", True, WHITE)
        self.screen.blit(pos_text, (SCREEN_WIDTH - 250, SCREEN_HEIGHT - 115))
        
        # Controls
        controls = [
            "W/S: Move Forward/Back",
            "A/D: Rotate Left/Right",
            "E: Interact/Collect Key",
            "M: Toggle Map",
            "ESC: Quit"
        ]
        
        control_y = 20
        for control in controls:
            control_text = self.small_font.render(control, True, WHITE)
            self.screen.blit(control_text, (20, control_y))
            control_y += 20


class DoomRenderer:
    """3D raycasting renderer in DOOM style"""
    
    def __init__(self, screen: pygame.Surface, aws_map: AWSMap):
        self.screen = screen
        self.aws_map = aws_map
        self.font = pygame.font.Font(None, 24)
        self.small_font = pygame.font.Font(None, 18)
        self.title_font = pygame.font.Font(None, 36)
        
    
    def render_wall_texture(self, x: int, y: int, height: int, width: int, 
                           color: tuple, pattern: int, shade: float):
        """Render wall with texture pattern"""
        # Apply shading
        shaded_color = tuple(int(c * shade) for c in color)
        
        # Draw base wall
        pygame.draw.rect(self.screen, shaded_color, (x, y, width, height))
        
        # Add texture pattern
        if pattern == 1:  # Vertical stripes
            stripe_width = max(2, width // 8)
            for i in range(0, int(width), stripe_width * 2):
                darker = tuple(int(c * 0.8) for c in shaded_color)
                pygame.draw.rect(self.screen, darker, (x + i, y, stripe_width, height))
        
        elif pattern == 2:  # Dotted pattern
            dot_spacing = max(8, int(height) // 10)
            lighter = tuple(min(255, int(c * 1.2)) for c in shaded_color)
            for dy in range(0, int(height), dot_spacing):
                pygame.draw.circle(self.screen, lighter, 
                                 (int(x + width/2), int(y + dy)), 2)
        
        elif pattern == 3:  # Grid pattern
            grid_size = max(10, int(height) // 8)
            darker = tuple(int(c * 0.7) for c in shaded_color)
            for dy in range(0, int(height), grid_size):
                pygame.draw.line(self.screen, darker, (x, y + dy), (x + width, y + dy), 1)
    
    def render_wall_sign(self, x: int, y: int, height: int, width: int,
                        sign_text: str, direction_text: str):
        """Render AWS-themed text sign on wall with service icons"""
        if not sign_text and not direction_text:
            return
        
        # Only render if width is significant
        if width < 5:
            return
        
        # AWS service icon mapping
        service_icons = {
            'VPC': '🔷',
            'Subnet': '🔹',
            'SG': '🔒',
            'EKS': '☸',
            'LB': '⚖',
            'RDS': '🗄',
            'CORRIDOR': '→',
        }
        
        # Detect service type from sign text
        icon = '▪'
        for service, sicon in service_icons.items():
            if service in sign_text:
                icon = sicon
                break
        
        # Sign background - AWS themed
        sign_height = min(90, int(height) // 3)
        sign_y = int(y + (height - sign_height) // 2)
        
        # Create sign with AWS orange border
        sign_surface = pygame.Surface((int(width), sign_height), pygame.SRCALPHA)
        sign_surface.fill((20, 30, 50, 220))  # Dark blue-black background
        
        # AWS orange border
        pygame.draw.rect(sign_surface, AWS_ORANGE, (0, 0, int(width), sign_height), 2)
        pygame.draw.rect(sign_surface, AWS_ORANGE, (2, 2, int(width)-4, sign_height-4), 1)
        
        self.screen.blit(sign_surface, (int(x), sign_y))
        
        # Render icon
        icon_surf = self.small_font.render(icon, True, AWS_ORANGE)
        self.screen.blit(icon_surf, (int(x) + 5, sign_y + 5))
        
        # Render main sign text
        if sign_text:
            display_text = sign_text[:28] if len(sign_text) > 28 else sign_text
            # AWS-style white text
            text_surface = self.small_font.render(display_text, True, (240, 240, 240))
            text_rect = text_surface.get_rect(center=(int(x + width//2), sign_y + sign_height//3 + 5))
            self.screen.blit(text_surface, text_rect)
        
        # Render direction indicator with AWS green
        if direction_text:
            dir_surface = self.small_font.render(direction_text, True, LAMBDA_GREEN)
            dir_rect = dir_surface.get_rect(center=(int(x + width//2), sign_y + 2*sign_height//3))
            self.screen.blit(dir_surface, dir_rect)
    
    def render_directional_arrow(self, x: int, y: int, height: int, 
                                 direction: str, color: tuple):
        """Render directional arrow on wall"""
        if not direction:
            return
        
        arrow_y = y + height // 2
        arrow_size = min(20, height // 4)
        
        # Parse direction
        if '→' in direction or 'right' in direction.lower():
            # Right arrow
            points = [
                (x + 10, arrow_y - arrow_size),
                (x + 10 + arrow_size, arrow_y),
                (x + 10, arrow_y + arrow_size)
            ]
            pygame.draw.polygon(self.screen, color, points)
        elif '←' in direction or 'left' in direction.lower():
            # Left arrow
            points = [
                (x + 30, arrow_y - arrow_size),
                (x + 10, arrow_y),
                (x + 30, arrow_y + arrow_size)
            ]
            pygame.draw.polygon(self.screen, color, points)
        elif '↑' in direction or 'up' in direction.lower():
            # Up arrow
            points = [
                (x + 20, arrow_y - arrow_size),
                (x + 20 + arrow_size, arrow_y + 10),
                (x + 20 - arrow_size, arrow_y + 10)
            ]
            pygame.draw.polygon(self.screen, color, points)

    def cast_ray(self, player: Player, ray_angle: float) -> Tuple[Optional[Wall], float]:
        """Cast a single ray and return the wall hit and distance"""
        sin_a = math.sin(ray_angle)
        cos_a = math.cos(ray_angle)
        
        min_dist = MAX_DEPTH
        hit_wall = None
        
        for wall in self.aws_map.walls:
            # Line-line intersection
            x1, y1 = wall.x1, wall.y1
            x2, y2 = wall.x2, wall.y2
            
            # Wall direction
            wall_dx = x2 - x1
            wall_dy = y2 - y1
            
            # Ray direction
            ray_dx = cos_a
            ray_dy = sin_a
            
            # Solve for intersection
            denominator = ray_dx * wall_dy - ray_dy * wall_dx
            
            if abs(denominator) < 0.0001:
                continue
                
            t = ((x1 - player.x) * wall_dy - (y1 - player.y) * wall_dx) / denominator
            u = ((x1 - player.x) * ray_dy - (y1 - player.y) * ray_dx) / denominator
            
            if t > 0 and 0 <= u <= 1:
                dist = t
                if dist < min_dist:
                    min_dist = dist
                    hit_wall = wall
                    
        return hit_wall, min_dist
    
    def render_3d_view(self, player: Player):
        """Render the 3D first-person view"""
        # Draw ceiling and floor
        pygame.draw.rect(self.screen, CEILING_COLOR, (0, 0, SCREEN_WIDTH, SCREEN_HEIGHT // 2))
        pygame.draw.rect(self.screen, FLOOR_COLOR, (0, SCREEN_HEIGHT // 2, SCREEN_WIDTH, SCREEN_HEIGHT // 2))
        
        # Cast rays
        ray_angle = player.angle - HALF_FOV
        
        for ray in range(NUM_RAYS):
            wall, dist = self.cast_ray(player, ray_angle)
            
            if wall:
                # Fix fish-eye effect
                dist = dist * math.cos(player.angle - ray_angle)
                
                # Calculate wall height
                wall_height = min(40000 / (dist + 0.0001), SCREEN_HEIGHT)
                
                # Calculate color with distance shading
                shade = max(0.2, 1 - dist / MAX_DEPTH)
                color = tuple(int(c * shade) for c in wall.color)
                
                # Draw wall slice
                slice_width = SCREEN_WIDTH / NUM_RAYS
                x = ray * slice_width
                y = (SCREEN_HEIGHT - wall_height) / 2
                
                # Get base color (with AWS service-specific colors)
                base_color = wall.color
                
                # Apply distance fog
                fogged_color = apply_distance_fog(base_color, dist)
                
                # Apply shading based on distance
                fogged_color = tuple(int(c * shade) for c in fogged_color)
                
                # Render wall column with scanline texture
                for scan_y in range(int(y), int(y + wall_height)):
                    if 0 <= scan_y < SCREEN_HEIGHT:
                        scan_color = apply_scanline_texture(fogged_color, scan_y - int(y), int(wall_height))
                        pixel_surf = pygame.Surface((slice_width + 1, 1))
                        pixel_surf.fill(scan_color)
                        self.screen.blit(pixel_surf, (x, scan_y))
                
                # Render sign if close enough and wall is roughly center-facing
                # Only render on the actual wall's center, not scattered
                if dist < 250 and abs(ray - NUM_RAYS//2) < 5 and wall.sign_text:
                    self.render_wall_sign(x, y, wall_height, slice_width + 1,
                                         wall.sign_text, wall.direction_to)
                
                # Render arrow separately if direction exists
                if dist < 200 and abs(ray - NUM_RAYS//2) < 8 and wall.direction_to:
                    self.render_directional_arrow(x, y, wall_height, 
                                                  wall.direction_to, (100, 255, 100))
                
                # Draw red overlay if door is locked
                if wall.requires_key and wall.resource_id not in player.keys:
                    lock_color = (200, 0, 0, 100)
                    s = pygame.Surface((slice_width + 1, wall_height), pygame.SRCALPHA)
                    s.fill(lock_color)
                    self.screen.blit(s, (x, y))
            
            ray_angle += DELTA_ANGLE
    
    def render_2d_map(self, player: Player, x_offset: int, y_offset: int, scale: float = 0.15):
        """Render minimap"""
        map_surface = pygame.Surface((300, 300), pygame.SRCALPHA)
        map_surface.fill((0, 0, 0, 180))
        
        # Draw walls
        for wall in self.aws_map.walls:
            x1 = int((wall.x1 - x_offset) * scale)
            y1 = int((wall.y1 - y_offset) * scale)
            x2 = int((wall.x2 - x_offset) * scale)
            y2 = int((wall.y2 - y_offset) * scale)
            
            if -50 <= x1 < 350 and -50 <= y1 < 350:
                pygame.draw.line(map_surface, wall.color, (x1, y1), (x2, y2), 2)
        
        # Draw player
        player_x = int((player.x - x_offset) * scale)
        player_y = int((player.y - y_offset) * scale)
        
        if 0 <= player_x < 300 and 0 <= player_y < 300:
            pygame.draw.circle(map_surface, GREEN, (player_x, player_y), 5)
            
            # Draw direction indicator
            dir_x = player_x + int(math.cos(player.angle) * 15)
            dir_y = player_y + int(math.sin(player.angle) * 15)
            pygame.draw.line(map_surface, GREEN, (player_x, player_y), (dir_x, dir_y), 2)
        
        self.screen.blit(map_surface, (SCREEN_WIDTH - 320, 20))
    
    def render_hud(self, player: Player, current_room: Optional[Room]):
        """Render HUD with AWS resource information"""
        # Draw HUD background
        hud_surface = pygame.Surface((SCREEN_WIDTH, 150), pygame.SRCALPHA)
        hud_surface.fill((0, 0, 0, 200))
        self.screen.blit(hud_surface, (0, SCREEN_HEIGHT - 150))
        
        # Current location
        y_pos = SCREEN_HEIGHT - 140
        
        if current_room:
            # Resource type and name
            type_text = self.font.render(f"Location: {current_room.resource_type.value.upper()}", 
                                        True, WHITE)
            self.screen.blit(type_text, (20, y_pos))
            y_pos += 30
            
            name_text = self.small_font.render(f"{current_room.resource_name}", 
                                              True, YELLOW)
            self.screen.blit(name_text, (20, y_pos))
            y_pos += 25
            
            # Metadata
            if current_room.metadata:
                meta_items = list(current_room.metadata.items())[:3]
                meta_str = " | ".join([f"{k}: {str(v)[:30]}" for k, v in meta_items])
                meta_text = self.small_font.render(meta_str, True, CYAN)
                self.screen.blit(meta_text, (20, y_pos))
            
            # Access status
            if current_room.requires_key:
                access_color = GREEN if current_room.resource_id in player.keys else RED
                access_text = "AUTHORIZED" if current_room.resource_id in player.keys else "LOCKED"
                lock_render = self.font.render(f"Access: {access_text}", True, access_color)
                self.screen.blit(lock_render, (SCREEN_WIDTH - 250, y_pos - 55))
        
        # Keys collected
        keys_text = self.small_font.render(f"Keys: {len(player.keys)}", True, YELLOW)
        self.screen.blit(keys_text, (SCREEN_WIDTH - 250, SCREEN_HEIGHT - 140))
        
        # Position
        pos_text = self.small_font.render(
            f"Position: ({int(player.x)}, {int(player.y)})", True, WHITE)
        self.screen.blit(pos_text, (SCREEN_WIDTH - 250, SCREEN_HEIGHT - 115))
        
        # Controls
        controls = [
            "W/S: Move Forward/Back",
            "A/D: Rotate Left/Right",
            "E: Interact/Collect Key",
            "M: Toggle Map",
            "ESC: Quit"
        ]
        
        control_y = 20
        for control in controls:
            control_text = self.small_font.render(control, True, WHITE)
            self.screen.blit(control_text, (20, control_y))
            control_y += 20



class AWSGameWindow:
    """Main game loop and window management"""
    
    def __init__(self, snapshot_path: str):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("AWS DOOM - Architecture Explorer")
        self.clock = pygame.time.Clock()
        
        # Load AWS map
        print("Generating AWS architecture map...")
        self.aws_map = AWSMap(snapshot_path)
        print(f"Generated {len(self.aws_map.rooms)} rooms and {len(self.aws_map.walls)} walls")
        
        # Initialize player
        self.player = Player(
            x=self.aws_map.spawn_x,
            y=self.aws_map.spawn_y,
            angle=0,
            keys=[]
        )
        
        # Renderer
        self.renderer = DoomRenderer(self.screen, self.aws_map)
        
        # Game state
        self.show_map = True
        self.running = True
        
    def get_current_room(self) -> Optional[Room]:
        """Get the room the player is currently in"""
        for room in self.aws_map.rooms:
            if (room.x <= self.player.x <= room.x + room.width and
                room.y <= self.player.y <= room.y + room.height):
                return room
        return None
    
    def handle_input(self):
        """Handle keyboard and mouse input"""
        keys = pygame.key.get_pressed()
        
        # Movement
        if keys[pygame.K_w]:
            new_x = self.player.x + math.cos(self.player.angle) * MOVE_SPEED
            new_y = self.player.y + math.sin(self.player.angle) * MOVE_SPEED
            
            # Simple collision detection
            if not self.check_collision(new_x, new_y):
                self.player.x = new_x
                self.player.y = new_y
        
        if keys[pygame.K_s]:
            new_x = self.player.x - math.cos(self.player.angle) * MOVE_SPEED
            new_y = self.player.y - math.sin(self.player.angle) * MOVE_SPEED
            
            if not self.check_collision(new_x, new_y):
                self.player.x = new_x
                self.player.y = new_y
        
        # Rotation
        if keys[pygame.K_a]:
            self.player.angle -= ROTATE_SPEED
        
        if keys[pygame.K_d]:
            self.player.angle += ROTATE_SPEED
        
        # Events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                elif event.key == pygame.K_m:
                    self.show_map = not self.show_map
                elif event.key == pygame.K_e:
                    self.interact()
    
    def check_collision(self, x: float, y: float) -> bool:
        """Check if position collides with walls"""
        collision_radius = 15
        
        for wall in self.aws_map.walls:
            # Skip hallway walls - they're always passable
            if wall.resource_type == ResourceType.HALLWAY:
                continue
            
            x1, y1 = wall.x1, wall.y1
            x2, y2 = wall.x2, wall.y2
            
            dx = x - x1
            dy = y - y1
            lx = x2 - x1
            ly = y2 - y1
            len_sq = lx * lx + ly * ly
            
            if len_sq == 0:
                continue
            
            t = max(0, min(1, (dx * lx + dy * ly) / len_sq))
            closest_x = x1 + t * lx
            closest_y = y1 + t * ly
            dist = math.sqrt((x - closest_x)**2 + (y - closest_y)**2)
            
            if dist < collision_radius:
                # Locked doors block passage
                if wall.requires_key and wall.resource_id not in self.player.keys:
                    return True
                # Regular walls block passage
                return True
        
        return False
    
    def interact(self):
        """Interact with nearby objects (collect keys, open doors)"""
        current_room = self.get_current_room()
        
        if current_room and current_room.requires_key:
            if current_room.resource_id not in self.player.keys:
                self.player.keys.append(current_room.resource_id)
                print(f"✓ Collected key: {current_room.resource_name}")
    
    def run(self):
        """Main game loop"""
        print("\n=== AWS DOOM Started ===")
        print(f"Spawn position: ({self.player.x}, {self.player.y})")
        print(f"Total rooms: {len(self.aws_map.rooms)}")
        print("Controls: W/S = Move, A/D = Rotate, E = Interact, M = Toggle Map, ESC = Quit\n")
        
        while self.running:
            self.handle_input()
            
            # Clear screen
            self.screen.fill(BLACK)
            
            # Render 3D view
            self.renderer.render_3d_view(self.player)
            
            # Render 2D minimap
            if self.show_map:
                self.renderer.render_2d_map(
                    self.player, 
                    self.aws_map.spawn_x - 500,
                    self.aws_map.spawn_y - 500
                )
            
            # Render HUD
            current_room = self.get_current_room()
            self.renderer.render_hud(self.player, current_room)
            
            # Update display
            pygame.display.flip()
            self.clock.tick(60)
        
        print("\nExiting AWS DOOM...")
        pygame.quit()


def main():
    """Entry point"""
    print("="*60)
    print("AWS DOOM - Architecture Explorer")
    print("A First-Person DOOM-style visualization of AWS infrastructure")
    print("="*60)
    
    # Find a snapshot file
    snapshot_dir = Path.home() / "AWS_Architecture_explorer" / "snapshots"
    
    if not snapshot_dir.exists():
        print(f"Error: Snapshot directory not found: {snapshot_dir}")
        sys.exit(1)
    
    snapshots = list(snapshot_dir.glob("*.json"))
    
    if not snapshots:
        print(f"Error: No snapshot files found in {snapshot_dir}")
        print(f"Please run the AWS snapshot collector first.")
        sys.exit(1)
    
    # Use the first snapshot or specified one
    snapshot_path = snapshots[0]
    
    if len(sys.argv) > 1:
        custom_path = Path(sys.argv[1])
        if custom_path.exists():
            snapshot_path = custom_path
    
    print(f"\nLoading AWS snapshot: {snapshot_path.name}")
    
    try:
        # Create and run game
        game = AWSGameWindow(str(snapshot_path))
        game.run()
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
