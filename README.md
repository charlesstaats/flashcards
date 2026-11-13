# Flash cards

A flash card trainer that runs in the terminal. It needs only Python 3 and its
standard library, including `curses`.

## Running it

    ./flashcards.py [cards.json]

With no argument it uses `if-then-flashcards.json`. That deck covers how
if / else-if / else and conditional expressions are written in about thirty
programming languages.

## Keys

| Key               | Action                                   |
| ----------------- | ---------------------------------------- |
| Space or Enter    | Show the other side of the card          |
| `y`               | You got it right                         |
| `n`               | You got it wrong                         |
| `q` or Ctrl-C     | Quit and print the score                 |

You grade yourself: the program shows the answer and asks whether you knew
it.

## How cards are chosen

Every pair in the deck becomes two cards, one in each direction, and each card
keeps its own score. A card marked one-way (see below) makes only the first.
On each turn the program shows the card you have missed most often relative
to how often you have answered it correctly. Ties are broken at random. So
cards you have missed come up before cards you haven't seen yet, and those
come up before cards you have been getting right.

After a card is shown, neither it nor its reverse can come up again for the
next 5 to 10 turns (the exact number is random). That way you can't answer a
card just because you saw its other side a moment ago.

## Writing a deck

A deck is a JSON file holding a list of pairs of strings:

```json
[
  ["Python: conditional expression", "y = a if x > 0 else b"],
  ["Ruby: if / elsif / else", "if x > 0\n  a\nelsif x < 0\n  b\nelse\n  c\nend"]
]
```

Either side can be shown as the cue, so each side should be enough on its own
to bring the other to mind. Line breaks (`\n`) and leading indentation are
kept, so a card can hold a block of code. Long lines wrap to fit the terminal.

### One-way cards

Some cards only make sense in one direction. Write such a card as an object
instead of a pair, with `"one_way": true`:

```json
[
  ["Python: conditional expression", "y = a if x > 0 else b"],
  {"front": "Which languages use `elsif`?", "back": "Ruby, Perl", "one_way": true}
]
```

A one-way card is always cued by `front` and answered by `back`. An object
without `"one_way"`, or with it set to `false`, is the same as the pair
`[front, back]`. Pairs and objects can be mixed freely in one deck.
