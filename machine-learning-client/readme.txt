The receipt parser takes OCR text from a US receipt and returns a draft for review.
parse_receipt(text) returns merchant, date (YYYY-MM-DD), subtotal_cents,
tax_cents, and total_cents. Subtotal is read from a printed subtotal line.
For the merchant, the parser checks the first eight nonempty header lines,
preferring a Merchant: or Store: label over a plausible name above the date.
Missing fields and conflicting amounts are returned as None. An explicit zero is kept.

Scan one English-language receipt from a PNG or JPEG with Python 3.10+.
Install Tesseract 5 with English language data and put tesseract on PATH.
On macOS use brew install tesseract. On Ubuntu or Debian install the packages
tesseract-ocr and tesseract-ocr-eng. Run these commands from this directory:

    python -m receipts.ocr tests/fixtures/corner-deli.png

The command prints JSON with raw_text and the parsed fields. On the synthetic
CORNER DELI receipt, it reads a subtotal of 1722 cents, tax of 153 cents, and
a total of 1875 cents. Replace its path with your own receipt, quoted if needed.

Run all tests, including the sample scan:
    python -m unittest discover -s tests
