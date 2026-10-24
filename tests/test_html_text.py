from tapelab.chunking import chunk_filing
from tapelab.html_text import html_to_text

# Made-up snippet shaped like an SEC filing: hidden XBRL header, a script, split table cells.
HTML = (
    '<html><body><div style="display:none"><ix:header>HIDDEN FACTS</ix:header></div>'
    "<p>Revenue <b>increased</b> 12%.</p><p>Second&nbsp;paragraph.</p><script>x = 1</script>"
    "<table><tr><td>Year</td><td></td><td>Revenue</td></tr>"
    "<tr><td>2024</td><td>$</td><td>112</td></tr>"
    "<tr><td>Loss</td><td>(5</td><td>)</td></tr></table><p>After.</p></body></html>"
)

EXPECTED = (
    "Revenue increased 12%.\n\nSecond paragraph.\n\n"
    "| Year | Revenue |\n| 2024 | 112 |\n| Loss | (5) |\n\nAfter."
)


def test_converts_paragraphs_and_tables_and_drops_hidden_content():
    assert html_to_text(HTML) == EXPECTED


def test_output_feeds_the_chunker_with_the_table_kept_whole():
    chunks = chunk_filing(html_to_text(HTML), "test", max_chars=30)
    tables = [c for c in chunks if c.kind == "table"]
    assert len(tables) == 1 and "| 2024 | 112 |" in tables[0].text and "(5)" in tables[0].text


def test_nested_table_does_not_crash_and_keeps_text():
    nested = "<table><tr><td>Outer <table><tr><td>inner</td></tr></table> end</td></tr></table>"
    assert "inner" in html_to_text(nested)
