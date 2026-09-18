from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from solitaire import IllegalMoveError, Position, SolitaireGame


class SolitaireWindow(tk.Tk):
    BACKGROUND = "#102821"
    BOARD = "#1b4939"
    EMPTY = "#0a241c"
    PEG = "#edce84"
    SELECTED = "#f67d59"
    HINT = "#7bd4b0"

    def __init__(self) -> None:
        super().__init__()
        self.title("Peg Solitaire | CS 449")
        self.resizable(False, False)
        self.configure(bg=self.BACKGROUND)
        self.board_type = tk.StringVar(value="English")
        self.board_size = tk.IntVar(value=7)
        self.show_hints = tk.BooleanVar(value=True)
        self.status = tk.StringVar()
        self.game = SolitaireGame()
        self.selected: Position | None = None
        self.autoplaying = False
        self._autoplay_job: str | None = None
        self._build_widgets()
        self.redraw()

    def _build_widgets(self) -> None:
        main = tk.Frame(self, bg=self.BACKGROUND, padx=24, pady=20)
        main.pack()
        tk.Label(
            main, text="PEG SOLITAIRE", bg=self.BACKGROUND, fg=self.PEG,
            font=("Segoe UI", 22, "bold"),
        ).grid(row=0, column=0, columnspan=2, sticky="w")
        tk.Label(
            main, text="Jump a peg over another peg into an empty hole.",
            bg=self.BACKGROUND, fg="#d9eee2", font=("Segoe UI", 10),
        ).grid(row=1, column=0, columnspan=2, sticky="w", pady=(0, 14))

        self.canvas = tk.Canvas(
            main, width=534, height=534, bg=self.BOARD,
            highlightthickness=0, cursor="hand2",
        )
        self.canvas.grid(row=2, column=0, padx=(0, 20))
        self.canvas.bind("<Button-1>", self.on_board_click)

        panel = tk.Frame(main, bg=self.BACKGROUND, width=210)
        panel.grid(row=2, column=1, sticky="n")
        panel.grid_propagate(False)
        self._panel_heading(panel, "BOARD TYPE")
        for name in SolitaireGame.BOARD_TYPES:
            tk.Radiobutton(
                panel, text=name, variable=self.board_type, value=name,
                command=self.new_game, bg=self.BACKGROUND, fg="white",
                selectcolor=self.BOARD, activebackground=self.BACKGROUND,
                activeforeground="white", font=("Segoe UI", 11),
            ).pack(anchor="w", pady=2)

        self._panel_heading(panel, "BOARD SIZE", top=20)
        ttk.Combobox(
            panel, textvariable=self.board_size, values=SolitaireGame.SIZES,
            state="readonly", width=8,
        ).pack(anchor="w")
        self._panel_heading(panel, "OPTIONS", top=20)
        tk.Checkbutton(
            panel, text="Show legal destinations", variable=self.show_hints,
            command=self.redraw, bg=self.BACKGROUND, fg="white",
            selectcolor=self.BOARD, activebackground=self.BACKGROUND,
            activeforeground="white", font=("Segoe UI", 10),
        ).pack(anchor="w")

        self._panel_heading(panel, "GAME", top=20)
        for label, command in (
            ("New Game", self.new_game),
            ("Undo", self.undo),
            ("Random Move", self.random_move),
            ("Autoplay / Stop", self.toggle_autoplay),
        ):
            tk.Button(
                panel, text=label, command=command, width=17,
                bg="#e8c87c", fg=self.BACKGROUND, activebackground="#fff0c2",
                relief="flat", font=("Segoe UI", 10, "bold"), pady=5,
            ).pack(anchor="w", pady=4)

        ttk.Separator(main, orient="horizontal").grid(
            row=3, column=0, columnspan=2, sticky="ew", pady=(16, 10)
        )
        tk.Label(
            main, textvariable=self.status, bg=self.BACKGROUND,
            fg="#d9eee2", font=("Segoe UI", 11),
        ).grid(row=4, column=0, columnspan=2, sticky="w")

    def _panel_heading(self, parent: tk.Widget, title: str, top: int = 0) -> None:
        tk.Label(
            parent, text=title, bg=self.BACKGROUND, fg=self.HINT,
            font=("Segoe UI", 10, "bold"),
        ).pack(anchor="w", pady=(top, 6))

    def _geometry(self) -> tuple[float, float]:
        spacing = 51 if self.game.size == 9 else 61
        start = (534 - (self.game.size - 1) * spacing) / 2
        return start, spacing

    def redraw(self) -> None:
        self.canvas.delete("all")
        start, spacing = self._geometry()
        moves = self.game.legal_moves()
        possible = {
            move.end for move in moves if move.start == self.selected
        }

        for row, col in sorted(self.game.holes):
            x, y = start + col * spacing, start + row * spacing
            for dr, dc in ((0, 1), (1, 0)):
                if (row + dr, col + dc) in self.game.holes:
                    self.canvas.create_line(
                        x, y, x + dc * spacing, y + dr * spacing,
                        fill="#39705a", width=2,
                    )

        for row, col in sorted(self.game.holes):
            x, y = start + col * spacing, start + row * spacing
            position = (row, col)
            radius = 18 if self.game.size == 9 else 21
            color = self.EMPTY
            if position in self.game.pegs:
                color = self.SELECTED if position == self.selected else self.PEG
            elif self.show_hints.get() and position in possible:
                color = self.HINT
            self.canvas.create_oval(
                x - radius, y - radius, x + radius, y + radius,
                fill=color, outline="#609479", width=2,
            )
            if position in self.game.pegs:
                self.canvas.create_oval(
                    x - radius + 6, y - radius + 5,
                    x - radius + 13, y - radius + 12,
                    fill="#fff3cd", outline="",
                )

        rating = self.game.rating()
        if rating:
            message = f"Game over  |  {self.game.remaining} pegs  |  {rating}"
        elif self.selected is not None:
            message = f"{self.game.remaining} pegs left  |  Select a highlighted hole."
        else:
            message = f"{self.game.remaining} pegs left  |  Select a peg to move."
        self.status.set(message)

    def on_board_click(self, event: tk.Event) -> None:
        start, spacing = self._geometry()
        col = round((event.x - start) / spacing)
        row = round((event.y - start) / spacing)
        position = (row, col)
        if position not in self.game.holes:
            return
        x, y = start + col * spacing, start + row * spacing
        if (event.x - x) ** 2 + (event.y - y) ** 2 > 23 ** 2:
            return
        if position in self.game.pegs:
            self.selected = None if position == self.selected else position
        elif self.selected is not None:
            try:
                self.game.move(self.selected, position)
            except IllegalMoveError:
                pass
            else:
                self.selected = None
        self.redraw()

    def new_game(self) -> None:
        self._stop_autoplay()
        self.game = SolitaireGame(self.board_type.get(), self.board_size.get())
        self.selected = None
        self.redraw()

    def undo(self) -> None:
        self._stop_autoplay()
        self.game.undo()
        self.selected = None
        self.redraw()

    def random_move(self) -> None:
        self._stop_autoplay()
        self.game.random_move()
        self.selected = None
        self.redraw()

    def toggle_autoplay(self) -> None:
        if self.autoplaying:
            self._stop_autoplay()
            return
        self.autoplaying = True
        self._autoplay_step()

    def _stop_autoplay(self) -> None:
        self.autoplaying = False
        if self._autoplay_job is not None:
            self.after_cancel(self._autoplay_job)
            self._autoplay_job = None

    def _autoplay_step(self) -> None:
        self._autoplay_job = None
        if not self.autoplaying:
            return
        if self.game.random_move() is None:
            self.autoplaying = False
        self.selected = None
        self.redraw()
        if self.autoplaying:
            self._autoplay_job = self.after(380, self._autoplay_step)


if __name__ == "__main__":
    SolitaireWindow().mainloop()