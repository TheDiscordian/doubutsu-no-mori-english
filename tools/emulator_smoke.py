#!/usr/bin/env python3
"""Silent ares tests on an isolated X display, with bounded process lifetime."""

import argparse
import ctypes
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import signal
import socket
import subprocess
import struct
import time


class RSP:
    def __init__(self, port):
        self.sock = socket.create_connection(("127.0.0.1", port), timeout=5)
        self.buf = b""
        self.sock.sendall(b"+")  # ares TCP security handshake requires this first.

    def send(self, text):
        data = text.encode()
        self.sock.sendall(b"$"+data+b"#"+f"{sum(data)&255:02x}".encode())

    def receive(self):
        while True:
            start = self.buf.find(b"$")
            end = self.buf.find(b"#", max(0, start))
            if start >= 0 and end >= 0 and len(self.buf) >= end+3:
                result = self.buf[start+1:end]
                checksum = int(self.buf[end+1:end+3], 16)
                self.buf = self.buf[end+3:]
                if sum(result)&255 != checksum:
                    raise ValueError("Invalid debugger packet checksum")
                self.sock.sendall(b"+")
                return result.decode()
            data = self.sock.recv(65536)
            if not data:
                raise RuntimeError("Debugger disconnected")
            self.buf += data

    def command(self, text):
        self.send(text)
        return self.receive()

    def read_memory(self, address, length):
        """Return exact bytes despite ares' aligned short-read optimisation."""
        if length < 1 or address < 0 or address+length > 0x100000000:
            raise ValueError("Invalid debugger memory range")
        start = address & ~3
        size = (address-start+length+3) & ~3
        data = bytes.fromhex(self.command(f"m{start:x},{size:x}"))
        if len(data) != size:
            raise ValueError("Truncated debugger memory read")
        return data[address-start:address-start+length]

    def write_memory(self, address, data):
        """Use byte edges and aligned bulk writes, without rewriting neighbours."""
        if not data or address < 0 or address+len(data) > 0x100000000:
            raise ValueError("Invalid debugger memory range")
        offset = 0
        while offset < len(data):
            count = ((len(data)-offset) & ~3) if (address+offset) % 4 == 0 else 1
            count = max(1, count)
            part = data[offset:offset+count]
            if self.command(f"M{address+offset:x},{count:x}:{part.hex()}") != "OK":
                raise ValueError("Debugger rejected test RAM write")
            offset += count

    def call(self, address, arguments):
        """Test-only o32 call in module scratch RAM; leaves the game paused.

        A checkpoint must restore the complete emulated machine afterwards.
        Bulk register packets avoid the scalar-register indexing discrepancy in
        the installed ares build. No game save is used or modified by this API.
        """
        address = int(address, 16)
        arguments = [int(value, 16) if isinstance(value, str) else value for value in arguments]
        if (address % 4 or not 0x80051A80 <= address < 0x801968E0 or len(arguments) > 9
                or any(not 0 <= value <= 0xFFFFFFFF for value in arguments)):
            raise ValueError("Invalid test function or o32 arguments")
        self.command("?")
        header = self.read_memory(0x801948E0, 20)
        magic, abi, reserved, used, ready = struct.unpack(">5I", header)
        if (magic, abi, reserved, ready) != (0x41465254, 1, 0x4000, 1) or used > 0x2000:
            raise ValueError("Module does not provide the required unused test scratch RAM")
        before = self.command("g")
        if len(before) != 71*16 or int(before[:16], 16):
            raise ValueError("Unknown debugger bulk register layout")
        registers = [int(before[i:i+16], 16) for i in range(0, len(before), 16)]
        stack = 0x80198880
        expected = dict(zip(range(4, 8), arguments[:4]))
        expected.update({29: stack, 31: 0x801968E0, 37: address})
        if len(arguments) > 4:
            outgoing = b"".join(struct.pack(">I", value) for value in arguments[4:])
            self.write_memory(stack+16, outgoing)
        for index, value in expected.items():
            registers[index] = value | (0xFFFFFFFF00000000 if value & 0x80000000 else 0)
        breakpoint = "0,801968e0,4"
        if self.command("Z"+breakpoint) != "OK":
            raise ValueError("Debugger rejected test return breakpoint")
        try:
            if self.command("G"+"".join(f"{value:016x}" for value in registers)) != "OK":
                raise ValueError("Debugger rejected test registers")
            observed = self.command("g")
            if any(int(observed[i*16:(i+1)*16], 16) != registers[i] for i in expected):
                raise ValueError("Debugger did not apply test argument/stack/PC registers")
            stopped = self.command("c")
            after = self.command("g")
            values = [int(after[i:i+16], 16) for i in range(0, len(after), 16)]
            if stopped[:3] not in ("T05", "S05") or values[37] & 0xFFFFFFFF != 0x801968E0:
                stack_dump = self.read_memory(stack-0x100, 0x180).hex()
                raise ValueError(f"Test function stopped unexpectedly: {stopped}, "
                                 f"PC={values[37]:016X}, SP={values[29]:016X}, RA={values[31]:016X}, "
                                 f"before_registers={before}, after_registers={after}, "
                                 f"scratch_stack={stack_dump}")
            if values[29] & 0xFFFFFFFF != stack:
                raise ValueError("Test function did not restore its stack")
            return {"test_only_function_call": f"{address:08X}", "arguments": arguments,
                    "return_value": values[2] & 0xFFFFFFFF, "return_breakpoint": "801968E0",
                    "stack_restored": True, "requires_checkpoint_restore": True}
        finally:
            self.command("z"+breakpoint)
            self.command("G"+before)


