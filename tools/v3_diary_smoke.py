"""Connected native diary/menu/keyboard probe on a disposable checkpoint.

Uses the installed packets and actual native menu loader. The game/controller
context and selected profile are test data, not ordinary room entry or hardware
evidence. No device erase/write calls are permitted by this probe.
"""
import json
from pathlib import Path
import struct
import sys
from types import SimpleNamespace

from aflib import CODE_RAM, CODE_VROM, by_vrom, sha256
from npc_mail_show import relocate_verified_data
from runtime_layout import MODULE_RAM, RESERVATION, TEST_STACK
from v3_asset_loader import BLOB
from v3_diary_selection import bindings
from v3_npc_draw_smoke import boot_proofs


def exercise_dma(debug, rom_path, record):
    """Execute the unchanged native overlay loader for the corrected resources.

    Borrow the actual reserved menu/player area while the native game thread is
    paused. This proves resource loading/relocation, not actor construction,
    ordinary gameplay, or a save cycle. Restore the checkpoint before resuming.
    """
    path=Path(rom_path);image=path.read_bytes();report=json.loads((path.parent/'build.json').read_bytes())
    if sha256(image)!=report['output_sha256']:raise ValueError('Native DMA probe requires checked cartridge')
    e=report['equipment_resources'];files=by_vrom(image);proofs=boot_proofs(image)
    read,write=debug.read_memory,debug.write_memory
    def word(at):return int.from_bytes(read(at,4),'big')
    start=word(0x8010DCE0);size=word(0x8010DCE4);dest=start+16;end=start+size-16
    if start&15 or not MODULE_RAM+RESERVATION<=start<dest<end<=0x80400000:
        raise ValueError('Invalid native reserved overlay area')
    if word(0x8003CE34):raise ValueError('Pre-existing native fault')
    guards=(start,end,TEST_STACK-0x1000,TEST_STACK+0x40);edge=b'DMAG'*4
    for at in guards:write(at,edge)
    pairs=[]
    for row in e['diaries']['hooks']['menus'].values():
        pairs.append((row['target_vrom'],row['target_reloc'],row['owner_after'][2],()))
    from shop_units import PRICE_BIASES
    for row in e['carried_items']['paper']['quantities']['native_consumers']:
        if row['name'].startswith('shop-'):
            # Native shops carry deliberately biased price-table bases. Retain
            # the checked original constants used by the existing shop probe.
            constants=(PRICE_BIASES[row['vrom']],) if row['vrom'] in PRICE_BIASES else ()
            pairs.append((row['installed_vrom'],row['installed_reloc'],row['ram'],constants))
    for row in e['bank']['resources']['pairs']:
        pairs.append((row['target_vrom'],row['target_relocation_vrom'],row['ram'],()))
    if len(pairs)!=10 or len(set(pairs))!=10:raise ValueError('Incomplete corrected native resource inventory')
    for vrom,reloc,ram,constants in pairs:
        data,rel=files[vrom].extract(image),files[reloc].extract(image)
        sections=struct.unpack_from('>5I',rel);resident=sum(sections[:4])
        if (files[reloc].index!=files[vrom].index+1 or vrom+len(data)>0x04000000 or
                reloc+len(rel)>0x04000000 or dest+resident+len(rel)>end):
            raise ValueError('Native DMA pair escapes checked loader/arena bounds')
        expected=relocate_verified_data(SimpleNamespace(ram=ram,resident_bytes=resident,sections=sections),data,rel,dest,
            address_constants=constants)
        result=debug.call('800262D0',[vrom,vrom+len(data),ram,ram+resident,dest,dest+resident,len(rel)],
            return_address=MODULE_RAM+0x6480,verified_code=proofs[0x800262D0])
        record(result)
        actual=read(dest,len(expected));fault=word(0x8003CE34)
        record(dict(native_dma_vrom=f'{vrom:08X}',relocation_vrom=f'{reloc:08X}',
            bytes=len(expected),expected_sha256=sha256(expected),actual_sha256=sha256(actual),
            passed=actual==expected and not fault,fault=fault))
        if actual!=expected or fault:raise ValueError('Native DMA load/relocation failed')
        for at in guards:
            if read(at,16)!=edge:raise ValueError('Native DMA changed guarded allocation/stack')
    return dict(native_dma_pairs_loaded=len(pairs),complete_resources_matched=True,
        native_loader_limit_unchanged=True,ordinary_gameplay_tested=False,
        checkpoint_restore_required=True,hardware_tested=False)


