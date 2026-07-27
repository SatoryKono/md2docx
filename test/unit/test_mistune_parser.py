from md2docx.adapters.outbound.mistune_parser import MistuneMarkdownParser
from md2docx.domain.model import Heading


def test_mistune_parser_parity_headings():
    p = MistuneMarkdownParser()
    blocks = list(p.parse("# ВВЕДЕНИЕ\n\nТекст.\n"))
    assert any(isinstance(b, Heading) and b.structural for b in blocks)