class Keyboard:
    def __init__(self, display):
        self.x11 = ctypes.CDLL("libX11.so.6")
        self.xtst = ctypes.CDLL("libXtst.so.6")
        self.x11.XOpenDisplay.argtypes = [ctypes.c_char_p]
        self.x11.XOpenDisplay.restype = ctypes.c_void_p
        self.x11.XStringToKeysym.argtypes = [ctypes.c_char_p]
        self.x11.XStringToKeysym.restype = ctypes.c_ulong
        self.x11.XKeysymToKeycode.argtypes = [ctypes.c_void_p, ctypes.c_ulong]
        self.x11.XKeysymToKeycode.restype = ctypes.c_uint
        self.x11.XFlush.argtypes = [ctypes.c_void_p]
        self.xtst.XTestFakeKeyEvent.argtypes = [ctypes.c_void_p, ctypes.c_uint,
                                               ctypes.c_int, ctypes.c_ulong]
        self.display = self.x11.XOpenDisplay(display.encode())
        if not self.display:
            raise RuntimeError("Cannot open isolated X display")

    def press(self, name, duration=0.15):
        names = [name] if isinstance(name, str) else name
        keys = [self.x11.XKeysymToKeycode(self.display, self.x11.XStringToKeysym(n.encode()))
                for n in names]
        if not keys or not all(keys):
            raise ValueError(f"Unknown key: {name}")
        for key in keys:
            self.xtst.XTestFakeKeyEvent(self.display, key, 1, 0)
        self.x11.XFlush(self.display)
        time.sleep(duration)
        for key in reversed(keys):
            self.xtst.XTestFakeKeyEvent(self.display, key, 0, 0)
        self.x11.XFlush(self.display)


def expand_actions(actions):
    for action in actions:
        if "repeat" in action:
            if not 1 <= action["repeat"] <= 100:
                raise ValueError("Invalid scenario repetition count")
            for index in range(action["repeat"]):
                for child in action["actions"]:
                    child = dict(child)
                    if "capture" in child:
                        child["capture"] = child["capture"].format(index=index)
                    yield child
        else:
            yield action


