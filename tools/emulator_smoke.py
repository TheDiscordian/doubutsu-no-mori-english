#!/usr/bin/env python3
"""Silent ares tests on an isolated X display, with bounded process lifetime."""

import argparse
from contextlib import contextmanager
import ctypes
import fcntl
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
from runtime_layout import MODULE_RAM, RESERVATION, LINKED_LIMIT, TEST_RETURN, TEST_STACK


@contextmanager
def reserve_x_display(tmp=Path("/tmp")):
    """Serialize startup and choose a display without touching existing sockets."""
    # Xvfb's automatic -displayfd allocation can replace a live filesystem
    # socket when its server does not also publish an abstract socket.
    allocation_lock = tmp / f"af-xvfb-allocation-{os.getuid()}.lock"
    fd = os.open(allocation_lock, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, "w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        for number in range(200, 1000):
            paths = (tmp/f".X{number}-lock", tmp/f".X11-unix/X{number}",
                     tmp/f".X11-unix/X{number}_")
            if any(os.path.lexists(path) for path in paths):
                continue
            yield str(number)
            return
        raise RuntimeError("No unused test X display available between :200 and :999")


def write_results(directory, results):
    """Publish one complete result snapshot for concurrent read-only observers."""
    temporary = directory/"results.json.tmp"
    temporary.write_text(json.dumps(results, indent=2)+"\n")
    temporary.replace(directory/"results.json")


def require_program_counter(registers, expected):
    if (not isinstance(registers,str) or len(registers) != 71*16
            or any(c not in '0123456789abcdefABCDEF' for c in registers)):
        raise ValueError('Unknown debugger bulk register layout for PC assertion')
    target = int(expected,16)
    actual = int(registers[37*16:38*16],16)&0xFFFFFFFF
    if actual != target:
        raise ValueError(f'Unexpected observed PC: {actual:08X}, expected {target:08X}')
    return f'{actual:08X}'


class RSP:
    def __init__(self, port, timeout=5):
        self.sock = socket.create_connection(("127.0.0.1", port), timeout=timeout)
        self.buf = b""
        try:
            self.sock.sendall(b"+")  # ares TCP security handshake requires this first.
        except OSError:
            self.sock.close()
            raise

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
        # The eight-byte fast path also aligns down, including cached accesses.
        start = address & ~7
        size = (address-start+length+7) & ~7
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
            if count == 8 and (address+offset) % 8:
                count = 4
            part = data[offset:offset+count]
            if self.command(f"M{address+offset:x},{count:x}:{part.hex()}") != "OK":
                raise ValueError("Debugger rejected test RAM write")
            offset += count

    def thread_snapshot(self):
        pointer = struct.unpack(">I", self.read_memory(0x8003CE30, 4))[0]
        if pointer % 8 or not 0x80000000 <= pointer <= 0x80400000-0x1B0:
            raise ValueError("Invalid running-thread pointer")
        data = self.read_memory(pointer, 24)
        return {"pointer": f"{pointer:08X}", "state": struct.unpack_from(">H", data, 16)[0],
                "id": struct.unpack_from(">I", data, 20)[0]}

    def pause_game_thread(self):
        """Stop at the graph thread's frame entry before constructing fixtures.

        Arbitrary pause usually lands in the idle loop. Injecting a synchronous
        DMA there can block the sole idle thread and empty the run queue.
        """
        self.command("?")
        before = self.command("g")
        if len(before) != 71*16:
            raise ValueError("Unknown debugger bulk register layout")
        origin = {"pc": before[37*16:38*16], "thread": self.thread_snapshot()}
        if self.read_memory(0x800D334C, 4) != bytes.fromhex("27BDFFE0"):
            raise ValueError("Native game-frame entry guard does not match")
        breakpoint = "0,800d334c,4"
        if self.command("Z"+breakpoint) != "OK":
            raise ValueError("Debugger rejected game-thread breakpoint")
        try:
            stopped = self.command("c")
            registers = self.command("g")
            thread = self.thread_snapshot()
            if (stopped[:3] not in ("T05", "S05") or len(registers) != 71*16
                    or int(registers[37*16:38*16], 16) & 0xFFFFFFFF != 0x800D334C
                    or thread != {"pointer": "80145630", "state": 4, "id": 4}):
                raise ValueError("Could not establish the native graph-thread test context")
            return {"test_call_context": "native_graph_frame_entry", "pc": "800D334C",
                    "thread": thread, "previous_context": origin}
        finally:
            self.command("z"+breakpoint)

    def advance_game_frame(self):
        """Execute past the current entry before waiting for the next frame.

        Installing the entry breakpoint while already stopped there can stop
        immediately again. The second instruction provides a guarded waypoint;
        no register, instruction, or game-state writes simulate frame progress.
        """
        self.command('?')
        require_program_counter(self.command('g'),'800D334C')
        if self.thread_snapshot() != {'pointer':'80145630','state':4,'id':4}:
            raise ValueError('Frame advancement requires the native graph thread')
        if self.read_memory(0x800D334C,8) != bytes.fromhex('27BDFFE0AFB00014'):
            raise ValueError('Native frame advancement instruction guard does not match')
        breakpoint = '0,800d3350,4'
        if self.command('Z'+breakpoint) != 'OK':
            raise ValueError('Debugger rejected frame advancement breakpoint')
        try:
            stopped = self.command('c')
            if stopped[:3] not in ('T05','S05'):
                raise ValueError('Native frame advancement stopped unexpectedly')
            require_program_counter(self.command('g'),'800D3350')
        finally:
            self.command('z'+breakpoint)
        return {'advanced_native_graph_frame':True,**self.pause_game_thread()}

    def call(self, address, arguments, *, return_address=TEST_RETURN, verified_code=None):
        """Test-only o32 call in module scratch RAM; leaves the game paused.

        A checkpoint must restore the complete emulated machine afterwards.
        Bulk register packets avoid the scalar-register indexing discrepancy in
        the installed ares build. Save-writing scenarios additionally require an
        isolated blank cartridge and explicit runner opt-in before invoking I/O.
        """
        address = int(address, 16)
        if isinstance(return_address, str):
            return_address = int(return_address, 16)
        if (type(return_address) is not int or return_address % 4
                or not TEST_RETURN <= return_address <= TEST_STACK-0x100):
            raise ValueError('Test return breakpoint must remain inside isolated scratch RAM')
        arguments = [int(value, 16) if isinstance(value, str) else value for value in arguments]
        if (address % 4 or len(arguments) > 9
                or any(not 0 <= value <= 0xFFFFFFFF for value in arguments)):
            raise ValueError("Invalid test function or o32 arguments")
        if verified_code is None:
            if not 0x80051A80 <= address < TEST_RETURN:
                raise ValueError('Invalid test function or o32 arguments')
        else:
            # Only Python fixture helpers can supply this proof. Ordinary JSON
            # calls retain their original target restrictions. Compare complete
            # independently expected code, not a caller-supplied address alone.
            base, expected_code = verified_code
            if (type(base) is not int or base & 3 or type(expected_code) is not bytes
                    or not 4 <= len(expected_code) <= 0x20000 or len(expected_code) & 3
                    or not 0x80000400 <= base <= 0x80400000-len(expected_code)
                    or not base <= address <= base+len(expected_code)-4
                    or (base < MODULE_RAM+RESERVATION and base+len(expected_code) > MODULE_RAM)):
                raise ValueError('Invalid verified native code range')
        self.command("?")
        header = self.read_memory(MODULE_RAM, 20)
        magic, abi, reserved, used, ready = struct.unpack(">5I", header)
        if (magic, abi, reserved, ready) != (0x41465254, 1, RESERVATION, 1) or not 0x300 <= used <= LINKED_LIMIT:
            raise ValueError("Module does not provide the required unused test scratch RAM")
        if verified_code is None and address >= MODULE_RAM+used:
            raise ValueError("Native test target is outside linked module code")
        if verified_code is not None and self.read_memory(base,len(expected_code)) != expected_code:
            raise ValueError('Verified native code differs from resident instructions')
        before = self.command("g")
        if len(before) != 71*16 or int(before[:16], 16):
            raise ValueError("Unknown debugger bulk register layout")
        registers = [int(before[i:i+16], 16) for i in range(0, len(before), 16)]
        thread = self.thread_snapshot()
        if (registers[37] & 0xFFFFFFFF != 0x800D334C
                or thread != {"pointer": "80145630", "state": 4, "id": 4}):
            raise ValueError("Native calls require pause_game_thread before test fixture writes")
        stack = TEST_STACK
        expected = dict(zip(range(4, 8), arguments[:4]))
        expected.update({29: stack, 31: return_address, 37: address})
        if len(arguments) > 4:
            outgoing = b"".join(struct.pack(">I", value) for value in arguments[4:])
            self.write_memory(stack+16, outgoing)
        for index, value in expected.items():
            registers[index] = value | (0xFFFFFFFF00000000 if value & 0x80000000 else 0)
        breakpoint = f"0,{return_address:x},4"
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
            if stopped[:3] not in ("T05", "S05") or values[37] & 0xFFFFFFFF != return_address:
                stack_dump = self.read_memory(stack-0x100, 0x180).hex()
                raise ValueError(f"Test function stopped unexpectedly: {stopped}, "
                                 f"PC={values[37]:016X}, SP={values[29]:016X}, RA={values[31]:016X}, "
                                 f"before_registers={before}, after_registers={after}, "
                                 f"scratch_stack={stack_dump}")
            if values[29] & 0xFFFFFFFF != stack:
                raise ValueError("Test function did not restore its stack")
            return {"test_only_function_call": f"{address:08X}", "arguments": arguments,
                    "return_value": values[2] & 0xFFFFFFFF, "return_value_v1": values[3] & 0xFFFFFFFF,
                    "return_breakpoint": f"{return_address:08X}",
                    "stack_restored": True, "requires_checkpoint_restore": True, "thread": thread}
        finally:
            self.command("z"+breakpoint)
            self.command("G"+before)


def connect_debugger(process, port, seconds=15, *, connect=RSP, now=time.monotonic, pause=time.sleep):
    """Wait for this live emulator's debugger socket, never restart the process."""
    deadline = now()+seconds
    last_error = None
    while True:
        status = process.poll()
        if status is not None:
            raise RuntimeError(f"Emulator exited before debugger connection: {status}")
        remaining = deadline-now()
        if remaining <= 0:
            raise TimeoutError("Emulator debugger did not become ready") from last_error
        try:
            result = connect(port, timeout=min(1, remaining))
            # The connection budget must not become the later command timeout.
            result.sock.settimeout(5)
            return result
        except (ConnectionRefusedError, ConnectionResetError, TimeoutError) as error:
            last_error = error
            pause(min(0.1, max(0, deadline-now())))


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


def villagers_snapshot(debug):
    """Observe native village/home records; never mark greetings or move actors."""
    common = 0x80126EA0
    maximum = debug.read_memory(common+0x18, 1)[0]
    if maximum > 15:
        raise ValueError("Invalid native village population limit")
    animals = debug.read_memory(common+0x9F18, 15*0x528)
    listing = debug.read_memory(common+0x10160, 15*0x38)
    residents, seen = [], set()
    for slot in range(15):
        at, live = slot*0x528, slot*0x38
        npc = struct.unpack_from(">H", animals, at)[0]
        if npc >> 12 != 0xE:
            continue
        if npc & 0xFFF >= 216 or npc in seen:
            raise ValueError("Invalid or duplicate native villager ID")
        seen.add(npc)
        home = animals[at+0x4E0:at+0x4E5]
        resident = {"slot": slot, "npc_id": f"{npc:04X}", "name_id": animals[at+0x0A],
                    "personality": animals[at+0x0B],
                    "home": dict(zip(("type", "acre_x", "acre_z", "unit_x", "unit_z"), home)),
                    "is_home": animals[at+0x524], "moved_in": animals[at+0x525]}
        listed_npc, field = struct.unpack_from(">2H", listing, live)
        if listed_npc == npc:
            coordinates = struct.unpack_from(">6f", listing, live+4)
            if not all(math.isfinite(value) for value in coordinates):
                raise ValueError("Invalid recorded villager coordinates")
            resident.update(home_position=dict(zip(("x", "y", "z"), coordinates[:3])),
                            recorded_position=dict(zip(("x", "y", "z"), coordinates[3:])),
                            field_id=f"{field:04X}", appear_flag=listing[live+0x1C])
        residents.append(resident)
    return {"villagers": residents, "population_limit": maximum, "read_only": True,
            "position_source": "native NpcList; not a guarantee of current on-screen actor position"}


def npc_actors_snapshot(debug):
    """Read live NPC actors for navigation; no actor or schedule mutations."""
    def read(address, size):
        if address % 4 or not 0x80000000 <= address <= 0x80400000-size:
            raise ValueError("Invalid live NPC/game address")
        data = debug.read_memory(address, size)
        if len(data) != size:
            raise ValueError("Truncated live NPC read")
        return data
    game = struct.unpack(">I", read(0x8010EF90, 4))[0]
    count, actor = struct.unpack_from(">2I", read(game, 0x1C9C), 0x1C94)
    if count > 32:
        raise ValueError("Invalid live NPC actor count")
    seen, result = set(), []
    while actor:
        if actor in seen or len(seen) >= 32:
            raise ValueError("Cyclic or excessive live NPC actor list")
        seen.add(actor)
        data = read(actor, 0x178)
        if data[2] != 3:
            raise ValueError("Non-NPC actor in live NPC list")
        coordinates = struct.unpack_from(">3f", data, 0x28)
        if not all(math.isfinite(value) for value in coordinates):
            raise ValueError("Invalid live NPC coordinates")
        animal = struct.unpack_from(">I", data, 0x174)[0]
        row = {"actor_pointer": f"{actor:08X}", "fg_name": f"{struct.unpack_from('>H', data, 6)[0]:04X}",
               "world_position": dict(zip(("x", "y", "z"), coordinates)), "is_drawn": data[0xB5],
               "update_function": f"{struct.unpack_from('>I', data, 0x164)[0]:08X}"}
        if animal:
            row["animal_id"] = f"{struct.unpack_from('>H', read(animal, 12))[0]:04X}"
        result.append(row)
        actor = struct.unpack_from(">I", data, 0x158)[0]
    if len(result) != count:
        raise ValueError("Live NPC list count does not match traversal")
    return {"live_npc_actors": result, "read_only": True}


def approach_npc(debug, keyboard, npc_id, max_steps=80):
    """Bounded controller navigation using observations, never position writes."""
    if not isinstance(npc_id, str) or len(npc_id) != 4 or not 1 <= max_steps <= 120:
        raise ValueError("Invalid controller-navigation target or step limit")
    target = f"{int(npc_id, 16):04X}"
    observations, positions = [], []
    outcome = "step_limit"
    for step in range(max_steps):
        message = message_snapshot(debug)
        if message.get("loaded"):
            outcome = "dialogue_active"
            observations.append({"message": message})
            break
        player = player_snapshot(debug)["world_position"]
        actors = npc_actors_snapshot(debug)["live_npc_actors"]
        matches = [a for a in actors if a.get("animal_id", a["fg_name"]) == target]
        if len(matches) != 1:
            outcome = "target_not_uniquely_loaded"
            break
        npc = matches[0]["world_position"]
        dx, dz = npc["x"]-player["x"], npc["z"]-player["z"]
        distance = math.hypot(dx, dz)
        positions.append((player["x"], player["z"]))
        if len(positions) >= 9 and math.dist(positions[-1], positions[-9]) < 4:
            outcome = "navigation_stalled"
            break
        key = ("g" if dx > 0 else "f") if abs(dx) >= abs(dz) else ("s" if dz > 0 else "w")
        duration = 0.025 if distance < 48 else 0.06
        observations.append({"step": step, "player": player, "target": npc,
                             "distance": distance, "key": key, "duration": duration})
        keyboard.press(key, duration)
        if distance < 48:
            keyboard.press("a", 0.06)
            time.sleep(0.5)
        else:
            time.sleep(0.12)
    return {"normal_controller_navigation": target, "outcome": outcome,
            "observations": observations, "position_or_schedule_writes": False}


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


def advance_to_choice(debug, keyboard, options, record, pause=time.sleep, *, stop_when_closed=False):
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
        if stop_when_closed and message.get("loaded") == 0:
            record({"dialogue_closed": True, "presses": pressed,
                    "message_id": message.get("message_id")})
            return
        if stop_when_closed and message.get("loaded") != 1:
            raise ValueError("Cannot advance dialogue without a valid loaded-state observation")
        if pressed < maximum:
            keyboard.press("a", 0.08)
    raise ValueError("No active choice within the declared page-advance limit")


def advance_to_message(debug, keyboard, options, record, pause=time.sleep):
    """Use bounded ordinary input until a named live message is observed."""
    target = options.get("message_id")
    maximum = options.get("max_presses", 30)
    settle = options.get("settle_seconds", 3)
    choose_first = options.get("choose_first_in", [])
    if not isinstance(target, str) or len(target) != 4 or any(c not in "0123456789ABCDEF" for c in target):
        raise ValueError("Target message must be four uppercase hexadecimal digits")
    if type(maximum) is not int or not 0 <= maximum <= 100:
        raise ValueError("Invalid advance-to-message press limit")
    if type(settle) not in (int, float) or not 0.1 <= settle <= 10:
        raise ValueError("Invalid advance-to-message settling time")
    if (not isinstance(choose_first, list) or len(choose_first) > 16
            or any(not isinstance(value, str) or len(value) != 4
                   or any(c not in "0123456789ABCDEF" for c in value) for value in choose_first)
            or len(set(choose_first)) != len(choose_first)):
        raise ValueError("Invalid explicit first-choice message list")
    for pressed in range(maximum+1):
        pause(settle)
        message = message_snapshot(debug)
        choice = choice_snapshot(debug)
        record(message)
        record(choice)
        if message.get("loaded") == 1 and message.get("message_id") == target:
            record({"advanced_to_message": target, "presses": pressed})
            return
        if choice["choice_state"] == 2 and choice["choice_count"] > 0:
            if (message.get("loaded") != 1 or message.get("message_id") not in choose_first
                    or choice.get("choice_cursor") != 0):
                raise ValueError("Unexpected active choice before target message")
            if pressed < maximum:
                record({"choose_first_in_message": message["message_id"]})
        if pressed < maximum:
            keyboard.press("a", 0.08)
    raise ValueError("Target message not reached within the declared press limit")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rom", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--xvfb", default=os.environ.get("AF_XVFB", "Xvfb"))
    parser.add_argument("--ares", default="/usr/bin/ares")
    parser.add_argument("--seconds", type=int, default=40)
    parser.add_argument('--expansion-pak', action='store_true', help='Enable eight MiB for an explicitly compatible test build')
    parser.add_argument("--scenario", type=Path)
    parser.add_argument('--no-initial-screenshot',action='store_true',
                        help='Skip the diagnostic startup image for memory-only batches; scenario image checks still run')
    parser.add_argument("--post-scenario", type=Path, help="Additional assertions after the main scenario")
    parser.add_argument("--port", type=int, default=19264)
    parser.add_argument("--seed-save", type=Path, help="Copy this isolated test directory's cartridge saves")
    parser.add_argument("--seed-state", type=Path, help="Resume this isolated test directory's matching-ROM state")
    parser.add_argument('--allow-test-flash-write',action='store_true',
                        help='Permit the native save fixture to write an otherwise blank isolated FlashRAM chip')
    parser.add_argument('--allow-test-pak-write',action='store_true',
                        help='Permit native note writes to an otherwise empty isolated Controller Pak')
    args = parser.parse_args()
    if args.seed_save and args.seed_state:
        parser.error("choose cartridge saves or a matching-ROM state, not both")
    if not 1 <= args.seconds <= 1200:
        parser.error("seconds must be between 1 and 1200")
    if args.output.exists():
        parser.error("output must be a fresh directory to isolate saves")
    out = args.output.resolve()
    out.mkdir(parents=True)
    rom = out / "test.z64"
    shutil.copyfile(args.rom, rom)
    rom_hash = hashlib.sha256(rom.read_bytes()).hexdigest()
    provenance = {"rom_sha256": rom_hash, "seed_files": [], "audio": "disabled", "expansion_pak": args.expansion_pak,
                  "initial_screenshot": not args.no_initial_screenshot,
                  "allow_test_flash_write": args.allow_test_flash_write,
                  "allow_test_pak_write": args.allow_test_pak_write,
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
                        f"Nintendo64\n  ExpansionPak: {str(args.expansion_pak).lower()}\n"
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
        with reserve_x_display() as selected_display:
            xvfb = subprocess.Popen(["timeout", "-s", "KILL", str(args.seconds+30), args.xvfb,
                                      ":"+selected_display, "-displayfd", str(writefd),
                                      "-screen", "0", "800x640x24", "-nolisten", "tcp"],
                                     pass_fds=(writefd,), stdout=log, stderr=log, start_new_session=True)
            processes.append(xvfb)
            os.close(writefd)
            display_number = os.read(readfd, 32).decode().strip()
            os.close(readfd)
            if display_number != selected_display:
                raise RuntimeError("Xvfb failed to start on the reserved display; see xvfb.log")
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
                   "--setting", f"Nintendo64/ExpansionPak={str(args.expansion_pak).lower()}", str(rom)]
        if args.seed_state:
            command[5:5] = ["--save-state", "1"]
        ares = subprocess.Popen(command, env=env, stdout=log, stderr=log, start_new_session=True)
        processes.append(ares)
        time.sleep(3)
        results = [{"rom_sha256": hashlib.sha256(rom.read_bytes()).hexdigest(),
                    "audio": "disabled", "expansion_pak": args.expansion_pak,
                    "scenario": str(args.scenario) if args.scenario else "default"}]
        if not args.no_initial_screenshot:
            try:
                subprocess.run(["ffmpeg", "-nostdin", "-loglevel", "error", "-f", "x11grab",
                                "-video_size", "800x640", "-i", display, "-frames:v", "1", str(out / "initial.png")],
                               env=env, check=True, timeout=15, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
            except subprocess.CalledProcessError as error:
                raise ValueError('Initial screenshot failed: '+error.stderr.decode(errors='replace')) from error
        debug = connect_debugger(ares, args.port)
        results.append({"debug_features": debug.command("qSupported:multiprocess+")})
        keyboard = Keyboard(display)
        actions = json.loads(args.scenario.read_text()) if args.scenario else [
            {"wait": args.seconds-5}, {"capture": "boot.png"},
            {"read": ["80090294", 4]}, {"read": ["80106AF4", 256]},
            {"read": ["8013A680", 32]}]
        if args.post_scenario:
            actions += json.loads(args.post_scenario.read_text())
        needs_checkpoint_restore = False
        test_mail_open = None
        def record(snapshot):
            results.append(snapshot)
            write_results(out, results)
        for action in expand_actions(actions):
            if action.get('verify_title_start'):
                from title_start_smoke import verify as verify_title_start
                record(verify_title_start(debug, args.rom.read_bytes()))
            if action.get('verify_title_logo'):
                from title_logo_smoke import diagnose as diagnose_title_logo, verify as verify_title_logo
                profile = json.loads((args.rom.parent/'preview.json').read_text())['actor']
                try:
                    record(verify_title_logo(debug, args.rom.read_bytes(), profile))
                except ValueError:
                    record(diagnose_title_logo(debug))
                    raise
            if "wait" in action:
                time.sleep(max(0, min(action["wait"], 60)))
            if "key" in action:
                keyboard.press(action["key"], action.get("duration", 0.15))
            if "advance_to_choice" in action:
                advance_to_choice(debug, keyboard, action["advance_to_choice"], record)
            if "advance_dialogue" in action:
                advance_to_choice(debug, keyboard, action["advance_dialogue"], record, stop_when_closed=True)
            if "advance_to_message" in action:
                advance_to_message(debug, keyboard, action["advance_to_message"], record)
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
                result = {'command':action['command'],'result':debug.command(action['command'])}
                # Keep malformed or out-of-order replies as failure evidence.
                results.append(result)
                write_results(out, results)
                if 'expect_result' in action and result['result'] != action['expect_result']:
                    raise ValueError(f"Unexpected debugger reply: {result!r}, "
                                     f"expected {action['expect_result']!r}")
                if 'expect_pc' in action:
                    if action['command'] != 'g':
                        raise ValueError('A PC assertion requires the bulk register command')
                    result['verified_pc'] = require_program_counter(result['result'],action['expect_pc'])
            if action.get("pause_game_thread"):
                results.append(debug.pause_game_thread())
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
                result = debug.call(call["address"], call.get("arguments", []),
                                    return_address=call.get('return_address', TEST_RETURN))
                needs_checkpoint_restore = True
                results.append(result)
                if "expect_return" in call and result["return_value"] != call["expect_return"]:
                    raise ValueError(f"Unexpected function return: {result['return_value']}")
                if 'expect_return_v1' in call and result['return_value_v1'] != call['expect_return_v1']:
                    raise ValueError(f"Unexpected v1 result: {result['return_value_v1']}")
            if 'test_extended_font' in action:
                from extended_font_smoke import exercise
                if not (out/'test.bs1').is_file():
                    raise ValueError('Native font probes require a saved emulator checkpoint')
                needs_checkpoint_restore = True
                results.append(exercise(debug,action['test_extended_font'],record))
            if 'test_extended_font_cartridge' in action:
                from extended_font_cartridge_smoke import exercise
                if not (out/'test.bs1').is_file():
                    raise ValueError('Cartridge font probes require a saved emulator checkpoint')
                needs_checkpoint_restore = True
                results.append(exercise(debug,action['test_extended_font_cartridge'],record))
            if 'test_npc_mail_sends' in action:
                from mail_npc_smoke import exercise
                if not (out/'test.bs1').is_file():
                    raise ValueError('NPC send probes require a saved emulator checkpoint')
                needs_checkpoint_restore = True
                results.append(exercise(debug,action['test_npc_mail_sends'],record))
            if 'test_mail_storage' in action:
                from mail_storage_smoke import exercise
                if not (out/'test.bs1').is_file():
                    raise ValueError('Mail storage probes require a saved emulator checkpoint')
                needs_checkpoint_restore = True
                results.append(exercise(debug,action['test_mail_storage'],record))
            if 'test_pelly_receipt' in action:
                from pelly_receipt_smoke import exercise
                if not (out/'test.bs1').is_file():
                    raise ValueError('Pelly receipt probes require a saved emulator checkpoint')
                needs_checkpoint_restore = True
                results.append(exercise(debug,action['test_pelly_receipt'],record))
            if 'test_native_flash_mail_save' in action or 'test_native_flash_mail_read' in action:
                from flash_mail_smoke import exercise
                writing = 'test_native_flash_mail_save' in action
                if not (out/'test.bs1').is_file() or writing and not args.allow_test_flash_write:
                    raise ValueError('Native FlashRAM fixtures require a checkpoint and explicit write opt-in')
                if not writing and (not args.seed_save or args.seed_state):
                    raise ValueError('Native FlashRAM readback requires a fresh start from cartridge saves only')
                needs_checkpoint_restore = True
                request = action['test_native_flash_mail_save' if writing else 'test_native_flash_mail_read']
                results.append(exercise(debug,request,record,
                    export_directory=out/'exported-save' if writing else None))
            if 'test_native_pak_mail_save' in action or 'test_native_pak_mail_read' in action:
                from pak_mail_smoke import exercise
                writing = 'test_native_pak_mail_save' in action
                if not (out/'test.bs1').is_file() or writing and not args.allow_test_pak_write:
                    raise ValueError('Native Pak fixtures require a checkpoint and explicit write opt-in')
                if not writing and (not args.seed_save or args.seed_state):
                    raise ValueError('Native Pak readback requires a fresh start from cartridge saves only')
                needs_checkpoint_restore = True
                request = action['test_native_pak_mail_save' if writing else 'test_native_pak_mail_read']
                results.append(exercise(debug,request,record,
                    export_directory=out/'exported-save' if writing else None))
            if 'test_mail_generation' in action:
                from mail_generate_smoke import exercise
                if not (out/'test.bs1').is_file():
                    raise ValueError('Native generation probes require an emulator checkpoint')
                needs_checkpoint_restore = True
                results.append(exercise(debug,action['test_mail_generation'],record))
            if 'test_fortune_slip' in action:
                from fortune_slip_smoke import exercise
                if not (out/'test.bs1').is_file():
                    raise ValueError('Native fortune-slip probes require an emulator checkpoint')
                needs_checkpoint_restore = True
                results.append(exercise(debug,action['test_fortune_slip'],record))
            if 'test_fortune_actor' in action:
                from fortune_actor_smoke import exercise
                if not (out/'test.bs1').is_file():
                    raise ValueError('Native fortune hand-off probes require an emulator checkpoint')
                needs_checkpoint_restore = True
                results.append(exercise(debug,action['test_fortune_actor'],record))
            if 'test_leaflet_dates' in action:
                from leaflet_date_smoke import exercise
                if not (out/'test.bs1').is_file():
                    raise ValueError('Native leaflet probes require an emulator checkpoint')
                needs_checkpoint_restore = True
                results.append(exercise(debug,action['test_leaflet_dates'],record))
            if 'test_leaflet_letters' in action:
                from leaflet_letter_smoke import exercise
                if not (out/'test.bs1').is_file():
                    raise ValueError('Native leaflet creation probes require an emulator checkpoint')
                needs_checkpoint_restore = True
                results.append(exercise(debug,action['test_leaflet_letters'],record))
            if 'test_renewal_actor' in action:
                from renewal_actor_smoke import exercise
                if not (out/'test.bs1').is_file():
                    raise ValueError('Native renewal probes require an emulator checkpoint')
                needs_checkpoint_restore = True
                results.append(exercise(debug,action['test_renewal_actor'],record))
            if 'test_event_actor' in action:
                from event_actor_smoke import exercise
                if not (out/'test.bs1').is_file():
                    raise ValueError('Native event probes require an emulator checkpoint')
                needs_checkpoint_restore = True
                results.append(exercise(debug,action['test_event_actor'],record))
            if 'test_mother_letters' in action:
                from mother_letter_smoke import exercise
                if not (out/'test.bs1').is_file():
                    raise ValueError('Native Mom-letter probes require an emulator checkpoint')
                needs_checkpoint_restore = True
                results.append(exercise(debug,action['test_mother_letters'],record))
            if 'test_departed_letters' in action:
                from departed_letter_smoke import exercise
                if not (out/'test.bs1').is_file():
                    raise ValueError('Departed-letter probes require an emulator checkpoint')
                needs_checkpoint_restore = True
                results.append(exercise(debug,action['test_departed_letters'],record))
            if 'test_villager_event_letters' in action:
                from villager_event_smoke import exercise
                if not (out/'test.bs1').is_file():
                    raise ValueError('Villager-event probes require an emulator checkpoint')
                needs_checkpoint_restore = True
                results.append(exercise(debug,action['test_villager_event_letters'],record))
            if 'test_academy_letters' in action:
                from academy_smoke import exercise
                if not (out/'test.bs1').is_file():
                    raise ValueError('Academy probes require an emulator checkpoint')
                needs_checkpoint_restore = True
                results.append(exercise(debug,action['test_academy_letters'],record))
            if 'test_academy_scores' in action:
                from academy_score_smoke import exercise
                if not (out/'test.bs1').is_file():
                    raise ValueError('Academy score probes require an emulator checkpoint')
                needs_checkpoint_restore = True
                results.append(exercise(debug,action['test_academy_scores'],record))
            if 'test_post_office_letters' in action:
                from post_office_smoke import exercise
                if not (out/'test.bs1').is_file():
                    raise ValueError('Post-office probes require an emulator checkpoint')
                needs_checkpoint_restore = True
                results.append(exercise(debug,action['test_post_office_letters'],record))
            if 'test_museum_letters' in action:
                from museum_smoke import exercise
                if not (out/'test.bs1').is_file():
                    raise ValueError('Museum probes require an emulator checkpoint')
                needs_checkpoint_restore = True
                results.append(exercise(debug,action['test_museum_letters'],record))
            if 'test_snowman_letters' in action:
                from snowman_smoke import exercise
                if not (out/'test.bs1').is_file():
                    raise ValueError('Snowman probes require an emulator checkpoint')
                needs_checkpoint_restore = True
                results.append(exercise(debug,action['test_snowman_letters'],record))
            if 'test_shop_notices' in action:
                from shop_notice_smoke import exercise
                if not (out/'test.bs1').is_file():
                    raise ValueError('Shop notice probes require an emulator checkpoint')
                needs_checkpoint_restore = True
                results.append(exercise(debug,action['test_shop_notices'],record))
            if 'test_secret_letters' in action:
                from secret_smoke import exercise
                if not (out/'test.bs1').is_file():
                    raise ValueError('Secret-letter probes require an emulator checkpoint')
                needs_checkpoint_restore = True
                results.append(exercise(debug,action['test_secret_letters'],record))
            if 'test_notice_reader' in action:
                from notice_reader_smoke import exercise
                if not (out/'test.bs1').is_file():
                    raise ValueError('Notice reader probes require an emulator checkpoint')
                needs_checkpoint_restore = True
                results.append(exercise(debug,action['test_notice_reader'],record))
            if 'test_notice_treasure' in action:
                from notice_treasure_smoke import exercise
                if not (out/'test.bs1').is_file():
                    raise ValueError('Treasure transaction probes require an emulator checkpoint')
                needs_checkpoint_restore = True
                results.append(exercise(debug,action['test_notice_treasure'],record))
            if 'test_notice_seasonal' in action:
                from notice_seasonal_smoke import exercise
                if not (out/'test.bs1').is_file():
                    raise ValueError('Seasonal publication probes require an emulator checkpoint')
                needs_checkpoint_restore = True
                results.append(exercise(debug,action['test_notice_seasonal'],record))
            if 'test_quest_replies' in action:
                from quest_reply_smoke import exercise
                if not (out/'test.bs1').is_file():
                    raise ValueError('Quest reply probes require an emulator checkpoint')
                needs_checkpoint_restore = True
                results.append(exercise(debug,action['test_quest_replies'],record))
            if 'test_mail_menu' in action:
                from mail_menu_smoke import exercise
                if not (out/'test.bs1').is_file():
                    raise ValueError('Native mail-menu probes require an emulator checkpoint')
                needs_checkpoint_restore = True
                results.append(exercise(debug,action['test_mail_menu'],record))
            if 'test_npc_mail_capture' in action:
                from npc_mail_capture_smoke import exercise
                if not (out/'test.bs1').is_file():
                    raise ValueError('NPC capture probes require a saved emulator checkpoint')
                needs_checkpoint_restore = True
                results.append(exercise(debug,action['test_npc_mail_capture'],record))
            if 'test_native_species_words' in action:
                from native_species_scenario import exercise
                if not (out/'test.bs1').is_file():
                    raise ValueError('Native species probes require a saved emulator checkpoint')
                needs_checkpoint_restore = True
                results.append(exercise(debug,action['test_native_species_words'],record))
            if 'test_gyroid_default' in action:
                from gyroid_default_smoke import exercise
                if not (out/'test.bs1').is_file():
                    raise ValueError('Gyroid default probes require a saved emulator checkpoint')
                needs_checkpoint_restore = True
                results.append(exercise(debug, action['test_gyroid_default'], record))
            if 'test_npc_mail_delivery' in action:
                from npc_mail_delivery_smoke import exercise
                if not (out/'test.bs1').is_file():
                    raise ValueError('NPC delivery gate probes require a saved emulator checkpoint')
                needs_checkpoint_restore = True
                results.append(exercise(debug,action['test_npc_mail_delivery'],record))
            if 'test_npc_mail_loader' in action:
                from npc_mail_loader_smoke import exercise
                if not (out/'test.bs1').is_file():
                    raise ValueError('Cartridge loader probes require a saved emulator checkpoint')
                needs_checkpoint_restore = True
                results.append(exercise(debug,action['test_npc_mail_loader'],record))
            if 'test_npc_mail_show' in action:
                from npc_mail_show_smoke import exercise
                if not (out/'test.bs1').is_file():
                    raise ValueError('NPC letter-show probes require a saved emulator checkpoint')
                needs_checkpoint_restore = True
                results.append(exercise(debug,keyboard,action['test_npc_mail_show'],record))
            if 'test_resident_words' in action:
                from resident_word_smoke import exercise
                if not (out/'test.bs1').is_file():
                    raise ValueError('Resident-word probes require a saved emulator checkpoint')
                needs_checkpoint_restore = True
                results.append(exercise(debug,action['test_resident_words'],record))
            if 'test_credits' in action:
                from credits_smoke import exercise
                if not (out/'test.bs1').is_file():
                    raise ValueError('Credits probes require a saved emulator checkpoint')
                needs_checkpoint_restore = True
                results.append(exercise(debug,action['test_credits'],record))
            if 'test_song_item_names' in action:
                from song_item_names_smoke import exercise
                if not (out/'test.bs1').is_file():
                    raise ValueError('Native song-title tests require an isolated checkpoint')
                needs_checkpoint_restore = True
                results.append(exercise(debug,action['test_song_item_names'],record))
            if 'test_shop_units' in action:
                from shop_unit_smoke import exercise
                if not (out/'test.bs1').is_file():
                    raise ValueError('Shop-unit probes require a saved emulator checkpoint')
                needs_checkpoint_restore = True
                results.append(exercise(debug,action['test_shop_units'],record))
            if 'test_resetti_replies' in action:
                from resetti_reply_smoke import exercise
                if not (out/'test.bs1').is_file():
                    raise ValueError('Resetti reply probes require a saved emulator checkpoint')
                needs_checkpoint_restore = True
                results.append(exercise(debug,action['test_resetti_replies'],record))
            if 'test_classic_letters' in action:
                if not (out/'test.bs1').is_file():
                    raise ValueError('Native classic-letter checks require a saved emulator checkpoint')
                needs_checkpoint_restore = True
                from classic_letter_smoke import exercise
                results.append(exercise(debug,action['test_classic_letters'],record))
            if 'test_accent_mail' in action:
                if not (out/'test.bs1').is_file():
                    raise ValueError('Native accent mail checks require a saved emulator checkpoint')
                needs_checkpoint_restore = True
                from accent_mail_smoke import exercise
                results.append(exercise(debug,action['test_accent_mail'],record))
            if 'test_apology_input' in action:
                from apology_input_smoke import exercise
                if not (out/'test.bs1').is_file():
                    raise ValueError('Apology input probes require a saved emulator checkpoint')
                needs_checkpoint_restore = True
                results.append(exercise(debug,action['test_apology_input'],record))
            if 'test_fortunes' in action:
                from fortune_smoke import exercise
                if not (out/'test.bs1').is_file():
                    raise ValueError('Fortune probes require a saved emulator checkpoint')
                needs_checkpoint_restore = True
                results.append(exercise(debug,action['test_fortunes'],record))
            if 'test_dialogue_dates' in action:
                from dialogue_dates_smoke import exercise
                if not (out/'test.bs1').is_file():
                    raise ValueError('Dialogue date probes require a saved emulator checkpoint')
                needs_checkpoint_restore = True
                results.append(exercise(debug,action['test_dialogue_dates'],record))
            if 'test_resident_animations' in action:
                from resident_animations_smoke import exercise
                if not (out/'test.bs1').is_file():
                    raise ValueError('Resident animation probes require a saved emulator checkpoint')
                needs_checkpoint_restore = True
                results.append(exercise(debug, action['test_resident_animations'], record))
            if 'open_test_mail' in action:
                from mail_view_smoke import open_test_mail
                if not (out/'test.bs1').is_file():
                    raise ValueError('Native mail-open probes require a saved emulator checkpoint')
                test_mail_open = open_test_mail(debug,action['open_test_mail'],
                                                snapshot_probe=action.get('snapshot_probe',False),
                                                open_mode=action.get('mail_open_mode',1))
                needs_checkpoint_restore = True
                results.append(test_mail_open)
            if action.get('snapshot_submenu'):
                from mail_view_smoke import snapshot as submenu_snapshot
                snapshot = submenu_snapshot(debug)
                results.append({'submenu_snapshot':snapshot})
                for field,expected in action.get('expect_submenu',{}).items():
                    if snapshot.get(field) != expected:
                        raise ValueError(f'Submenu {field}: {snapshot.get(field)!r}, expected {expected!r}')
            if action.get('assert_test_mail_unchanged'):
                from mail_view_smoke import verify_unchanged
                results.append(verify_unchanged(debug,test_mail_open))
            if 'read_all_mail_pages' in action:
                from mail_reader_smoke import all_pages
                if not needs_checkpoint_restore or not test_mail_open:
                    raise ValueError('Complete mail-page probes require an isolated open and checkpoint')
                all_pages(debug,keyboard,action['read_all_mail_pages'],record)
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
            if action.get("snapshot_villagers"):
                results.append(villagers_snapshot(debug))
            if action.get("snapshot_npc_actors"):
                results.append(npc_actors_snapshot(debug))
            if "approach_npc" in action:
                results.append(approach_npc(debug, keyboard, action["approach_npc"], action.get("max_steps", 80)))
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
            write_results(out, results)
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
        write_results(out, results)
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
