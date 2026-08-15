# How to Run - GAIT Assignment 2

This document explains how to run both parts of the assignment: Part 1 (A* Pathfinding) and Part 2 (MCTS Connect4). They are two separate, independent programs and are run separately.

---

## Table of Contents

1. [Requirements](#1-requirements)
2. [Project structure](#2-project-structure)
3. [Part 1 - A* Pathfinding](#3-part-1--a-pathfinding)
4. [Part 2 - MCTS Connect4](#4-part-2--mcts-connect4)
5. [Troubleshooting](#5-troubleshooting)

---

## 1. Requirements

- Python 3.9 or newer
- The `pygame` library

Install `pygame` if it is not already installed:

```bash
pip install pygame
```

or, on systems where `pip` is mapped to Python 2:

```bash
pip3 install pygame
```

No other third-party packages are required for either part.

---

## 2. Project structure

```
project-root/
├── part1/                  Part 1 - A* Pathfinding
│   ├── main.py                 entry point
│   ├── grid.py
│   ├── frog.py
│   ├── pathfinding.py
│   ├── settings.py
│   ├── effects.py
│   └── audio_fx.py
│
└── part2/                     Part 2 - MCTS Connect4
    ├── connect4_mcts.py        entry point
    ├── assets/                 optional image/audio assets
    ├── audit_baseline/         reference copies of the core MCTS logic
    └── tools/
```

Each part is self-contained within its own folder. Running either program requires being inside that folder (or providing the correct relative/absolute path), since each script imports its neighboring modules by relative filename.

---

## 3. Part 1 - A* Pathfinding

### 3.1 Run

```bash
cd a2_part1
python3 main.py
```

On Windows, `python` may be used in place of `python3` depending on how Python was installed.

### 3.2 Controls

| Input | Action |
|---|---|
| Right-click a reachable, non-wall cell | Run A* from the frog's current position to the clicked cell |
| Left-click a non-frog cell | Toggle that cell between Wall and Grass |
| D | Toggle diagonal movement on/off |
| H | Toggle the cost heatmap overlay |
| C | Toggle per-cell numeric cost labels |
| R | Restart with a fresh layout |

### 3.3 Closing

Close the window, or press the standard window-close shortcut for the operating system in use.

---

## 4. Part 2 - MCTS Connect4

### 4.1 Run

```bash
cd part2
python3 connect4_mcts.py
```

### 4.2 Menu

The menu is mouse-driven. Hover over a difficulty tag to preview it, click a tag to select it, and click the corresponding PLAY button to start that mode.

- **Human vs AI** - select a difficulty for the AI opponent, then click PLAY.
- **AI vs AI** - select a difficulty for each side independently, then click PLAY.

Keyboard shortcuts remain available as an alternative to the mouse (number keys and arrow keys for mode/difficulty selection), but are not required.

### 4.3 In-game controls

| Input | Action |
|---|---|
| Left-click a column (Human vs AI only) | Drop a disc in that column |
| R | Restart the current game |
| TAB | Show or hide the debug telemetry panel |
| ESC | Return to the menu |

### 4.4 Assets

The `assets/` folder is optional. If it is present and populated, the game loads real images for the discs and AI avatars. If it is absent or incomplete, the game falls back to procedurally drawn discs automatically; this does not cause an error.

---

## 5. Troubleshooting

**`ModuleNotFoundError: No module named 'pygame'`**
Run `pip install pygame` (or `pip3 install pygame`), then try again.

**The window opens but nothing responds to clicks**
Confirm the terminal/command window used to launch the script is not itself capturing keyboard focus; click directly on the game window first.

**No sound is heard**
Audio failures are handled silently by design - if the system has no available audio output device, the game continues to run without sound rather than crashing. This does not indicate a bug.

**Script exits immediately with a traceback**
Confirm the command is being run from inside the correct folder (`a2_part1` or `part2`), since both entry points rely on relative imports from their own folder.