def message_snapshot(debug):
    pointer = int.from_bytes(debug.read_memory(0x8014241C, 4), "big")
    if not 0x80000000 <= pointer <= 0x803FFBF0:
        return {"message_pointer": f"{pointer:08X}", "status": "not_loaded"}
    header = debug.read_memory(pointer, 16)
    loaded, number, length, cut = struct.unpack(">4I", header)
    result = {"message_pointer": f"{pointer:08X}", "loaded": loaded,
              "message_id": f"{number:04X}", "length": length, "cut": cut}
    if loaded and 0 < length <= 1024:
        result["data"] = debug.read_memory(pointer+16, length).hex()
    return result


def player_snapshot(debug):
    """Read the native player actor; never change position or progression."""
    def read(address, length):
        data = debug.read_memory(address, length)
        if len(data) != length:
            raise ValueError("Truncated player state read")
        return data
    def pointer(address, size):
        value = struct.unpack(">I", read(address, 4))[0]
        if value % 4 or not 0x80000000 <= value <= 0x80400000-size:
            raise ValueError("No valid loaded player/game pointer")
        return value
    game = pointer(0x8010EF90, 0x1C94)
    player = pointer(game+0x1C90, 0x3C)
    state = read(player, 0x3C)
    if state[2] != 2:
        raise ValueError("Loaded actor is not the player")
    position = struct.unpack_from(">3f", state, 0x28)
    if not all(math.isfinite(value) for value in position):
        raise ValueError("Invalid native player coordinates")
    return {"game_pointer": f"{game:08X}", "player_pointer": f"{player:08X}",
            "block_x": struct.unpack_from(">b", state, 8)[0],
            "block_z": struct.unpack_from(">b", state, 9)[0],
            "world_position": dict(zip(("x", "y", "z"), position)), "read_only": True}


def inventory_snapshot(debug):
    """Read the current native PrivateInfo without editing pockets or clothes."""
    pointer = int.from_bytes(debug.read_memory(0x80136FD8, 4), "big")
    if pointer % 4 or not 0x80000000 <= pointer <= 0x80400000-0xBD0:
        raise ValueError("No valid loaded private-info pointer")
    data = debug.read_memory(pointer, 0xA7A)
    if data[0x10] > 1 or data[0x11] > 7:
        raise ValueError("Invalid native private-info identity")
    pockets = struct.unpack_from(">15H", data, 0x14)
    conditions, wallet, loan = struct.unpack_from(">3I", data, 0x34)
    cloth_id, cloth_item = struct.unpack_from(">2H", data, 0xA76)
    return {"private_pointer": f"{pointer:08X}", "pockets": [f"{item:04X}" for item in pockets],
            "item_conditions": [(conditions >> (slot*2)) & 3 for slot in range(15)],
            "wallet": wallet, "loan": loan, "cloth_id": f"{cloth_id:04X}",
            "cloth_item": f"{cloth_item:04X}", "read_only": True}


def keyboard_snapshot(debug):
    """Locate the English-first overlay in four-MiB RAM and read its state."""
    marker = bytes.fromhex("A0660000A0660001A060000224190300A4790004A4780006")
    matches = []
    previous = b""
    for address in range(0x80200000, 0x80400000, 0x10000):
        chunk = debug.read_memory(address, 0x10000)
        if len(chunk) != 0x10000:
            raise ValueError("Truncated keyboard RAM search")
        data = previous+chunk
        offset = data.find(marker)
        while offset >= 0:
            matches.append(address-len(previous)+offset-0x760)
            offset = data.find(marker, offset+1)
        previous = data[-(len(marker)-1):]
    if len(matches) != 1:
        raise ValueError(f"Expected one loaded English keyboard overlay, found {len(matches)}")
    base = matches[0]
    state = debug.read_memory(base+0x39B0, 48)
    pointer = struct.unpack_from(">I", state, 0x24)[0]
    columns, rows, length = struct.unpack_from(">3h", state, 0x18)
    if not (1 <= rows <= 16 and 1 <= columns <= 96 and 0 <= length <= rows*columns <= 1024):
        raise ValueError("Invalid keyboard state dimensions")
    if not 0x80000000 <= pointer <= 0x80400000-rows*columns:
        raise ValueError("Invalid keyboard string pointer")
    return {"keyboard_base": f"{base:08X}", "mode": state[4],
            "cursor": struct.unpack_from(">h", state, 0x16)[0],
            "rows": rows, "columns": columns, "length": length,
            "text_hex": debug.read_memory(pointer, rows*columns).hex()}


