"""2D Tile-Based Platformer Engine.

A modular, OOP-designed 2D platformer implementing discrete-stage game loops,
matrix grid level parsing, axis-separated AABB collision resolution, kinematic vector
physics, collectible entities, patrolling AI agents, sprite rendering with
graceful procedural fallbacks, smooth scrolling camera tracking, animated
sprite sequences, and a structural Game State Machine.
"""

from __future__ import annotations

import os
import sys
import pygame

# =====================================================================
# Global Engine & Simulation Configuration
# =====================================================================

# Display & Timing
SCREEN_WIDTH: int = 800
SCREEN_HEIGHT: int = 600
FPS: int = 60
WINDOW_TITLE: str = "2D Protocol Engine | Portfolio Showcase"

# World & Grid Topology
TILE_SIZE: int = 40
GRID_ROWS: int = SCREEN_HEIGHT // TILE_SIZE  # 15 rows

# Physics & Kinematics
GRAVITY: float = 0.8
JUMP_FORCE: float = -14.0
PLAYER_SPEED: float = 5.0
ENEMY_SPEED: float = 2.0

# Entity Dimensions (Pixels)
PLAYER_WIDTH: int = 40
PLAYER_HEIGHT: int = 60
ENEMY_WIDTH: int = 40
ENEMY_HEIGHT: int = 55  # Scaled noticeably taller for imposing presence
COIN_SIZE: int = 18

# Visual Color Palette (RGB Fallback Colors)
COLOR_BG: tuple[int, int, int] = (30, 30, 35)
COLOR_TILE: tuple[int, int, int] = (130, 115, 100)
COLOR_TILE_BORDER: tuple[int, int, int] = (75, 65, 55)
COLOR_PLAYER: tuple[int, int, int] = (64, 156, 255)
COLOR_ENEMY: tuple[int, int, int] = (220, 50, 50)
COLOR_COIN: tuple[int, int, int] = (255, 215, 0)
COLOR_COIN_HIGHLIGHT: tuple[int, int, int] = (255, 245, 140)
COLOR_COIN_BORDER: tuple[int, int, int] = (180, 140, 0)
COLOR_TEXT: tuple[int, int, int] = (255, 255, 255)
COLOR_ACCENT: tuple[int, int, int] = (64, 156, 255)
COLOR_WIN: tuple[int, int, int] = (80, 225, 120)
COLOR_LOSE: tuple[int, int, int] = (245, 75, 75)

# =====================================================================
# Asset Management & Loading System
# =====================================================================

def load_texture(filename: str, target_size: tuple[int, int]) -> pygame.Surface | None:
    """Safely attempt to load and scale an image asset, returning None on failure.

    Attempts to load the image from an 'assets/' directory relative to this script
    or the current working directory. On success, applies .convert_alpha() and
    scales the surface to target_size. Catches missing files and Pygame decoding
    exceptions gracefully to prevent crashes.

    Args:
        filename: Base name of the image file (e.g., 'tile.png').
        target_size: Target dimensions (width, height) to scale the texture to.

    Returns:
        A scaled, alpha-converted pygame.Surface if successful; otherwise None.
    """
    base_dir = os.path.dirname(os.path.abspath(__file__))
    candidate_paths = [
        os.path.join(base_dir, "assets", filename),
        os.path.join("assets", filename),
    ]

    for path in candidate_paths:
        if os.path.isfile(path):
            try:
                surface = pygame.image.load(path).convert_alpha()
                return pygame.transform.scale(surface, target_size)
            except (pygame.error, OSError) as exc:
                print(f"[Asset Warning] Failed loading '{path}': {exc}. Using fallback.")
                return None

    return None


