# ============================================================================
# settings.py
# Purpose
#   Central place for all constants and tuning values.
#   You can tweak speeds, radii, and counts here without touching logic.
# Reading guide
#   Each variable has a short note so you know what it controls.
# ============================================================================

# Window size in pixels
WIDTH, HEIGHT = 1280, 720

# Target frames per second for the game loop
FPS = 60

# Colors as RGB tuples. Used by drawing code for the UI and agents.
BG    = (28, 33, 38)     # background color
WHITE = (240, 240, 240)  # text and highlights
GREEN = (90, 220, 120)   # frog color
BLUE  = (120, 180, 250)  # bubble color
YELLOW= (250, 225, 120)  # fly color when flocking or idle
PURPLE= (185, 120, 250)  # fly color when fleeing
RED   = (232, 88, 88)    # health hearts
MUTED = (180, 188, 196)  # hint text

# Frog setup
FROG_RADIUS = 16          # draw size and collision size for the frog
FROG_SPEED  = 300.0       # top speed for the frog in pixels per second
HURT_INVULN = 3.0         # seconds of temporary invulnerability after damage
FROG_FACING_MIN_SPEED_SQ = 16.0 # speed for facing shotting
# Bubble setup
BUBBLE_RADIUS   = 8       # visual radius and collision radius
BUBBLE_SPEED    = 380.0   # how fast the bubble travels
BUBBLE_LIFETIME = 2.0     # seconds before the bubble pops automatically

# Fly setup
FLY_CLUSTER_COUNT = 4        # number of initial flock clusters
FLY_CLUSTER_SPAWN_RADIUS = 90.0  # max offset from a cluster center when spawning
NUM_FLIES = 10           # how many flies spawn
FLY_RADIUS = 8            # fly draw and collision radius
FLY_SPEED  = 120.0        # fly max speed

# Fly panic/fleeing tuning
FLEE_PANIC_RANGE    = 220.0   # distance at which panic scaling starts kicking in
FLEE_PANIC_EXPONENT = 2.4     # >1 = sharper, more dramatic ramp-up as distance shrinks
FLEE_PANIC_MAX_MULT = 3.0     # maximum multiplier applied to evade force at point-blank range
FLEE_BURST_STRENGTH = 360.0   # one-time velocity kick applied the instant a fly starts fleeing

# Fly FSM perception radii and timers
FLY_SCARED_RANGE      = 160.0   # frog proximity that triggers Fleeing
FLY_BUBBLE_FLEE_RANGE = 140.0   # bubble proximity that triggers Fleeing
FLY_CALM_RANGE        = 220.0   # frog and bubbles must both clear this to start calming
FLY_IDLE_DISTANCE     = 380.0   # frog distance beyond which an isolated fly may idle
FLY_IDLE_DELAY        = 10     # seconds of isolation+distance before entering Idle
FLY_SCARE_TIMER       = 0.6     # seconds a fly stays nervous after the last scare

# Boids neighborhood and weights
# These determine how flies react to neighbors
NEIGHBOR_RADIUS = 150.0   # how far a fly considers other flies as neighbors
REGROUP_RADIUS  = 500.0   # search radius for the nearest fly when totally alone
REGROUP_WEIGHT  = 0.6     # how gently an isolated fly steers back toward the group
SEP_RADIUS      = 40.0    # separation threshold distance
SEP_WEIGHT      = 2.0     # weight for separation force
COH_WEIGHT      = 0.8     # weight for cohesion force
ALI_WEIGHT      = 1.1     # weight for alignment force
ALI_STRENGTH    = 1.5     # base scale for the alignment force before ALI_WEIGHT is applied
ANCHOR_WEIGHT   = 0.6     # small pull to arena center to keep flock on screen
CATCHUP_GROUP_DELTA  = 1     # how many more neighbors the other group needs to trigger catch-up
CATCHUP_SPEED_MULT   = 1.6   # speed multiplier while hurrying to join a bigger group
CATCHUP_WEIGHT       = 1.4   # steering weight while catching up
CATCHUP_MIN_OWN_GROUP = 2     # only consider catch-up if my own group is this small or smaller 
CATCHUP_MAX_OWN_GROUP = 4    # only consider catch-up if my own group is this small or smaller
CATCHUP_SEARCH_RADIUS = 350.0 
COH_DEAD_ZONE_RADIUS  = 6.0  # boids cohesion: no pull if within this distance of flock center
COH_SLOW_ZONE_RADIUS  = 30.0 # boids cohesion: full-strength pull begins beyond this distance

# Arrive behavior
# Slow inside slow radius and stop inside stop radius
ARRIVE_SLOW_RADIUS  = 120.0
ARRIVE_STOP_RADIUS  = 8.0
ARRIVE_STOP_DAMPING = 14.0   # 1/seconds — higher = faster hard stop once inside stop radius
ARRIVE_STOP_SNAP    = 2.0    # px/s — below this speed, snap directly to zero
STEER_MAX_FORCE = 1500.0

# Snake setup
NUM_SNAKES  = 0
SNAKE_RADIUS = 18
SNAKE_SPEED  = 160.0

# Snake perception ranges for FSM transitions
AGGRO_RANGE   = 260.0     # start chasing when frog gets this close
DEAGGRO_RANGE = 360.0     # stop chasing when frog moves this far

# Snake FSM thresholds and obstacle-avoidance weight curve
SNAKE_ARRIVE_THRESHOLD    = 10.0  # distance considered "reached" for patrol/home targets
SNAKE_CONFUSED_DURATION   = 5   # seconds a snake wanders confused after reaching home
SNAKE_HARMLESS_SPEED_MULT = 0.9   # Harmless state moves slightly slower than normal
SNAKE_AVOID_WEIGHT_MIN    = 0.25  # avoid_weight floor, far from any obstacle
SNAKE_AVOID_WEIGHT_MAX    = 0.65  # avoid_weight ceiling, right next to an obstacle
SNAKE_AVOID_NEAR_DIST     = 80.0  # obstacle distance at which avoid_weight reaches max

# Obstacle avoidance tuning
AVOID_LOOKAHEAD       = 260.0   # how far the snake looks ahead when checking a corridor
AVOID_ANGLE_INCREMENT = 12      # degrees to rotate per step when searching for a free path
AVOID_MAX_ANGLE       = 160     # maximum deviation to try on either side
AVOID_MAX_ANGLE       = 160     # maximum deviation to try on either side
SNAKE_AVOID_RETREAT_RADIUS_MULT = 3.0  # if nearest obstacle is closer than radius * this, retreat instead of creeping forward

# Game rules
START_HEALTH = 3                 # how many hits the frog can take
FLIES_TO_WIN = 10                # win condition counter

# Visual/effect timing
PARTICLE_LIFETIME   = 2   # seconds a burst particle stays visible
HURT_FLASH_DURATION = 0.15  # seconds the red damage flash stays on screen

# --- A* Pathfinding (Assignment 2, Part 1) ---
CELL_SIZE = 24                             # grid cell size in pixels
PATH_OBSTACLE_PADDING = FROG_RADIUS + 6    # inflate obstacles so the path keeps the frog's body clear
PATH_WAYPOINT_RADIUS = FROG_RADIUS * 1.5   # distance at which the frog advances to the next waypoint
PATH_REVEAL_CELLS_PER_FRAME = 40           # how fast the explored-area heatmap animates in
EXPLORED_COLOR_LOW  = (60, 90, 200)        # heatmap color at g-cost = 0 (blue = cheap)
EXPLORED_COLOR_HIGH = (220, 70, 70)        # heatmap color at max explored g-cost (red = expensive)
