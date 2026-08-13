# assets/ — Connect4 MCTS Art Assets

All files here are **optional**. The game runs identically with or without them,
falling back to procedurally-drawn pygame circles for discs.

## Expected files

| Filename               | Slot            | Recommended size | Description                                 |
|------------------------|-----------------|------------------|---------------------------------------------|
| `player1_disc.png`     | `player1`       | 90×90 px         | Coral disc for Human / Player 1             |
| `player2_disc.png`     | `player2`       | 90×90 px         | Amber disc for Player 2                     |
| `ai_alpha_avatar.png`  | `ai_alpha`      | 32×32 px         | Avatar icon for AI in status/debug panels   |
| `ai_beta_avatar.png`   | `ai_beta`       | 32×32 px         | Avatar icon for second AI (AI vs AI)        |
| `board_texture.png`    | `board_texture` | 700×600 px       | Optional texture over the board area        |
| `menu_background.png`  | `menu_background`| 700×1010 px     | Optional background behind menu             |

## Notes
- PNG with alpha (RGBA) recommended.
- Disc images are scaled to (RADIUS*2)×(RADIUS*2) = 90×90 at runtime.
- All slots fail gracefully — missing files never crash the game.

## Generating placeholders
Run from the part2/ directory:
  python3 tools/generate_placeholder_assets.py