def load_player_animations() -> dict[str, list[pygame.Surface]]:
    """Load player animation sequences with procedural fallback generation.

    Tries to load frame sequences ('player_run1.png', 'player_run2.png', etc.)
    or single sprite 'player.png' from 'assets/'. For any state with missing
    textures, programmatically generates distinct geometric frame variants
    with walking strides, breathing bobs, and jump poses so the engine never
    crashes.

    Returns:
        Dictionary mapping states ('idle', 'run', 'jump') to lists of Surfaces.
    """
    animations: dict[str, list[pygame.Surface]] = {
        "idle": [],
        "run": [],
        "jump": [],
    }

    # 1. Attempt loading specific animation frame sequences
    idle_filenames = ["player_idle1.png", "player_idle2.png"]
    for f in idle_filenames:
        tex = load_texture(f, (PLAYER_WIDTH, PLAYER_HEIGHT))
        if tex:
            animations["idle"].append(tex)

    run_filenames = ["player_run1.png", "player_run2.png"]
    for f in run_filenames:
        tex = load_texture(f, (PLAYER_WIDTH, PLAYER_HEIGHT))
        if tex:
            animations["run"].append(tex)

    jump_tex = load_texture("player_jump.png", (PLAYER_WIDTH, PLAYER_HEIGHT))
    if jump_tex:
        animations["jump"].append(jump_tex)

    # If general player.png exists, map it across any states missing specific sequences
    base_player = load_texture("player.png", (PLAYER_WIDTH, PLAYER_HEIGHT))
    if base_player:
        if not animations["idle"]:
            animations["idle"].append(base_player)
        if not animations["run"]:
            animations["run"].append(base_player)
        if not animations["jump"]:
            animations["jump"].append(base_player)

    # 2. Programmatic Fallback Generation only for states completely missing images
    # Fallback Idle: 2-frame breathing / visor bob
    if not animations["idle"]:
        s1 = pygame.Surface((PLAYER_WIDTH, PLAYER_HEIGHT), pygame.SRCALPHA)
        pygame.draw.rect(s1, COLOR_PLAYER, (0, 0, PLAYER_WIDTH, PLAYER_HEIGHT), border_radius=4)
        pygame.draw.rect(s1, (255, 255, 255), (PLAYER_WIDTH - 12, 10, 8, 8))
        pygame.draw.rect(s1, (20, 20, 20), (PLAYER_WIDTH - 8, 12, 4, 4))
        pygame.draw.rect(s1, (40, 110, 200), (0, 32, PLAYER_WIDTH, 6))

        s2 = pygame.Surface((PLAYER_WIDTH, PLAYER_HEIGHT), pygame.SRCALPHA)
        pygame.draw.rect(s2, COLOR_PLAYER, (0, 2, PLAYER_WIDTH, PLAYER_HEIGHT - 2), border_radius=4)
        pygame.draw.rect(s2, (255, 255, 255), (PLAYER_WIDTH - 12, 12, 8, 8))
        pygame.draw.rect(s2, (20, 20, 20), (PLAYER_WIDTH - 8, 14, 4, 4))
        pygame.draw.rect(s2, (40, 110, 200), (0, 34, PLAYER_WIDTH, 6))

        animations["idle"] = [s1, s2]

    # Fallback Run: 2-frame kinetic striding
    if not animations["run"]:
        r1 = pygame.Surface((PLAYER_WIDTH, PLAYER_HEIGHT), pygame.SRCALPHA)
        pygame.draw.rect(r1, COLOR_PLAYER, (2, 0, PLAYER_WIDTH - 4, PLAYER_HEIGHT), border_radius=4)
        pygame.draw.rect(r1, (255, 255, 255), (PLAYER_WIDTH - 10, 10, 8, 8))
        pygame.draw.rect(r1, (20, 20, 20), (PLAYER_WIDTH - 6, 12, 4, 4))
        pygame.draw.rect(r1, (240, 200, 80), (0, 48, 14, 12))
        pygame.draw.rect(r1, (40, 110, 200), (PLAYER_WIDTH - 14, 48, 14, 12))

        r2 = pygame.Surface((PLAYER_WIDTH, PLAYER_HEIGHT), pygame.SRCALPHA)
        pygame.draw.rect(r2, COLOR_PLAYER, (2, 0, PLAYER_WIDTH - 4, PLAYER_HEIGHT), border_radius=4)
        pygame.draw.rect(r2, (255, 255, 255), (PLAYER_WIDTH - 10, 10, 8, 8))
        pygame.draw.rect(r2, (20, 20, 20), (PLAYER_WIDTH - 6, 12, 4, 4))
        pygame.draw.rect(r2, (40, 110, 200), (0, 48, 14, 12))
        pygame.draw.rect(r2, (240, 200, 80), (PLAYER_WIDTH - 14, 48, 14, 12))

        animations["run"] = [r1, r2]

    # Fallback Jump: 1-frame stretched airborne posture
    if not animations["jump"]:
        j1 = pygame.Surface((PLAYER_WIDTH, PLAYER_HEIGHT), pygame.SRCALPHA)
        pygame.draw.rect(j1, (90, 180, 255), (0, 0, PLAYER_WIDTH, PLAYER_HEIGHT - 6), border_radius=4)
        pygame.draw.rect(j1, (255, 255, 255), (PLAYER_WIDTH - 12, 8, 8, 8))
        pygame.draw.rect(j1, (20, 20, 20), (PLAYER_WIDTH - 8, 10, 4, 4))
        pygame.draw.rect(j1, (40, 110, 200), (4, PLAYER_HEIGHT - 12, PLAYER_WIDTH - 8, 6))

        animations["jump"] = [j1]

    return animations

