"""Control preservation, expansion budgets, and conservative dialogue layout checks."""

from textcodec import LATIN, tokenize

# Only presentation pauses and text colour may differ under this opt-in policy.
# Wait-for-button, page clearing, choices, branches, animation, sound, and every
# string insertion remain exact and ordered.
PRESENTATION = {0x03, 0x05}


def signature(data, info, policy="exact"):
    if policy not in ("exact", "presentation"):
        raise ValueError("Unknown control policy")
    return [token.data for token in tokenize(data, info) if token.kind == "cmd"
            and not (policy == "presentation" and token.data[1] in PRESENTATION)]


def expanded_bound(data, info):
    """Upper bound for the unmodified retail substitution routines.

    Use 32 bytes per dynamic insertion (retail names 6, free/item strings 10,
    country name + suffix at most 16, colour wrapper 6). Embedded mail receives
    96 bytes even though its message setter currently caps at 68. Include a
    16-byte work/alignment reserve. Unknown two-byte tags require manual work.
    """
    total = len(data)+16
    for token in tokenize(data, info):
        if token.kind == "glyph":
            raise ValueError("Two-byte message tags need explicit semantic review")
        if token.kind == "cmd" and 0x1A <= token.data[1] <= 0x40:
            total += (96 if token.data[1] == 0x40 else 32)-len(token.data)
    return total


def validate_entry(original, replacement, info, bank, policy="exact"):
    if signature(original, info, policy) != signature(replacement, info, policy):
        raise ValueError("Control signature changed")
    if bank == "message":
        if expanded_bound(replacement, info) > 1024:
            raise ValueError("Expanded message bound exceeds 1024 bytes")
    elif bank == "select":
        if len(replacement) > 10:
            raise ValueError("Choice exceeds retail 10-byte buffer")
        # Choice substitution has a separate 10-byte destination. Until its
        # complete expansion proof exists, dynamic edits may not grow.
        if any(t.kind == "cmd" for t in tokenize(replacement, info)) and len(replacement) > len(original):
            raise ValueError("Dynamic choice expansion requires review")
    elif len(replacement) > len(original):
        raise ValueError("Translation exceeds current entry budget")


def layout_issues(data, info, advances, max_width=192, max_lines=4):
    """Conservative retail-size bubble check; unknown dynamic layout is flagged."""
    x, line, issues, page = 0, 1, [], 0
    for token in tokenize(data, info):
        if token.kind == "text":
            if token.data == b"\xcd":
                x, line = 0, line+1
                continue
            x += advances.get(token.data[0], 12)
        elif token.kind == "glyph":
            issues.append("unknown_message_tag")
        elif token.kind == "cmd":
            command = token.data[1]
            if command in (0x02,):
                x, line, page = 0, 1, page+1
            elif 0x1A <= command <= 0x40:
                chars = {0x1A: 6, 0x1B: 6, 0x1C: 4, 0x2F: 16, 0x40: 68}.get(command, 10)
                x += chars*12  # Existing Japanese names remain possible.
            elif command in (0x51, 0x52, 0x53, 0x5A):
                issues.append("explicit_layout_command_needs_review")
        if x > max_width:
            issues.append(f"page_{page}_line_{line}_width_{x}")
        if line > max_lines and token.kind == "text" and token.data != b" ":
            issues.append(f"page_{page}_line_count_{line}")
    return sorted(set(issues))
