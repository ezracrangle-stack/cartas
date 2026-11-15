"""Turn text like 'Q3 2026', 'q4-25', '2012-q1', 'YE 2025', '3Q2026',
'H1 2026' or 'Annual Letter 2024' into a period the site can sort.

Returns a dict {year, part, label, sort} or None.
part is one of Q1..Q4, H1, H2, Annual.
"""
import re

_MONTHS = ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"]
SHORT = {"Q1": "1T", "Q2": "2T", "Q3": "3T", "Q4": "4T", "H1": "1S", "H2": "2S", "Annual": "Anual"}
_ES_MONTHS = {"ene": 1, "feb": 2, "mar": 3, "abr": 4, "may": 5, "jun": 6, "jul": 7, "ago": 8,
              "sep": 9, "set": 9, "oct": 10, "nov": 11, "dic": 12}
_ORD = {"1": "1", "primer": "1", "primero": "1", "2": "2", "segundo": "2", "3": "3", "tercer": "3",
        "tercero": "3", "4": "4", "cuarto": "4"}
_MONTH_END = {"Q1": 3, "Q2": 6, "Q3": 9, "Q4": 12, "H1": 6, "H2": 12, "Annual": 12}


def _y(two_or_four):
    y = int(two_or_four)
    return y + 2000 if y < 100 else y


def make(year, part):
    year = int(year)
    if not 1980 <= year <= 2100:
        return None
    label = f"{SHORT[part]} {year}" if part != "Annual" else f"{year}"
    return {"year": year, "part": part, "label": label,
            "sort": year * 100 + _MONTH_END[part]}


_ORDW = r"(1|2|3|4|primer|primero|segundo|tercer|tercero|cuarto)(?:er|ero|o|º|ª|°)?"
# Ordered from most to least specific. Each returns (year, part).
_PATTERNS = [
    # Roman: Carta II Semestre 2024 · I trimestre 2023
    (r"\b(i{1,3}|iv)[\s_\-]+(trimestre|semestre)\D{0,12}(20\d\d|19\d\d)",
     lambda m: (m[3], ("Q" if m[2] == "trimestre" else "H") + str({"i": 1, "ii": 2, "iii": 3, "iv": 4}[m[1]]))),
    # 2Sem-2019
    (r"(?<![\w])([12])\s?sem[\s_\-]*(20\d\d)", lambda m: (m[2], f"H{m[1]}")),
    # Spanish: 1T 2024 · 1T24 · T1 2024 · 1er trimestre 2024 · tercer trimestre de 2024 · 2º semestre 2023
    (_ORDW + r"[\s_\-]*trimestre\D{0,12}(20\d\d|19\d\d)", lambda m: (m[2], f"Q{_ORD[m[1]]}")),
    (_ORDW + r"[\s_\-]*semestre\D{0,12}(20\d\d|19\d\d)", lambda m: (m[2], f"H{_ORD[m[1]]}")),
    (r"(?<![\w])([1-4])t[\s_\-'.]{0,3}(20\d\d|\d\d)(?!\d)", lambda m: (_y(m[2]), f"Q{m[1]}")),
    (r"(?<![\w])t([1-4])[\s_\-'.]{0,3}(20\d\d|\d\d)(?!\d)", lambda m: (_y(m[2]), f"Q{m[1]}")),
    (r"(?<!\d)(20\d\d)[\s_\-/.]{0,3}([1-4])t\b", lambda m: (m[1], f"Q{m[2]}")),
    (r"(?<![\w])([12])s[\s_\-'.]{0,3}(20\d\d|\d\d)(?!\d)", lambda m: (_y(m[2]), f"H{m[1]}")),
    (r"(?<![\w])s([12])[\s_\-'.]{0,3}(20\d\d|\d\d)(?!\d)", lambda m: (_y(m[2]), f"H{m[1]}")),
    # enero 2024 · dic-2023 · septiembre de 2024
    (r"\b(ene|feb|mar|abr|may|jun|jul|ago|sep|set|oct|nov|dic)[a-záéíóú]*[\s_\-.,']{1,3}(?:de[\s_\-]+)?(20\d\d|19\d\d)\b",
     lambda m: (m[2], f"Q{(_ES_MONTHS[m[1]] - 1) // 3 + 1}")),
    # Q3 2026 · Q3-2026 · Q3_2026 · Q3 Brookfield ... (no) · 2026 Q3 · 2026/Q3
    (r"\bq([1-4])[\s_\-'.]{0,3}(20\d\d|19\d\d)\b", lambda m: (m[2], f"Q{m[1]}")),
    (r"(?<!\d)(20\d\d|19\d\d)[\s_\-/.]{0,3}q([1-4])", lambda m: (m[1], f"Q{m[2]}")),
    # 2026 2Q (Maran)
    (r"(?<!\d)(20\d\d)[\s_\-/.]{0,3}([1-4])q\b", lambda m: (m[1], f"Q{m[2]}")),
    # 3Q2026 · 3Q26 · 3Q 2026
    (r"\b([1-4])q[\s_\-']{0,2}(20\d\d|\d\d)\b", lambda m: (_y(m[2]), f"Q{m[1]}")),
    # H1 2026 · 2026 H1 · 1H26
    (r"\bh([12])[\s_\-'.]{0,3}(20\d\d|19\d\d)\b", lambda m: (m[2], f"H{m[1]}")),
    (r"(?<!\d)(20\d\d|19\d\d)[\s_\-/.]{0,3}h([12])\b", lambda m: (m[1], f"H{m[2]}")),
    (r"\b([12])h[\s_\-']{0,2}(20\d\d|\d\d)\b", lambda m: (_y(m[2]), f"H{m[1]}")),
    # H1'24 · H2 24 (Saga)
    (r"\bh([12])[\s_\-'.]{0,2}(\d\d)(?!\d)", lambda m: (_y(m[2]), f"H{m[1]}")),
    # Q4-25 · Q1'26 · Q126 (1 Main style) · Q4 25
    (r"\bq([1-4])[\s_\-'.]{0,2}(\d\d)(?!\d)", lambda m: (_y(m[2]), f"Q{m[1]}")),
    # Semi-annual letter 2025 (Fundsmith)
    (r"semi[\s_\-]?annual\D{0,40}(20\d\d)", lambda m: (m[1], "H1")),
    (r"(20\d\d)\D{0,10}semi[\s_\-]?annual", lambda m: (m[1], "H1")),
    # 3/2026 (Vltava)
    (r"(?<![\d/])([1-4])/(20\d\d)\b", lambda m: (m[2], f"Q{m[1]}")),
    # 2nd-Qtr-2024 · 3rd Quarter 2024 (Massif)
    (r"\b([1-4])(?:st|nd|rd|th)[\s_\-]*q(?:tr|uarter)[\s_\-]*(20\d\d)", lambda m: (m[2], f"Q{m[1]}")),
    # August 1999 · March-2020 · Aug 2026
    (r"\b(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*[\s_\-.,']{1,3}(20\d\d|19\d\d)\b",
     lambda m: (m[2], f"Q{(_MONTHS.index(m[1]) // 3) + 1}")),
    # Year-end 2017 · YE 2025 · YE25
    (r"\b(?:year[\s_\-]?end|ye)[\s_\-']{0,2}(20\d\d|\d\d)\b", lambda m: (_y(m[1]), "Q4")),
]


