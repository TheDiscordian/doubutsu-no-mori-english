"""Read executable ranges from the pinned Splat definitions, without guessing.

This is deliberately a parser for the small forms present in the pinned files,
not a general YAML parser. New forms and unknown section types fail closed.
"""

from bisect import bisect_right
from dataclasses import dataclass
from pathlib import Path
import re

from aflib import sha256

TEXT = {"c", "asm", "hasm"}
DATA = {"data", ".data", "rodata", ".rodata", "bss", ".bss", "pad", "bin", "header", "end"}


@dataclass(frozen=True)
class CodeSegment:
    name: str
    vrom: int
    ram: int
    starts: tuple
    executable: tuple

    def is_text(self, offset):
        index = bisect_right(self.starts, offset)-1
        return index >= 0 and self.executable[index]


def parse_segments(content):
    segments = []
    for block in re.split(r"(?m)^  - name: ", content)[1:]:
        if not re.search(r"(?m)^    type: code\s*$", block):
            continue
        start = re.search(r"(?m)^    start: (0x[0-9a-fA-F]+)\s*$", block)
        ram = re.search(r"(?m)^    vram: (0x[0-9a-fA-F]+)\s*$", block)
        if not start or not ram:
            raise ValueError("Unexpected pinned executable-segment definition")
        vrom, base = int(start[1], 16), int(ram[1], 16)
        boundaries, flags, bss_started = [], [], False
        for sub in re.split(r"(?m)^      - ", block)[1:]:
            line = sub.splitlines()[0].split("#", 1)[0].strip()
            if line.startswith("[") and line.endswith("]"):
                parts = [part.strip() for part in line[1:-1].split(",")]
                address = int(parts[0], 16)
                kind = parts[1] if len(parts) > 1 else "end"
                section = parts[4] if len(parts) > 4 else ".text"
            else:
                # Inline or block mappings. Nested data subsegments are not CPU text.
                if line.startswith("{") and line.endswith("}"):
                    fields = dict(part.strip().split(":", 1) for part in line[1:-1].split(","))
                elif line.startswith("start:"):
                    fields = dict(re.findall(r"(?m)^\s{0,8}(start|type|section):\s*(\S+)\s*$", sub))
                else:
                    raise ValueError("Unsupported pinned subsegment form")
                fields = {key.strip(): value.strip() for key, value in fields.items()}
                kind, section = fields.get("type"), fields.get("section", ".text")
                if "start" not in fields:
                    if kind not in ("bss", ".bss") and not (kind == "lib" and section == ".bss"):
                        raise ValueError("Non-BSS subsegment lacks a ROM boundary")
                    bss_started = True
                    continue
                address = int(fields["start"], 16)
            is_bss = kind in ("bss", ".bss") or kind == "lib" and section == ".bss"
            if bss_started:
                if not is_bss:
                    raise ValueError("File-backed section follows BSS")
                continue
            if is_bss:
                # Only the first BSS boundary ends file-backed data. Later BSS
                # entries use shared or synthetic ROM addresses in pinned Splat.
                bss_started = True
                if boundaries and address-vrom == boundaries[-1] and not flags[-1]:
                    continue
            if kind == "lib":
                if section not in (".text", ".data", ".rodata", ".bss"):
                    raise ValueError("Unknown pinned library section")
                is_text = section == ".text"
            elif kind in TEXT | DATA:
                is_text = kind in TEXT
            else:
                raise ValueError(f"Unknown pinned subsegment type: {kind}")
            offset = address-vrom
            if offset < 0 or boundaries and offset <= boundaries[-1]:
                raise ValueError(f"Unordered pinned subsegment boundaries in {block.splitlines()[0]}: {address:08X}")
            boundaries.append(offset)
            flags.append(is_text)
        if not boundaries or boundaries[0] != 0:
            raise ValueError("Incomplete pinned subsegment boundaries")
        segments.append(CodeSegment(block.splitlines()[0].strip(), vrom, base,
                                    tuple(boundaries), tuple(flags)))
    return segments


def code_segments():
    root = Path(__file__).resolve().parents[1]/"upstream/af/yamls/jp"
    segments, definitions = {}, {}
    for name in ("makerom.yaml", "boot.yaml", "code.yaml", "overlays.yaml"):
        data = (root/name).read_bytes()
        definitions[name] = sha256(data)
        for segment in parse_segments(data.decode()):
            if segment.vrom in segments:
                raise ValueError("Duplicate pinned code segment")
            segments[segment.vrom] = segment
    return segments, definitions