# =====================================================================
# Expanded Level Grid Matrix (15 Rows x 60 Columns = 2400px Wide)
# =====================================================================
_SECTION_1 = [
    "10000000000000000000",  # Row 0
    "10000000000000000000",  # Row 1
    "10000000000000000000",  # Row 2
    "1000000000000CC00000",  # Row 3
    "10000000000001111000",  # Row 4: High platform
    "100000000CC000000000",  # Row 5
    "10000000111100000000",  # Row 6: Mid platform
    "100CC000000000000000",  # Row 7
    "10111100000000000000",  # Row 8: Low platform
    "10000000001000010000",  # Row 9: Patrol barrier
    "10000000001E0C010000",  # Row 10: Enemy + coin
    "10000000001111110000",  # Row 11: Base
    "10000000000000000000",  # Row 12
    "10000E0000CC0000E000",  # Row 13: Ground enemies & coins
    "11111111111111111111",  # Row 14: Continuous solid ground
]

_SECTION_2 = [
    "00000000000000000000",  # Row 0
    "00000000000000000000",  # Row 1
    "00000000000000000000",  # Row 2
    "00000000000000000000",  # Row 3
    "000011110000000CC000",  # Row 4: Stepped sky island
    "00000000000000111100",  # Row 5
    "00000000000000000000",  # Row 6
    "00000000CC0000000000",  # Row 7
    "00000001111000000000",  # Row 8: Mid platform
    "00100000000001000000",  # Row 9: Elevated patrol walls
    "0010E0CC0E0001000000",  # Row 10: Double patrol + coins
    "00111111111111000000",  # Row 11: Long bridge
    "00000000000000000000",  # Row 12
    "0000E0000000CC000E00",  # Row 13: Ground hazards
    "11111111111111111111",  # Row 14: Continuous solid ground
]

_SECTION_3 = [
    "00000000000000000001",  # Row 0
    "00000000000000000001",  # Row 1
    "00000000000000000001",  # Row 2
    "000000000000CCCC0001",  # Row 3: Golden treasure vault!
    "00000000000111111001",  # Row 4: Vault roof
    "000000CC000100001001",  # Row 5: Vault chamber
    "0000011110010E001001",  # Row 6: Vault guardian enemy
    "00000000000111001001",  # Row 7: Stepped ascent
    "00CC0000000000001001",  # Row 8
    "01111000000000001001",  # Row 9: High ledge
    "00000000000000001001",  # Row 10
    "00000000000000001001",  # Row 11
    "00000000000000001001",  # Row 12
    "000E0000CC0000E00001",  # Row 13: Final gauntlet
    "11111111111111111111",  # Row 14: Continuous solid ground
]

LEVEL_MAP: list[list[str]] = [
    list(s1 + s2 + s3) for s1, s2, s3 in zip(_SECTION_1, _SECTION_2, _SECTION_3)
]


