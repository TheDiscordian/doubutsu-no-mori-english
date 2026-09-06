#!/usr/bin/env python3
"""Read GameCube ISO/CISO files and extract files without expanding sparse images."""

import argparse
import json
from pathlib import Path, PurePosixPath
import struct

from aflib import sha256, u32, yaz0_decode


def rarc_files(data):
    """Yield paths and data from a RARC archive, validating node and file bounds."""
    if data[:4] != b"RARC" or len(data) < 0x40 or u32(data, 4) != len(data):
        raise ValueError("Invalid RARC header/size")
    body = u32(data, 0xC)+0x20
    node_count, node_rel, file_count, file_rel, str_size, str_rel = struct.unpack_from(">6I", data, 0x20)
    nodes, files, names = node_rel+0x20, file_rel+0x20, str_rel+0x20
    if max(nodes+node_count*16, files+file_count*20, names+str_size, body) > len(data):
        raise ValueError("RARC tables exceed archive")
    active = set()
    def name_at(at):
        if at >= str_size:
            raise ValueError("Invalid RARC string offset")
        end = data.index(0, names+at, names+str_size)
        return data[names+at:end].decode("ascii")
    def walk(index, parent):
        if index >= node_count or index in active:
            raise ValueError("Invalid/cyclic RARC node")
        active.add(index)
        count = struct.unpack_from(">H", data, nodes+index*16+10)[0]
        first = u32(data, nodes+index*16+12)
        if first+count > file_count:
            raise ValueError("RARC node exceeds file table")
        for i in range(first, first+count):
            at = files+i*20
            flags, name_offset = struct.unpack_from(">2H", data, at+4)
            offset, size = struct.unpack_from(">2I", data, at+8)
            name = name_at(name_offset)
            if name in (".", ".."):
                continue
            if "/" in name or "\\" in name or not name:
                raise ValueError("Unsafe RARC path")
            path = parent/name
            if flags & 0x0200:
                yield from walk(offset, path)
            else:
                if body+offset+size > len(data):
                    raise ValueError("RARC file exceeds archive")
                yield str(path), data[body+offset:body+offset+size]
        active.remove(index)
    yield from walk(0, PurePosixPath())


class Disc:
    def __init__(self, path):
        self.file = path.open("rb")
        header = self.file.read(0x8000)
        self.block_size, self.blocks = 0, []
        if header[:4] == b"CISO":
            self.block_size = struct.unpack_from("<I", header, 4)[0]
            if not 512 <= self.block_size <= 0x1000000 or self.block_size & (self.block_size-1):
                raise ValueError("Invalid CISO block size")
            physical = 0x8000
            for used in header[8:]:
                if used not in (0, 1):
                    raise ValueError("Invalid CISO allocation map")
                self.blocks.append(physical if used else None)
                if used:
                    physical += self.block_size
        self.header = self.read(0, 0x440)
        if u32(self.header, 0x1C) != 0xC2339F3D:
            raise ValueError("Not a GameCube disc")

    def read(self, offset, size):
        if offset < 0 or size < 0 or size > 64*1024*1024:
            raise ValueError("Invalid disc read bounds")
        if not self.block_size:
            self.file.seek(offset)
            data = self.file.read(size)
            if len(data) != size:
                raise ValueError("Truncated ISO file")
            return data
        result = bytearray()
        while size:
            block, within = divmod(offset, self.block_size)
            if block >= len(self.blocks):
                raise ValueError("CISO read exceeds map")
            count = min(size, self.block_size-within)
            physical = self.blocks[block]
            if physical is None:
                result.extend(bytes(count))
            else:
                self.file.seek(physical+within)
                data = self.file.read(count)
                if len(data) != count:
                    raise ValueError("Truncated CISO allocated block")
                result.extend(data)
            offset += count
            size -= count
        return bytes(result)

    def files(self):
        offset, size = struct.unpack_from(">2I", self.header, 0x424)
        fst = self.read(offset, size)
        count = u32(fst, 8)
        if count*12 > len(fst):
            raise ValueError("Invalid FST entry count")
        names = fst[count*12:]
        stack, result = [(count, PurePosixPath())], []
        for i in range(1, count):
            while i >= stack[-1][0]:
                stack.pop()
            kind_name, start, length = struct.unpack_from(">3I", fst, i*12)
            at = kind_name & 0xFFFFFF
            if at >= len(names) or b"\0" not in names[at:]:
                raise ValueError("Invalid FST name offset")
            name = names[at:names.index(0, at)].decode("ascii")
            if name in (".", "..") or "/" in name or "\\" in name:
                raise ValueError("Unsafe FST path")
            path = stack[-1][1] / name
            if kind_name >> 24:
                if not i < length <= stack[-1][0]:
                    raise ValueError("Invalid FST directory range")
                stack.append((length, path))
            else:
                result.append({"path": str(path), "offset": start, "size": length})
        return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--disc", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("build/gamecube"))
    parser.add_argument("--extract", action="store_true")
    args = parser.parse_args()
    disc = Disc(args.disc)
    files = disc.files()
    args.output.mkdir(parents=True, exist_ok=True)
    if args.extract:
        for entry in files:
            data = disc.read(entry["offset"], entry["size"])
            entry["sha256"] = sha256(data)
            path = args.output / "files" / entry["path"]
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
            if data[:4] == b"RARC":
                archived = []
                for member, content in rarc_files(data):
                    target = path.with_name(path.name+".unpacked") / member
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes(content)
                    archived.append({"path": member, "size": len(content), "sha256": sha256(content)})
                entry["archive_files"] = archived
            if data[:4] == b"Yaz0":
                unpacked = yaz0_decode(data)
                path.with_name(path.name+".decoded").write_bytes(unpacked)
                entry["decoded_size"] = len(unpacked)
    report = {"disc_id": disc.header[:6].decode("ascii"), "revision": disc.header[7],
              "container_sha256": sha256(args.disc.read_bytes()), "files": files}
    (args.output / "disc.json").write_text(json.dumps(report, indent=2)+"\n")
    print(json.dumps({"disc_id": report["disc_id"], "revision": report["revision"],
                      "files": len(files), "output": str(args.output)}, indent=2))


if __name__ == "__main__":
    main()
