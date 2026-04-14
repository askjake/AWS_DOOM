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
COLORS = {
    'vpc': BLUE,
    'subnet': CYAN,
    'security_group': ORANGE,
    'eks_cluster': PURPLE,
    'load_balancer': GREEN,
    'rds': RED,
    's3': YELLOW,
    'default': GRAY
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
        """Generate the entire map structure from AWS snapshot"""
        # Start position
        current_x = 100
        current_y = 100
        room_size = 150
        hallway_width = 50
        
        # Handle both nested and flat snapshot structures
        # Try nested structure first (vpc.vpcs), then flat (vpcs)
        vpcs = []
        if 'vpc' in self.snapshot and isinstance(self.snapshot['vpc'], dict):
            vpcs = self.snapshot['vpc'].get('vpcs', [])
        elif 'vpcs' in self.snapshot:
            vpcs = self.snapshot.get('vpcs', [])
        
        # Generate VPC rooms (main areas)
        for vpc_idx, vpc in enumerate(vpcs[:10]):  # Limit to 10 VPCs
            vpc_id = vpc.get('VpcId', f'vpc-{vpc_idx}')
            vpc_cidr = vpc.get('CidrBlock', 'Unknown')
            
            # Create VPC room (large container)
            vpc_x = current_x
            vpc_y = current_y + (vpc_idx * (room_size * 3))
            
            vpc_room = self._create_room(
                vpc_x, vpc_y, room_size * 2, room_size * 2,
                ResourceType.VPC, f"VPC {vpc_cidr}", vpc_id,
                metadata={'cidr': vpc_cidr, 'vpc_id': vpc_id}
            )
            self.rooms.append(vpc_room)
            
            # Generate subnet rooms inside VPC
            subnets = []
            if 'vpc' in self.snapshot and isinstance(self.snapshot['vpc'], dict):
                subnets = [s for s in self.snapshot['vpc'].get('subnets', []) 
                          if s.get('VpcId') == vpc_id]
            elif 'subnets' in self.snapshot:
                subnets = [s for s in self.snapshot.get('subnets', []) 
                          if s.get('VpcId') == vpc_id]
            
            for sub_idx, subnet in enumerate(subnets[:6]):  # Limit subnets
                subnet_id = subnet.get('SubnetId', f'subnet-{sub_idx}')
                subnet_cidr = subnet.get('CidrBlock', 'Unknown')
                az = subnet.get('AvailabilityZone', 'Unknown')
                
                # Position subnets in a grid inside VPC
                sub_x = vpc_x + 50 + (sub_idx % 2) * (room_size + 20)
                sub_y = vpc_y + 50 + (sub_idx // 2) * (room_size + 20)
                
                subnet_room = self._create_room(
                    sub_x, sub_y, room_size, room_size,
                    ResourceType.SUBNET, f"Subnet {subnet_cidr[:12]}", 
                    subnet_id, metadata={'cidr': subnet_cidr, 'az': az}
                )
                self.rooms.append(subnet_room)
            
            # Connect VPC to first subnet with hallway
            if subnets:
                first_subnet_x = vpc_x + 50 + room_size // 2
                first_subnet_y = vpc_y + 50 + room_size // 2
                vpc_center_x = vpc_x + room_size
                vpc_center_y = vpc_y + room_size
                
                # Create doorway in VPC wall
                self._create_doorway(vpc_x, vpc_y, room_size * 2, room_size * 2, 'right')
                
                # Add hallway
                self._add_hallway(vpc_center_x, vpc_center_y, 
                                first_subnet_x, first_subnet_y, width=50)
        
        # Generate security group rooms (locked areas requiring keys)
        sgs = []
        if 'vpc' in self.snapshot and isinstance(self.snapshot['vpc'], dict):
            sgs = self.snapshot['vpc'].get('security_groups', [])[:8]
        elif 'security_groups' in self.snapshot:
            sgs = self.snapshot.get('security_groups', [])[:8]
        
        for sg_idx, sg in enumerate(sgs):
            sg_id = sg.get('GroupId', f'sg-{sg_idx}')
            sg_name = sg.get('GroupName', 'Unknown')[:20]
            vpc_id = sg.get('VpcId', '')
            
            sg_x = current_x + 400 + (sg_idx % 3) * (room_size + 30)
            sg_y = current_y + (sg_idx // 3) * (room_size + 30)
            
            # Security groups require "keys" (authorization)
            sg_room = self._create_room(
                sg_x, sg_y, room_size, room_size,
                ResourceType.SECURITY_GROUP, f"SG {sg_name}", sg_id,
                requires_key=True,
                metadata={'group_name': sg_name, 'vpc_id': vpc_id}
            )
            self.rooms.append(sg_room)
            
        # Generate EKS cluster rooms (major zones)
        clusters = []
        if 'eks' in self.snapshot and isinstance(self.snapshot['eks'], dict):
            clusters = self.snapshot['eks'].get('clusters', [])
        elif 'eks' in self.snapshot and isinstance(self.snapshot['eks'], list):
            clusters = self.snapshot['eks']
        
        for cls_idx, cluster in enumerate(clusters[:4]):
            cls_name = cluster.get('name', f'cluster-{cls_idx}')[:20]
            cls_status = cluster.get('status', 'Unknown')
            
            cls_x = current_x + 800
            cls_y = current_y + cls_idx * (room_size * 2 + 50)
            
            cluster_room = self._create_room(
                cls_x, cls_y, room_size * 1.5, room_size * 1.5,
                ResourceType.EKS_CLUSTER, f"EKS {cls_name}",
                cls_name, metadata={'status': cls_status}
            )
            self.rooms.append(cluster_room)
            
        # Generate load balancer rooms (entry points)
        lbs = []
        if 'elbv2' in self.snapshot and isinstance(self.snapshot['elbv2'], dict):
            lbs = self.snapshot['elbv2'].get('load_balancers', [])
        elif 'load_balancers' in self.snapshot:
            lbs = self.snapshot.get('load_balancers', [])
        
        for lb_idx, lb in enumerate(lbs[:5]):
            lb_name = lb.get('LoadBalancerName', f'lb-{lb_idx}')[:20]
            lb_scheme = lb.get('Scheme', 'internal')
            
            lb_x = current_x - 200
            lb_y = current_y + lb_idx * (room_size + 50)
            
            # Internet-facing LBs are entry points (no key required)
            lb_room = self._create_room(
                lb_x, lb_y, room_size, room_size,
                ResourceType.LOAD_BALANCER, f"LB {lb_name}",
                lb_name, requires_key=(lb_scheme != 'internet-facing'),
                metadata={'scheme': lb_scheme}
            )
            self.rooms.append(lb_room)
            
            # Connect load balancer to nearest VPC
            if vpcs and self.rooms:
                # Find nearest VPC
                min_dist = float('inf')
                nearest_vpc = None
                for room in self.rooms:
                    if room.resource_type == ResourceType.VPC:
                        dist = math.sqrt((room.x - lb_x)**2 + (room.y - lb_y)**2)
                        if dist < min_dist:
                            min_dist = dist
                            nearest_vpc = room
                
                if nearest_vpc:
                    # Create doorway in LB
                    self._create_doorway(lb_x, lb_y, room_size, room_size, 'right')
                    
                    # Create doorway in VPC  
                    self._create_doorway(nearest_vpc.x, nearest_vpc.y, 
                                       nearest_vpc.width, nearest_vpc.height, 'left')
                    
                    # Add hallway
                    lb_center_x = lb_x + room_size // 2
                    lb_center_y = lb_y + room_size // 2
                    vpc_center_x = nearest_vpc.x + nearest_vpc.width // 2
                    vpc_center_y = nearest_vpc.y + nearest_vpc.height // 2
                    
                    self._add_hallway(lb_center_x, lb_center_y, 
                                    vpc_center_x, vpc_center_y, width=60)
            
        # Generate RDS rooms (data vaults - require keys)
        # FIXED: Handle both nested dict and flat list structures
        dbs = []
        if 'rds' in self.snapshot:
            if isinstance(self.snapshot['rds'], dict):
                dbs = self.snapshot['rds'].get('db_instances', [])
            elif isinstance(self.snapshot['rds'], list):
                dbs = self.snapshot['rds']
        
        for db_idx, db in enumerate(dbs[:4]):
            db_id = db.get('DBInstanceIdentifier', f'db-{db_idx}')[:20]
            db_engine = db.get('Engine', 'Unknown')
            db_public = db.get('PubliclyAccessible', False)
            
            db_x = current_x + 1200
            db_y = current_y + db_idx * (room_size + 50)
            
            db_room = self._create_room(
                db_x, db_y, room_size, room_size,
                ResourceType.RDS, f"RDS {db_id}",
                db_id, requires_key=(not db_public),
                metadata={'engine': db_engine, 'public': db_public}
            )
            self.rooms.append(db_room)
        
        # Set spawn point (start at first load balancer or VPC)
        if lbs:
            self.spawn_x = current_x - 200 + room_size // 2
            self.spawn_y = current_y + room_size // 2
        elif vpcs:
            self.spawn_x = 100 + room_size // 2
            self.spawn_y = 100 + room_size // 2
        elif dbs:
            # If no VPCs or LBs, spawn at first RDS
            self.spawn_x = current_x + 1200 + room_size // 2
            self.spawn_y = current_y + room_size // 2
            
    def _create_room(self, x: float, y: float, width: float, height: float,
                     resource_type: ResourceType, name: str, resource_id: str,
                     requires_key: bool = False, metadata: Dict = None) -> Room:
        """Create a room with four walls"""
        color = COLORS.get(resource_type.value, COLORS['default'])
        
        # Create walls for the room
        walls = [
            Wall(x, y, x + width, y, color, resource_type, name, resource_id, requires_key),  # Top
            Wall(x + width, y, x + width, y + height, color, resource_type, name, resource_id, requires_key),  # Right
            Wall(x + width, y + height, x, y + height, color, resource_type, name, resource_id, requires_key),  # Bottom
            Wall(x, y + height, x, y, color, resource_type, name, resource_id, requires_key)  # Left
        ]
        
        self.walls.extend(walls)
        
        return Room(x, y, width, height, resource_type, name, resource_id, 
                   walls, requires_key, metadata or {})


    
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
        
        # Add hallway walls
        self.walls.append(
            Wall(wall1_x1, wall1_y1, wall1_x2, wall1_y2, 
                 color, ResourceType.HALLWAY, "Hallway", "hallway", False)
        )
        self.walls.append(
            Wall(wall2_x1, wall2_y1, wall2_x2, wall2_y2, 
                 color, ResourceType.HALLWAY, "Hallway", "hallway", False)
        )
    
    def _create_doorway(self, room_x: float, room_y: float, room_width: float, 
                        room_height: float, side: str = 'right'):
        """Create an opening (doorway) in a room wall by removing wall segments"""
        doorway_size = 60
        
        # Remove the appropriate wall segment and create opening
        new_walls = []
        for wall in self.walls:
            keep_wall = True
            
            if side == 'right':
                # Check if this is the right wall of the room
                if (abs(wall.x1 - (room_x + room_width)) < 1 and 
                    abs(wall.x2 - (room_x + room_width)) < 1):
                    # This is the right wall - split it to create doorway
                    wall_mid_y = (wall.y1 + wall.y2) / 2
                    
                    # Create top segment
                    if wall.y1 < wall_mid_y - doorway_size/2:
                        new_walls.append(
                            Wall(wall.x1, wall.y1, wall.x2, wall_mid_y - doorway_size/2,
                                 wall.color, wall.resource_type, wall.resource_name, 
                                 wall.resource_id, wall.requires_key)
                        )
                    
                    # Create bottom segment
                    if wall.y2 > wall_mid_y + doorway_size/2:
                        new_walls.append(
                            Wall(wall.x1, wall_mid_y + doorway_size/2, wall.x2, wall.y2,
                                 wall.color, wall.resource_type, wall.resource_name,
                                 wall.resource_id, wall.requires_key)
                        )
                    keep_wall = False
            
            elif side == 'left':
                # Check if this is the left wall
                if (abs(wall.x1 - room_x) < 1 and abs(wall.x2 - room_x) < 1):
                    wall_mid_y = (wall.y1 + wall.y2) / 2
                    
                    if wall.y1 < wall_mid_y - doorway_size/2:
                        new_walls.append(
                            Wall(wall.x1, wall.y1, wall.x2, wall_mid_y - doorway_size/2,
                                 wall.color, wall.resource_type, wall.resource_name,
                                 wall.resource_id, wall.requires_key)
                        )
                    
                    if wall.y2 > wall_mid_y + doorway_size/2:
                        new_walls.append(
                            Wall(wall.x1, wall_mid_y + doorway_size/2, wall.x2, wall.y2,
                                 wall.color, wall.resource_type, wall.resource_name,
                                 wall.resource_id, wall.requires_key)
                        )
                    keep_wall = False
            
            if keep_wall:
                new_walls.append(wall)
        
        self.walls = new_walls


class DoomRenderer:
    """3D raycasting renderer in DOOM style"""
    
    def __init__(self, screen: pygame.Surface, aws_map: AWSMap):
        self.screen = screen
        self.aws_map = aws_map
        self.font = pygame.font.Font(None, 24)
        self.small_font = pygame.font.Font(None, 18)
        self.title_font = pygame.font.Font(None, 36)
        
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
                
                pygame.draw.rect(self.screen, color, 
                               (x, y, slice_width + 1, wall_height))
                
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
            # Simple distance-to-line check
            x1, y1 = wall.x1, wall.y1
            x2, y2 = wall.x2, wall.y2
            
            # Vector from line start to point
            dx = x - x1
            dy = y - y1
            
            # Line vector
            lx = x2 - x1
            ly = y2 - y1
            
            # Length squared
            len_sq = lx * lx + ly * ly
            
            if len_sq == 0:
                continue
            
            # Project point onto line
            t = max(0, min(1, (dx * lx + dy * ly) / len_sq))
            
            # Closest point on line
            closest_x = x1 + t * lx
            closest_y = y1 + t * ly
            
            # Distance to closest point
            dist = math.sqrt((x - closest_x)**2 + (y - closest_y)**2)
            
            if dist < collision_radius:
                # Check if this is a locked door
                if wall.requires_key and wall.resource_id not in self.player.keys:
                    return True
                # Normal walls block movement
                if wall.resource_type not in [ResourceType.HALLWAY]:
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