class Camera:
    """Scrolling viewport coordinator implementing smoothed linear interpolation (lerp) tracking."""

    def __init__(self, viewport_width: int, viewport_height: int, level_width: int, level_height: int) -> None:
        self.viewport_width = viewport_width
        self.viewport_height = viewport_height
        self.level_width = level_width
        self.level_height = level_height
        self.x: float = 0.0
        self.y: float = 0.0
        self.smooth_speed: float = 0.08

    def update(self, target: Player) -> None:
        """Smoothly track target entity, keeping it centered horizontally in the viewport."""
        target_x = target.rect.centerx - self.viewport_width // 2
        target_y = target.rect.centery - self.viewport_height // 2

        max_scroll_x = max(0, self.level_width - self.viewport_width)
        max_scroll_y = max(0, self.level_height - self.viewport_height)

        clamped_x = max(0, min(target_x, max_scroll_x))
        clamped_y = max(0, min(target_y, max_scroll_y))

        self.x += (clamped_x - self.x) * self.smooth_speed
        self.y += (clamped_y - self.y) * self.smooth_speed

    def apply(self, rect: pygame.Rect) -> pygame.Rect:
        """Transform world-space coordinates into screen-space viewport coordinates."""
        return pygame.Rect(
            rect.x - int(self.x),
            rect.y - int(self.y),
            rect.width,
            rect.height,
        )


class Coin:
    """Collectible reward item placed throughout the environment."""

    def __init__(
        self,
        x: float,
        y: float,
        size: int = COIN_SIZE,
        image: pygame.Surface | None = None,
    ) -> None:
        offset = (TILE_SIZE - size) // 2
        self.rect = pygame.Rect(int(x) + offset, int(y) + offset, size, size)
        self.color = COLOR_COIN
        self.highlight_color = COLOR_COIN_HIGHLIGHT
        self.border_color = COLOR_COIN_BORDER
        self.image = image

    def draw(self, surface: pygame.Surface, camera: Camera) -> None:
        """Render the coin sprite or fallback gold medallion in screen space."""
        screen_rect = camera.apply(self.rect)
        if self.image is not None:
            surface.blit(self.image, screen_rect)
        else:
            center = screen_rect.center
            radius = screen_rect.width // 2

            pygame.draw.circle(surface, self.border_color, center, radius)
            pygame.draw.circle(surface, self.color, center, radius - 2)
            pygame.draw.circle(
                surface,
                self.highlight_color,
                (center[0] - 2, center[1] - 2),
                radius // 3,
            )


class Enemy:
    """Patrolling adversary featuring autonomous movement, taller scaling, and collision avoidance."""

    def __init__(
        self,
        x: float,
        y: float,
        width: int = ENEMY_WIDTH,      # 40px
        height: int = ENEMY_HEIGHT,    # 55px (noticeably taller)
        speed: float = ENEMY_SPEED,
        color: tuple[int, int, int] = COLOR_ENEMY,
        image: pygame.Surface | None = None,
    ) -> None:
        """Initialize enemy entity, scale texture transformation, and set taller hitbox."""
        self.width = width
        self.height = height

        # Scale transforming configuration to force taller sprite dimensions (40x55)
        if image is not None:
            self.image = pygame.transform.scale(image, (self.width, self.height))
        else:
            self.image = None

        # Align feet with tile bottom
        offset_x = (TILE_SIZE - self.width) // 2
        offset_y = TILE_SIZE - self.height

        # Hit-box rectangle configuration matching taller size scale exactly for AABB precision
        self.rect = pygame.Rect(int(x) + offset_x, int(y) + offset_y, self.width, self.height)

        self.vx = speed
        self.vy = 0.0
        self.gravity = GRAVITY
        self.color = color
        self.eye_color = (255, 255, 255)

    def update(self, tiles: list[pygame.Rect]) -> None:
        """Advance enemy kinematics and resolve axis-separated environment collisions."""
        # Step A: Horizontal Kinematics & Wall Bounce
        self.rect.x += int(self.vx)
        for tile in tiles:
            if self.rect.colliderect(tile):
                if self.vx > 0:
                    self.rect.right = tile.left
                    self.vx = -abs(self.vx)
                elif self.vx < 0:
                    self.rect.left = tile.right
                    self.vx = abs(self.vx)

        # Step B: Vertical Kinematics & Platform Landing
        self.vy += self.gravity
        self.rect.y += int(self.vy)
        for tile in tiles:
            if self.rect.colliderect(tile):
                if self.vy > 0:
                    self.rect.bottom = tile.top
                    self.vy = 0.0
                elif self.vy < 0:
                    self.rect.top = tile.bottom
                    self.vy = 0.0

    def draw(self, surface: pygame.Surface, camera: Camera) -> None:
        """Render the taller enemy sprite or fallback body with directional eyes."""
        screen_rect = camera.apply(self.rect)
        if self.image is not None:
            sprite = pygame.transform.flip(self.image, True, False) if self.vx < 0 else self.image
            surface.blit(sprite, screen_rect)
        else:
            pygame.draw.rect(surface, self.color, screen_rect, border_radius=4)
            eye_x = screen_rect.x + (5 if self.vx < 0 else screen_rect.width - 11)
            pygame.draw.rect(surface, self.eye_color, pygame.Rect(eye_x, screen_rect.y + 12, 6, 6))


