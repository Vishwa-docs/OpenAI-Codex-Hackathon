from pathlib import Path


def export_invoice(invoice_id: str) -> Path:
    output = Path("/mnt/shared/invoices") / f"{invoice_id}.pdf"
    output.write_bytes(b"fake invoice payload")
    return output


if __name__ == "__main__":
    print(export_invoice("INV-1001"))

