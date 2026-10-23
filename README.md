# Custom 2D Kinematic Platformer Engine from Scratch

A high-performance, architecture-focused 2D tile-based platformer game engine engineered entirely from scratch in Python using Pygame. This repository demonstrates standard game loop design patterns, discrete physics integration, spatial data handling, and custom rendering state architectures without relying on high-level game engines.

---

## ⚙️ Core Technical Implementation

### 1. The Game Loop & Double-Buffered Rendering
The application handles engine states through a structured delta-time throttled `while` loop running at a targeted 60 frames per second. Visuals leverage a double-buffered surface canvas, queuing rendering commands sequentially to eliminate visual flicker:
`Background Layer` ➔ `Static Tile Grid` ➔ `Interactive Entities (Coins/Enemies)` ➔ `Player Asset` ➔ `HUD Overlays`

### 2. Classical Kinematics Physics Integration
Entity movement utilizes Semi-Implicit Euler Integration rather than immediate coordinate mutations. The engine maintains dynamic vectors for positioning, velocity, and gravity vectors:
- **Vertical Kinematics:** $v_y = v_y + \text{gravity} \cdot \Delta t$
- **Position Update:** $x = x + v_x$, $y = y + v_y$
Jumping mechanics inject an instantaneous upward vector impulse ($v_y = -u$) executed solely when the entity's grounded state evaluates to true.

### 3. $O(1)$ Spatial Matrix Indexing & AABB Collisions
Level layouts map directly to a nested 2D integer array grid matrix. Instead of checking calculations against all level blocks in an unoptimized $O(N)$ sweep loop, the environment references tile spatial sizes (`TILE_SIZE = 40`). This translates coordinates instantly into grid lookup positions via fast integer division, keeping world intersections at a constant **$O(1)$ time complexity**.

### 4. Asymptotic Linear Interpolation (Lerp) Camera Matrices
The virtual camera translation matrix decouples internal tracking mechanics from the active monitor viewport boundaries. To remove harsh screen jerking as the player shifts along an expanded, ultra-wide custom horizontal matrix map layout, target tracking uses a smoothed calculation:
$$X_{\text{camera}} \leftarrow X_{\text{camera}} + (X_{\text{player}} - \frac{W_{\text{screen}}}{2} - X_{\text{camera}}) \times 0.1$$

---

## 🐛 Core Engineering Bugs Encountered & Architectural Resolutions

Building a custom system from scratch introduces architectural edge-cases. The following structural bugs were diagnosed and resolved during development:

### Bug 1: The Diagonal Bumping & Corner-Clipping Defect
- **The Issue:** Updating both X and Y coordinate updates simultaneously caused the player rectangle to snag on tile edges or clip diagonally directly inside solid blocks when jumping at corners.
- **The Fix:** Implemented a strict **Axis Separation Resolution Pipeline**. Horizontal velocities are processed and resolved against grid matrices first (snapping edges to target blocks and halting $v_x$). Vertical velocities and gravity factors are evaluated separately immediately afterward.

### Bug 2: Endless Multi-Jump Exploit
- **The Issue:** The player could continuously trigger jump impulse variables while airborne, floating past environmental boundaries.
- **The Fix:** Bound a state flag check (`on_ground`) strictly to the vertical processing channel. The impulse check is rejected unless the baseline AABB intersection validates that the player's lower coordinate boundary is resting perfectly flush on a solid tile surface.

### Bug 3: I/O Hardware Bottlenecks & Asset Corruption
- **The Issue:** Attempting to force incorrect file extensions or loading textures every single frame dropped rendering frequencies to unplayable levels.
- **The Fix:** Structured defensive `try/except` initialization wrappers loading components once into RAM surfaces using `.convert_alpha()` for optimization. Programmatic vector rectangle geometry calculations function automatically as structural execution fallbacks if asset paths ever break.

---

## 🚀 Execution & Setup Instructions

### Prerequisites
Ensure your local environment runs Python 3.10+ and has the Pygame library installed:
```bash
pip install pygame
```

### Running the Application
Clone this repository and run the primary script from your terminal:
```bash
git clone https://github.com[YourGitHubUsername]/tile-platformer-game.git
cd tile-platformer-game
python app.py
```