class World:
    """Level environment parser and manager for static and interactive elements."""

    def __init__(
        self,
        map_data: list[list[str]],
        tile_image: pygame.Surface | None = None,
        coin_image: pygame.Surface | None = None,
        enemy_image: pygame.Surface | None = None,
    ) -> None:
        self.tiles: list[pygame.Rect] = []
        self.coins: list[Coin] = []
        self.enemies: list[Enemy] = []
        self.tile_color = COLOR_TILE
        self.border_color = COLOR_TILE_BORDER
        self.tile_image = tile_image
        self.coin_image = coin_image
        self.enemy_image = enemy_image
        self.load_map(map_data)

    def load_map(self, map_data: list[list[str]]) -> None:
        """Parse grid matrix rows and columns to instantiate tiles, coins, and enemies."""
        self.tiles.clear()
        self.coins.clear()
        self.enemies.clear()

        for row_idx, row in enumerate(map_data):
            for col_idx, tile in enumerate(row):
                x = col_idx * TILE_SIZE
                y = row_idx * TILE_SIZE

                if tile == "1":
                    tile_rect = pygame.Rect(x, y, TILE_SIZE, TILE_SIZE)
                    self.tiles.append(tile_rect)
                elif tile == "C":
                    self.coins.append(Coin(x, y, image=self.coin_image))
                elif tile == "E":
                    self.enemies.append(
                        Enemy(
                            x,
                            y,
                            width=ENEMY_WIDTH,
                            height=ENEMY_HEIGHT,
                            image=self.enemy_image,
                        )
                    )

    def draw(self, surface: pygame.Surface, camera: Camera) -> None:
        """Render all world tiles, coins, and enemies in screen space with frustum culling."""
        for tile in self.tiles:
            screen_rect = camera.apply(tile)
            if -TILE_SIZE <= screen_rect.x <= SCREEN_WIDTH and -TILE_SIZE <= screen_rect.y <= SCREEN_HEIGHT:
                if self.tile_image is not None:
                    surface.blit(self.tile_image, screen_rect)
                else:
                    pygame.draw.rect(surface, self.tile_color, screen_rect)
                    pygame.draw.rect(surface, self.border_color, screen_rect, width=2)

        for coin in self.coins:
            coin.draw(surface, camera)

        for enemy in self.enemies:
            enemy.draw(surface, camera)


