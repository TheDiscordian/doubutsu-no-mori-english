"""Guarded English choice runtimes and town-name substitution."""

from dataclasses import dataclass
import struct

from aflib import CODE_RAM, CODE_VROM, by_vrom, sha256
from runtime_layout import MODULE_RAM, LINKED_LIMIT

CHOICE_BYTES = 16
CHOICE_ROWS = 0x8009F4B8
CHOICE_SELECTED = CHOICE_ROWS+64
QUEST_VROM, QUEST_RAM = 0x849B50, 0x80954D80
PLAYER_SELECT_VROM, PLAYER_SELECT_RAM = 0x8A1F10, 0x809BE720
SOURCE_HASHES = {
    CODE_VROM: "2639d08d6a3de000fa270ebd3837f86d546041cd4a00d40fbf817a63f7b13810",
    QUEST_VROM: "67464dc7e81d45cb168ca929c80ec56c1eea09b9c64c48c03d7a53815ed5c51b",
    PLAYER_SELECT_VROM: "f353eee3bff0758dac7ddeb1fd9c0541e3cc4584830289f9e851ae10bf6a9e48",
}
WIDTH_CODE = bytes.fromhex(
    "27BDFFD8AFBF0024AFB00020AFB1001CAFB20018AFB300148C92007C2490005C"
    "3C11800A2631F4B81A40000C000098258E050000022020250C0240B300003025"
    "0262082A1020000226100004004098252652FFFF1640FFF62631001002601025"
    "8FBF00248FB000208FB1001C8FB200188FB3001403E0000827BD00280000000000000000")
TOWN_RETURN = bytes.fromhex("8FA200548FBF00248FB0002003E0000827BD0058")


@dataclass(frozen=True)
class ChoiceLayout:
    capacity: int = 16
    stride: int = 16
    rows: int = CHOICE_ROWS
    selected: int = CHOICE_SELECTED

    def __post_init__(self):
        if (self.capacity, self.stride, self.rows, self.selected) == (16, 16, CHOICE_ROWS, CHOICE_SELECTED):
            return
        if (self.capacity != 20 or self.stride != 32 or self.rows % 32
                or not 0x80194BE0 <= self.rows < self.selected
                or self.selected != self.rows+128 or self.selected+32 > MODULE_RAM+LINKED_LIMIT):
            raise ValueError("Unsupported English choice storage layout")


def split_address(address):
    return ((address+0x8000) >> 16) & 0xFFFF, address & 0xFFFF


def width_code(layout=ChoiceLayout()):
    code = bytearray(WIDTH_CODE)
    high, low = split_address(layout.rows)
    struct.pack_into(">2I", code, 32, 0x3C110000 | high, 0x26310000 | low)
    struct.pack_into(">I", code, 88, 0x26310000 | layout.stride)
    return bytes(code)


class GuardedCode:
    def __init__(self, original, current, base, expected_sha256):
        if sha256(original) != expected_sha256 or len(current) != len(original):
            raise ValueError("English runtime source file does not match retail")
        self.original, self.data, self.base = original, bytearray(current), base
        self.changes = []
        self.touched = set()

    def word(self, address):
        return struct.unpack_from(">I", self.original, address-self.base)[0]

    def write(self, address, data):
        offset = address-self.base
        region = set(range(offset, offset+len(data)))
        if not 0 <= offset <= len(self.data)-len(data) or region & self.touched:
            raise ValueError("Overlapping or out-of-range English runtime patch")
        if self.data[offset:offset+len(data)] != self.original[offset:offset+len(data)]:
            raise ValueError(f"English runtime instruction guard failed at {address:08X}")
        self.data[offset:offset+len(data)] = data
        self.touched.update(region)
        self.changes.append({"ram": f"{address:08X}", "bytes": len(data),
                             "patched_sha256": sha256(data)})

    def instruction(self, address, expected, replacement):
        if self.word(address) != expected:
            raise ValueError(f"Unexpected retail instruction at {address:08X}")
        self.write(address, struct.pack(">I", replacement))

    def immediate(self, address, expected, replacement):
        word = self.word(address)
        if word & 0xFFFF != expected & 0xFFFF:
            raise ValueError(f"Unexpected retail immediate at {address:08X}")
        self.write(address, struct.pack(">I", (word & 0xFFFF0000) | (replacement & 0xFFFF)))

    def grow_stack(self, start, end, old_frame, after_array, growth=24):
        """Grow only stack references beyond a fixed local array.

        All source instructions are hash-guarded. The array starts in place;
        temporaries above its old end and incoming arguments move by growth.
        Saved registers and outgoing argument space below it do not move.
        """
        changed = 0
        for address in range(start, end, 4):
            word = self.word(address)
            op, rs, rt, immediate = word >> 26, (word >> 21) & 31, (word >> 16) & 31, word & 0xFFFF
            if rs != 29:
                continue
            if op == 9 and rt == 29 and immediate in ((-old_frame) & 0xFFFF, old_frame):
                new = -(old_frame+growth) if immediate & 0x8000 else old_frame+growth
            elif op in (9, 32, 33, 35, 36, 37, 40, 41, 43, 49, 57) and after_array <= immediate <= old_frame+12:
                new = immediate+growth
            else:
                continue
            self.immediate(address, immediate, new)
            changed += 1
        if changed < 2:
            raise ValueError("Missing English choice stack-frame adjustments")


