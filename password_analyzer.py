#!/usr/bin/env python3
"""
Password Strength Analyzer + Production-grade Custom Wordlist Generator (interactive + CLI)

Key features:
 - Full CLI options (--name, --pet, --favorite, --dob, --years, --extra, --out, --gzip, --maxwords, --generate-only, --add-reversed, --add-repeats)
 - If no CLI parts provided, asks interactive questions to collect personal info (name, dob, pet, favorites, extra, years)
 - If CLI parts provided, it offers to add more interactively
 - Uses zxcvbn for password analysis and feeds user inputs to it
 - Bounded leetspeak/capitalization/permutation rules
 - NLTK tokenization optional (if installed)
 - gzip output option
"""

import argparse
import itertools
import os
import sys
import gzip
from datetime import datetime

# zxcvbn import
try:
    from zxcvbn import zxcvbn
except Exception as e:
    print("ERROR: zxcvbn not installed. Run: pip install zxcvbn")
    raise

# optional nltk
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
    s = set()
    s.add(word)
    s.add(word.lower())
    s.add(word.upper())
    s.add(word.capitalize())
    if len(word) > 1:
        s.add(word[0].upper() + word[1:].lower())
    return sorted(s)

def leet_variants(word, max_variants=MAX_LEET_VARIANTS_PER_WORD):
    """
    Bounded leet substitution variants.
    Replace up to 2 positions (choose first alt for each replaced pos) to avoid explosion.
    """
    chars = list(word)
    indices = [i for i, ch in enumerate(chars) if ch in LEET_MAP]
    variants = set([word])
    # replace 1 or 2 positions
    for r in range(1, min(3, len(indices)+1)):
        for combo in itertools.combinations(indices, r):
            base = chars.copy()
            # choose first substitute for each selected index (simple & fast)
            for idx in combo:
                subs = LEET_MAP.get(chars[idx], [])
                if subs:
                    base[idx] = subs[0]
            variants.add("".join(base))
    # also include a version where all mapped chars are replaced by their first mapping
    base_all = chars.copy()
    changed = False
    for i, ch in enumerate(chars):
        if ch in LEET_MAP:
            base_all[i] = LEET_MAP[ch][0]
            changed = True
    if changed:
        variants.add("".join(base_all))
    out = list(variants)[:max_variants]
    return out

def expand_years(years_arg):
    if not years_arg:
        return []
    if len(years_arg) == 1:
        return [int(years_arg[0])]
    if len(years_arg) == 2:
        a, b = int(years_arg[0]), int(years_arg[1])
        if a <= b:
            return list(range(a, b+1))
        else:
            return list(range(b, a+1))
    return [int(y) for y in years_arg]

def generate_from_parts(parts, years=None, max_words=MAX_COMBINED_WORDS, add_reversed=False, add_repeats=False):
    years = years or []
    words = set()
    parts = [p for p in parts if p and p.strip()]
    if not parts:
        return []

    # single-part variants
    for part in parts:
        for form in permutations_case(part):
            words.add(form)
            for lv in leet_variants(form):
                words.add(lv)
            for suf in COMMON_SUFFIXES:
                words.add(form + suf)
            for pre in COMMON_PREFIXES:
                words.add(pre + form)
            for y in years:
                words.add(form + str(y))
        if add_reversed:
            words.add(part[::-1])
        if add_repeats:
            words.add(part + part)
            words.add(part * 3)

    # combine parts (1..MAX_COMBO_PARTS)
    for r in range(1, min(MAX_COMBO_PARTS, len(parts)) + 1):
        for combo in itertools.permutations(parts, r):
            base = "".join(combo)
            for form in permutations_case(base):
                words.add(form)
                for lv in leet_variants(form):
                    words.add(lv)
                for suf in COMMON_SUFFIXES:
                    words.add(form + suf)
                for pre in COMMON_PREFIXES:
                    words.add(pre + form)
                for y in years:
                    words.add(form + str(y))
            if add_reversed:
                words.add(base[::-1])
            if add_repeats:
                words.add(base + base)

    # optional NLTK tokenization
    if NLTK_AVAILABLE:
        joined = " ".join(parts)
        try:
            tokens = word_tokenize(joined)
            for t in tokens:
                if t.isalnum() and len(t) > 1:
                    for form in permutations_case(t):
                        words.add(form)
        except Exception:
            pass

    words_list = sorted(words)
    if len(words_list) > max_words:
        words_list = words_list[:max_words]
    return words_list

def analyze_password(password, user_inputs=None):
    user_inputs = user_inputs or []
    try:
        return zxcvbn(password, user_inputs=user_inputs)
    except Exception:
        return {"score": 0, "crack_times_display": {}, "feedback": {"warning":"zxcvbn error","suggestions":[]}}

def save_wordlist(words, outpath="wordlist.txt", gzip_out=False):
    if gzip_out:
        if not outpath.endswith(".gz"):
            outpath = outpath + ".gz"
        with gzip.open(outpath, "wt", encoding="utf-8") as f:
            for w in words:
                f.write(w + "\n")
    else:
        with open(outpath, "w", encoding="utf-8") as f:
            for w in words:
                f.write(w + "\n")
    return outpath

