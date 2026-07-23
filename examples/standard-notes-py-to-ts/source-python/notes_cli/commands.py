"""Command implementations backed by a plain-text file."""
import os

NOTES_FILE = os.environ.get("NOTES_FILE", os.path.expanduser("~/.notes.txt"))


def _read():
    if not os.path.exists(NOTES_FILE):
        return []
    with open(NOTES_FILE) as f:
        return [line.rstrip("\n") for line in f if line.strip()]


def _write(notes):
    with open(NOTES_FILE, "w") as f:
        for n in notes:
            f.write(n + "\n")


def add(args):
    notes = _read()
    notes.append(args.text)
    _write(notes)
    print(f"Added note {len(notes)}.")
    return 0


def list_notes(args):
    for i, n in enumerate(_read(), 1):
        print(f"{i}. {n}")
    return 0


def search(args):
    for i, n in enumerate(_read(), 1):
        if args.term.lower() in n.lower():
            print(f"{i}. {n}")
    return 0


def remove(args):
    notes = _read()
    if not 1 <= args.number <= len(notes):
        print(f"error: no note number {args.number}", file=os.sys.stderr)
        return 1
    removed = notes.pop(args.number - 1)
    _write(notes)
    print(f"Removed: {removed}")
    return 0
