import argparse
import copy
import subprocess
import time
from enum import Enum, auto
from typing import List, Optional

import chess

DEFAULT_ENGINE_PATH = (
    "/home/joseph/personal_projects/wheatley_bot/target/release/wheatley_bot"
)
DEFAULT_TIME_SECONDS = 1
DEFAULT_TRIES = 200
SLEEP_START_TIME = 0.05


class GameOutcome(Enum):
    WHITE_WIN_MATE = (auto(),)
    WHITE_WIN_TIME = (auto(),)
    WHITE_WIN_FOREFIT = (auto(),)
    BLACK_WIN_MATE = (auto(),)
    BLACK_WIN_TIME = (auto(),)
    BLACK_WIN_FOREFIT = (auto(),)
    DRAW = (auto(),)
    STALEMATE = (auto(),)

    def is_white_win(self):
        return (
            self is GameOutcome.WHITE_WIN_MATE
            or self is GameOutcome.WHITE_WIN_TIME
            or self is GameOutcome.WHITE_WIN_FOREFIT
        )

    def is_black_win(self):
        return (
            self is GameOutcome.BLACK_WIN_MATE
            or self is GameOutcome.BLACK_WIN_TIME
            or self is GameOutcome.BLACK_WIN_FOREFIT
        )

    def is_drawn(self):
        return self is GameOutcome.DRAW or self is GameOutcome.STALEMATE

    def is_forefit(self):
        return (
            self is GameOutcome.BLACK_WIN_FOREFIT
            or self is GameOutcome.WHITE_WIN_FOREFIT
        )


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
    run_match([], args.NewEngine, args.OldEngine)


def run_match(opening_moves: List[str], new_engine_path: str, old_engine_path: str):
    new_as_white_outcome = run_game(opening_moves, new_engine_path, old_engine_path)
    new_as_black_outcome = run_game(opening_moves, old_engine_path, new_engine_path)
    return [new_as_white_outcome, new_as_black_outcome]


def run_game(
    opening_moves: List[str], white_engine_path: str, black_engine_path: str
) -> GameOutcome:
    white_engine = subprocess.Popen(
        white_engine_path, stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True
    )
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
        moves.append(bestmove)
        board.push_uci(bestmove)
    print(f"Game over with moves {moves}")
    white_engine.terminate()
    black_engine.terminate()
    outcome = board.outcome(claim_draw=True)
    assert outcome is not None
    if outcome.termination == chess.Termination.STALEMATE:
        return GameOutcome.STALEMATE
    elif outcome.termination == chess.Termination.INSUFFICIENT_MATERIAL:
        return GameOutcome.DRAW
    elif outcome.termination == chess.Termination.SEVENTYFIVE_MOVES:
        return GameOutcome.DRAW
    elif outcome.termination == chess.Termination.FIVEFOLD_REPETITION:
        return GameOutcome.DRAW
    elif outcome.termination == chess.Termination.FIFTY_MOVES:
        return GameOutcome.DRAW
    elif outcome.termination == chess.Termination.THREEFOLD_REPETITION:
        return GameOutcome.DRAW
    assert outcome.winner is not None
    if outcome.winner == chess.WHITE:
        return GameOutcome.WHITE_WIN_MATE
    else:
        return GameOutcome.BLACK_WIN_MATE


def boot_engine(engine_process: subprocess.Popen):
    print(f"bootline = {blocking_readline(engine_process)}")
    assert engine_process.stdout is not None
    assert engine_process.stdin is not None
    engine_process.stdin.write("uci\n")
    engine_process.stdin.flush()
    print(f"UCI response line 1 = {blocking_readline(engine_process)}")
    print(f"UCI response line 2 = {blocking_readline(engine_process)}")
    print(f"UCI response line 3 = {blocking_readline(engine_process)}")
    print(f"UCI response line uciok = {blocking_readline(engine_process)}")
    engine_process.stdin.write("isready\n")
    engine_process.stdin.flush()
    print(f"UCI response line ready_ok = {blocking_readline(engine_process)}")
    # for _ in range(5):
    #     print(engine_process.stdin.readline())


def get_bestmove(
    moves: List[str],
    engine_process: subprocess.Popen,
    w_time: Optional[float] = None,
    b_time: Optional[float] = None,
) -> str:
    assert engine_process.stdout is not None
    assert engine_process.stdin is not None
    engine_process.stdin.write(get_position(moves))
    engine_process.stdin.flush()
    if w_time is not None and b_time is not None:
        engine_process.stdin.write("go infinite\n")  # TODO: Add time tracking
        engine_process.stdin.flush()
    else:
        engine_process.stdin.write("go infinite\n")
        engine_process.stdin.flush()
    best_move_line = blocking_readline(
        engine_process
    )  # TODO: Handle more than 1 line of output
    best_move_split = best_move_line.split()
    assert best_move_split
    return best_move_split[1]


def blocking_readline(engine_process: subprocess.Popen):
    assert engine_process.stdout is not None
    line = None
    counter = 0
    while line is None and counter <= DEFAULT_TRIES:
        line = engine_process.stdout.readline()
        counter += 1
        if line is None:
            time.sleep(SLEEP_START_TIME * (counter**2))
    if line is None:
        raise AssertionError("Number of tries failed")
    return line


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