def interactive_collect(existing_parts=None):
    """Ask user questions interactively, returns parts list and years list."""
    existing_parts = existing_parts or []
    print("\n--- Interactive Wordlist Input 📝 (press Enter to skip a field) ---")
    if existing_parts:
        print("Existing inputs detected from CLI:", existing_parts)
        more = input("Do you want to add more data interactively? [Y/n] 🤔: ").strip().lower()
        if more == "n":
            edit = input("Press Enter to keep them, or type comma-separated additional words ✍️: ").strip()
            if edit:
                extras = [x.strip() for x in edit.split(",") if x.strip()]
                existing_parts.extend(extras)
            return existing_parts, []
    # collect fresh
    names = input("👤 Name(s) (comma-separated): ").strip()
    pets = input("🐶 Pet name(s) (comma-separated): ").strip()
    favorites = input("⭐ Favorite things (comma-separated): ").strip()
    dobs = input("📅 DOB or important dates (comma-separated, e.g., 20010101 or 2001): ").strip()
    extra = input("🆕 Any other words (comma-separated): ").strip()
    years_raw = input("📆 Years or year range (e.g., '1990 2025' or '2018,2019') (press Enter to skip): ").strip()

    parts = existing_parts.copy()
    for s in (names, pets, favorites, dobs, extra):
        if s:
            parts.extend([x.strip() for x in s.replace(",", " ").split() if x.strip()])

    years = []
    if years_raw:
        tokens = years_raw.replace(",", " ").split()
        if len(tokens) == 2:
            years = expand_years(tokens)
        else:
            try:
                years = [int(t) for t in tokens]
            except:
                years = []

    return parts, years

    # collect fresh
    names = input("Name(s) (comma-separated): ").strip()
    pets = input("Pet name(s) (comma-separated): ").strip()
    favorites = input("Favorite things (comma-separated): ").strip()
    dobs = input("DOB or important dates (comma-separated, e.g., 20010101 or 2001): ").strip()
    extra = input("Any other words (comma-separated): ").strip()
    years_raw = input("Years or year range (e.g., '1990 2025' for range or '2018,2019' for list) (press Enter to skip): ").strip()

    parts = existing_parts.copy()
    for s in (names, pets, favorites, dobs, extra):
        if s:
            parts.extend([x.strip() for x in s.replace(",", " ").split() if x.strip()])

    years = []
    if years_raw:
        # support "1990 2025" or comma separated
        tokens = years_raw.replace(",", " ").split()
        if len(tokens) == 2:
            years = expand_years(tokens)
        else:
            try:
                years = [int(t) for t in tokens]
            except:
                years = []

    return parts, years

def parse_args():
    p = argparse.ArgumentParser(description="Password Strength Analyzer & Custom Wordlist Generator (production-grade + interactive)")
    p.add_argument("--password", "-p", help="Password to analyze", required=False)
    p.add_argument("--name", help="Name(s) (space-separated)", nargs="*")
    p.add_argument("--pet", help="Pet name(s) (space-separated)", nargs="*")
    p.add_argument("--favorite", help="Favorite things (space-separated)", nargs="*")
    p.add_argument("--dob", help="DOB or dates (space-separated)", nargs="*")
    p.add_argument("--extra", help="Extra words to include", nargs="*")
    p.add_argument("--years", help="Years to append (provide two numbers for a range, or a list)", nargs="+")
    p.add_argument("--out", help="Output filename (default: wordlist.txt)", default="wordlist.txt")
    p.add_argument("--gzip", action="store_true", help="Compress output as gzip (.gz)")
    p.add_argument("--maxwords", type=int, default=MAX_COMBINED_WORDS, help=f"Max words to generate (default {MAX_COMBINED_WORDS})")
    p.add_argument("--generate-only", action="store_true", help="Only generate wordlist; skip password analysis")
    p.add_argument("--add-reversed", action="store_true", help="Include reversed variants of parts")
    p.add_argument("--add-repeats", action="store_true", help="Include repeated-word variants (e.g., name+name, name*3)")
    return p.parse_args()

def main():
    args = parse_args()

    # collect parts from CLI
    parts = []
    for group in (args.name, args.pet, args.favorite, args.dob, args.extra):
        if group:
            for it in group:
                cleaned = str(it).strip()
                if cleaned:
                    parts.append(cleaned)

    years = expand_years(args.years) if args.years else []

    # If no parts provided, collect interactive input
    if not parts:
        parts, interactive_years = interactive_collect([])
        if interactive_years:
            years = interactive_years

    # If parts exist but user might want to add more interactively
    else:
        # we ask interactively if they want to add more; interactive_collect handles this
        parts, interactive_years = interactive_collect(parts)
        if interactive_years:
            years = interactive_years

    # Password analysis if requested
    if not args.generate_only and args.password:
        user_inputs = [p for p in parts]
        analysis = analyze_password(args.password, user_inputs=user_inputs)
        print("\n" + "="*60)
        print("Password analysis for:", args.password)
        print("Score (0=weak .. 4=strong):", analysis.get("score", "N/A"))
        print("Crack times (display):")
        for k, v in analysis.get("crack_times_display", {}).items():
            print(f"  {k}: {v}")
        print("Feedback:")
        fb = analysis.get("feedback", {})
        if fb.get("warning"):
            print("  Warning:", fb.get("warning"))
        for s in fb.get("suggestions", []):
            print("  -", s)
        print("="*60)

    # Generate wordlist if parts available
    if parts:
        print("\nGenerating wordlist from parts:", parts)
        words = generate_from_parts(parts, years=years, max_words=args.maxwords,
                                    add_reversed=args.add_reversed, add_repeats=args.add_repeats)
        if not words:
            print("No words generated. Check your inputs.")
            sys.exit(1)
        outpath = save_wordlist(words, outpath=args.out, gzip_out=args.gzip)
        print(f"Saved {len(words)} words to {outpath}")
    else:
        if args.generate_only:
            print("No input parts provided. Use CLI args or run interactively.")
            sys.exit(1)
        if not args.password:
            print("No inputs given. Use --password or provide names/pets/etc.")
            sys.exit(1)

if __name__ == "__main__":
    main()
