"""Table-aware chunking: filing tables stay whole so numbers keep their row/column context."""
from dataclasses import dataclass


@dataclass(frozen=True)
class Chunk:
    text: str
    kind: str  # "text" or "table"
    source: str
    index: int


def _is_table_line(line: str) -> bool:
    return line.lstrip().startswith("|")


def chunk_filing(text: str, source: str, max_chars: int = 1200) -> list[Chunk]:
    """Split markdown-ish filing text. Table blocks are never split; prose is packed by paragraph."""
    blocks: list[tuple[str, str]] = []
    buf: list[str] = []
    in_table = False
    for line in text.splitlines():
        if _is_table_line(line) != in_table and buf:
            blocks.append(("table" if in_table else "text", "\n".join(buf).strip()))
            buf = []
        in_table = _is_table_line(line)
        buf.append(line)
    if buf:
        blocks.append(("table" if in_table else "text", "\n".join(buf).strip()))

    chunks: list[Chunk] = []
    pending = ""
    for kind, body in blocks:
        if not body:
            continue
        if kind == "table":
            if pending:
                chunks.append(Chunk(pending, "text", source, len(chunks)))
                pending = ""
            chunks.append(Chunk(body, "table", source, len(chunks)))
            continue
        for para in body.split("\n\n"):
            if pending and len(pending) + len(para) + 2 > max_chars:
                chunks.append(Chunk(pending, "text", source, len(chunks)))
                pending = ""
            pending = f"{pending}\n\n{para}".strip()
    if pending:
        chunks.append(Chunk(pending, "text", source, len(chunks)))
    return chunks
