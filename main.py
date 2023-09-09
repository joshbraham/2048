""" Main script for the 2048 application """
import random


Pos = tuple[int, int]  # Type alias for Board matrix positions


class Board:
    """
    NB: For methods of Board
    Parameter <i> maps to a y-axis value
    Parameter <j> maps to an x-axis value
    """

    def __init__(self, size: int):
        """
        Construct a new <size>x<size> grid with 2 randomly set cells (each value 2)
        """
        self.has_2048 = False
        self._size = size
        self._matrix = [[None] * size for _ in range(size)]

        self._empty_cells: set[Pos] = set()
        for i in range(size):
            for j in range(size):
                self._empty_cells.add((i, j))

        self.set_random_empty_cell(amount=2)

    def __repr__(self):
        """
        For repr(self)
        """
        return f"Board(size={self._size}, is_playable={self.is_playable}, has_2048={self.has_2048})"

    def __str__(self):
        """
        For str(self) or print(self)
        """
        return "\n".join(
            " ".join(f"{cell or '-':^5}" for cell in row) for row in self._matrix
        )

    @classmethod
    def from_size_input(cls, *, prompt="Enter board size: ", max_size=10):
        """
        Continuously prompt user for a board size. Return a board when valid size entered
        """
        while True:
            input_ = input(prompt)
            if not input_.isdigit():
                print("Size must be a non-negative integer.")
            elif (size := int(input_)) > max_size:
                print(f"Too large! (Maximum {max_size})")
            elif size < 2:
                print("Too small! (Minimum 2)")
            else:
                return cls(size)

    @property
    def is_playable(self):
        """
        Attribute checks if moves can be made.
        """
        if self._empty_cells:
            return True

        # Checks if any two adjacent cells have the same value
        for i in range(self._size):
            for j in range(self._size):
                value = self.get_cell(i, j)
                if value == self.get_cell(i, j + 1) or value == self.get_cell(i + 1, j):
                    return True

        return False

    def get_cell(self, i: int, j: int) -> int | None:
        """
        Retrieve value at cell (<i>, <j>).
        Returns -1 for inaccessible indices
        """
        if i > self._size - 1 or j > self._size - 1:
            return -1
        return self._matrix[i][j]

    def set_cell(self, i: int, j: int, value: int):
        """
        Update change cell (<i>, <j>) to <value>
        <value> cannot be None (instead use self.reset_cell)
        """
        # Except clause to support self.merge_cells functionality:
        # In the case that there is already a value at (i, j) it will not exist in the empty cell set
        try:
            self._empty_cells.remove((i, j))
        except KeyError:
            pass
        self._matrix[i][j] = value

    def reset_cell(self, i: int, j: int):
        """
        Set cell (<i>, <j>) to None
        """
        self._empty_cells.add((i, j))
        self._matrix[i][j] = None

    def move_cell(self, old_pos: Pos, new_pos: Pos):
        """
        Override value of <new_pos>: (new_i, new_j) and unset <old_pos>: (old_i, old_j)
        (only meant for cases in which <new_pos> is empty/has no value)
        """
        if self.get_cell(*new_pos) is not None:
            raise ValueError("Cell at new position is not empty. Use self.merge_cells")
        self.set_cell(*new_pos, self._matrix[old_pos[0]][old_pos[1]])
        self.reset_cell(*old_pos)

    def merge_cells(self, cell_pos: Pos, merge_pos: Pos):
        """
        Add value at <cell_pos> to value at <merge_pos> and unset <cell_pos>
        For 2048, should result in value at <merge_pos> being doubled
        """
        value = self.get_cell(*cell_pos) + self.get_cell(*merge_pos)
        self.set_cell(*merge_pos, value)
        self.reset_cell(*cell_pos)

    def set_random_empty_cell(self, *, amount=1):
        """
        Set <amount> random empty cells to the value of 2
        """
        for _ in range(amount):
            cell = random.choice(tuple(self._empty_cells))
            self.set_cell(*cell, 2)

    def collapse_board(self, direction: str):
        """
        Main logic of 2048.
        Determines state of board after a move left, up, right or down.
        <direction> must be a [WASD] key
        """
        # determines if (i, j) maps to (outer_pos, inner_pos) (not inverted) or (inner_pos, outer_pos)
        inverted = direction in "WS"  # dependent on a vertical direction

        # determines whether or not inner_pos iterates in reverse for backwards board traversal (down or right)
        inner_iterator = (
            range(self._size - 1, -1, -1) if direction in "SD" else range(self._size)
        )

        board_has_changed = False
        for outer_pos in range(self._size):
            empty_positions, carry_pos = [], None

            for inner_pos in inner_iterator:
                current_pos = (
                    (inner_pos, outer_pos) if inverted else (outer_pos, inner_pos)
                )
                value = self.get_cell(*current_pos)
                carry_value = self.get_cell(*carry_pos) if carry_pos is not None else -1

                if value is None:
                    # If no value, add to empty positions
                    empty_positions.insert(0, current_pos)
                elif value != carry_value and not empty_positions:
                    # (No carry value OR carry value does not match) AND no vacant cell to move to
                    carry_pos = current_pos
                elif value == carry_value:
                    # Match found
                    self.merge_cells(
                        current_pos, carry_pos
                    )  # Double value stored in carry_pos. Handles self._empty_cells set changes
                    empty_positions.insert(
                        0, current_pos
                    )  # Add current position to empty cell list
                    carry_pos = None  # Reset carry position (one merge at a time)
                    board_has_changed = True
                    self.has_2048 = value + carry_value >= 2048
                else:
                    # At this point there must be no (matching) carry value but a vacant cell to move to
                    empty_pos = empty_positions.pop()  # pop from empty_positions
                    self.move_cell(
                        current_pos, empty_pos
                    )  # swap current_pos and empty position
                    carry_pos = (
                        empty_pos  # set carry_pos to position that cell has moved to
                    )
                    empty_positions.insert(
                        0, current_pos
                    )  # add old cell position to empty_indices
                    board_has_changed = True

        # Only spawn in a new cell if a move was made
        if board_has_changed:
            self.set_random_empty_cell()

    @staticmethod
    def get_direction():
        """
        Continuously prompt input from user until valid input is entered
        """
        while True:
            direction = input("COLLAPSE (WASD) ").upper()
            if direction in ("W", "A", "S", "D"):
                return direction
            print(
                "Invalid direction! Enter 'W' for UP, 'A' for LEFT, 'S' for DOWN, 'D' for RIGHT (case insensitive)"
            )


def prompt_encore():
    """
    Post-game code that asks if the user would like another game
    """
    print()

    while True:
        input_ = input("Would you like another game? (Y/N) ").upper()
        if input_ == "Y":
            print()
            main()
        elif input_ == "N":
            print("Goodbye!")
            exit()
        else:
            print("Please enter 'Y' or 'N' (case insensitive)")


def main():
    b = Board.from_size_input()
    print()  # New line

    # Main loop
    while True:
        print(b)
        if b.has_2048:
            print("\n--------- YOU WIN! ---------")
            break
        if not b.is_playable:
            print("\nNo further moves can be made.")
            print("--------- GAME OVER ---------")
            break
        b.collapse_board(Board.get_direction())
        print()

    prompt_encore()


if __name__ == "__main__":
    main()
