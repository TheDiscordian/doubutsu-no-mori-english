"""Control preservation, expansion budgets, and conservative dialogue layout checks."""

from textcodec import LATIN, tokenize
from glyph_codes import WIDTHS as EXTENDED_WIDTHS
from aflib import sha256
from reference_sequences import SequencePermit
from native_diagnostics import validate_diagnostic
from reference_fields import ReferenceFieldPermit, SpeakerCatchphrasePermit
from reference_animations import ResidentAnimationPermit, is_resident_animation, verify_animation_values
from mail_controls import BANKS as MAIL_BANKS, validate_tokens as validate_mail_tokens
from placeholder_text import validate_placeholder
from fortune_strings import FortunePermit
from resetti_replies import ResettiReplyPermit
from shop_units import ShopUnitPermit
from resident_words import ResidentWordPermit

# Only presentation pauses and text colour may differ under this opt-in policy.
# Wait-for-button, page clearing, choices, branches, animation, sound, and every
# string insertion remain exact and ordered.
PRESENTATION = {0x03, 0x05}
# Read-only substitutions. Random-number generation (30) and embedded mail
# (40) remain ordered commands, not freely movable text fields.
TEXT_FIELDS = set(range(0x1A, 0x30)) | set(range(0x31, 0x40)) | {0x76}
DATE_FIELDS = set(range(0x1D, 0x24))
RUNTIME_PRESENTATION = {0x72, 0x73, 0x75}
# Native sentence/character consumers agree with the English reference. Sound
# control 51 is intentionally absent. No reference line breaks are rewritten.
FONT_PRESENTATION = {0x50, 0x52, 0x53, 0x54, 0x5A}


def compared_commands(policy, resident_runtime=False):
    presentation = PRESENTATION | (RUNTIME_PRESENTATION if resident_runtime else set())
    if policy == "exact":
        return set()
    if policy == "presentation":
        return presentation
    if policy == "reference_text":
        return presentation | TEXT_FIELDS
    if policy == "reference_delivery":
        return presentation | TEXT_FIELDS | {0x02, 0x04}
    if policy == "reference_layout":
        return presentation | TEXT_FIELDS | {0x02, 0x04} | FONT_PRESENTATION | ({0x67} if resident_runtime else set())
    raise ValueError("Unknown control policy")


def signature(data, info, policy="exact", resident_runtime=False):
    ignored = compared_commands(policy, resident_runtime)
    def canonical(command):
        # Both enable B-to-last-option. Only their closing-sound policy differs.
        return b"\x7f\x5e" if resident_runtime and policy != "exact" and command == b"\x7f\x62" else command
    return [canonical(token.data) for token in tokenize(data, info) if token.kind == "cmd"
            and token.data[1] not in ignored]


def expanded_bound(data, info, *, extended_glyphs=False):
    """Upper bound for the unmodified retail substitution routines.

    Use 32 bytes per dynamic insertion (retail names 6, free/item strings 10,
    country name + suffix at most 16, colour wrapper 6). Embedded mail receives
    96 bytes even though its message setter currently caps at 68. Include a
    16-byte work/alignment reserve. Unknown two-byte tags require manual work.
    """
    total = len(data)+16
    for token in tokenize(data, info):
        if token.kind == "glyph" and not (extended_glyphs and token.data in EXTENDED_WIDTHS):
            raise ValueError("Two-byte message tags need explicit semantic review")
        if token.kind == "cmd" and (0x1A <= token.data[1] <= 0x40 or token.data[1] == 0x76):
            total += (96 if token.data[1] == 0x40 else 32)-len(token.data)
    return total


