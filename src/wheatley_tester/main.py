import argparse
import copy
import subprocess
from typing import List, Optional

import chess

DEFAULT_ENGINE_PATH = (
    "/home/joseph/personalProjects/wheatley_bot/target/release/wheatley_bot"
)
DEFAULT_TIME_SECONDS = 1


def get_parser():
    parser = argparse.ArgumentParser(
        prog="Wheatley Bot Tester",
        description="Tests UCI compatable chess engines that pefer to lose",
    )
    parser.add_argument("NewEngine", default=DEFAULT_ENGINE_PATH)
    parser.add_argument("OldEngine", default=DEFAULT_ENGINE_PATH)
    parser.add_argument("--time-limit", type=int, default=DEFAULT_TIME_SECONDS)
    return parser


def main():
    parser = get_parser()
    args = parser.parse_args()
    print(args.NewEngine)
    print(args.OldEngine)
    run_game([], args.NewEngine, args.OldEngine)


def run_game(opening_moves: List[str], white_engine_path: str, black_engine_path: str):
    white_engine = subprocess.Popen(
        white_engine_path, stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True
    )
    # print(type(white_engine))
    black_engine = subprocess.Popen(
        black_engine_path, stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True
    )
    boot_engine(white_engine)
    boot_engine(black_engine)

    board = chess.Board()
    for move in opening_moves:
        board.push_uci(move)

    moves = copy.deepcopy(opening_moves)
    while not board.is_game_over(claim_draw=True):
        if board.turn == chess.WHITE:
            bestmove = get_bestmove(moves, white_engine)
        else:
            bestmove = get_bestmove(moves, black_engine)
        print(bestmove)
        moves.append(bestmove)
        board.push_uci(bestmove)
    print(f"Game over with moves {moves}")
    white_engine.terminate()
    black_engine.terminate()


def boot_engine(engine_process: subprocess.Popen):
    engine_process.stdin.write("uci\n")
    engine_process.stdin.flush()
    print(engine_process.stdout.readline())
    print(engine_process.stdout.readline())
    print(engine_process.stdout.readline())
    print(engine_process.stdout.readline())
    engine_process.stdin.write("isready\n")
    engine_process.stdin.flush()
    print(engine_process.stdin.readline())
    # for _ in range(5):
    #     print(engine_process.stdin.readline())


def get_bestmove(
    moves: List[str],
    engine_process: subprocess.Popen,
    w_time: Optional[float] = None,
    b_time: Optional[float] = None,
) -> str:
    engine_process.stdin.write(get_position(moves))
    engine_process.stdin.flush()
    print("Got here")
    if w_time is not None and b_time is not None:
        engine_process.stdin.write("go infinite\n")  # TODO: Add time tracking
        engine_process.stdin.flush()
    else:
        engine_process.stdin.write("go infinite\n")
        engine_process.stdin.flush()
        print("Got here 2")
    print("Got here 3")
    best_move_line = (
        engine_process.stdout.readline()
    )  # TODO: Handle more than 1 line of output
    best_move_split = best_move_line.split()
    assert best_move_split
    return best_move_split[1]


def get_position(moves: List[str]) -> str:
    if not moves:
        return "position startpos \n"
    position_arr = []
    position_arr.append("position startpos moves")

    for move in moves:
        position_arr.append(move)
    position_arr.append("\n")
    return " ".join(position_arr)


if __name__ == "__main__":
    main()
