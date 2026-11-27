"""Examples of US receipt text after OCR."""

import unittest

from receipts.parser import parse_receipt


class ReceiptParserTests(unittest.TestCase):
    """Check the fields we show a user for review."""

    def test_cash_and_change_are_not_the_sale_total(self):
        """A cash sale can print both a larger tender and a zero balance."""
        text = (
            "Corner Deli\n11/25/2026 12:30\nSubtotal $17.22\n"
            "Sales Tax (8.875%) $1.53\nTOTAL $18.75\nCASH $20.00\n"
            "CHANGE $1.25\nBalance Due $0.00"
        )
        self.assertEqual(
            parse_receipt(text),
            {
                "merchant": "Corner Deli",
                "date": "2026-11-25",
                "subtotal_cents": 1722,
                "total_cents": 1875,
                "tax_cents": 153,
            },
        )

    def test_missing_tax_is_different_from_zero_tax(self):
        """The review screen needs to distinguish unknown tax from an exemption."""
        self.assertIsNone(parse_receipt("Total $23.00")["tax_cents"])
        self.assertEqual(parse_receipt("TAX 0.00")["tax_cents"], 0)

    def test_rate_is_not_a_tax_amount(self):
        """A printed percentage can precede the dollar figure on the same line."""
        self.assertIsNone(parse_receipt("Tax 8.875%")["tax_cents"])
        self.assertEqual(parse_receipt("VAT (15%): $15.00")["tax_cents"], 1500)

    def test_fallback_total_and_thousands_separator(self):
        """An amount-due label alone can identify a purchase price."""
        fields = parse_receipt("2026-11-25\nAmount due: $1,250.40")
        self.assertEqual(fields["total_cents"], 125040)
        self.assertEqual(fields["date"], "2026-11-25")

    def test_repeated_and_conflicting_totals(self):
        """Identical totals agree, while differing printed totals need review."""
        self.assertEqual(parse_receipt("TOTAL 8.10\nTOTAL 8.10")["total_cents"], 810)
        self.assertIsNone(parse_receipt("TOTAL 8.10\nTOTAL 9.10")["total_cents"])

    def test_unlabeled_prices_do_not_fill_in_a_total(self):
        """Partial OCR text can contain prices and an impossible calendar date."""
        fields = parse_receipt("11/31/2026\nCoffee $4.00\nSUBTOTAL $4.00")
        self.assertIsNone(fields["merchant"])
        self.assertIsNone(fields["date"])
        self.assertIsNone(fields["total_cents"])
        self.assertIsNone(fields["tax_cents"])
        self.assertEqual(fields["subtotal_cents"], 400)

    def test_merchant_from_labeled_header(self):
        """Prefer the labeled name over another plausible heading."""
        for label in ("Merchant", "MERCHANT NAME", "Store", "Store Name"):
            with self.subTest(label=label):
                text = f"Downtown location\n{label}:  7-Eleven\nTotal $12.50"
                self.assertEqual(parse_receipt(text)["merchant"], "7-Eleven")
        self.assertEqual(
            parse_receipt("Store: 5.11 Tactical")["merchant"], "5.11 Tactical"
        )

    def test_merchant_from_printed_heading(self):
        """Preserve the spelling on the storefront, including digits and accents."""
        text = "SALES RECEIPT\n*** Café 42 & Co. ***\n123 Main St\nTOTAL 10.00"
        self.assertEqual(parse_receipt(text)["merchant"], "Café 42 & Co.")

    def test_merchant_after_metadata(self):
        """Skip receipt identifiers and addresses while preserving store names."""
        text = "Receipt #145\n123 Main St Suite 2\n9th Street Market\nTOTAL $12.50"
        self.assertEqual(parse_receipt(text)["merchant"], "9th Street Market")
        self.assertEqual(
            parse_receipt("Date: 11/25/2026\nMerchant: Main Street")["merchant"],
            "Main Street",
        )

    def test_partial_receipt_without_merchant(self):
        """Contact details, item descriptions and footers are not merchant names."""
        text = (
            "CUSTOMER COPY\n123 Main Street\nNew York, NY 10001\n"
            "Tel: 212-555-0100\nItem   Qty   Price\nBagel\n$3.25\nThank you!"
        )
        self.assertIsNone(parse_receipt(text)["merchant"])
        self.assertIsNone(parse_receipt("Coffee $3.25\nCorner Deli")["merchant"])
        self.assertIsNone(parse_receipt("SUBTOTAL\n$3.25")["merchant"])
        self.assertIsNone(parse_receipt("Sales tax 8.875%")["merchant"])
        self.assertIsNone(parse_receipt("11/25/2026\nBagel\nTOTAL $3.25")["merchant"])

    def test_subtotal_labels_and_amounts(self):
        """Read explicit subtotal lines, including zero and refund amounts."""
        for line, cents in [
            ("Sub Total: $1,234.50", 123450),
            ("sUb-ToTaL    0.00", 0),
            ("SUB - TOTAL: $0.05", 5),
            ("SUBTOTAL -2.15", -215),
        ]:
            with self.subTest(line=line):
                self.assertEqual(parse_receipt(line)["subtotal_cents"], cents)

    def test_subtotal_must_be_printed_and_unambiguous(self):
        """Keep conflicting or missing subtotals blank instead of computing one."""
        for text, expected in [
            ("Tax 1.53\nTOTAL 18.75", None),
            ("SUBTOTAL 17.22\nSub Total $17.22", 1722),
            ("SUBTOTAL 17.22\nSub Total $19.22", None),
        ]:
            with self.subTest(text=text):
                self.assertEqual(parse_receipt(text)["subtotal_cents"], expected)
