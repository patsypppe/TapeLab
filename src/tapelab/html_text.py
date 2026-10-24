"""Converts a filing's HTML into plain text, turning table rows into '| cell | cell |' lines."""
import re
from html.parser import HTMLParser

SKIP = {"script", "style", "ix:header"}  # ix:header holds hidden XBRL facts, not readable text
BLOCK = {"p", "div", "br", "li", "ul", "ol", "section", "article", "h1", "h2", "h3", "h4", "h5", "h6"}


def _clean(text: str) -> str:
    return re.sub(r"\s+", " ", text.replace("\xa0", " ")).strip()


def _merge_cells(cells: list[str]) -> list[str]:
    """Filings split '$ 1,234' and '(5 )' across cells; drop the blanks and rejoin the pieces."""
    out: list[str] = []
    for cell in cells:
        if cell in ("", "$"):
            continue
        if cell in (")", "%", ")%") and out:
            out[-1] += cell
        else:
            out.append(cell)
    return out


class _Extractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.blocks: list[str] = []  # paragraphs and whole tables, in reading order
        self.text: list[str] = []
        self.rows: list[str] = []
        self.row: list[str] | None = None
        self.cell: list[str] | None = None
        self.skip = 0
        self.depth = 0  # table nesting; only the outermost table is turned into rows

    def _flush_text(self) -> None:
        paragraph = _clean("".join(self.text))
        self.text = []
        if paragraph:
            self.blocks.append(paragraph)

    def handle_starttag(self, tag: str, attrs: list) -> None:
        if tag in SKIP:
            self.skip += 1
        elif tag == "table":
            if self.depth == 0:
                self._flush_text()
            self.depth += 1
        elif tag == "tr" and self.depth == 1:
            self.row = []
        elif tag in ("td", "th") and self.depth == 1 and self.row is not None:
            self.cell = []
        elif tag in BLOCK and self.depth == 0:
            self._flush_text()

    def handle_endtag(self, tag: str) -> None:
        if tag in SKIP:
            self.skip = max(0, self.skip - 1)
        elif tag in ("td", "th") and self.cell is not None and self.row is not None:
            self.row.append(_clean("".join(self.cell)))
            self.cell = None
        elif tag == "tr" and self.row is not None and self.depth == 1:
            cells = _merge_cells(self.row)
            if cells:
                self.rows.append("| " + " | ".join(cells) + " |")
            self.row = None
        elif tag == "table":
            self.depth = max(0, self.depth - 1)
            if self.depth == 0 and self.rows:
                self.blocks.append("\n".join(self.rows))
                self.rows = []
        elif tag in BLOCK and self.depth == 0:
            self._flush_text()

    def handle_data(self, data: str) -> None:
        if self.skip:
            return
        if self.cell is not None:
            self.cell.append(data)
        elif self.depth == 0:
            self.text.append(data)


def html_to_text(html: str) -> str:
    """Return readable text: paragraphs separated by blank lines, tables as contiguous '|' rows."""
    parser = _Extractor()
    parser.feed(html)
    parser.close()
    parser._flush_text()
    return "\n\n".join(parser.blocks)
