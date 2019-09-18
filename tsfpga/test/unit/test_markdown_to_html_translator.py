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
        text = r"This sentence __should have a large portion__ in bold face"
        assert expected in self.markdown_to_html.translate(text)

        expected = "This sentence <em>should have a large portion</em> in italics"
        text = "This sentence *should have a large portion* in italics"
        assert expected in self.markdown_to_html.translate(text)
        text = "This sentence _should have a large portion_ in italics"
        assert expected in self.markdown_to_html.translate(text)

    def test_markdown_parser_can_handle_escaped_underscores_and_asterisks(self):
        expected = "Part of this sentence **should be surrounded** by double asterisks"
        text = r"Part of this sentence \*\*should be surrounded\*\* by double asterisks"
        assert expected in self.markdown_to_html.translate(text)
        expected = "Part of this sentence __should be surrounded__ by double underscores"
        text = r"Part of this sentence \_\_should be surrounded\_\_ by double underscores"
        assert expected in self.markdown_to_html.translate(text)

        expected = "Part of this sentence *should be surrounded* by asterisks"
        text = r"Part of this sentence \*should be surrounded\* by asterisks"
        assert expected in self.markdown_to_html.translate(text)
        expected = "Part of this sentence _should be surrounded_ by underscores"
        text = r"Part of this sentence \_should be surrounded\_ by underscores"
        assert expected in self.markdown_to_html.translate(text)

        expected = "Part of this sentence <em>*should be in italics and surrounded*</em> by asterisks"
        text = r"Part of this sentence *\*should be in italics and surrounded\** by asterisks"
        assert expected in self.markdown_to_html.translate(text)
        expected = "Part of this sentence <em>_should be in italics and surrounded_</em> by underscores"
        text = r"Part of this sentence _\_should be in italics and surrounded\__ by underscores"
        assert expected in self.markdown_to_html.translate(text)

        expected = "Part of this sentence *<em>should be in italics and surrounded</em>* by asterisks"
        text = r"Part of this sentence \**should be in italics and surrounded*\* by asterisks"
        assert expected in self.markdown_to_html.translate(text)
        expected = "Part of this sentence _<em>should be in italics and surrounded</em>_ by underscores"
        text = r"Part of this sentence \__should be in italics and surrounded_\_ by underscores"
        assert expected in self.markdown_to_html.translate(text)

        expected = "Part of this sentence should have an <em>*</em> in italics"
        text = r"Part of this sentence should have an *\** in italics"
        assert expected in self.markdown_to_html.translate(text)
        expected = "Part of this sentence should have an <em>_</em> in italics"
        text = r"Part of this sentence should have an _\__ in italics"
        assert expected in self.markdown_to_html.translate(text)
