# ------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
# ------------------------------------------------------------------------------

import re


class MarkdownToHtmlTranslator:
    def __init__(self):
        self._compile_markdown_parser()

    def translate(self, text):
        return self._insert_line_breaks(self._annotate(text))

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
            not_escaped + double_asterisks + match_text + not_escaped + double_asterisks
        )
        self.em_pattern = re.compile(
            not_escaped + single_asterisk + match_text + not_escaped + single_asterisk
        )

        # This pattern matches escaped asterisks
        self.escaped_literal_pattern = re.compile(r"\\(\*)")

        # Consecutive newlines is a paragraph separator
        self.paragraph_separator = re.compile(r"\n{2,}")

    def _annotate(self, text):
        result = re.sub(self.strong_pattern, r"<b>\g<1></b>", text)
        result = re.sub(self.em_pattern, r"<em>\g<1></em>", result)
        # Remove the escape sign
        result = re.sub(self.escaped_literal_pattern, r"\g<1>", result)
        return result

    def _insert_line_breaks(self, text):
        # Two line breaks to get new paragraph.
        result = re.sub(self.paragraph_separator, "<br /><br />", text)
        # A single newline in Markdown should be a space
        result = result.replace("\n", " ")
        # Split to get nicer HTML file formatting
        result = result.replace("<br />", "<br />\n")
        return result