def choice_snapshot(debug):
    """Read the opt-in English runtime's singleton choice window and rows."""
    from english_runtime import ChoiceLayout, split_address
    layout = ChoiceLayout()
    header = debug.read_memory(0x801948E0, 56)
    if header[:4] == b"AFRT" and header[40:44] == bytes.fromhex("00000014"):
        candidate = ChoiceLayout(*struct.unpack_from(">4I", header, 40))
        high, low = split_address(candidate.rows)
        # A module can be built without enabling the expanded choice patches.
        instructions = struct.pack(">2I", 0x3C030000 | high, 0x24630000 | low)
        if debug.read_memory(0x80065208, 8) == instructions:
            layout = candidate
    state = debug.read_memory(0x801425C0, 0xBC)
    lengths = list(struct.unpack_from(">4i", state, 0x5C))
    selected_length, count, last_selected, cursor = struct.unpack_from(">4i", state, 0x78)
    if (not 0 <= count <= 4 or not 0 <= selected_length <= layout.capacity
            or any(not 0 <= n <= layout.capacity for n in lengths[:count])):
        raise ValueError("Invalid expanded choice dimensions")
    rows = debug.read_memory(layout.rows, 4*layout.stride)
    selected = debug.read_memory(layout.selected, layout.capacity)
    return {"choice_count": count, "choice_lengths": lengths[:count],
            "choice_capacity": layout.capacity, "choice_stride": layout.stride,
            "choice_hex": [rows[i*layout.stride:i*layout.stride+lengths[i]].hex() for i in range(count)],
            "selected_length": selected_length, "selected_hex": selected[:selected_length].hex(),
            "last_selected": last_selected, "choice_cursor": cursor,
            "choice_state": struct.unpack_from(">i", state, 0x9C)[0]}


