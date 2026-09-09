"""Native treasure scheduler, real burial, transaction phases, and rollback.

The isolated fixture supplies field collision data, familiar animals, time, and
one eligible unit. Native selection and deposit instructions execute unchanged.
Ordinary-item cases substitute a known wide-name item at the original placement
call; they do not claim validation of the random furniture selector.
"""

import struct
from aflib import sha256
from flash_mail import SAVE_RAM, SAVE_BYTES
from runtime_layout import MODULE_RAM, RESERVATION, TEST_STACK, GUARD_ADDRESS, GUARD_WORD
from notice_treasure_scenario import rng

POSTS, FG, FLAGS, BURIED, CHECKED, ANIMALS = 0x80129E0A, 0x8012D148, 0x801362DC, 0x8013673C, 0x80136744, 0x80130DB8
EDGE = b'NTED'*4


def words(*values): return struct.pack('>'+'I'*len(values), *values)


def traced_call(debug, address, stops, record, limit=32, rearm=None):
    """Observe bounded native waypoints without replacing code or returns.

    RSP.call retains its usual graph-thread, code-range, final PC, stack, and
    register-restoration checks. This interceptor only handles the extra native
    breakpoints before returning its final stop packet to that existing method.
    """
    original = debug.command
    hits = 0
    installed = set()
    rearm = rearm or {}
    if any(at not in stops or any(target not in stops or target == at for target in targets)
           for at, targets in rearm.items()): raise ValueError('Invalid treasure breakpoint rearm')
    def resume():
        try:
            return original('c')
        except TimeoutError:
            # Preserve the stopped native PC before RSP.call restores its entry
            # registers. This is diagnostic evidence, never a successful call.
            original('?')
            raw = original('g')
            record({'treasure_native_timeout_registers': raw})
            raise
    def command(packet):
        nonlocal hits
        answer = resume() if packet == 'c' else original(packet)
        if packet != 'c': return answer
        while answer[:3] in ('T05', 'S05'):
            raw = original('g')
            if len(raw) != 71*16: raise ValueError('Unknown treasure register layout')
            registers = [int(raw[i:i+16], 16) & 0xFFFFFFFF for i in range(0, len(raw), 16)]
            at = registers[37]
            if at not in stops: break
            hits += 1
            if hits > limit: raise ValueError('Treasure native waypoint limit exceeded')
            record({'treasure_native_waypoint': f'{at:08X}', 'stack': f'{registers[29]:08X}'})
            key = f'0,{at:x},4'
            if key not in installed: raise ValueError('Inactive treasure breakpoint stopped again')
            # ares resumes on the current instruction; leaving this breakpoint
            # installed would stop again without executing it. Remove each
            # waypoint, and rearm the shared malloc return at phase-two entry.
            if original('z'+key) != 'OK': raise ValueError('Rejected treasure breakpoint removal')
            installed.remove(key)
            stops[at](registers)
            for target in rearm.get(at, ()):
                key = f'0,{target:x},4'
                if key not in installed:
                    if original('Z'+key) != 'OK': raise ValueError('Rejected treasure breakpoint rearm')
                    installed.add(key)
            answer = resume()
        return answer
    try:
        for at in stops:
            key = f'0,{at:x},4'
            if original('Z'+key) != 'OK': raise ValueError('Rejected treasure native breakpoint')
            installed.add(key)
        debug.command = command
        result = debug.call(f'{address:08X}', [])
        record(result)
        return result
    finally:
        debug.command = original
        for key in sorted(installed): original('z'+key)


