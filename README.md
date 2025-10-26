# 🔐 Password Strength Analyzer & Custom Wordlist Generator

A **Python-based tool** to analyze password strength and generate custom wordlists for security testing.  
It combines **password strength evaluation**, **user-specific wordlist generation**, and an optional **GUI interface** built with Tkinter.

---

## 🚀 Features

### 🧠 Password Strength Analysis
- Uses the `zxcvbn` library to evaluate password strength.
- Provides:
  - Strength score (0 = weak, 4 = strong)
  - Estimated crack times under different attack scenarios
  - Feedback and suggestions for stronger passwords

### 🧩 Custom Wordlist Generator
- Generates personalized wordlists based on user data such as:
  - Name(s)
  - Pet name(s)
  - Favorite things (food, color, team, etc.)
  - Date of birth or important dates
  - Specific year ranges
- Applies common password mutation patterns:
  - Prefixes: `@`, `!`, `#`
  - Suffixes: `123`, `2024`, `!`
  - Leetspeak substitutions (e.g., `a → 4`, `e → 3`)
  - Capitalization variants
- Exportable to `.txt` for use with password cracking tools.

### 💻 Optional GUI (Tkinter)
- Built with Python’s `Tkinter` library.
- Modern, user-friendly interface.
- Real-time password feedback and wordlist generation.
- Color-coded strength meter and scrollable output view.

---

## ⚙️ Installation

1. **Clone the Repository**
   git clone <your-repo-url>  
   cd "Password Strength Analyzer"

2. **Create a Virtual Environment (Recommended)**
   python -m venv venv  
   venv\Scripts\activate   # Windows  
   source venv/bin/activate   # Mac/Linux

3. **Install Dependencies**
   pip install --upgrade pip  
   pip install zxcvbn nltk

4. **Download NLTK Data (if not installed)**
   python -c "import nltk; nltk.download('punkt')"

---

## 🧮 Usage

### 🔸 CLI Mode (Command Line Interface)

**Analyze a Password**  
python password_analyzer.py --password "YourPassword123!"

Output includes:  
- Score (0–4)  
- Estimated crack times  
- Feedback and suggestions  

**Generate a Custom Wordlist**  
python password_analyzer.py --name "John" --pet "Rex" --dob "20000101" --years 1990 2025

Automatically:  
- Generates permutations of provided input  
- Applies leetspeak conversions, prefixes, suffixes, and year appendages  
- Saves output to wordlist.txt by default

**Full Example: Analyze + Generate**  
python password_analyzer.py --password "MySecurePass!2025" --name "Alice" --pet "Fluffy" --dob "20120101" --years 2010 2025 --favorite "Pizza"

**Interactive Mode**  
python password_analyzer.py  

You’ll be prompted for:  
- Name  
- Pet name  
- Favorites  
- Date of Birth  
- Years range  

The tool will then:  
- Generate your custom wordlist  
- Optionally analyze a password if you enter one  

---

## ⚡ Options

| Option | Description |
|--------|--------------|
| `--generate-only` | Only generate a wordlist, skip password analysis. |
| `--out <filename>` | Specify a custom output file name. |
| `--maxwords <number>` | Limit number of generated words (default = 20,000). |

---

## 🖥️ GUI Mode (Tkinter)

To run the graphical interface:  
python password_analyzer_gui.py

### GUI Features
- Enter a password to analyze its strength.  
- Fill optional fields to generate customized wordlists.  
- Click buttons to analyze or generate.  
- Wordlist automatically saved in the current directory.  
- Visual password strength meter with color-coded bar.  
- Scrollable output view for generated words.  
- Tooltips for easy guidance.

---

## 🔍 How It Works

**1. Password Analysis**
- Uses the `zxcvbn` algorithm to check password entropy.  
- Detects dictionary words, common phrases, and predictable patterns.  
- Calculates scores from 0–4 with estimated crack times.

**2. Wordlist Generation**
- Takes user input data like names, pets, favorite items, DOBs, and year ranges.  
- Creates permutations using capitalization variants, leetspeak substitutions, prefixes, suffixes, and year combinations.  
- Outputs all results to a `.txt` file for:  
  - Security testing  
  - Ethical hacking/password audits  
  - Educational purposes in password entropy demonstrations  

---

## 📊 Example Output

**CLI Password Analysis**
Password analysis for: YourPassword123!  
Score (0=weak .. 4=strong): 3  

Crack times:  
  online_throttling_100_per_hour: centuries  
  online_no_throttling_10_per_second: 4 months  
  offline_slow_hashing_1e4_per_second: 3 hours  
  offline_fast_hashing_1e10_per_second: less than a second  

Feedback:  
  Warning: This is a top-10 common password.  
  - Add more words or symbols to increase complexity.

**Wordlist Sample (wordlist.txt)**  
John  
john  
JOHN  
John123  
@John  
J0hn  
John2025  
...

---

## 🤔 Why Wordlists?

Wordlists are essential tools in:  
- Penetration testing and ethical hacking  
- Security auditing and password policy evaluation  
- Demonstrations of weak password predictability  

They highlight how user-based data patterns make passwords easier to guess and crack.

---

## 🧱 Dependencies

- **Python 3.8+**  
- **zxcvbn** — Password strength evaluation  
- **nltk** — Tokenization for wordlist generation  
- **Tkinter** — Built-in GUI framework for Python (no external installation required)

---

## 🛠️ Future Enhancements
- Add cloud-based entropy testing (API integration)  
- Save/load user profiles for repeat analysis  
- Export JSON and CSV reports  
- Dark mode for GUI  

---

## 🧑‍💻 Author
Developed by **P Samuel Vijay**  
Security-focused Python utility for ethical password testing and awareness 
Made as Final Project for Elevate Labs Cybersecurity Internship