def patch_main(code, layout):
    cap, stride = layout.capacity, layout.stride
    high, low = split_address(layout.rows)
    selected_high, selected_low = split_address(layout.selected)
    shift = 4 if stride == 16 else 5
    code.write(0x8009F4A4, TOWN_RETURN+b" "*80+bytes(4))
    code.write(0x80065348, width_code(layout))
    # Add and set: preserve the Choice structure and its length array.
    for address in (0x800651C0, 0x800652AC, 0x800652D4, 0x800652FC, 0x80065324, 0x80065604):
        code.immediate(address, 11, cap+1)
    for address, before, after in (
        (0x80065204, 0x0009C080, 0x0009C000 | shift << 6),
        (0x80065208, 0x0309C021, 0x3C030000 | high),
        (0x8006520C, 0x0018C040, 0x24630000 | low),
        (0x80065210, 0x00D81821, 0x00781821),
        (0x8006521C, 0x24630034, 0),
        (0x80066144, 0x24E5006C, 0x3C040000 | high),
        (0x80066148, 0x00037080, 0x24840000 | low),
        (0x8006614C, 0x01C37021, 0x00037000 | shift << 6),
        (0x80066150, 0x000E7040, 0x24850000 | 4*stride),
        (0x80066154, 0x00EE2021, 0x008E2021),
        (0x80066158, 0x24840034, 0),
        # t9 already holds the selected row's length pointer on the first
        # iteration. Reload it in the existing loop's branch delay slot.
        (0x80066C38, 0x26150034, 0x3C150000 | high),
        (0x80066C3C, 0x02008825, 0x26B50000 | low),
        (0x80066C40, 0x8FAA009C, 0x02008825),
        (0x80066C4C, 0x162A0015, 0x16390015),
        (0x80066D08, 0x8FAA009C, 0x8FB9009C),
        (0x8009F3FC, 0x8FA50030, 0x3C050000 | selected_high),
        (0x8009F410, 0x24A5021C, 0x24A50000 | selected_low),
    ):
        code.instruction(address, before, after)
    for address in (0x80065DD0, 0x80065E20, 0x80065E34, 0x80065E74,
                    0x80065EA8, 0x80065EB0, 0x80065EBC, 0x8006615C,
                    0x800A0F58, 0x800A0F5C,
                    0x800A0F60, 0x800A0F7C):
        code.immediate(address, 10, cap)
    code.immediate(0x80066D00, 10, stride)
    code.immediate(0x800A0F14, 10, stride)
    # Main message staging may share rows: SetChoiceData copies each row to
    # itself, without a prior clear. The selected-answer buffer is separate.
    for address in (0x800A0EDC, 0x800A0F24, 0x800A0F3C, 0x800A0F50, 0x800A0F54):
        # These pointers use signed low immediates; each row is checked below.
        code.immediate(address, 0x8014, high)
    for address, before, after in (
        (0x800A0EEC, 0x2700, 0), (0x800A0F2C, 0x2714, 2),
        (0x800A0F44, 0x271E, 3), (0x800A0F70, 0x270A, 1),
        (0x800A0F74, 0x2700, 0),
    ):
        row_high, row_low = split_address(layout.rows+after*stride)
        if row_high != high:
            raise ValueError("Choice rows cross a signed address boundary")
        code.immediate(address, before, row_low)