def exercise(debug, request, record):
    read, write = debug.read_memory, debug.write_memory
    assertions = completed = failures = 0
    def check(label, at, expected):
        nonlocal assertions
        actual = read(at, len(expected))
        record({'treasure_check': label, 'address': f'{at:08X}', 'bytes': len(expected),
                'assertion': 'passed' if actual == expected else 'failed',
                'expected_sha256': sha256(expected), 'observed_sha256': sha256(actual)})
        if actual != expected: raise ValueError('Native treasure mismatch: '+label)
        assertions += 1
    def call(at, args=(), expected=None):
        result = debug.call(f'{at:08X}', args)
        record(result)
        if expected is not None and result['return_value'] != expected: raise ValueError('Unexpected treasure helper result')
        return result['return_value']
    for at, value in request['guards'].items(): check('source-bound installed treasure code', int(at, 16), bytes.fromhex(value))
    symbols = request['module']['symbols']
    capital = int(symbols['af_mail_generation_capital'], 16)
    session = int(symbols['af_npc_mail_session'], 16)
    check('detached creator at entry', session, bytes(4))
    saved = read(SAVE_RAM, SAVE_BYTES)
    globals_before = {at: read(at, size) for at, size in
                      ((capital, 4), (0x8003C590, 8), (0x80140680, 200), (MODULE_RAM+56, 48),
                       (0x8013A248, 4), (0x80106818, 4), (0x80106A68, 32), (0x80136FBC, 20))}
    allocation = call(0x8009BFC0, [0x18000])
    if allocation & 15 or not MODULE_RAM+RESERVATION <= allocation <= 0x80400000-0x18000:
        raise ValueError('Treasure field fixture allocation failed')
    actor, blocks, metrics = allocation+16, allocation+0x200, allocation+0x15700
    if blocks+56*1556 > metrics-16: raise ValueError('Treasure collision fixture overlaps metrics')
    edges = (allocation, actor+0x180, blocks-16, blocks+56*1556, metrics-16, metrics+12,
             allocation+0x17FF0, TEST_STACK-0x1800, TEST_STACK+0x30)
    for at in edges: write(at, EDGE)
    write(actor, bytes(0x180))
    write(actor+0x148, words(blocks))
    write(actor+0x166, bytes((7, 8)))
    # Retain enough space for the real creator, but not its valid maximum-sized
    # request. This permits an actual allocation failure in either phase.
    pressure = call(0x8009BFC0, [0x6000])
    if pressure & 15 or not MODULE_RAM+RESERVATION <= pressure <= 0x80400000-0x6000:
        raise ValueError('Treasure memory-pressure fixture allocation failed')
    call(0x8009C0C0, [metrics, metrics+4, metrics+8])
    heap = read(metrics, 12)
    original_config = globals_before[MODULE_RAM+56][16:48]
    config = list(struct.unpack('>8I', original_config))
    large = config[:]; large[2] = 65536; large[1] = large[2]+large[3]
    largest = struct.unpack('>3I', heap)[1]
    if not config[1]+5359 <= largest < large[1]+5359:
        raise ValueError('Treasure fixture does not establish the intended allocation boundary')
    rtc = bytes.fromhex('00120e04040907d1')
    empty = b' '*96+bytes.fromhex(request['empty_rtc'])
    collision = bytes(56*1556)
    write(blocks, collision)
    written = []

    def fixture(case, fault=None):
        state = bytearray(saved)
        def put(at, value): state[at-SAVE_RAM:at-SAVE_RAM+len(value)] = value
        put(SAVE_RAM+0x14, words(7))
        put(0x80129E00, b'Town  '+bytes(2)+bytes.fromhex('1234'))
        put(POSTS, empty*15)
        put(BURIED, rtc if fault == 'recent' else bytes.fromhex(request['empty_rtc']))
        put(CHECKED, rtc if fault == 'checked' else bytes.fromhex(request['empty_rtc']))
        put(ANIMALS, bytes(1320*15))
        if fault != 'unfamiliar':
            put(ANIMALS, bytes.fromhex(case['animal']))
            put(ANIMALS+0x16, b'Town  ')
            put(ANIMALS+0x1E, bytes.fromhex('1234'))
        put(FG, bytes.fromhex('2030')*7680)
        if fault != 'no_unit': put(FG+case['unit']*2, bytes(2))
        put(FLAGS, bytes.fromhex('aaaa')*480)
        write(SAVE_RAM, state)
        write(0x8013A248, words(actor))
        write(0x80106818, bytes(4))
        write(0x80106A68, words(3, 1, 3, 2, 0, 0, 0, 0))
        write(0x80136FBC, rtc)
        if fault == 'early': write(0x80136FBE, b'\x05')
        write(0x80136FCC, bytes(4))
        write(MODULE_RAM+56, globals_before[MODULE_RAM+56])
        write(capital, words(case['capital']))
        write(0x8003C590, words(case['seed']))
        write(blocks, collision)
        attribute = 0x04000000 if fault == 'no_hole' else request['hole_profiles'][case['hole']]
        write(blocks+8*1556+32+case['unit']*4, words(attribute))
        return bytes(state)

    def run_case(case, fault=None):
        before = fixture(case, fault)
        phases, mallocs = [], []
        frame = None
        expected_body = bytes.fromhex(case['wire'])+rtc
        expected_fg = bytearray(before[FG-SAVE_RAM:FG-SAVE_RAM+15360])
        expected_flags = bytearray(before[FLAGS-SAVE_RAM:FLAGS-SAVE_RAM+960])
        unit = case['unit']; cell, flag = FG+unit*2, FLAGS+unit//16*2
        buried_item = 0x2A+case['hole'] if case['item'] == 0x2512 else case['item']
        expected_fg[unit*2:unit*2+2] = struct.pack('>H', buried_item)
        if case['item'] != 0x2512:
            struct.pack_into('>H', expected_flags, unit//16*2, 0xAAAA | (1 << (unit % 16)))
        undo = words(cell, flag)+bytes(2)+bytes.fromhex('aaaa')+struct.pack('>H', buried_item)+b'NT'
        def entering(regs):
            nonlocal frame
            frame = regs[29]
            phases.append('begin')
            check('original scheduler selects a pitfall from the bound seed', frame+0x66, bytes.fromhex('2512'))
            if case['item'] != 0x2512: write(frame+0x66, struct.pack('>H', case['item']))
            if fault == 'phase1_alloc': write(MODULE_RAM+0x48, words(*large))
        def placed(regs):
            phases.append('placed')
            success = fault not in ('phase1_alloc', 'no_hole', 'no_unit')
            if bool(regs[2]) != success: raise ValueError('Native burial returned the wrong result')
            if success:
                check('actual native buried foreground', FG, bytes(expected_fg))
                check('actual native buried flags', FLAGS, bytes(expected_flags))
                check('native stack-only undo', frame+0xD0, undo)
            else:
                check('failed native burial retains all save state', SAVE_RAM, before)
            check('burial never publishes a partial post', POSTS, empty*15)
        def creating(regs):
            phases.append('create')
            check('native selector keeps the original template', regs[29]+0x10, words(case['template']))
            check('native selected animal identity', regs[22], bytes.fromhex(case['animal']))
            if fault == 'phase2_alloc': write(MODULE_RAM+0x48, words(*large))
            elif fault == 'catalog': write(MODULE_RAM+68, bytes(4))
            elif fault == 'names': write(MODULE_RAM+56, bytes(4))
            elif fault == 'creator_crc':
                changed = config[:]; changed[6] ^= 1
                write(MODULE_RAM+0x48, words(*changed))
        def published(regs):
            phases.append('end')
            if bool(regs[2]) != (fault is None): raise ValueError('Native publication returned the wrong result')
        def allocated(regs):
            mallocs.append(regs[2])
            record({'treasure_native_malloc_return': f'{regs[2]:08X}', 'fault': fault})
        def bridge(regs):
            # Observe the actual callee entry, after its caller's jal delay slot.
            # Mid-block call-site stops are unreliable in the installed ares JIT.
            if regs[31] == 0x800A6178: entering(regs)
            elif regs[31] == 0x800A62A8: creating(regs)
            else: raise ValueError('Unexpected native treasure bridge caller')
        stops = {0x800A5E58: bridge, 0x800A6178: placed,
                 0x800A62A8: published, 0x80197D78: allocated}
        traced_call(debug, 0x800A5F08, stops, record,
                    rearm={0x800A6178: (0x800A5E58,), 0x800A5E58: (0x80197D78,)})
        expected = bytearray(before)
        if fault is None:
            expected[FG-SAVE_RAM:FG-SAVE_RAM+15360] = expected_fg
            expected[FLAGS-SAVE_RAM:FLAGS-SAVE_RAM+960] = expected_flags
            expected[POSTS-SAVE_RAM:POSTS-SAVE_RAM+104] = expected_body
            expected[BURIED-SAVE_RAM:BURIED-SAVE_RAM+8] = rtc
            check('native parent contains the complete post and timestamp', frame+0x68, expected_body)
            written.append({**case, 'created_wire': read(POSTS, 96).hex()})
        check('only complete treasure publication changes save state', SAVE_RAM, bytes(expected))
        check('native creator detaches its session', session, bytes(4))
        check('unrelated native text fields retained', 0x80140680, globals_before[0x80140680])
        draws = 0 if fault in ('early', 'recent', 'checked', 'unfamiliar') else 2 if fault in ('no_unit', 'phase1_alloc') else 4 if fault == 'no_hole' else 6
        check('native RNG consumes the original draws', 0x8003C590, words(rng(case['seed'], draws)[0]))
        expected_phases = [] if not draws else ['begin', 'placed'] if draws < 6 else ['begin', 'placed', 'create', 'end']
        if phases != expected_phases: raise ValueError('Missing or repeated native treasure phase')
        if fault in ('phase1_alloc', 'phase2_alloc'):
            if not mallocs or mallocs[-1] != 0 or any(not p for p in mallocs[:-1]):
                raise ValueError('Allocation-failure case did not observe the actual native null return')
        call(0x8009C0C0, [metrics, metrics+4, metrics+8])
        check('native treasure retains heap accounting', metrics, heap)
        write(MODULE_RAM+56, globals_before[MODULE_RAM+56])
        for at in edges: check('treasure fixture and stack guard', at, EDGE)
        return phases

    for index, case in enumerate(request['cases'][request.get('skip_complete', 0):], request.get('skip_complete', 0)):
        run_case(case)
        completed += 1
        record({'native_treasure_complete': index, 'template': case['template'], 'capital': case['capital'],
                'item': case['item'], 'hole': case['hole'], 'wire': written[-1]['created_wire'], 'passed': True})
    case = request['cases'][0]
    for fault in ('phase1_alloc', 'phase2_alloc', 'catalog', 'names', 'creator_crc', 'no_hole',
                  'no_unit', 'early', 'recent', 'checked', 'unfamiliar'):
        phases = run_case(case, fault)
        failures += 1
        record({'native_treasure_fault': fault, 'phases': phases, 'passed': True})
    for at, value in request['guards'].items(): check('treasure code retained after execution', int(at, 16), bytes.fromhex(value))
    check('resident module guard', GUARD_ADDRESS, words(*([GUARD_WORD]*4)))
    write(SAVE_RAM, saved); check('complete saved payload restored', SAVE_RAM, saved)
    for at, value in globals_before.items():
        write(at, value); check('treasure global restored', at, value)
    call(0x8009C040, [pressure]); call(0x8009C040, [allocation])
    return {'native_treasure_cases': completed, 'native_treasure_faults': failures,
            'treasure_assertions': assertions, 'actual_burial_and_publication': True,
            'ordinary_item_substitution_at_original_call': True, 'normal_random_furniture_selection': False,
            'debugger_uploaded_creator_bytes': 0, 'full_reader_executed': False,
            'normal_gameplay': False, 'save_io_tested': False, 'hardware_verified': False,
            'requires_checkpoint_restore': True}
