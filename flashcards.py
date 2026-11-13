#!/usr/bin/env python3
"""Terminal flash cards.

Reads a JSON file holding a list of [a, b] string pairs.  Each pair makes
two cards, one cued by a and answered by b and its inverse, and the two are
scored separately.

    ./flashcards.py [cards.json]
"""

import argparse
import curses
import json
import random
import sys
import textwrap
from fractions import Fraction
from pathlib import Path

DEFAULT_DECK = Path(__file__).with_name("if-then-flashcards.json")

# Showing a card rests it and its inverse for a random number of turns
# in this range, inclusive.
REST_MIN, REST_MAX = 5, 10


class Card:
    def __init__(self, cue, answer):
        self.cue = cue
        self.answer = answer
        self.correct = 0
        self.incorrect = 0
        self.inverse = None
        self.eligible_at = 0    # first turn on which it may be shown again

    @property
    def ratio(self):
        return Fraction(self.incorrect + 1, self.correct + 1)


class Deck:
    def __init__(self, pairs, rng=random):
        self.rng = rng
        self.cards = []
        for a, b in pairs:
            front, back = Card(a, b), Card(b, a)
            front.inverse, back.inverse = back, front
            self.cards += [front, back]
        self.turn = 0
        self.correct = 0
        self.incorrect = 0

    @property
    def never_correct(self):
        return sum(1 for c in self.cards if c.correct == 0)

    def draw(self):
        """Pick the card for this turn and rest it and its inverse."""
        pool = [c for c in self.cards if c.eligible_at <= self.turn]
        if not pool:
            # A deck too small to outlast the rest period: take whatever
            # comes back soonest rather than showing nothing.
            soonest = min(c.eligible_at for c in self.cards)
            pool = [c for c in self.cards if c.eligible_at == soonest]
        worst = max(c.ratio for c in pool)
        card = self.rng.choice([c for c in pool if c.ratio == worst])
        rest = self.rng.randint(REST_MIN, REST_MAX)
        card.eligible_at = card.inverse.eligible_at = self.turn + rest + 1
        self.turn += 1
        return card

    def mark(self, card, correct):
        if correct:
            card.correct += 1
            self.correct += 1
        else:
            card.incorrect += 1
            self.incorrect += 1


def load_pairs(path):
    with open(path, encoding="utf-8") as f:
        pairs = json.load(f)
    if not isinstance(pairs, list) or not pairs:
        raise ValueError("expected a non-empty list of pairs")
    for n, pair in enumerate(pairs, 1):
        if (not isinstance(pair, list) or len(pair) != 2
                or not all(isinstance(s, str) for s in pair)):
            raise ValueError(f"item {n} is not a pair of strings")
    return pairs


def put(win, y, x, text, attr=0):
    """addstr that clips to the window instead of raising."""
    height, width = win.getmaxyx()
    if 0 <= y < height and 0 <= x < width:
        try:
            win.addstr(y, x, text[:width - x], attr)
        except curses.error:
            pass    # writing the bottom-right cell always raises


def put_wrapped(win, y, x, text, attr=0):
    """Write text wrapped to the window width; return the next free row.

    Line breaks and leading indentation are kept, so cards can hold code.
    """
    width = max(win.getmaxyx()[1] - x - 2, 10)
    for paragraph in text.split("\n"):
        for line in textwrap.wrap(paragraph, width) or [""]:
            put(win, y, x, line, attr)
            y += 1
    return y


def draw_screen(win, deck, card, revealed):
    win.erase()
    height, width = win.getmaxyx()
    put(win, 0, 2, f"Flash cards   card {deck.turn}", curses.A_BOLD)
    put(win, 1, 2, "-" * max(width - 4, 0), curses.A_DIM)

    y = 3
    put(win, y, 2, "CUE", curses.A_DIM)
    y = put_wrapped(win, y + 1, 4, card.cue, curses.A_BOLD) + 1
    if revealed:
        put(win, y, 2, "ANSWER", curses.A_DIM)
        put_wrapped(win, y + 1, 4, card.answer, curses.A_BOLD)

    put(win, height - 4, 2, "-" * max(width - 4, 0), curses.A_DIM)
    put(win, height - 3, 2,
        f"Correct: {deck.correct}   Incorrect: {deck.incorrect}   "
        f"Never answered correctly: {deck.never_correct} of {len(deck.cards)}")
    if revealed:
        keys = "[y] got it right   [n] got it wrong   [q] quit"
    else:
        keys = "[space] show the other side   [q] quit"
    put(win, height - 1, 2, keys, curses.A_REVERSE)
    win.refresh()


def run(win, deck):
    curses.curs_set(0)
    while True:
        card = deck.draw()
        revealed = False
        while True:
            draw_screen(win, deck, card, revealed)
            key = win.getch()
            if key in (ord("q"), ord("Q")):
                return
            if not revealed:
                if key in (ord(" "), ord("\n"), curses.KEY_ENTER):
                    revealed = True
            elif key in (ord("y"), ord("Y")):
                deck.mark(card, True)
                break
            elif key in (ord("n"), ord("N")):
                deck.mark(card, False)
                break
            # Anything else, KEY_RESIZE included, just redraws.


def main():
    parser = argparse.ArgumentParser(description="Terminal flash cards.")
    parser.add_argument("deck", nargs="?", default=DEFAULT_DECK,
                        help="JSON file of [a, b] string pairs "
                             "(default: %(default)s)")
    args = parser.parse_args()
    try:
        deck = Deck(load_pairs(args.deck))
    except (OSError, ValueError) as e:
        sys.exit(f"{args.deck}: {e}")

    try:
        curses.wrapper(run, deck)
    except KeyboardInterrupt:
        pass
    print(f"Correct: {deck.correct}   Incorrect: {deck.incorrect}   "
          f"Never answered correctly: {deck.never_correct} "
          f"of {len(deck.cards)}")


if __name__ == "__main__":
    main()
