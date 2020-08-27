# ------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
# ------------------------------------------------------------------------------

import unittest

from tsfpga.markdown_to_html_translator import MarkdownToHtmlTranslator


class TestMarkdownToHtmlTranslator(unittest.TestCase):

    def setUp(self):
        self.markdown_to_html = MarkdownToHtmlTranslator()

    def test_markdown_parser_can_handle_annotating_sentences(self):
        expected = "This sentence <b>should have a large portion</b> in bold face"
        text = r"This sentence **should have a large portion** in bold face"
        assert expected in self.markdown_to_html.translate(text)

        expected = "This sentence <em>should have a large portion</em> in italics"
        text = "This sentence *should have a large portion* in italics"
        assert expected in self.markdown_to_html.translate(text)

    def test_markdown_parser_can_handle_escaped_asterisks(self):
        expected = "Part of this sentence **should be surrounded** by double asterisks"
        text = r"Part of this sentence \*\*should be surrounded\*\* by double asterisks"
        assert expected in self.markdown_to_html.translate(text)

        expected = "Part of this sentence *should be surrounded* by asterisks"
        text = r"Part of this sentence \*should be surrounded\* by asterisks"
        assert expected in self.markdown_to_html.translate(text)

        expected = "Part of this sentence <em>*should be in italics and surrounded*</em> by asterisks"
        text = r"Part of this sentence *\*should be in italics and surrounded\** by asterisks"
        assert expected in self.markdown_to_html.translate(text)

        expected = "Part of this sentence *<em>should be in italics and surrounded</em>* by asterisks"
        text = r"Part of this sentence \**should be in italics and surrounded*\* by asterisks"
        assert expected in self.markdown_to_html.translate(text)

        expected = "Part of this sentence should have an <em>*</em> in italics"
        text = r"Part of this sentence should have an *\** in italics"
        assert expected in self.markdown_to_html.translate(text)

    def test_line_breaks(self):
        expected = "Two empty lines<br />\n<br />\nbetween paragraphs."
        text = "Two empty lines\n\nbetween paragraphs."
        assert expected in self.markdown_to_html.translate(text)

        expected = "Three empty lines<br />\n<br />\nbetween paragraphs."
        text = "Three empty lines\n\n\nbetween paragraphs."
        assert expected in self.markdown_to_html.translate(text)

        expected = r"Escaped \n\n\n should not result in paragraph break."
        text = r"Escaped \n\n\n should not result in paragraph break."
        assert expected in self.markdown_to_html.translate(text)

        expected = "One empty line means same paragraph."
        text = "One empty line\nmeans same paragraph."
        assert expected in self.markdown_to_html.translate(text)

    def test_literal_underscore_can_be_used(self):
        # We do not translate underscores, unlike some markdown
        expected = "This sentence <b>contains_underscores</b> in some_places"
        text = r"This sentence **contains_underscores** in some_places"
        assert expected in self.markdown_to_html.translate(text)
