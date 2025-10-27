#!/usr/bin/env python3
"""
Password Strength Analyzer + Production-grade Custom Wordlist Generator (Interactive + CLI)

Key Features:
 - CLI & Interactive hybrid operation
 - zxcvbn-based password strength analysis with user input context
 - Smart custom wordlist generation using:
     → Leetspeak, capitalization, prefix/suffix combos, year appends
     → Optional reversed and repeated patterns
 - Optional gzip compression for large wordlists
 - Bounded and performance-optimized generation (~20k words max)
 - Clean CLI help and modern interactive UX
"""

import argparse
import itertools
import sys
import gzip
from datetime import datetime

# ------------------ Imports & Optional Dependencies ------------------
try:
    from zxcvbn import zxcvbn
except Exception:
    print("ERROR: zxcvbn not installed. Run: pip install zxcvbn")
    sys.exit(1)

try:
    import nltk
    from nltk.tokenize import word_tokenize
    NLTK_AVAILABLE = True
except Exception:
    NLTK_AVAILABLE = False

# ------------------ Configuration ------------------
COMMON_SUFFIXES = ["", "1", "12", "123", "1234", "12345", "!", "@", "#", "$", "2022", "2023", "2024", "2025"]
COMMON_PREFIXES = ["", "!", "@", "#"]
LEET_MAP = {
    "a": ["4", "@"], "A": ["4", "@"],
    "e": ["3"], "E": ["3"],
    "i": ["1", "!"], "I": ["1", "!"],
    "o": ["0"], "O": ["0"],
    "s": ["5", "$"], "S": ["5", "$"],
    "t": ["7"], "T": ["7"],
    "l": ["1"], "L": ["1"]
}
MAX_LEET_VARIANTS_PER_WORD = 40
MAX_COMBINED_WORDS = 20000
MAX_COMBO_PARTS = 3
# ---------------------------------------------------


def permutations_case(word):
    """Generate case variations for a given word."""
    s = {word, word.lower(), word.upper(), word.capitalize()}
    if len(word) > 1:
        s.add(word[0].upper() + word[1:].lower())
    return sorted(s)


def leet_variants(word, max_variants=MAX_LEET_VARIANTS_PER_WORD):
    """Generate limited leetspeak variants for a word."""
    chars = list(word)
    indices = [i for i, ch in enumerate(chars) if ch in LEET_MAP]
    variants = {word}

    # replace 1 or 2 positions
    for r in range(1, min(3, len(indices) + 1)):
        for combo in itertools.combinations(indices, r):
            w = chars.copy()
            for idx in combo:
                subs = LEET_MAP.get(chars[idx], [])
                if subs:
                    w[idx] = subs[0]
            variants.add("".join(w))

    # replace all mapped chars
    w_all = chars.copy()
    for i, ch in enumerate(chars):
        if ch in LEET_MAP:
            w_all[i] = LEET_MAP[ch][0]
    variants.add("".join(w_all))

    return list(variants)[:max_variants]


def expand_years(years_arg):
    """Expand year inputs into lists."""
    if not years_arg:
        return []
    try:
        years = [int(y) for y in years_arg]
        if len(years) == 2 and abs(years[1] - years[0]) > 1:
            start, end = sorted(years)
            return list(range(start, end + 1))
        return years
    except Exception:
        return []


def generate_from_parts(parts, years=None, max_words=MAX_COMBINED_WORDS,
                        add_reversed=False, add_repeats=False):
    """Generate password wordlist combinations from given parts."""
    years = years or []
    words = set()
    parts = [p for p in parts if p.strip()]

    # single-part and multi-part combos
    for r in range(1, min(MAX_COMBO_PARTS, len(parts)) + 1):
        for combo in itertools.permutations(parts, r):
            base = "".join(combo)
            for variant in permutations_case(base):
                words.add(variant)
                for leet in leet_variants(variant):
                    words.add(leet)
                for suf in COMMON_SUFFIXES:
                    words.add(variant + suf)
                for pre in COMMON_PREFIXES:
                    words.add(pre + variant)
                for y in years:
                    words.add(variant + str(y))
            if add_reversed:
                words.add(base[::-1])
            if add_repeats:
                words.add(base * 2)

    # optional tokenization
    if NLTK_AVAILABLE:
        try:
            tokens = word_tokenize(" ".join(parts))
            for t in tokens:
                if t.isalnum() and len(t) > 1:
                    words.update(permutations_case(t))
        except Exception:
            pass

    # cap total
    return sorted(words)[:max_words]


def analyze_password(password, user_inputs=None):
    """Analyze password using zxcvbn."""
    try:
        return zxcvbn(password, user_inputs=user_inputs or [])
    except Exception:
        return {"score": 0, "crack_times_display": {}, "feedback": {"warning": "zxcvbn error", "suggestions": []}}