def patch_quest(code, layout):
    cap = layout.capacity
    code.grow_stack(0x80955814, 0x80955940, 176, 0xAC, growth=4*(cap-10))
    for address, before, after in (
        (0x80955870, 0x0011C080, 0x0011C100),
        (0x80955874, 0x00114080, 0x00114100),
        (0x80955878, 0x01114021, 0),
        (0x8095587C, 0x0311C021, 0),
        (0x80955880, 0x0018C040, 0),
        (0x80955884, 0x00084040, 0),
    ):
        if cap == 16:
            code.instruction(address, before, after)
    if cap == 20:
        # Existing (row*4 + row)*2 becomes (row*4 + row)*4.
        code.instruction(0x80955880, 0x0018C040, 0x0018C080)
        code.instruction(0x80955884, 0x00084040, 0x00084080)
    for address in (0x809558E0, 0x809558E4, 0x809558E8, 0x80955900):
        code.immediate(address, 10, cap)


def patch_player_select(code, layout):
    cap = layout.capacity
    code.grow_stack(0x809BF244, 0x809BF3E4, 136, 0x84, growth=4*(cap-10))
    code.grow_stack(0x809BF3E4, 0x809BF4C0, 128, 0x7C, growth=4*(cap-10))
    for address in (0x809BF0B4, 0x809BF170, 0x809BF39C, 0x809BF3A0,
                    0x809BF3A4, 0x809BF3C0, 0x809BF478, 0x809BF47C,
                    0x809BF480, 0x809BF498):
        code.immediate(address, 10, cap)
    for address in (0x809BF26C, 0x809BF40C):
        code.immediate(address, 40, 4*cap)
    for address, before, after in (
        (0x809BF218, 20, 2*cap), (0x809BF230, 30, 3*cap),
        (0x809BF41C, 0x5E, 0x54+cap), (0x809BF420, 0x68, 0x54+2*cap),
        (0x809BF424, 0x72, 0x54+3*cap),
    ):
        code.immediate(address, before, after)
    for address, before, after in (
        (0x809BF308, 0x00104080, 0x00104100),
        (0x809BF30C, 0x01104021, 0),
        (0x809BF314, 0x00084040, 0),
        (0x809BF318, 0x0010C080, 0x0010C100),
        (0x809BF31C, 0x0310C021, 0),
        (0x809BF320, 0x0018C040, 0),
    ):
        if cap == 16:
            code.instruction(address, before, after)
    if cap == 20:
        code.instruction(0x809BF314, 0x00084040, 0x00084080)
        code.instruction(0x809BF320, 0x0018C040, 0x0018C080)


def make_english_runtime(rom, replacements, layout=ChoiceLayout()):
    files, result, reports = by_vrom(rom), {}, {}
    for vrom, ram, patcher in ((CODE_VROM, CODE_RAM, patch_main),
                               (QUEST_VROM, QUEST_RAM, patch_quest),
                               (PLAYER_SELECT_VROM, PLAYER_SELECT_RAM, patch_player_select)):
        original = files[vrom].extract(rom)
        code = GuardedCode(original, replacements.get(vrom, original), ram, SOURCE_HASHES[vrom])
        patcher(code, layout)
        result[vrom] = bytes(code.data)
        reports[f"{vrom:08X}"] = {"size": len(code.data), "changes": code.changes}
    return result, {"choice_bytes": layout.capacity, "choice_row_stride": layout.stride,
                    "choice_rows_ram": f"{layout.rows:08X}",
                    "choice_selected_ram": f"{layout.selected:08X}",
                    "town_suffix": "none", "extra_permanent_ram": 0,
                    "resident_storage_bytes": 160 if layout.capacity == 20 else 0,
                    "largest_added_stack_bytes": 4*(layout.capacity-10), "files": reports}


def verify_english_runtime(rom, replacements, layout=ChoiceLayout()):
    """Capacity opt-in requires every runtime/actor patch, not just a flag."""
    expected, report = make_english_runtime(rom, {}, layout)
    bases = {CODE_VROM: CODE_RAM, QUEST_VROM: QUEST_RAM, PLAYER_SELECT_VROM: PLAYER_SELECT_RAM}
    for key, file in report["files"].items():
        vrom = int(key, 16)
        current = replacements.get(vrom, b"")
        if len(current) != len(expected[vrom]):
            raise ValueError("Expanded choice capacity requires the complete English runtime")
        for change in file["changes"]:
            start = int(change["ram"], 16)-bases[vrom]
            end = start+change["bytes"]
            if current[start:end] != expected[vrom][start:end]:
                raise ValueError(f"Missing English runtime patch at {change['ram']}")
