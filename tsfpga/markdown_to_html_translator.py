# ------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
# ------------------------------------------------------------------------------

import re


class MarkdownToHtmlTranslator:

    def __init__(self):
        self._compile_markdown_parser()

    def _compile_markdown_parser(self):
        r"""
        Strong: **double asterisks** or __double underscores__
        Emphasis: *single asterisks* or _single underscores_
        Literal asterisks or underscores are escaped: \* \_
        """
        not_escaped = r"(?<!\\)"
        double_asterisks = r"\*\*"
        double_underscores = r"\_\_"
        single_asterisk = r"\*"
        single_underscore = r"\_"
        match_text = r"(.*?)"

        # These patterns match underscores and asterisks only if they are not preceded by \escape
        self.strong_pattern1 = re.compile(
            not_escaped + double_asterisks + match_text + not_escaped + double_asterisks)
        self.strong_pattern2 = re.compile(
            not_escaped + double_underscores + match_text + not_escaped + double_underscores)
        self.em_pattern1 = re.compile(
            not_escaped + single_asterisk + match_text + not_escaped + single_asterisk)
        self.em_pattern2 = re.compile(
            not_escaped + single_underscore + match_text + not_escaped + single_underscore)

        # This pattern matches escaped underscores and asterisks
        self.escaped_literal_pattern = re.compile(r"\\(\*|_)")

    def translate(self, text):
        text = re.sub(self.strong_pattern1, r"<b>\g<1></b>", text)
        text = re.sub(self.strong_pattern2, r"<b>\g<1></b>", text)
        text = re.sub(self.em_pattern1, r"<em>\g<1></em>", text)
        text = re.sub(self.em_pattern2, r"<em>\g<1></em>", text)
        # Remove the escape sign
        text = re.sub(self.escaped_literal_pattern, r"\g<1>", text)
        return text
