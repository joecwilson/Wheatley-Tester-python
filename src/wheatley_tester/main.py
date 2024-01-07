import argparse
import copy
import subprocess
import time
from dataclasses import dataclass
from datetime import datetime
from enum import Enum, auto
from typing import List, Optional, TextIO, Tuple

import chess
import chess.pgn

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


@dataclass
class GameResult:
    is_drawn: bool
    outcome: GameOutcome
    new_engine_win: bool
    new_engine_loss: bool
    moves: List[str]
    opening_moves: List[str]


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
    match_results = []
    openings = [[]]
    openings.extend(parse_opening_book())
    counter = 0
    for opening in openings:
        print(f"Working on opening {counter}")
        match_results.extend(run_match(opening, args.NewEngine, args.OldEngine))
        counter += 1
    losses, wins, draws, forefits = num_losses_wins_draws_forefits(match_results)
    passed_run = True
    if forefits > 0:
        passed_run = False
    if wins > losses:
        passed_run = False
    write_games_to_disk(
        match_results,
        args.OldEngine,
        args.NewEngine,
        passed_run,
        losses,
        wins,
        draws,
        forefits,
    )
    if not passed_run:
        exit(1)


def parse_opening_book() -> List[List[str]]:
    result = []
    with open("OpeningBook.txt") as f:
        lines = f.readlines()
    for line in lines:
        result.append(line.split())
    return result


def run_match(
    opening_moves: List[str], new_engine_path: str, old_engine_path: str
) -> Tuple[GameResult, GameResult]:
    new_as_white_outcome, new_as_white_moves = run_game(
        opening_moves, new_engine_path, old_engine_path
    )
    new_as_black_outcome, new_as_black_moves = run_game(
        opening_moves, old_engine_path, new_engine_path
    )

    new_as_white_result = GameResult(
        is_drawn=new_as_white_outcome.is_drawn(),
        outcome=new_as_white_outcome,
        new_engine_win=new_as_white_outcome.is_white_win(),
        new_engine_loss=new_as_white_outcome.is_black_win(),
        moves=new_as_white_moves,
        opening_moves=opening_moves,
    )
    new_as_black_result = GameResult(
        is_drawn=new_as_black_outcome.is_drawn(),
        outcome=new_as_black_outcome,
        new_engine_win=new_as_black_outcome.is_black_win(),
        new_engine_loss=new_as_black_outcome.is_white_win(),
        moves=new_as_black_moves,
        opening_moves=opening_moves,
    )
    return (new_as_white_result, new_as_black_result)


def run_game(
    opening_moves: List[str], white_engine_path: str, black_engine_path: str
) -> Tuple[GameOutcome, List[str]]:
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
    white_engine.terminate()
    black_engine.terminate()
    outcome = board.outcome(claim_draw=True)
    assert outcome is not None
    if outcome.termination == chess.Termination.STALEMATE:
        return (GameOutcome.STALEMATE, moves)
    elif outcome.termination == chess.Termination.INSUFFICIENT_MATERIAL:
        return (GameOutcome.DRAW, moves)
    elif outcome.termination == chess.Termination.SEVENTYFIVE_MOVES:
        return (GameOutcome.DRAW, moves)
    elif outcome.termination == chess.Termination.FIVEFOLD_REPETITION:
        return (GameOutcome.DRAW, moves)
    elif outcome.termination == chess.Termination.FIFTY_MOVES:
        return (GameOutcome.DRAW, moves)
    elif outcome.termination == chess.Termination.THREEFOLD_REPETITION:
        return (GameOutcome.DRAW, moves)
    assert outcome.winner is not None
    if outcome.winner == chess.WHITE:
        return (GameOutcome.WHITE_WIN_MATE, moves)
    else:
        return (GameOutcome.BLACK_WIN_MATE, moves)


def boot_engine(engine_process: subprocess.Popen):
    blocking_readline(engine_process)
    assert engine_process.stdout is not None
    assert engine_process.stdin is not None
    engine_process.stdin.write("uci\n")
    engine_process.stdin.flush()
    blocking_readline(engine_process)
    blocking_readline(engine_process)
    blocking_readline(engine_process)
    blocking_readline(engine_process)
    engine_process.stdin.write("isready\n")
    engine_process.stdin.flush()
    blocking_readline(engine_process)


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


def blocking_readline(engine_process: subprocess.Popen, should_print: bool = False):
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
    if should_print:
        print(line)
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


def num_losses_wins_draws_forefits(
    games: List[GameResult],
) -> Tuple[int, int, int, int]:
    losses = 0
    wins = 0
    draws = 0
    forefits = 0
    for game in games:
        if game.new_engine_loss:
            losses += 1
        if game.new_engine_win:
            wins += 1
        if game.outcome.is_forefit():
            forefits += 1
        if game.is_drawn:
            draws += 1
    return (losses, wins, draws, forefits)


def write_games_to_disk(
    games: List[GameResult],
    old_engine_path: str,
    new_engine_path: str,
    passed: bool,
    losses: int,
    wins: int,
    draws: int,
    forefits: int,
):
    now = datetime.now()
    formatted_time = now.strftime("%Y-%m-%d %H:%M:%S")
    filename = f"GameResults-{formatted_time}.txt"
    with open(filename, "w") as f:
        f.write(f"Test run {formatted_time} {'passed' if passed else 'failed'}\n")
        f.write(f"Old Engine = {old_engine_path} \nNew Engine = {new_engine_path}\n")
        f.write(
            f"Wins = {wins}, losses = {losses}, draws = {draws}, forefits = {forefits}\n"
        )
        for game_run in games:
            write_game_to_disk(game_run, f)


def write_game_to_disk(game: GameResult, file: TextIO):
    file.write(f"Outcome = {game.outcome.name}\n")
    file.write(f"Opening = {game.opening_moves}\n")
    moves_as_string = " ".join(game.moves)
    file.write(f"Moves = {moves_as_string}\n")

    pgn_game = chess.pgn.Game()
    node = pgn_game.add_variation(chess.Move.from_uci(game.moves[0]))
    opening_end = len(game.opening_moves) - 2
    exporter = chess.pgn.FileExporter(file)
    for idx, move in enumerate(game.moves[1:]):
        node = node.add_variation(chess.Move.from_uci(move))
        if idx == opening_end:
            node.comment = "End Of Opening"
    pgn_game.accept(exporter)


if __name__ == "__main__":
    main()
