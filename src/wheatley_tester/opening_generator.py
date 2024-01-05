import random
from typing import List, Optional

import chess


def main():
    openings = []
    for _ in range(100):
        opening = None
        while opening is None:
            opening = generate_opening(random.randint(4, 8))
        openings.append(opening)
    save_openings(openings)


def save_openings(openings: List[List[str]]):
    with open("OpeningBook.txt", "w") as f:
        for opening in openings:
            for move in opening:
                f.write(f"{move} ")
            f.write("\n")


def generate_opening(depth: int) -> Optional[List[str]]:
    board = chess.Board()
    moves = []
    while depth > 0:
        # print(type(board.legal_moves))
        legal_moves = []
        for move in board.legal_moves:
            legal_moves.append(move)

        selected_move = random.choice(legal_moves)
        moves.append(selected_move.uci())
        board.push(selected_move)
        depth -= 1
        if board.is_game_over(claim_draw=True):
            return None
    return moves


if __name__ == "__main__":
    main()