class Player:
    """User-controlled avatar with kinematic physics, AABB collisions, and animated sprites."""

    def __init__(
        self,
        x: float = 100.0,
        y: float = 200.0,
        width: int = PLAYER_WIDTH,
        height: int = PLAYER_HEIGHT,
        color: tuple[int, int, int] = COLOR_PLAYER,
        animations: dict[str, list[pygame.Surface]] | None = None,
    ) -> None:
        self.spawn_x = float(x)
        self.spawn_y = float(y)
        self.rect = pygame.Rect(int(x), int(y), width, height)

        self.vx = 0.0
        self.vy = 0.0

        self.speed = PLAYER_SPEED
        self.jump_force = JUMP_FORCE
        self.gravity = GRAVITY

        self.on_ground = False
        self.color = color

        self.state: str = "idle"
        self.frame_index: float = 0.0
        self.animation_speed: float = 0.15
        self.facing_right: bool = True

        self.animations: dict[str, list[pygame.Surface]] = (
            animations if animations is not None else load_player_animations()
        )

    def reset(self) -> None:
        """Reset player coordinates to original spawn location and zero velocities."""
        self.rect.topleft = (int(self.spawn_x), int(self.spawn_y))
        self.vx = 0.0
        self.vy = 0.0
        self.on_ground = False
        self.state = "idle"
        self.frame_index = 0.0
        self.facing_right = True

    def handle_input(self) -> None:
        """Stage 1: Sample continuous keyboard state for movement and jump initiation."""
        keys = pygame.key.get_pressed()

        move_dir = 0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            move_dir -= 1
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            move_dir += 1

        self.vx = move_dir * self.speed

        if (keys[pygame.K_SPACE] or keys[pygame.K_w]) and self.on_ground:
            self.vy = self.jump_force
            self.on_ground = False

    def update(self, tiles: list[pygame.Rect]) -> None:
        """Stage 2: Execute AABB collision resolution and update animation frame state."""
        # --- Step A: Horizontal Kinematics & Collision ---
        self.rect.x += int(self.vx)
        for tile in tiles:
            if self.rect.colliderect(tile):
                if self.vx > 0:
                    self.rect.right = tile.left
                elif self.vx < 0:
                    self.rect.left = tile.right

        # --- Step B: Vertical Kinematics & Collision ---
        self.on_ground = False
        self.vy += self.gravity
        self.rect.y += int(self.vy)
        for tile in tiles:
            if self.rect.colliderect(tile):
                if self.vy > 0:
                    self.rect.bottom = tile.top
                    self.on_ground = True
                elif self.vy < 0:
                    self.rect.top = tile.bottom
                self.vy = 0.0

        # --- Step C: Animation State & Sequencer Tracking ---
        if self.vx > 0:
            self.facing_right = True
        elif self.vx < 0:
            self.facing_right = False

        if not self.on_ground:
            new_state = "jump"
        elif abs(self.vx) > 0.1:
            new_state = "run"
        else:
            new_state = "idle"

        if new_state != self.state:
            self.state = new_state
            self.frame_index = 0.0

        current_frames = self.animations.get(self.state, [])
        if current_frames:
            self.frame_index = (self.frame_index + self.animation_speed) % len(current_frames)

    def draw(self, surface: pygame.Surface, camera: Camera) -> None:
        """Stage 3: Render animated sprite directly onto the surface without drawing a solid box.

        If the player frame asset exists, ONLY surface.blit() is called.
        Drawing a solid fallback background rect is completely bypassed.
        """
        screen_rect = camera.apply(self.rect)
        current_frames = self.animations.get(self.state, [])

        if current_frames:
            frame_idx = int(self.frame_index) % len(current_frames)
            image = current_frames[frame_idx]

            if not self.facing_right:
                image = pygame.transform.flip(image, True, False)

            # ONLY blit the sprite - completely bypass drawing any solid background rect
            surface.blit(image, screen_rect)
        else:
            # Strictly executes as fallback if no texture frames could be loaded or generated
            pygame.draw.rect(surface, self.color, screen_rect)