def save_wordlist(words, outpath="wordlist.txt", gzip_out=False):
    """Save wordlist to .txt or .gz file."""
    if gzip_out:
        if not outpath.endswith(".gz"):
            outpath += ".gz"
        with gzip.open(outpath, "wt", encoding="utf-8") as f:
            f.writelines(w + "\n" for w in words)
    else:
        with open(outpath, "w", encoding="utf-8") as f:
            f.writelines(w + "\n" for w in words)
    return outpath


def interactive_collect(existing_parts=None):
    """Interactively collect inputs for wordlist generation."""
    existing_parts = existing_parts or []
    print("\n--- Interactive Wordlist Input 📝 (press Enter to skip) ---")

    if existing_parts:
        print("Existing inputs detected from CLI:", existing_parts)
        if input("Add more data interactively? [Y/n]: ").strip().lower() == "n":
            extra = input("Add additional comma-separated words: ").strip()
            if extra:
                existing_parts.extend([x.strip() for x in extra.split(",") if x.strip()])
            return existing_parts, []

    # fresh inputs
    names = input("👤 Name(s): ").strip()
    pets = input("🐶 Pet name(s): ").strip()
    favorites = input("⭐ Favorite things: ").strip()
    dobs = input("📅 DOB / Dates (YYYYMMDD or YYYY): ").strip()
    extra = input("🆕 Any extra words: ").strip()
    years_raw = input("📆 Years (e.g., '1990 2025' or '2018,2019'): ").strip()

    parts = existing_parts.copy()
    for field in (names, pets, favorites, dobs, extra):
        if field:
            parts.extend([x.strip() for x in field.replace(",", " ").split() if x.strip()])

    years = expand_years(years_raw.replace(",", " ").split()) if years_raw else []
    return parts, years


def parse_args():
    """CLI argument parser."""
    p = argparse.ArgumentParser(description="Password Strength Analyzer & Custom Wordlist Generator")
    p.add_argument("--password", "-p", help="Password to analyze")
    p.add_argument("--name", nargs="*", help="Name(s)")
    p.add_argument("--pet", nargs="*", help="Pet name(s)")
    p.add_argument("--favorite", nargs="*", help="Favorite things")
    p.add_argument("--dob", nargs="*", help="DOB or dates")
    p.add_argument("--extra", nargs="*", help="Extra words")
    p.add_argument("--years", nargs="+", help="Years to append (range or list)")
    p.add_argument("--out", default="wordlist.txt", help="Output filename")
    p.add_argument("--gzip", action="store_true", help="Compress output as .gz")
    p.add_argument("--maxwords", type=int, default=MAX_COMBINED_WORDS, help="Max words to generate")
    p.add_argument("--generate-only", action="store_true", help="Skip password analysis")
    p.add_argument("--add-reversed", action="store_true", help="Add reversed variants")
    p.add_argument("--add-repeats", action="store_true", help="Add repeated variants (e.g., name+name)")
    return p.parse_args()


def main():
    args = parse_args()

    # gather parts
    parts = [x.strip() for group in (args.name, args.pet, args.favorite, args.dob, args.extra) if group for x in group]
    years = expand_years(args.years) if args.years else []

    if not parts:
        parts, interactive_years = interactive_collect()
        if interactive_years:
            years = interactive_years
    else:
        parts, extra_years = interactive_collect(parts)
        if extra_years:
            years = extra_years

    if not args.generate_only and args.password:
        print("\n" + "=" * 60)
        print(f"🔐 Password Analysis for: {args.password}")
        result = analyze_password(args.password, user_inputs=parts)
        print(f"Score (0=weak .. 4=strong): {result['score']}")
        print("Estimated Crack Times:")
        for k, v in result.get("crack_times_display", {}).items():
            print(f"  {k}: {v}")
        fb = result.get("feedback", {})
        if fb.get("warning"):
            print(f"⚠️  Warning: {fb['warning']}")
        for s in fb.get("suggestions", []):
            print("  -", s)
        print("=" * 60)

    # generate wordlist
    if parts:
        print("\n🧠 Generating custom wordlist...")
        words = generate_from_parts(parts, years=years, max_words=args.maxwords,
                                    add_reversed=args.add_reversed, add_repeats=args.add_repeats)
        path = save_wordlist(words, args.out, args.gzip)
        print(f"✅ Saved {len(words)} words to: {path}")
        print("\n🎉 Operation complete! You can open the file or use it in password cracking tools.")
    else:
        print("No parts provided. Please rerun with CLI args or interactively.")


if __name__ == "__main__":
    main()
