from tapelab.chunking import chunk_filing
from tapelab.grounding import is_grounded, ungrounded_numbers
from tapelab.retrieval import bm25_rank, rrf


def test_tables_are_never_split():
    text = "Intro paragraph.\n\n| Year | Revenue |\n| 2023 | 100 |\n| 2024 | 120 |\n\nOutro."
    chunks = chunk_filing(text, "t", max_chars=20)
    tables = [c for c in chunks if c.kind == "table"]
    assert len(tables) == 1 and "2024" in tables[0].text and "2023" in tables[0].text


def test_bm25_prefers_matching_doc():
    docs = ["cats and dogs", "net revenue grew 12% year over year", "weather today"]
    assert bm25_rank("revenue growth 12%", docs)[0] == 1


def test_rrf_rewards_agreement():
    assert rrf([[0, 1, 2], [1, 0, 2]])[:2] in ([0, 1], [1, 0])
    assert rrf([[2, 0, 1], [2, 1, 0]])[0] == 2


def test_grounding_flags_fabricated_number():
    ev = ["Revenue was $1,234.5 million, up 12%."]
    assert is_grounded("Revenue rose 12% to $1,234.5 million.", ev)
    assert ungrounded_numbers("Revenue rose 15% to $1,234.5 million.", ev) == {"15"}