def parse(text, fallback_year=None):
    """Find a period inside text. fallback_year is used when only a
    quarter is present (e.g. '.../2020/letters-to-shareholders-q4.pdf')."""
    if not text:
        return None
    # underscores count as word characters for regex, so treat them as spaces
    s = text.lower().replace("%20", " ").replace("_", " ")
    for pat, fn in _PATTERNS:
        m = re.search(pat, s)
        if m:
            year, part = fn(m)
            return make(year, part)
    m = re.search(r"\bq([1-4])\b", s)
    if m and fallback_year:
        return make(fallback_year, f"Q{m[1]}")
    m = re.search(r"(?<!\d)(20\d\d|19\d\d)(?!\d)", s)
    if m:
        return make(m[1], "Annual")
    return None


def parse_url(url):
    """Try the file name first, then the full path (folder years)."""
    path = url.split("?")[0]
    name = path.rsplit("/", 1)[-1]
    folder_year = None
    m = re.findall(r"/(20\d\d)/", path)
    if m:
        folder_year = m[-1]
    return parse(name, folder_year) or parse(path, folder_year)


def from_parts(year, part):
    """For sites that give year and quarter in separate fields."""
    if not year:
        return None
    part = (part or "").strip().upper()
    if part in {"Q1", "Q2", "Q3", "Q4", "H1", "H2"}:
        return make(year, part)
    if part in {"1", "2", "3", "4"}:
        return make(year, f"Q{part}")
    return make(year, "Annual")


def from_manual(text):
    """Periods typed by hand in managers.yaml."""
    s = str(text).strip()
    if re.fullmatch(r"\d{4}", s):
        return make(s, "Annual")
    return parse(s)
