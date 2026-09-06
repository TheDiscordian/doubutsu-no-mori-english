"""Small, explicit GameCube-to-retail-N64 text adaptations."""

import re

from textcodec import encode, tokenize
from textvalidate import FONT_PRESENTATION, compared_commands

COMMAND = re.compile(r"\{cmd:([0-9A-Fa-f]+)\}")


def remove_redundant_article_suppression(text):
    """N64 insertion routines never prepend GameCube grammatical articles.

    Accept CUTARTICLE only directly before a supported string insertion. Do
    not erase arbitrary unknown commands, capitalization, or date directives.
    """
    edits = []
    pattern = re.compile(r"\{cmd:7F74\}(?=\{cmd:7F([0-9A-F]{2})\})", re.IGNORECASE)
    def replace(match):
        if 0x1A <= int(match[1], 16) <= 0x3F:
            edits.append({"operation": "remove_redundant_cutarticle", "character_offset": match.start()})
            return ""
        return match[0]
    return pattern.sub(replace, text), edits


def adapt_reference(text, source, info, policy="presentation", resident_runtime=False):
    text, edits = remove_redundant_article_suppression(text)
    candidate = encode(text, info)
    ignored = compared_commands(policy, resident_runtime)
    old = [t.data for t in tokenize(source, info) if t.kind == "cmd" and t.data[1] not in ignored]
    new = [t.data for t in tokenize(candidate, info) if t.kind == "cmd" and t.data[1] not in ignored]
    if policy in ("reference_delivery", "reference_layout"):
        def delivery(data):
            codes = [t.data[1] for t in tokenize(data, info) if t.kind == "cmd"]
            return {"page_clears": codes.count(0x02), "button_waits": codes.count(0x04)}
        edits.append({"operation": "retain_gamecube_page_and_button_delivery",
                      "n64": delivery(source), "gamecube": delivery(candidate)})
    if policy == "reference_layout":
        def formatting(data):
            return [t.data.hex().upper() for t in tokenize(data, info)
                    if t.kind == "cmd" and t.data[1] in FONT_PRESENTATION | {0x67}]
        edits.append({"operation": "retain_gamecube_native_text_formatting",
                      "n64": formatting(source), "gamecube": formatting(candidate)})
    # Demo animation arguments are platform-specific. Only adapt when the
    # complete command opcode sequence agrees; preserve all original N64 demo
    # arguments in their corresponding positions. Never align by fuzzy text.
    if [c[1] for c in old] == [c[1] for c in new]:
        index = 0
        def replace(match):
            nonlocal index
            data = bytes.fromhex(match[1])
            if data[1] in ignored:
                return match[0]
            original = old[index]
            index += 1
            if 0x08 <= data[1] <= 0x0C and data != original:
                edits.append({"operation": "preserve_n64_demo_arguments", "command_index": index-1,
                              "gamecube": data.hex().upper(), "n64": original.hex().upper()})
                return "{cmd:"+original.hex().upper()+"}"
            return match[0]
        text = COMMAND.sub(replace, text)
    return text, edits
