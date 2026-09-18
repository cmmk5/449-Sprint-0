from __future__ import annotations

import random
from dataclasses import dataclass


Position = tuple[int, int]


@dataclass(frozen=True)
class Move:

    start: Position
    end: Position


class IllegalMoveError(ValueError):
    """Raised when a requested peg jump is invalid."""


class SolitaireGame:

    BOARD_TYPES = ("English", "Hexagon", "Diamond")
    SIZES = (5, 7, 9)
    _DIRECTIONS = (
        (-1, 0), (1, 0), (0, -1), (0, 1),
        (-1, -1), (-1, 1), (1, -1), (1, 1),
    )

    def __init__(
        self,
        board_type: str = "English",
        size: int = 7,
        pegs: set[Position] | None = None,
    ) -> None:
        if board_type not in self.BOARD_TYPES:
            raise ValueError(f"Unknown board type: {board_type}")
        if size not in self.SIZES:
            raise ValueError("Board size must be 5, 7, or 9")

        self.board_type = board_type
        self.size = size
        self.holes = frozenset(self._make_holes())
        center = (size // 2, size // 2)
        initial = set(self.holes - {center}) if pegs is None else set(pegs)
        if not initial.issubset(self.holes):
            raise ValueError("A peg cannot be outside the board")
        self._pegs = initial
        self._history: list[frozenset[Position]] = []

    @property
    def pegs(self) -> frozenset[Position]:
        return frozenset(self._pegs)

    @property
    def remaining(self) -> int:
        return len(self._pegs)

    def _make_holes(self) -> set[Position]:
        middle = self.size // 2
        width = max(1, self.size // 3)
        if width % 2 == 0:
            width += 1
        holes = set()
        for row in range(self.size):
            for col in range(self.size):
                x, y = row - middle, col - middle
                if self.board_type == "English":
                    included = abs(x) <= width // 2 or abs(y) <= width // 2
                elif self.board_type == "Diamond":
                    included = abs(x) + abs(y) <= middle
                else:
                    included = max(abs(x), abs(y), abs(x + y)) <= middle
                if included:
                    holes.add((row, col))
        return holes

    def _directions(self) -> tuple[Position, ...]:
        if self.board_type == "Hexagon":
            return self._DIRECTIONS[:4] + ((-1, 1), (1, -1))
        return self._DIRECTIONS

    def legal_moves(self) -> list[Move]:
        moves = []
        for row, col in sorted(self._pegs):
            for dr, dc in self._directions():
                jumped = (row + dr, col + dc)
                end = (row + 2 * dr, col + 2 * dc)
                if jumped in self._pegs and end in self.holes - self._pegs:
                    moves.append(Move((row, col), end))
        return moves

    def move(self, start: Position, end: Position) -> None:
        if Move(start, end) not in self.legal_moves():
            raise IllegalMoveError(f"Illegal jump: {start} to {end}")
        self._history.append(self.pegs)
        midpoint = ((start[0] + end[0]) // 2, (start[1] + end[1]) // 2)
        self._pegs.remove(start)
        self._pegs.remove(midpoint)
        self._pegs.add(end)

    def undo(self) -> bool:
        if not self._history:
            return False
        self._pegs = set(self._history.pop())
        return True

    def random_move(self, rng: random.Random | None = None) -> Move | None:
        moves = self.legal_moves()
        if not moves:
            return None
        chosen = (rng or random).choice(moves)
        self.move(chosen.start, chosen.end)
        return chosen

    def rating(self) -> str | None:
        if self.legal_moves():
            return None
        if self.remaining == 1:
            return "Outstanding"
        if self.remaining == 2:
            return "Very Good"
        if self.remaining == 3:
            return "Good"
        return "Average"