def validate_entry(original, replacement, info, bank, policy="exact", *, choice_bytes=10, resident_runtime=False,
                   sequence_permit=None, field_permit=None, catchphrase_permit=None, animation_permit=None,
                   extended_glyphs=False, fortune_permit=None, resetti_permit=None, shop_unit_permit=None,
                   resident_word_permit=None):
    if resident_word_permit is not None:
        if (not isinstance(resident_word_permit, ResidentWordPermit) or bank!='string' or policy!='exact'
                or not resident_runtime or resident_word_permit.capacity not in (10,16)
                or any(p is not None for p in (fortune_permit,resetti_permit,shop_unit_permit))
                or resident_word_permit.source_sha256!=sha256(original)
                or resident_word_permit.encoded_sha256!=sha256(replacement)
                or not 1<=len(replacement)<=resident_word_permit.capacity
                or any(t.kind!='text' for t in tokenize(replacement,info))):
            raise ValueError('Resident-word capacity requires an exact complete field permit and resident runtime')
    if shop_unit_permit is not None:
        if (not isinstance(shop_unit_permit, ShopUnitPermit) or bank != 'string' or policy != 'exact'
                or fortune_permit is not None or resetti_permit is not None
                or shop_unit_permit.source_sha256 != sha256(original)
                or shop_unit_permit.encoded_sha256 != sha256(replacement) or len(replacement)>10
                or any(t.kind!='text' for t in tokenize(replacement,info))):
            raise ValueError('Shop-unit capacity requires an exact complete counter permit')
    if resetti_permit is not None:
        if (not isinstance(resetti_permit, ResettiReplyPermit) or bank != 'string' or policy != 'exact'
                or fortune_permit is not None or resetti_permit.source_sha256 != sha256(original)
                or resetti_permit.encoded_sha256 != sha256(replacement) or len(replacement) > 10
                or any(t.kind != 'text' for t in tokenize(replacement,info))):
            raise ValueError('Resetti capacity requires an exact complete reply permit')
    if fortune_permit is not None:
        if (not isinstance(fortune_permit, FortunePermit) or bank != 'string' or not resident_runtime
                or policy != 'exact' or fortune_permit.source_sha256 != sha256(original)
                or fortune_permit.encoded_sha256 != sha256(replacement) or len(replacement) > 16
                or any(t.kind != 'text' for t in tokenize(replacement, info))):
            raise ValueError('Fortune capacity requires an exact complete resident string permit')
    if extended_glyphs and (bank != 'message' or not resident_runtime):
        raise ValueError('Extended glyphs require the resident main-dialogue capability')
    if bank == 'message' and policy != 'reviewed_sequence':
        validate_placeholder(original, replacement, info)
        validate_diagnostic(original, replacement, info)
    if choice_bytes not in (10, 16, 20) or choice_bytes == 20 and not resident_runtime:
        raise ValueError("Unsupported choice runtime capacity")
    if animation_permit is not None:
        if (not isinstance(animation_permit, ResidentAnimationPermit) or bank != 'message'
                or policy != 'reference_layout' or not resident_runtime
                or any(p is not None for p in (sequence_permit, field_permit, catchphrase_permit))
                or animation_permit.source_sha256 != sha256(original)
                or animation_permit.encoded_sha256 != sha256(replacement)
                or animation_permit.context != 'native_resident_talk'):
            raise ValueError('Animations require a complete reviewed resident-context permit')
        verify_animation_values(original, replacement, info)
    if field_permit is not None:
        if (not isinstance(field_permit, ReferenceFieldPermit) or bank != "message"
                or policy != "reference_layout" or not resident_runtime
                or field_permit.source_sha256 != sha256(original)
                or field_permit.encoded_sha256 != sha256(replacement)
                or not field_permit.fields or not field_permit.fields <= {0x1A, 0x2F}):
            raise ValueError("Additional fields require a complete reviewed player/town-field permit")
    if catchphrase_permit is not None:
        if (not isinstance(catchphrase_permit, SpeakerCatchphrasePermit) or bank != "message"
                or policy != "reference_layout" or not resident_runtime
                or field_permit is not None or sequence_permit is not None
                or catchphrase_permit.source_sha256 != sha256(original)
                or catchphrase_permit.encoded_sha256 != sha256(replacement)
                or catchphrase_permit.context != "native_resident_talk"):
            raise ValueError("Catchphrases require a complete reviewed resident-speaker permit")
    if bank in MAIL_BANKS:
        validate_mail_tokens(tokenize(replacement, info))
    for token in tokenize(replacement, info):
        if token.kind == "cmd":
            if token.data[1] == 0x53 and token.data[2] > 2:
                raise ValueError("Line anchor exceeds native three-entry table")
            if token.data[1] in (0x54, 0x5A) and token.data[2] == 0:
                raise ValueError("Text scale must be nonzero")
    if resident_runtime:
        hour_seen = False
        for token in tokenize(replacement, info):
            if token.kind == "cmd":
                if token.data[1] == 0x21:
                    hour_seen = True
                elif token.data[1] == 0x76 and not hour_seen:
                    raise ValueError("AM/PM requires a preceding hour field in the message")
    if policy in ("reference_text", "reference_delivery", "reference_layout"):
        if bank != "message":
            raise ValueError("Reference text policy is only audited for dialogue")
        def fields(data):
            return {t.data[1] for t in tokenize(data, info)
                    if t.kind == "cmd" and t.data[1] in TEXT_FIELDS}
        available = fields(original)
        if resident_runtime and available & DATE_FIELDS:
            available |= DATE_FIELDS
        if resident_runtime and 0x21 in available:
            available.add(0x76)
        if field_permit is not None:
            if fields(replacement)-available != field_permit.fields:
                raise ValueError("Additional fields differ from the exact reviewed player/town set")
            available |= field_permit.fields
        if catchphrase_permit is not None:
            if fields(replacement)-available != {0x1C}:
                raise ValueError("Additional fields differ from the exact reviewed catchphrase set")
            available.add(0x1C)
        if not fields(replacement) <= available:
            raise ValueError("Reference requests a text field absent from the N64 message")
    if policy == "reviewed_sequence":
        if (bank != "message" or not isinstance(sequence_permit, SequencePermit)
                or sequence_permit.source_sha256 != sha256(original)
                or sequence_permit.encoded_sha256 != sha256(replacement)):
            raise ValueError("Reviewed sequence requires complete hash-bound approval")
    else:
        before = signature(original, info, policy, resident_runtime)
        after = signature(replacement, info, policy, resident_runtime)
        if animation_permit is not None:
            before = [c for c in before if not is_resident_animation(c)]
            after = [c for c in after if not is_resident_animation(c)]
        if before != after:
            raise ValueError("Control signature changed")
    if bank == "message":
        if expanded_bound(replacement, info, extended_glyphs=extended_glyphs) > 1024:
            raise ValueError("Expanded message bound exceeds 1024 bytes")
    elif bank == "select":
        if len(replacement) > choice_bytes:
            raise ValueError(f"Choice exceeds {'retail ' if choice_bytes == 10 else ''}{choice_bytes}-byte buffer")
        if choice_bytes > 10 and any(t.kind != "text" for t in tokenize(replacement, info)):
            raise ValueError("Expanded choice runtime requires plain text")
        # Choice substitution has a separate 10-byte destination. Until its
        # complete expansion proof exists, dynamic edits may not grow.
        if any(t.kind == "cmd" for t in tokenize(replacement, info)) and len(replacement) > len(original):
            raise ValueError("Dynamic choice expansion requires review")
    elif (len(replacement) > len(original) and fortune_permit is None
          and resetti_permit is None and shop_unit_permit is None and resident_word_permit is None):
        raise ValueError("Translation exceeds current entry budget")
    if bank != 'message' and any(t.kind == 'glyph' for t in tokenize(replacement, info)):
        raise ValueError('Two-byte message tags need explicit semantic review')


