# ------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
# ------------------------------------------------------------------------------

import re


class MarkdownToHtmlTranslator:

    def __init__(self):
        self._compile_markdown_parser()

    def _compile_markdown_parser(self):
        r"""
        Strong: **double asterisks**
        Emphasis: *single asterisks*
        Literal asterisks are escaped: \*
        """
        not_escaped = r"(?<!\\)"
        double_asterisks = r"\*\*"
        single_asterisk = r"\*"
        match_text = r"(.*?)"

        # These patterns match asterisks only if they are not preceded by \escape
        self.strong_pattern = re.compile(
            not_escaped + double_asterisks + match_text + not_escaped + double_asterisks)
        self.em_pattern = re.compile(
            not_escaped + single_asterisk + match_text + not_escaped + single_asterisk)

        # This pattern matches escaped asterisks
        self.escaped_literal_pattern = re.compile(r"\\(\*)")

    def translate(self, text):
        text = re.sub(self.strong_pattern, r"<b>\g<1></b>", text)
        text = re.sub(self.em_pattern, r"<em>\g<1></em>", text)
        # Remove the escape sign
        text = re.sub(self.escaped_literal_pattern, r"\g<1>", text)
        return text
