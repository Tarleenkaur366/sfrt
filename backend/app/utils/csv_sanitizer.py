from typing import Any

DANGEROUS_PREFIXES = ("=", "+", "-", "@", "\t", "\r", "%")

def sanitize_csv_cell(value: Any) -> Any:
    """
    Protects against CSV / Spreadsheet formula injection attacks (CSV Injection / CWE-1236).
    If a string starts with a formula trigger character (=, +, -, @, tab, CR),
    it is prepended with a single quote (').
    """
    if value is None:
        return ""
    str_val = str(value)
    if str_val and str_val.startswith(DANGEROUS_PREFIXES):
        return f"'{str_val}"
    return str_val