def layout_issues(data, info, advances, max_width=192, max_lines=4, *, resident_runtime=False,
                  extended_glyphs=False):
    """Conservative retail-size bubble check; unknown dynamic layout is flagged."""
    x, line, issues, page = 0, 1, [], 0
    for token in tokenize(data, info):
        if token.kind == "text":
            if token.data == b"\xcd":
                x, line = 0, line+1
                continue
            x += advances.get(token.data[0], 12)
        elif token.kind == "glyph":
            if extended_glyphs and token.data in EXTENDED_WIDTHS:
                x += EXTENDED_WIDTHS[token.data]
            else:
                issues.append("unknown_message_tag")
        elif token.kind == "cmd":
            command = token.data[1]
            if command in (0x02,):
                x, line, page = 0, 1, page+1
            elif 0x1A <= command <= 0x40 or command == 0x76:
                chars = {0x1A: 6, 0x1B: 6, 0x1C: 4, 0x2F: 16, 0x40: 68}.get(command, 10)
                width = chars*12  # Existing Japanese names remain possible.
                if command == 0x1C and resident_runtime:
                    # A default may display ten English bytes while saved
                    # custom/Japanese phrases still occupy four native cells.
                    width = max(width, 10*max(advances.values(), default=12))
                x += width
            elif command in (0x52, 0x53, 0x54, 0x5A, 0x67):
                issues.append("explicit_layout_command_needs_review")
        if x > max_width:
            issues.append(f"page_{page}_line_{line}_width_{x}")
        if line > max_lines and token.kind == "text" and token.data != b" ":
            issues.append(f"page_{page}_line_count_{line}")
    return sorted(set(issues))
