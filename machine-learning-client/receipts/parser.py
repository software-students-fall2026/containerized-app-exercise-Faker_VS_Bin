"""Extract printed merchant names, dates and amounts from OCR text on US receipts."""

from datetime import datetime
import re


_MONEY = r"(-?\d{1,3}(?:,\d{3})+\.\d{2}|-?\d+\.\d{2})"
_TOTAL = re.compile(
    rf"(grand total|total due|total|amount due|balance due)\s*:?\s*\$?\s*{_MONEY}",
    re.IGNORECASE,
)
_TAX = re.compile(
    r"(?:total tax|sales tax|tax|VAT)\s*(?:\(?\d+(?:\.\d+)?\s*%\)?)?"
    rf"\s*:?\s*\$?\s*{_MONEY}",
    re.IGNORECASE,
)
_SUBTOTAL = re.compile(rf"sub\s*-?\s*total\s*:?\s*\$?\s*{_MONEY}", re.IGNORECASE)
_DATE = re.compile(r"\b(?:\d{4}-\d{2}-\d{2}|\d{1,2}/\d{1,2}/\d{4})\b")
_MERCHANT_LABEL = re.compile(r"(?:merchant|store)(?: name)?\s*:\s*(.*)", re.IGNORECASE)
_ITEM_HEADER = re.compile(
    r"^(?:items?|qty|quantity|description)"
    r"(?:$|\s+(?:qty|quantity|price|amount|description|item)\b)",
    re.IGNORECASE,
)
_PRICE = re.compile(r"\b\d+[.,]\d{2}\b")
_HEADER_NOISE = re.compile(
    r"^(?:(?:sales |payment |purchase )?receipt|(?:tax )?invoice"
    r"|(?:merchant|customer|cardholder) copy|welcome(?: to)?)\s*[!:.]*$"
    r"|^(?:sub[ -]?total|grand total|total(?: due)?|sales tax|tax|vat|amount due|balance due"
    r"|cash|change)\s*(?:$|[:$(]|[-+]?\d)"
    r"|^(?:thank you\b|(?:tel|phone|fax)\b|www\.|https?://)"
    r"|^(?:date|time|cashier|register|server|table|order)\s*[:#]"
    r"|^(?:merchant|store|order|transaction|receipt|invoice)\s*(?:#|no\b|id\b|number\b|:)"
    r"|^\d+\s+.*\b(?:street|st|ave|avenue|road|rd|blvd|lane|ln|drive|dr)\b"
    r"|\b[A-Z]{2}\s+\d{5}\b|@",
    re.IGNORECASE,
)


def _cents(amount: str) -> int:
    return int(amount.replace(",", "").replace(".", ""))


def _printed_date(text: str) -> str | None:
    for match in _DATE.finditer(text):
        value = match.group()
        fmt = "%m/%d/%Y" if "/" in value else "%Y-%m-%d"
        try:
            return datetime.strptime(value, fmt).date().isoformat()
        except ValueError:
            continue
    return None


def _unambiguous(values: set[int]) -> int | None:
    return next(iter(values)) if len(values) == 1 else None


def _printed_merchant(lines: list[str]) -> str | None:
    """Prefer a labeled merchant over the first plausible heading above the date."""
    heading = None
    above_date = True
    for line in lines[:8]:
        line = line.strip(" *|=")
        labeled = _MERCHANT_LABEL.fullmatch(line)
        name = labeled.group(1) if labeled else line
        if _DATE.search(line):
            above_date = False
            continue
        if not labeled and (_ITEM_HEADER.match(line) or _PRICE.search(line)):
            break
        if not any(char.isalpha() for char in name) or _HEADER_NOISE.search(name):
            continue
        if labeled:
            return name
        if above_date and heading is None:
            heading = name
    return heading


def parse_receipt(text: str) -> dict[str, str | int | None]:
    """Return the printed merchant, date, and amounts in integer cents for review."""
    lines = [" ".join(line.split()) for line in text.splitlines() if line.strip()]
    totals = set()
    balances = set()
    taxes = set()
    subtotals = set()
    for line in lines:
        total = _TOTAL.fullmatch(line)
        if total:
            label, amount = total.groups()
            if label.lower() in {"amount due", "balance due"}:
                balances.add(_cents(amount))
            else:
                totals.add(_cents(amount))
        tax = _TAX.fullmatch(line)
        if tax:
            taxes.add(_cents(tax.group(1)))
        subtotal = _SUBTOTAL.fullmatch(line)
        if subtotal:
            subtotals.add(_cents(subtotal.group(1)))

    return {
        "merchant": _printed_merchant(lines),
        "date": _printed_date(text),
        "subtotal_cents": _unambiguous(subtotals),
        "total_cents": _unambiguous(totals or balances),
        "tax_cents": _unambiguous(taxes),
    }