def advance_to_choice(debug, keyboard, options, record, pause=time.sleep):
    """Advance at most the declared page count, never confirm an active menu."""
    maximum = options.get("max_presses", 40)
    settle = options.get("settle_seconds", 3)
    if type(maximum) is not int or not 1 <= maximum <= 100:
        raise ValueError("Invalid advance-to-choice press limit")
    if not isinstance(settle, (int, float)) or not 0.1 <= settle <= 10:
        raise ValueError("Invalid advance-to-choice settling time")
    for pressed in range(maximum+1):
        pause(settle)
        message = message_snapshot(debug)
        choice = choice_snapshot(debug)
        record(message)
        record(choice)
        if choice["choice_state"] == 2 and choice["choice_count"] > 0:
            record({"advanced_to_active_choice": True, "presses": pressed,
                    "message_id": message.get("message_id")})
            return
        if pressed < maximum:
            keyboard.press("a", 0.08)
    raise ValueError("No active choice within the declared page-advance limit")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rom", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--xvfb", default=os.environ.get("AF_XVFB", "Xvfb"))
    parser.add_argument("--ares", default="/usr/bin/ares")
    parser.add_argument("--seconds", type=int, default=40)
    parser.add_argument("--scenario", type=Path)
    parser.add_argument("--post-scenario", type=Path, help="Additional assertions after the main scenario")
    parser.add_argument("--port", type=int, default=19264)
    parser.add_argument("--seed-save", type=Path, help="Copy this isolated test directory's cartridge saves")
    parser.add_argument("--seed-state", type=Path, help="Resume this isolated test directory's matching-ROM state")
    args = parser.parse_args()
    if args.seed_save and args.seed_state:
        parser.error("choose cartridge saves or a matching-ROM state, not both")
    if not 1 <= args.seconds <= 600:
        parser.error("seconds must be between 1 and 600")
    if args.output.exists():
        parser.error("output must be a fresh directory to isolate saves")
    out = args.output.resolve()
    out.mkdir(parents=True)
    rom = out / "test.z64"
    shutil.copyfile(args.rom, rom)
    rom_hash = hashlib.sha256(rom.read_bytes()).hexdigest()
    provenance = {"rom_sha256": rom_hash, "seed_files": [], "audio": "disabled", "expansion_pak": False,
                  "runner_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                  "scenario_sha256": hashlib.sha256(args.scenario.read_bytes()).hexdigest() if args.scenario else None,
                  "post_scenario_sha256": hashlib.sha256(args.post_scenario.read_bytes()).hexdigest()
                  if args.post_scenario else None}
    if args.seed_state:
        source_rom = args.seed_state / "test.z64"
        if not source_rom.is_file() or hashlib.sha256(source_rom.read_bytes()).hexdigest() != rom_hash:
            parser.error("save states require the identical test ROM; use cartridge saves for cross-build tests")
    seed = args.seed_state or args.seed_save
    if seed:
        for suffix in ("flash", "rtc", "pak") + (("bs1",) if args.seed_state else ()):
            source = seed / ("test."+suffix)
            if not source.is_file():
                if suffix in ("flash", "bs1"):
                    parser.error(f"missing seed file: {source}")
                continue
            content = source.read_bytes()
            if not content or len(content) > 128*1024*1024:
                parser.error(f"invalid seed file size: {source}")
            shutil.copyfile(source, out/source.name)
            provenance["seed_files"].append({"file": source.name, "sha256": hashlib.sha256(content).hexdigest(),
                                             "bytes": len(content)})
    (out/"run.json").write_text(json.dumps(provenance, indent=2)+"\n")
    settings = out / "settings.bml"
    settings.write_text("Video\n  Driver: OpenGL 3.2\n  Multiplier: 2\n"
                        "Audio\n  Driver: None\n  Mute: true\n  Volume: 0.0\n"
                        "Input\n  Driver: SDL\n  Defocus: Allow\n"
                        "General\n  NoFilePrompt: true\n  AutoSaveMemory: true\n"
                        "Hotkey\n  SaveState: 0x1/0/5;;\n  LoadState: 0x1/0/6;;\n"
                        "  QuitEmulator: 0x1/0/12;;\n"
                        "Nintendo64\n  ExpansionPak: false\n"
                        "  Input\n    Controller.Port.1\n      Gamepad\n"
                        "        A: 0x1/0/35;;\n        B: 0x1/0/36;;\n"
                        "        Start: 0x1/0/89;;\n"
                        "        Z: 0x1/0/60;;\n"
                        "        L: 0x1/0/51;;\n        R: 0x1/0/52;;\n"
                        "        X-Axis\n          Lo: 0x1/0/40;;\n          Hi: 0x1/0/41;;\n"
                        "        Y-Axis\n          Lo: 0x1/0/57;;\n          Hi: 0x1/0/53;;\n"
                        "        C-Up: 0x1/0/55;;\n        C-Down: 0x1/0/44;;\n"
                        "        C-Left: 0x1/0/42;;\n        C-Right: 0x1/0/45;;\n"
                        "        Up: 0x1/0/84;;\n        Down: 0x1/0/85;;\n"
                        "        Left: 0x1/0/86;;\n        Right: 0x1/0/87;;\n")
    logs, processes, debug = [], [], None
    readfd, writefd = os.pipe()
    try:
        log = (out / "xvfb.log").open("wb")
        logs.append(log)
        xvfb = subprocess.Popen(["timeout", "-s", "KILL", str(args.seconds+30), args.xvfb,
                                  "-displayfd", str(writefd), "-screen", "0", "800x640x24", "-nolisten", "tcp"],
                                 pass_fds=(writefd,), stdout=log, stderr=log, start_new_session=True)
        processes.append(xvfb)
        os.close(writefd)
        display_number = os.read(readfd, 32).decode().strip()
        os.close(readfd)
        if not display_number.isdigit():
            raise RuntimeError("Xvfb failed to start; see xvfb.log")
        display = ":"+display_number
        env = dict(os.environ, DISPLAY=display, GDK_BACKEND="x11",
                   SDL_AUDIODRIVER="dummy", PULSE_SERVER="unix:/nonexistent-af-audio")
        env.pop("WAYLAND_DISPLAY", None)
        log = (out / "ares.log").open("wb")
        logs.append(log)
        command = ["timeout", "-s", "KILL", str(args.seconds+10), args.ares,
                   "--settings-file", str(settings), "--no-file-prompt", "--system", "Nintendo 64",
                   "--setting", "Audio/Driver=None", "--setting", "Audio/Mute=true",
                   "--setting", "DebugServer/Enabled=true", "--setting", "DebugServer/UseIPv4=true",
                   "--setting", f"DebugServer/Port={args.port}",
                   "--setting", "Nintendo64/ExpansionPak=false", str(rom)]
        if args.seed_state:
            command[5:5] = ["--save-state", "1"]
        ares = subprocess.Popen(command, env=env, stdout=log, stderr=log, start_new_session=True)
        processes.append(ares)
        time.sleep(3)
        results = [{"rom_sha256": hashlib.sha256(rom.read_bytes()).hexdigest(),
                    "audio": "disabled", "expansion_pak": False,
                    "scenario": str(args.scenario) if args.scenario else "default"}]
        subprocess.run(["ffmpeg", "-nostdin", "-loglevel", "error", "-f", "x11grab",
                        "-video_size", "800x640", "-i", display, "-frames:v", "1", str(out / "initial.png")],
                       env=env, check=True, timeout=15, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        debug = RSP(args.port)
        results.append({"debug_features": debug.command("qSupported:multiprocess+")})
        keyboard = Keyboard(display)
        actions = json.loads(args.scenario.read_text()) if args.scenario else [
            {"wait": args.seconds-5}, {"capture": "boot.png"},
            {"read": ["80090294", 4]}, {"read": ["80106AF4", 256]},
            {"read": ["8013A680", 32]}]
        if args.post_scenario:
            actions += json.loads(args.post_scenario.read_text())
        needs_checkpoint_restore = False
        def record(snapshot):
            results.append(snapshot)
            (out / "results.json").write_text(json.dumps(results, indent=2)+"\n")
        for action in expand_actions(actions):
            if "wait" in action:
                time.sleep(max(0, min(action["wait"], 60)))
            if "key" in action:
                keyboard.press(action["key"], action.get("duration", 0.15))
            if "advance_to_choice" in action:
                advance_to_choice(debug, keyboard, action["advance_to_choice"], record)
            if "read" in action:
                address, length = action["read"]
                data = debug.read_memory(int(address, 16), length).hex()
                if len(data) != length*2:
                    raise ValueError("Debugger memory read length mismatch")
                if "expect" in action and data.lower() != action["expect"].lower():
                    raise ValueError(f"Runtime assertion failed at {address}: {data}")
                results.append({"read": action["read"], "data": data,
                                "assertion": "passed" if "expect" in action else "not_requested"})
            if "command" in action:
                results.append({"command": action["command"], "result": debug.command(action["command"])})
            if "write" in action:
                address, value = action["write"]
                data = bytes.fromhex(value)
                location = int(address, 16)
                if not data or not 0x80000000 <= location <= 0x80400000-len(data):
                    raise ValueError("Scenario writes must stay inside four-MiB test RAM")
                debug.write_memory(location, data)
                results.append({"test_only_ram_write": address, "bytes": len(data), "data": data.hex()})
            if action.get("resume"):
                debug.send("c")  # Stop-mode RSP replies only on a later halt.
            if "call" in action:
                if not (out/"test.bs1").is_file():
                    raise ValueError("Test function calls require a saved emulator checkpoint")
                call = action["call"]
                result = debug.call(call["address"], call.get("arguments", []))
                needs_checkpoint_restore = True
                results.append(result)
                if "expect_return" in call and result["return_value"] != call["expect_return"]:
                    raise ValueError(f"Unexpected function return: {result['return_value']}")
            if action.get("snapshot_message"):
                snapshot = message_snapshot(debug)
                results.append(snapshot)
                if "expect_message" in action and snapshot.get("message_id") != action["expect_message"]:
                    raise ValueError(f"Unexpected message: {snapshot.get('message_id')}")
            if action.get("snapshot_player"):
                results.append(player_snapshot(debug))
            if action.get("snapshot_inventory"):
                snapshot = inventory_snapshot(debug)
                results.append(snapshot)
                for field, expected in action.get("expect_inventory", {}).items():
                    if snapshot.get(field) != expected:
                        raise ValueError(f"Inventory {field}: {snapshot.get(field)!r}, expected {expected!r}")
            if action.get("snapshot_keyboard"):
                snapshot = keyboard_snapshot(debug)
                results.append(snapshot)
                for field, expected in action.get("expect_keyboard", {}).items():
                    if snapshot.get(field) != expected:
                        raise ValueError(f"Keyboard {field}: {snapshot.get(field)!r}, expected {expected!r}")
            if action.get("snapshot_choices"):
                snapshot = choice_snapshot(debug)
                results.append(snapshot)
                for field, expected in action.get("expect_choices", {}).items():
                    if snapshot.get(field) != expected:
                        raise ValueError(f"Choice {field}: {snapshot.get(field)!r}, expected {expected!r}")
            if "capture" in action:
                target = out / Path(action["capture"]).name
                subprocess.run(["ffmpeg", "-nostdin", "-loglevel", "error", "-f", "x11grab",
                                "-video_size", "800x640", "-i", display, "-frames:v", "1", str(target)],
                               env=env, check=True, timeout=15, stdout=subprocess.DEVNULL,
                               stderr=subprocess.PIPE)
                results.append({"capture": target.name})
            if action.get("save_state"):
                keyboard.press("F5", 0.08)
                time.sleep(1)
                state = out/"test.bs1"
                if not state.is_file() or state.stat().st_size < 1024:
                    raise ValueError("Emulator did not create the requested checkpoint state")
                results.append({"state_file": state.name, "bytes": state.stat().st_size,
                                "sha256": hashlib.sha256(state.read_bytes()).hexdigest(),
                                "kind": "emulator_checkpoint_not_game_save_validation"})
            if action.get("load_state"):
                if not (out/"test.bs1").is_file():
                    raise ValueError("Missing emulator checkpoint")
                keyboard.press("F6", 0.08)
                time.sleep(1)
                results.append({"loaded_state": "test.bs1"})
                needs_checkpoint_restore = False
            (out / "results.json").write_text(json.dumps(results, indent=2)+"\n")
        if needs_checkpoint_restore:
            raise ValueError("Test function calls must finish by restoring the emulator checkpoint")
        # Register numbering has changed across ares builds; retain the raw
        # response without claiming this is a trustworthy PC measurement.
        results.append({"raw_register_p25": debug.command("p25"), "process_alive": ares.poll() is None})
        debug.sock.close()
        debug = None
        keyboard.press("F12", 0.08)
        status = ares.wait(timeout=10)
        if status != 0:
            raise ValueError(f"Emulator failed graceful shutdown: {status}")
        results.append({"graceful_shutdown": True, "save_files": [
            {"file": p.name, "bytes": p.stat().st_size, "sha256": hashlib.sha256(p.read_bytes()).hexdigest()}
            for p in (out/"test.flash", out/"test.rtc", out/"test.pak") if p.is_file()]})
        (out / "results.json").write_text(json.dumps(results, indent=2)+"\n")
        print(json.dumps({"output": str(out), "steps": len(results)}, indent=2))
    finally:
        if debug:
            debug.sock.close()
        for process in reversed(processes):
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            process.wait(timeout=5)
        for log in logs:
            log.close()


if __name__ == "__main__":
    main()
