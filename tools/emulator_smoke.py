#!/usr/bin/env python3
"""Silent ares tests on an isolated X display, with bounded process lifetime."""

import argparse
import ctypes
import json
import os
from pathlib import Path
import shutil
import signal
import socket
import subprocess
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
        key = self.x11.XKeysymToKeycode(self.display, self.x11.XStringToKeysym(name.encode()))
        if not key:
            raise ValueError(f"Unknown key: {name}")
        self.xtst.XTestFakeKeyEvent(self.display, key, 1, 0)
        self.x11.XFlush(self.display)
        time.sleep(duration)
        self.xtst.XTestFakeKeyEvent(self.display, key, 0, 0)
        self.x11.XFlush(self.display)


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
        results = []
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
        for action in actions:
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
            if "capture" in action:
                target = out / Path(action["capture"]).name
                subprocess.run(["ffmpeg", "-nostdin", "-loglevel", "error", "-f", "x11grab",
                                "-video_size", "800x640", "-i", display, "-frames:v", "1", str(target)],
                               env=env, check=True, timeout=15, stdout=subprocess.DEVNULL,
                               stderr=subprocess.PIPE)
                results.append({"capture": target.name})
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
