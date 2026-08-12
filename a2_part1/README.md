# A2 Part 1

Standalone demo: cost-weighted A* over a grid with reveal-before-move visualization and a frog that follows the final path using explicit Seek steering.

## Run

From inside `a2_part1/`:

```bash
python main.py
```

## Controls

- Right-click: run A* to the clicked cell
- Left-click: toggle Wall/Grass on a cell (cannot place wall on frog cell)
- `D`: toggle diagonal movement
- `H`: toggle terrain heatmap
- `C`: toggle per-cell cost labels
- `R`: restart the map and frog

The project uses standard A* over a weighted-cost grid. It does not implement formal Weighted A*.
The HUD includes a dedicated path-cost panel with total cost, terrain-cell composition, and path length.