def exercise(debug, rom_path, record, *, visitor=False):
    path=Path(rom_path);image=path.read_bytes();report=json.loads((path.parent/'build.json').read_bytes())
    if sha256(image)!=report['output_sha256']:
        raise ValueError('Diary probe requires the current checked cartridge')
    rows=bindings(image,report)
    if len(rows)!=16:raise ValueError('Diary probe requires the connected category')
    files=by_vrom(image);core=files[CODE_VROM].extract(image)
    d=report['equipment_resources']['diaries'];ui=d['ui_compiled'];symbols=ui['symbols']
    read,write=debug.read_memory,debug.write_memory;proofs=boot_proofs(image)
    calls=assertions=0
    def check(label,address,wanted):
        nonlocal assertions
        actual=read(address,len(wanted));assertions+=1
        record(dict(diary_check=label,address=f'{address:08X}',bytes=len(wanted),
            expected_sha256=sha256(wanted),actual_sha256=sha256(actual),passed=actual==wanted))
        if actual!=wanted:raise ValueError('Native diary mismatch: '+label)
    def word(at):return int.from_bytes(read(at,4),'big')
    def put(at,*values):write(at,struct.pack('>'+str(len(values))+'I',*values))
    def call(at,args=(),proof=None):
        nonlocal calls
        try:
            result=debug.call(f'{at:08X}',list(args),return_address=MODULE_RAM+0x6480,
                verified_code=proof or proofs.get(at))
        except ValueError:
            record(dict(diary_native_failed_call=f'{at:08X}',thread=debug.thread_snapshot(),
                scratch_stack=read(TEST_STACK-0x400,0x440).hex(),
                fault_thread=f'{word(0x8003CE34):08X}'))
            raise
        calls+=1;record(result)
        return result['return_value']
    for p in (*d['packets'].values(),report['equipment_resources']['diary_items']['packet']):
        check('installed diary packet',p['ram'],image[p['physical']:p['physical']+p['bytes']])
    check('no pre-existing fault',0x8003CE34,bytes(4))
    current_game=word(0x8010EF90)
    if current_game&3 or not 0x80000400<=current_game<=0x80400000-0xE0:
        raise ValueError('Invalid game arena owner for diary fixture')
    arena_header=read(current_game+0x78,16)
    arena_size,start,head,tail=struct.unpack('>4I',arena_header)
    size=0x400 if visitor else 0x90000
    record(dict(diary_fixture_arena=dict(start=start,head=head,tail=tail,bytes=arena_size)))
    if visitor:
        # The title has handed its whole TwoHeadArena to the scene allocator.
        # Allocate through that real owner, rather than treating the exhausted
        # parent arena as spare space or overwriting existing scene objects.
        node=word(0x80141FA0);previous=0;seen=set();largest=0
        while node:
            if node in seen or node&15 or len(seen)>=256 or not 0x80000400<=node<=0x80400000-16:
                raise ValueError('Invalid native scene arena link for diary fixture')
            seen.add(node)
            magic,free,extent,following,prev=struct.unpack('>2H3I',read(node,16))
            if magic!=0x7373 or free not in (0,1) or prev!=previous or node+16+extent>0x80400000:
                raise ValueError('Invalid native scene arena block for diary fixture')
            if free:largest=max(largest,extent)
            previous,node=node,following
        record(dict(diary_fixture_scene_arena=dict(nodes=len(seen),largest_free_bytes=largest)))
        if largest<size:raise ValueError('Native scene arena lacks checked diary fixture space')
        at=0x8009BFC0
        allocation=call(at,[size],(at,core[at-CODE_RAM:at-CODE_RAM+32]))
    else:
        if not 0x80000400<=start<=head<=(tail&~15)-size<tail<=start+arena_size<=0x80400000:
            raise ValueError('Native game arena lacks checked diary fixture space')
        at=0x800D17D4
        allocation=call(at,[current_game+0x78,size],(at,core[at-CODE_RAM:at-CODE_RAM+32]))
    if allocation&15 or not MODULE_RAM+RESERVATION<=allocation<=0x80400000-size:
        raise ValueError('Native diary fixture allocation failed')
    if visitor:
        # Menus share the existing reserved player/menu overlay area. Use the
        # native link manager and live graph/context, not a second oversized
        # fabricated game, graphics, texture, and menu allocation.
        game=current_game;sub=game+0x1CBC;graph=word(game)
        parent=word(0x8010DCE0);parent_bytes=word(0x8010DCE4)
        if parent&15 or not 0x80000400<=parent<parent+parent_bytes<=0x80400000:
            raise ValueError('Invalid native reserved menu area')
        if graph&3 or not 0x80000400<=graph<=0x80400000-0x308:
            raise ValueError('Invalid live native graph context')
        native_arenas={offset:read(graph+offset,16) for offset in (0x290,0x2B0)}
        bridge=allocation+16;bank=parent+parent_bytes
        guards=(allocation,allocation+size-16,TEST_STACK-0x1000,TEST_STACK+0x40)
        record(dict(diary_native_menu_area=dict(start=parent,bytes=parent_bytes,
            game=game,graph=graph,small_fixture_bytes=size)))
    else:
        parent=allocation+16;game=allocation+0x40000;sub=game+0x1CBC
        graph=allocation+0x43000;gfx=allocation+0x44000;assets=allocation+0x55000
        bridge=allocation+0x80000;bank=allocation+0x70000
        guards=(allocation,game-16,game+0x2000,graph-16,graph+0x300,gfx-16,
            gfx+0x10000,assets-16,bank-16,bridge-16,allocation+size-16,TEST_STACK-0x1000,TEST_STACK+0x40)
    edge=b'DIAR'*4
    for at in guards:write(at,edge)
    if not visitor:write(game,bytes(0x2000));write(graph,bytes(0x300))
    data,rel=(files[v].extract(image) for v in (0x7749C0,0x7778B0))
    sections=struct.unpack_from('>5I',rel);resident=sum(sections[:4]);ram=0x8085BAC0
    expected=relocate_verified_data(SimpleNamespace(ram=ram,resident_bytes=resident,sections=sections),data,rel,parent)
    if visitor:
        if resident+len(rel)>parent_bytes:raise ValueError('Diary parent exceeds native reserved menu area')
    else:
        if parent+resident+len(rel)>=game-16:raise ValueError('Diary parent overlaps fixture data')
        call(0x800262D0,[0x7749C0,0x7749C0+len(data),ram,ram+resident,parent,parent+resident,len(rel)])
        check('complete native menu load',parent,expected)
    parent_code=(parent,expected[:sections[0]])
    # The resident functions are invoked through checked low-RAM tail stubs,
    # preserving the debugger's existing high-RAM entry restriction.
    targets={**d['compiled']['symbols'],**symbols}
    names=('af_diary_native_selected','af_diary_native_open','af_diary_screen_owned',
        'af_diary_menu_edit','af_v3_save_reset','af_v3_save_prepare','af_v3_save_check',
        'af_v3_save_commit','af_v3_diary_data')
    stubs={name:bridge+i*16 for i,name in enumerate(names)}
    code=b''.join(struct.pack('>4I',0x08000000|(targets[name]>>2&0x3FFFFFF),0,0,0) for name in names)
    write(bridge,code);call(0x8002FE00,[bridge,len(code)]);call(0x80034CE0,[bridge,len(code)])
    def entry(name,args=()):return call(stubs[name],args,(bridge,code))
    saved_game=read(0x8010EF90,4)
    write(0x8010EF90,struct.pack('>I',game))
    try:
        if not visitor:put(game,graph);put(game+0x110+0x1818,assets)
        put(0x80104F94,0)  # The title-demo input mask is test context, not code.
        write(0x80136EA3,b'\0');write(0x80136FBC,bytes((0,0,12,15,0,6,7,214)))
        write(0x80126EA0,bytes(0xF980));write(0x80126EA0+0x2F68,b'\x30\x01')
        put(0x80136FD8,0x80126EC0)
        profile=bytearray(bytes.fromhex(report['save_runtime']['profile_hex']))
        for row in rows.values():
            put(row['enable_ram'],1);profile[row['profile_byte']]|=row['profile_mask']
        write(0x80460020,profile)
        if entry('af_v3_save_reset')!=1 or entry('af_diary_native_selected')!=65535:
            raise ValueError('Native diary selection/save initialization failed')
        live=entry('af_v3_diary_data')
        if visitor:
            write(0x80136EA3,b'\x04');put(0x80136FD8,0x801439A0)
            write(live+16+104+5*992,b'Host diary')
            # Refreshing an owner must not alter unrelated calendar/page rows.
            for slot in range(4):write(live+16+slot*12008+100,b'\x07\xD6\x06')
            expected_diary=read(live,48048)
        call(0x800C4D1C,[sub]);put(sub,3)  # Menu-open Game_Play context; no world actor reload.
        if not visitor:put(sub+0x24,parent,parent+((resident+63)&~63))
        if entry('af_diary_native_open',[game,0])!=1:
            raise ValueError('Native diary open rejected the valid isolated owner')
        if visitor:
            put(sub,4)  # Isolated menu context; omit world audio/actor handover.
            call(0x800C510C,[sub])
            check('native manager complete menu load',parent,expected)
            put(sub,3)  # The loaded constructor uses the Game_Play texture bank.
        call(parent+0x8085DAEC-ram,[sub],parent_code)
        overlay=word(sub+0x2C);screen=symbols['af_diary_native_screen'];menu=screen+8
        if entry('af_diary_screen_owned',[sub])!=screen:
            raise ValueError('Native HBOARD constructor did not acquire the diary')
        def snapshot(label):
            state=int.from_bytes(read(screen+0x7E0,2),'big')
            phase=int.from_bytes(read(screen+0x884,2),'big');fault=word(screen+ui['state_bytes']-4)
            record(dict(diary_native_state=label,state=state,phase=phase,fault=fault,
                program=word(sub+4),menu_owner=f'{overlay:08X}',arena_end=f'{word(sub+0x28):08X}'))
            if fault or word(0x8003CE34):raise ValueError('Native diary UI fault')
            limit=bank if visitor else game-16
            if word(sub+0x28)>limit or word(overlay+0x10000)>=bank-16:
                raise ValueError('Native diary menus/resources exceed fixture allocations')
            return state,phase
        def step(button=0,count=1):
            write(game+0x14,struct.pack('>H',button));write(game+0x20,struct.pack('>H',button))
            for _ in range(count):call(parent+0x8085DA28-ram,[sub],parent_code)
            write(game+0x14,bytes(2));write(game+0x20,bytes(2))
        def draw(label):
            if visitor:
                for offset,header in native_arenas.items():
                    extent,start,head,tail=struct.unpack('>4I',header)
                    if not 0x80000400<=start<=head<tail<=start+extent<=0x80400000:
                        raise ValueError('Invalid native diary graphics arena')
                    write(graph+offset,header)
                extent,graphics_start,initial_front,initial_tail=struct.unpack('>4I',native_arenas[0x290])
            else:
                for offset in (0x290,0x2B0):put(graph+offset,0xFFF0,gfx,gfx,gfx+0xFFF0)
                initial_front,initial_tail=gfx,gfx+0xFFF0
            call(parent+0x8085DA9C-ram,[sub,game],parent_code)
            front,tail=struct.unpack('>2I',read(graph+0x298,8))
            if not initial_front<front<tail<=initial_tail:raise ValueError('Diary draw escapes its native graphics arena')
            record(dict(diary_draw=label,command_bytes=front-initial_front,matrix_bytes=initial_tail-tail))
            snapshot(label)
        if visitor:
            mode=report['equipment_resources']['npc_extra']['events']['calendar']['code']['symbols']['af_holiday_calendar_choice']
            saved_mode=read(mode,4)
            def reopen():
                # Ordinary top-level closure unlinks the parent before its next
                # load. Its code/data contains child descriptors with relocated
                # callbacks and loaded flags; a constructor alone cannot reset
                # that lifecycle. Execute the real unlink/link, not flag edits.
                area=word(0x8010DCE8)
                if area!=0x8010DCEC:raise ValueError('Unexpected native submenu area owner')
                call(0x800C4648,[area,sub])
                if entry('af_diary_native_open',[game,0])!=1:
                    raise ValueError('Visitor diary reopen failed')
                put(sub,4);call(0x800C510C,[sub])
                check('complete native menu reload',parent,expected)
                put(sub,3);call(parent+0x8085DAEC-ram,[sub],parent_code)
            try:
                for selected_mode in (0,1):
                    put(mode,selected_mode)
                    # Opening resets the event cache, so each mode uses its
                    # actual dates and labels, not a previous mode's month.
                    if selected_mode:reopen()
                    step(count=12);snapshot('visitor calendar');draw('visitor calendar')
                    step(0x8000);step();step(0x8000);step(count=35)
                    if snapshot('visitor reading')[0]!=3:raise ValueError('Visitor could not read unlocked diary')
                    draw('visitor reading')
                    if int.from_bytes(read(menu+2004,2),'big')!=4 or int.from_bytes(read(menu+1992,2),'big')!=1:
                        raise ValueError('Visitor diary lost its viewer/read-only identity')
                    check('visitor reads host page',menu,b'Host diary')
                    if entry('af_diary_menu_edit',[menu,screen+0x7EC,8,ord('Z')]) not in (0xFFFFFFFF,0xFFFFFFFD):
                        raise ValueError('Visitor edit unexpectedly accepted')
                    step(0x8000);step(count=24)
                    if snapshot('visitor returns to calendar')[0]!=2 or word(sub+4)==10:
                        raise ValueError('Visitor entered an editor or failed to return')
                    check('visitor leaves all diaries unchanged',live,expected_diary)
                    step(0x4000);step();step(0x4000);step(count=20)
                    if word(screen)!=0:raise ValueError('Visitor diary owner failed to close')
                    write(live+16+98,b'\x01')
                    reopen()
                    step(count=12);step(0x8000);step();step(0x8000);step(count=12)
                    if snapshot('visitor locked warning')[0]!=7:raise ValueError('Visitor bypassed diary privacy')
                    draw('visitor locked warning');step(0x8000);step(count=12)
                    snapshot('visitor dismissed privacy warning')
                    step(0x4000);step();snapshot('visitor locked calendar back')
                    step(0x4000);step(count=20)
                    snapshot('visitor locked diary closing')
                    if word(screen)!=0:raise ValueError('Locked diary owner failed to close')
                    write(live+16+98,b'\0')
                    check('privacy refusal leaves saved pages unchanged',live,expected_diary)
                for at in guards:check('fixture/stack guard',at,edge)
                return dict(native_visitor_diary_open_read_locked_close=True,calendar_modes=2,
                    native_calls=calls,assertions=assertions,rendered_frame_tested=False,
                    ordinary_room_entry_tested=False,visitor_edits_allowed=False,
                    saved_pages_unchanged=True,flashram_device_tested=False,
                    checkpoint_restore_required=True,hardware_tested=False)
            finally:write(mode,saved_mode)
        step(count=12);snapshot('calendar');draw('calendar')
        step(0x8000);step();step(0x8000);step(count=35)
        if snapshot('read')[0]!=3:raise ValueError('Native calendar did not open the monthly page')
        draw('read');step(0x8000);step(count=24)
        if snapshot('editor')[0]!=4 or word(sub+4)!=10:
            raise ValueError('Native diary did not enter its keyboard child')
        draw('editor')
        # Call the actual shared edit command, not a fabricated committed page.
        # Native keyboard ownership/init/draw is checked above; controller key
        # selection itself remains a separate ordinary-play check.
        for char in b'Diary':
            if entry('af_diary_menu_edit',[menu,screen+0x7EC,8,char])!=1:
                raise ValueError('Native diary edit command failed')
        if entry('af_diary_menu_edit',[menu,screen+0x7EC,5,0])!=1:
            raise ValueError('Native diary Done command failed')
        # The native Done routine owns child return, as in the installed adapter.
        keyboard=d['hooks']['menus']['keyboard'];descriptor=keyboard['owner_after']
        keyboard_base=word(parent+keyboard['owner_at']+16)-(descriptor[4]-descriptor[2])
        vrom=descriptor[0];kd=files[vrom].extract(image);kr=files[vrom+0x10000].extract(image)
        ks=struct.unpack_from('>5I',kr)
        kl=relocate_verified_data(SimpleNamespace(ram=descriptor[2],resident_bytes=sum(ks[:4]),sections=ks),kd,kr,keyboard_base)
        at=0x808860A0-descriptor[2];target=keyboard_base+at
        call(target,[sub,overlay+0x10358],(target,kl[at:at+0x5C]))
        step(count=24)
        if snapshot('finish')[0]!=5 or word(sub+4)!=2:
            raise ValueError('Native keyboard did not return to diary confirmation')
        draw('finish');step(0x8000);step(count=6);step(0x8000);step(count=12)
        if snapshot('privacy')[0]!=6:raise ValueError('Native diary did not reach privacy confirmation')
        draw('privacy');step(0x8000);step(count=24)
        if snapshot('committed')[0]!=2:raise ValueError('Native diary did not commit and return to calendar')
        page=0x80676000+16+104+5*992
        check('committed English page',page,b'Diary')
        expected_diary=read(0x80676000,48048)
        write(bank,read(0x80126EA0,0xF980)+bytes(0x680))
        entry('af_v3_save_prepare',[bank]);check('format-eleven envelope',bank+0xF985,b'\x0B')
        if entry('af_v3_save_check',[bank,65536,0x80460020,0])!=1:
            raise ValueError('Native prepared diary save does not validate')
        entry('af_v3_save_reset');entry('af_v3_save_commit',[bank,0x80126EA0,0xF980])
        check('complete native diary save/reset/reload',0x80676000,expected_diary)
        draw('reloaded');step(0x4000);step();step(0x4000);step(count=20)
        if word(screen)!=0:raise ValueError('Native diary destructor retained an active owner')
        for at in guards:check('fixture/stack guard',at,edge)
        return dict(native_diary_open_read_keyboard=True,native_calls=calls,assertions=assertions,
            rendered_frame_tested=False,ordinary_room_entry_tested=False,save_codec_reload_tested=True,
            flashram_device_tested=False,controller_typing_tested=False,
            checkpoint_restore_required=True,hardware_tested=False)
    finally:
        write(0x8010EF90,saved_game)
        if visitor and sys.exc_info()[0] is None:
            at=0x8009C040
            call(at,[allocation],(at,core[at-CODE_RAM:at-CODE_RAM+32]))
        elif not visitor:write(current_game+0x78,arena_header)
