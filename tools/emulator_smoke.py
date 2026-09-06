#!/usr/bin/env python3
"""Silent ares tests on an isolated X display, with bounded process lifetime."""

import argparse
import ctypes
import hashlib
import json
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
    pointer = int(debug.command("m8014241c,4"), 16)
    if not 0x80000000 <= pointer <= 0x803FFBF0:
        return {"message_pointer": f"{pointer:08X}", "status": "not_loaded"}
    header = bytes.fromhex(debug.command(f"m{pointer:x},10"))
    loaded, number, length, cut = struct.unpack(">4I", header)
    result = {"message_pointer": f"{pointer:08X}", "loaded": loaded,
              "message_id": f"{number:04X}", "length": length, "cut": cut}
    if loaded and 0 < length <= 1024:
        result["data"] = debug.command(f"m{pointer+16:x},{length:x}")
    return result


def keyboard_snapshot(debug):
    """Locate the English-first overlay in four-MiB RAM and read its state."""
    marker = bytes.fromhex("A0660000A0660001A060000224190300A4790004A4780006")
    matches = []
    previous = b""
    for address in range(0x80200000, 0x80400000, 0x10000):
        chunk = bytes.fromhex(debug.command(f"m{address:x},10000"))
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
    state = bytes.fromhex(debug.command(f"m{base+0x39b0:x},30"))
    pointer = struct.unpack_from(">I", state, 0x24)[0]
    rows, columns, length = struct.unpack_from(">3h", state, 0x18)
    if not (1 <= rows <= 16 and 1 <= columns <= 96 and 0 <= length <= rows*columns <= 1024):
        raise ValueError("Invalid keyboard state dimensions")
    if not 0x80000000 <= pointer <= 0x80400000-rows*columns:
        raise ValueError("Invalid keyboard string pointer")
    return {"keyboard_base": f"{base:08X}", "mode": state[4],
            "cursor": struct.unpack_from(">h", state, 0x16)[0],
            "rows": rows, "columns": columns, "length": length,
            "text_hex": debug.command(f"m{pointer:x},{rows*columns:x}")}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rom", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--xvfb", default=os.environ.get("AF_XVFB", "Xvfb"))
    parser.add_argument("--ares", default="/usr/bin/ares")
    parser.add_argument("--seconds", type=int, default=40)
    parser.add_argument("--scenario", type=Path)
    parser.add_argument("--port", type=int, default=19264)
    args = parser.parse_args()
    if not 1 <= args.seconds <= 600:
        parser.error("seconds must be between 1 and 600")
    if args.output.exists():
        parser.error("output must be a fresh directory to isolate saves")
    out = args.output.resolve()
    out.mkdir(parents=True)
    rom = out / "test.z64"
    shutil.copyfile(args.rom, rom)
    settings = out / "settings.bml"
    settings.write_text("Video\n  Driver: OpenGL 3.2\n  Multiplier: 2\n"
                        "Audio\n  Driver: None\n  Mute: true\n  Volume: 0.0\n"
                        "Input\n  Driver: SDL\n  Defocus: Allow\n"
                        "General\n  NoFilePrompt: true\n"
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
        for action in expand_actions(actions):
            if "wait" in action:
                time.sleep(max(0, min(action["wait"], 60)))
            if "key" in action:
                keyboard.press(action["key"], action.get("duration", 0.15))
            if "read" in action:
                address, length = action["read"]
                data = debug.command(f"m{address},{length:x}")
                if len(data) != length*2:
                    raise ValueError("Debugger memory read length mismatch")
                if "expect" in action and data.lower() != action["expect"].lower():
                    raise ValueError(f"Runtime assertion failed at {address}: {data}")
                results.append({"read": action["read"], "data": data,
                                "assertion": "passed" if "expect" in action else "not_requested"})
            if "command" in action:
                results.append({"command": action["command"], "result": debug.command(action["command"])})
            if action.get("snapshot_message"):
                snapshot = message_snapshot(debug)
                results.append(snapshot)
                if "expect_message" in action and snapshot.get("message_id") != action["expect_message"]:
                    raise ValueError(f"Unexpected message: {snapshot.get('message_id')}")
            if action.get("snapshot_keyboard"):
                snapshot = keyboard_snapshot(debug)
                results.append(snapshot)
                for field, expected in action.get("expect_keyboard", {}).items():
                    if snapshot.get(field) != expected:
                        raise ValueError(f"Keyboard {field}: {snapshot.get(field)!r}, expected {expected!r}")
            if "capture" in action:
                target = out / Path(action["capture"]).name
                subprocess.run(["ffmpeg", "-nostdin", "-loglevel", "error", "-f", "x11grab",
                                "-video_size", "800x640", "-i", display, "-frames:v", "1", str(target)],
                               env=env, check=True, timeout=15, stdout=subprocess.DEVNULL,
                               stderr=subprocess.PIPE)
                results.append({"capture": target.name})
            (out / "results.json").write_text(json.dumps(results, indent=2)+"\n")
        # Register numbering has changed across ares builds; retain the raw
        # response without claiming this is a trustworthy PC measurement.
        results.append({"raw_register_p25": debug.command("p25"), "process_alive": ares.poll() is None})
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
