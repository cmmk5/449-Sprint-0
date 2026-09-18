import unittest

from solitaire import SolitaireGame


class SolitaireTests(unittest.TestCase):
    def test_english_board_starts_with_empty_center(self):
        game = SolitaireGame()

        self.assertEqual(len(game.holes), 33)
        self.assertEqual(game.remaining, 32)
        self.assertNotIn((3, 3), game.pegs)

    def test_valid_jump_removes_the_jumped_peg(self):
        game = SolitaireGame()

        game.move((1, 3), (3, 3))

        self.assertEqual(game.remaining, 31)
        self.assertNotIn((1, 3), game.pegs)
        self.assertNotIn((2, 3), game.pegs)
        self.assertIn((3, 3), game.pegs)


if __name__ == "__main__":
    unittest.main()