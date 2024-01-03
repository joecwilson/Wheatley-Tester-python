import chess
import chess.pgn
import chess.engine
from typing import List
import argparse
from timeit import default_timer

DEFAULT_ENGINE_PATH = "/home/joseph/personalProjects/wheatley_bot/target/release/wheatley_bot"
DEFAULT_TIME_SECONDS = 1 # 5 Seconds

def parse_input():
    pass
    # parser = argparse.ArgumentParser

def run_game(opening_moves: List[str], white_engine_path: str, black_engine_path: str):
    white_engine = chess.engine.SimpleEngine.popen_uci(white_engine_path)
    black_engine = chess.engine.SimpleEngine.popen_uci(black_engine_path)
    color = chess.WHITE
    board = chess.Board()
    white_clock = DEFAULT_TIME_SECONDS
    black_clock = DEFAULT_TIME_SECONDS
    # white_engine.quit()
    while not board.is_game_over():
        if (color == chess.WHITE):
            start_time = default_timer()
            result = white_engine.play(board, chess.engine.Limit(white_clock=white_clock, black_clock=black_clock))
            end_time = default_timer()
            elapsed_time = end_time - start_time
            white_clock -= elapsed_time
            color = chess.BLACK
        else:
            start_time = default_timer()
            result = black_engine.play(board, chess.engine.Limit(white_clock=white_clock, black_clock=black_clock)) 
            end_time = default_timer()
            elapsed_time = end_time - start_time
            black_clock -= elapsed_time
            color = chess.WHITE
        board.push(result.move)
        if (white_clock < 0):
            white_engine.quit()
            black_engine.quit()
            return chess.Outcome(chess.Termination.VARIANT_WIN, winner=chess.BLACK)
        if (black_clock < 0):
            white_engine.quit()
            black_engine.quit()
            return chess.Outcome(chess.Termination.VARIANT_WIN, winner=chess.WHITE)
        
    print(board.outcome())

    white_engine.quit()
    black_engine.quit()


def main():
    run_game(["e2e4"], DEFAULT_ENGINE_PATH, DEFAULT_ENGINE_PATH)

if __name__ == "__main__":
    main()