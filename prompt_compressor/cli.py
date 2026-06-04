"""CLI for prompt-compressor.

Usage:
    prompt-compressor input.txt --level low
    prompt-compressor input.txt --level medium --no-protect-vars
    echo "my prompt" | prompt-compressor --level very-low
    prompt-compressor input.txt --level low --stats
"""

import argparse
import sys
from . import compress, VALID_LEVELS


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="prompt-compressor",
        description="Compress LLM prompts using rule-based algorithms. Zero dependencies.",
    )
    parser.add_argument(
        "input",
        nargs="?",
        help="Input file path. Reads from stdin if omitted.",
    )
    parser.add_argument(
        "--level", "-l",
        choices=VALID_LEVELS,
        default="low",
        help="Compression level (default: low)",
    )
    parser.add_argument(
        "--no-protect-vars",
        action="store_true",
        help="Disable variable protection ({{var}}, {var}, <tag>, ${var})",
    )
    parser.add_argument(
        "--stats", "-s",
        action="store_true",
        help="Print token stats to stderr",
    )
    parser.add_argument(
        "--output", "-o",
        help="Output file path. Prints to stdout if omitted.",
    )

    args = parser.parse_args()

    # Read input
    if args.input:
        try:
            with open(args.input, "r", encoding="utf-8") as f:
                text = f.read()
        except FileNotFoundError:
            print(f"Error: file not found: {args.input}", file=sys.stderr)
            sys.exit(1)
    else:
        if sys.stdin.isatty():
            print("Error: no input file given and stdin is a TTY.", file=sys.stderr)
            parser.print_help(sys.stderr)
            sys.exit(1)
        text = sys.stdin.read()

    if not text.strip():
        print("Error: input is empty.", file=sys.stderr)
        sys.exit(1)

    result = compress(
        text,
        level=args.level,
        protect_vars=not args.no_protect_vars,
    )

    # Write output
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(result.output)
    else:
        print(result.output)

    # Print stats to stderr
    if args.stats:
        print(
            f"\n── Stats ─────────────────────────────\n"
            f"  Level      : {args.level}\n"
            f"  Before     : {result.tokens_before:,} tokens\n"
            f"  After      : {result.tokens_after:,} tokens\n"
            f"  Saved      : {result.saved:,} tokens\n"
            f"  Reduction  : {result.reduction_pct:.1f}%\n"
            f"──────────────────────────────────────",
            file=sys.stderr,
        )


if __name__ == "__main__":
    main()