class Game:
    """Core coordinator managing the engine lifecycle, state machine, and loops."""

    def __init__(self) -> None:
        """Initialize Pygame, display surfaces, assets, camera, and the state machine."""
        pygame.init()
        pygame.display.set_caption(WINDOW_TITLE)

        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.clock = pygame.time.Clock()
        self.dt = 0.0
        self.is_running = True

        # State Machine Variable ("START", "PLAYING", "GAME_OVER", "WIN")
        self.game_state: str = "START"

        # Typography System
        self.font_title = pygame.font.SysFont("Arial", 46, bold=True)
        self.font_subtitle = pygame.font.SysFont("Arial", 22)
        self.font_prompt = pygame.font.SysFont("Arial", 24, bold=True)
        self.font_hud = pygame.font.SysFont("Arial", 22, bold=True)

        # Asset Management
        self.assets: dict[str, pygame.Surface | None] = {
            "background": load_texture("background.png", (SCREEN_WIDTH, SCREEN_HEIGHT)),
            "tile": load_texture("tile.png", (TILE_SIZE, TILE_SIZE)),
            "enemy": load_texture("enemy.png", (ENEMY_WIDTH, ENEMY_HEIGHT)),
            "coin": load_texture("coin.png", (COIN_SIZE, COIN_SIZE)),
        }
        self.player_animations = load_player_animations()

        # World & Entity Instantiation
        self.score = 0
        self.world = World(
            LEVEL_MAP,
            tile_image=self.assets["tile"],
            coin_image=self.assets["coin"],
            enemy_image=self.assets["enemy"],
        )
        self.player = Player(
            x=100.0,
            y=200.0,
            animations=self.player_animations,
        )

        level_pixel_width = len(LEVEL_MAP[0]) * TILE_SIZE
        level_pixel_height = len(LEVEL_MAP) * TILE_SIZE
        self.camera = Camera(SCREEN_WIDTH, SCREEN_HEIGHT, level_pixel_width, level_pixel_height)

    def reset_game(self) -> None:
        """Recreate the world grid, reset entities, score, camera, and enter PLAYING state."""
        self.score = 0
        self.world = World(
            LEVEL_MAP,
            tile_image=self.assets["tile"],
            coin_image=self.assets["coin"],
            enemy_image=self.assets["enemy"],
        )
        self.player.reset()
        self.camera.x = 0.0
        self.camera.y = 0.0
        self.game_state = "PLAYING"

    def process_input(self) -> None:
        """Stage 1: Process OS events and route inputs based on the active state."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.is_running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.is_running = False

                # State Transition Event Triggers
                if self.game_state == "START":
                    if event.key == pygame.K_SPACE:
                        self.reset_game()
                elif self.game_state in ("GAME_OVER", "WIN"):
                    if event.key == pygame.K_r:
                        self.reset_game()

        # Continuous physics movement controls active only during PLAYING
        if self.game_state == "PLAYING":
            self.player.handle_input()

    def update(self) -> None:
        """Stage 2: Advance gameplay simulations only while in PLAYING state."""
        if self.game_state != "PLAYING":
            return

        # 1. Kinematic updates
        self.player.update(self.world.tiles)
        for enemy in self.world.enemies:
            enemy.update(self.world.tiles)

        # 2. Camera tracking
        self.camera.update(self.player)

        # 3. Collectible interactions
        for coin in self.world.coins[:]:
            if self.player.rect.colliderect(coin.rect):
                self.score += 1
                self.world.coins.remove(coin)

        # 4. Win Condition: Check if all coins have been collected
        if len(self.world.coins) == 0:
            self.game_state = "WIN"
            return

        # 5. Hazard Condition: Enemy collision triggers GAME_OVER
        for enemy in self.world.enemies:
            if self.player.rect.colliderect(enemy.rect):
                self.game_state = "GAME_OVER"
                break

    def render(self) -> None:
        """Stage 3: Render visual scenes based on active state conditional branches."""
        # -------------------------------------------------------------
        # State: START SCREEN
        # -------------------------------------------------------------
        if self.game_state == "START":
            self.screen.fill(COLOR_BG)

            # Title
            title_surf = self.font_title.render("2D PROTOCOL ENGINE", True, COLOR_ACCENT)
            title_rect = title_surf.get_rect(center=(SCREEN_WIDTH // 2, 180))
            self.screen.blit(title_surf, title_rect)

            # Subtitle / Controls
            controls_text = "CONTROLS:  A / D or ARROWS to Move   |   SPACE or W to Jump"
            controls_surf = self.font_subtitle.render(controls_text, True, (180, 190, 205))
            controls_rect = controls_surf.get_rect(center=(SCREEN_WIDTH // 2, 260))
            self.screen.blit(controls_surf, controls_rect)

            objective_text = "MISSION:  Collect all gold protocol coins while avoiding red hazards"
            obj_surf = self.font_subtitle.render(objective_text, True, (140, 150, 165))
            obj_rect = obj_surf.get_rect(center=(SCREEN_WIDTH // 2, 305))
            self.screen.blit(obj_surf, obj_rect)

            # Blinking Start Prompt
            blink_visible = (pygame.time.get_ticks() % 1000) < 600
            if blink_visible:
                prompt_surf = self.font_prompt.render("PRESS SPACE TO START", True, COLOR_TEXT)
                prompt_rect = prompt_surf.get_rect(center=(SCREEN_WIDTH // 2, 420))
                self.screen.blit(prompt_surf, prompt_rect)

            pygame.display.flip()
            return

        # -------------------------------------------------------------
        # Base Graphic Cycle (Used by PLAYING, GAME_OVER, and WIN)
        # -------------------------------------------------------------
        if self.assets["background"] is not None:
            self.screen.blit(self.assets["background"], (0, 0))
        else:
            self.screen.fill(COLOR_BG)

        # Layer 1: World geometry, coins, and enemies
        self.world.draw(self.screen, self.camera)

        # Layer 2: Player avatar (strictly blits sprite without solid background rect)
        self.player.draw(self.screen, self.camera)

        # Layer 3: Heads-Up Display (HUD)
        score_surface = self.font_hud.render(f"Score: {self.score}", True, COLOR_TEXT)
        self.screen.blit(score_surface, (20, 16))

        coins_left_surface = self.font_hud.render(
            f"Coins Remaining: {len(self.world.coins)}", True, (255, 230, 120)
        )
        self.screen.blit(coins_left_surface, (20, 44))

        # -------------------------------------------------------------
        # State: GAME OVER OVERLAY
        # -------------------------------------------------------------
        if self.game_state == "GAME_OVER":
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((15, 10, 15, 200))
            self.screen.blit(overlay, (0, 0))

            over_surf = self.font_title.render("PROTOCOL COMPROMISED", True, COLOR_LOSE)
            over_rect = over_surf.get_rect(center=(SCREEN_WIDTH // 2, 200))
            self.screen.blit(over_surf, over_rect)

            stats_surf = self.font_subtitle.render(f"Final Data Score: {self.score}", True, COLOR_TEXT)
            stats_rect = stats_surf.get_rect(center=(SCREEN_WIDTH // 2, 275))
            self.screen.blit(stats_surf, stats_rect)

            blink_visible = (pygame.time.get_ticks() % 1000) < 600
            if blink_visible:
                retry_surf = self.font_prompt.render("PRESS R TO RESTART", True, (255, 220, 100))
                retry_rect = retry_surf.get_rect(center=(SCREEN_WIDTH // 2, 380))
                self.screen.blit(retry_surf, retry_rect)

        # -------------------------------------------------------------
        # State: WIN OVERLAY
        # -------------------------------------------------------------
        elif self.game_state == "WIN":
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((10, 20, 15, 200))
            self.screen.blit(overlay, (0, 0))

            win_surf = self.font_title.render("MISSION ACCOMPLISHED!", True, COLOR_WIN)
            win_rect = win_surf.get_rect(center=(SCREEN_WIDTH // 2, 200))
            self.screen.blit(win_surf, win_rect)

            stats_surf = self.font_subtitle.render(
                f"All Coins Collected! Perfect Score: {self.score}", True, COLOR_TEXT
            )
            stats_rect = stats_surf.get_rect(center=(SCREEN_WIDTH // 2, 275))
            self.screen.blit(stats_surf, stats_rect)

            blink_visible = (pygame.time.get_ticks() % 1000) < 600
            if blink_visible:
                retry_surf = self.font_prompt.render("PRESS R TO REPLAY", True, (255, 230, 120))
                retry_rect = retry_surf.get_rect(center=(SCREEN_WIDTH // 2, 380))
                self.screen.blit(retry_surf, retry_rect)

        pygame.display.flip()

    def run(self) -> None:
        """Execute the primary 60 FPS delta-time game loop."""
        while self.is_running:
            self.dt = self.clock.tick(FPS) / 1000.0

            self.process_input()
            self.update()
            self.render()

        self.cleanup()

    def cleanup(self) -> None:
        """Gracefully release Pygame hardware contexts and terminate process."""
        pygame.quit()
        sys.exit()


def main() -> None:
    """Initialize engine runtime and start the primary game loop."""
    game = Game()
    game.run()


if __name__ == "__main__":
    main()