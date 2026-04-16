from __future__ import annotations

from io import BytesIO

from ..domain.models import ArtifactFormat, Report

try:
    from reportlab.lib.pagesizes import LETTER
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer
except ModuleNotFoundError:  # pragma: no cover - exercised indirectly in tests
    LETTER = None
    Paragraph = None
    SimpleDocTemplate = None
    Spacer = None
    getSampleStyleSheet = None


class ReportExporter:
    """Generates lightweight deterministic exports for seeded reports."""

    def export(self, report: Report, fmt: ArtifactFormat) -> tuple[bytes, str]:
        if fmt == "pdf":
            return self._to_pdf(report), "application/pdf"
        if fmt == "markdown":
            return self._to_markdown(report).encode("utf-8"), "text/markdown; charset=utf-8"
        if fmt == "json":
            return report.model_dump_json(by_alias=True, indent=2).encode("utf-8"), "application/json"
        raise ValueError(f"Unsupported export format for report: {fmt}")

    def _to_markdown(self, report: Report) -> str:
        sections = "\n\n".join(
            f"## {section.title}\n\n{section.body}\n\nCitations: "
            + ", ".join(citation.source_uri for citation in section.citations)
            for section in report.sections
        )
        return (
            f"# {report.title}\n\n"
            f"Summary: {report.summary}\n\n"
            f"Confidence: {report.confidence}\n\n"
            f"{sections}\n"
        )

    def _to_pdf(self, report: Report) -> bytes:
        if SimpleDocTemplate is None or getSampleStyleSheet is None:
            return self._fallback_pdf(report)

        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=LETTER)
        styles = getSampleStyleSheet()
        story = [
            Paragraph(report.title, styles["Title"]),
            Spacer(1, 12),
            Paragraph(report.summary, styles["BodyText"]),
            Spacer(1, 12),
            Paragraph(f"Confidence: {report.confidence}", styles["BodyText"]),
            Spacer(1, 18),
        ]
        for section in report.sections:
            story.append(Paragraph(section.title, styles["Heading2"]))
            story.append(Spacer(1, 8))
            story.append(Paragraph(section.body, styles["BodyText"]))
            story.append(Spacer(1, 8))
            citations = ", ".join(citation.source_uri for citation in section.citations) or "None"
            story.append(Paragraph(f"Citations: {citations}", styles["Italic"]))
            story.append(Spacer(1, 16))
        doc.build(story)
        return buffer.getvalue()

    def _fallback_pdf(self, report: Report) -> bytes:
        lines = [report.title, "", report.summary, "", f"Confidence: {report.confidence}"]
        for section in report.sections:
            lines.extend(["", section.title, section.body])
        content = "\n".join(lines).replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
        stream = f"BT /F1 12 Tf 50 750 Td ({content}) Tj ET"
        objects = [
            "1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj",
            "2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj",
            "3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >> endobj",
            f"4 0 obj << /Length {len(stream)} >> stream\n{stream}\nendstream endobj",
            "5 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj",
        ]
        buffer = BytesIO()
        buffer.write(b"%PDF-1.4\n")
        offsets: list[int] = []
        for obj in objects:
            offsets.append(buffer.tell())
            buffer.write(f"{obj}\n".encode("utf-8"))
        xref_offset = buffer.tell()
        buffer.write(f"xref\n0 {len(objects) + 1}\n".encode("utf-8"))
        buffer.write(b"0000000000 65535 f \n")
        for offset in offsets:
            buffer.write(f"{offset:010d} 00000 n \n".encode("utf-8"))
        buffer.write(
            (
                f"trailer << /Root 1 0 R /Size {len(objects) + 1} >>\n"
                f"startxref\n{xref_offset}\n%%EOF"
            ).encode("utf-8")
        )
        return buffer.getvalue()
