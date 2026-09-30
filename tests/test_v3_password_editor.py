"""Current code keyboard: complete diary prefix, allocation, and input rules."""
import ctypes
import json
import os
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import CODE_RAM,CODE_VROM,by_vrom,sha256,u32
from catalogue_names import Image
from npc_mail_show import relocate_verified_data
from v3_furniture_install import inputs,reuse_resource_tail
import v3_password_editor as editor

OUT=ROOT/os.environ.get('V3_PASSWORD_EDITOR','build/v3-nook-password-editor-05')


class PasswordEditorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.image,cls.report=inputs(OUT/'build-lock.json')
        cls.base,cls.prior=inputs(OUT/'base-lock.json')

    def test_complete_diary_keyboard_and_unrelated_resources_retained(self):
        files,before=by_vrom(self.image),by_vrom(self.base)
        self.assertEqual(set(files),set(before))
        r=self.report['password_editor'];c=r['compiled']
        old=before[editor.VROM].extract(self.base)
        current=files[editor.VROM].extract(self.image)
        oldrel=before[editor.RELOC].extract(self.base)
        rel=files[editor.RELOC].extract(self.image)
        self.assertEqual(sha256(current),c['overlay_sha256'])
        self.assertEqual(len(old),r['complete_previous_bytes'])
        self.assertEqual(current,(OUT/'password_editor/installed.bin').read_bytes())
        changed=set(c['touched_offsets'])
        for ram in (0x80200010,0x80370010):
            a=relocate_verified_data(Image(editor.RAM,len(old),struct.unpack_from('>5I',oldrel)),old,oldrel,ram)
            b=relocate_verified_data(Image(editor.RAM,len(current),struct.unpack_from('>5I',rel)),current,rel,ram)
            self.assertEqual(bytes(v for i,v in enumerate(a) if i not in changed),
                             bytes(b[i] for i in range(len(a)) if i not in changed))
        diary=self.report['equipment_resources']['diaries']['hooks']['menus']['keyboard']
        original=self.prior['equipment_resources']['diaries']['hooks']['menus']['keyboard']
        self.assertEqual(diary['symbols'],original['symbols'])
        self.assertEqual(diary['overlay_sha256'],sha256(current))
        self.assertEqual(diary['relocation_sha256'],sha256(rel))
        self.assertEqual(diary['owner_after'][:4],
            [editor.VROM,editor.VROM+len(current),editor.RAM,editor.RAM+len(current)])
        for name in ('init','update'):
            self.assertEqual(r['retained_diary_'+name],editor.RAM+diary['symbols']['af_diary_editor_'+name])
        self.assertEqual(u32(current,0x8088883C-editor.RAM),editor.RAM+c['symbols']['af_pw_editor_update'])
        self.assertEqual(struct.unpack_from('>4I',files[editor.OWNER].extract(self.image),11088),
            tuple(diary['owner_after'][:4]))
        self.assertEqual(self.report['save_codec'],self.prior['save_codec'])
        self.assertEqual(self.report['save_runtime'],self.prior['save_runtime'])
        self.assertTrue(self.report['equipment_resources']['passwords']['keyboard_installed'])
        self.assertFalse(r['shop_route_installed'])
        from v3_asset_loader import BLOB,MODULE
        for v in files:
            if v not in (editor.VROM,editor.RELOC,editor.OWNER,CODE_VROM,0x1060,0x19D40,BLOB,MODULE):
                self.assertEqual(files[v].extract(self.image),before[v].extract(self.base),hex(v))

    def test_whole_owner_zero_gap_plans_and_menu_growth(self):
        files,before=by_vrom(self.image),by_vrom(self.base)
        plans=self.report['resource_growth']
        self.assertTrue({editor.VROM,editor.RELOC}<=set(r['vrom'] for r in plans))
        for plan in plans:
            start,end=plan['physical'],plan['physical']+plan['bytes']
            self.assertFalse(any(self.base[start:end]))
            self.assertEqual(files[plan['vrom']].pstart,start)
            self.assertEqual(sha256(self.image[start:end]),plan['sha256'])
            self.assertEqual(self.image[before[plan['vrom']].pstart:
                before[plan['vrom']].pend or before[plan['vrom']].pstart+before[plan['vrom']].size],
                self.base[before[plan['vrom']].pstart:
                before[plan['vrom']].pend or before[plan['vrom']].pstart+before[plan['vrom']].size])
        r=self.report['password_editor'];core=files[CODE_VROM].extract(self.image)
        hi,lo=u32(core,0x800C4AFC-CODE_RAM),u32(core,0x800C4B10-CODE_RAM)
        self.assertEqual(((hi&65535)<<16)+struct.unpack('>h',struct.pack('>H',lo&65535))[0],r['pool_bound'])
        self.assertEqual(r['pool_bound']-r['previous_pool_bound'],r['additional_menu_pool_bytes'])
        self.assertEqual(self.report['physical_resources'],self.prior['physical_resources'])
        from v3_asset_loader import BLOB
        blob=files[BLOB].extract(self.image)
        prefix,reused=reuse_resource_tail(self.image,self.report,blob)
        self.assertEqual(prefix,blob[:len(prefix)])
        self.assertFalse(any(blob[len(prefix):]))

    def test_two_row_commands_and_cancel(self):
        class Draft(ctypes.Structure):
            _fields_=[('text',ctypes.c_ubyte*28),('line',ctypes.c_ubyte),
                ('cursor',ctypes.c_ubyte),('finished',ctypes.c_ubyte)]
        with tempfile.TemporaryDirectory(prefix='v3-code-editor-') as tmp:
            lib=Path(tmp)/'draft.so'
            result=subprocess.run(['cc','-std=c11','-Wall','-Wextra','-Werror','-shared','-fPIC',
                str(ROOT/'overlays/v3/password_edit.c'),'-o',str(lib)],capture_output=True,text=True,timeout=30)
            self.assertEqual(result.returncode,0,result.stderr)
            edit=ctypes.CDLL(str(lib)).af_pw_edit
            edit.argtypes=[ctypes.POINTER(Draft),ctypes.c_int,ctypes.c_uint]
            # Commands use the accepted shared keyboard enum, not guessed IDs.
            header=(ROOT/'overlays/keyboard_grid/core.h').read_text()
            import re
            header=re.sub(r'/\*.*?\*/','',header,flags=re.S)
            enum=re.search(r'enum\s+af_grid_command\s*\{([^}]*)\}',header,re.S).group(1)
            commands={};n=0
            for part in enum.split(','):
                token=part.strip()
                if not token:continue
                if '=' in token:token,value=map(str.strip,token.split('='));n=int(value,0)
                commands[token]=n;n+=1
            d=Draft();d.text[:]=b' '*28
            def run(command,code=0):return edit(ctypes.byref(d),commands['AF_GRID_'+command],code)
            for ch in b'ABCDEFGHIJKLMN':self.assertEqual(run('INSERT',ch),1)
            self.assertEqual((d.line,d.cursor),(1,0))
            for ch in b'abcdefghij%&#@':self.assertEqual(run('INSERT',ch),1)
            self.assertEqual((d.line,d.cursor),(1,14))
            self.assertEqual(run('INSERT',ord('Z')),3)
            self.assertEqual(run('DONE'),2)
            self.assertEqual(bytes(d.text),b'ABCDEFGHIJKLMNabcdefghij%&#@')
            self.assertEqual(run('BACKSPACE'),3)
            d=Draft();d.text[:]=b' '*28
            self.assertEqual(run('INSERT',ord('!')),3)
            self.assertEqual(run('DONE'),2) # blank/unfinished second row cancels
            self.assertEqual(bytes(d.text),b' '*28)
            d=Draft();d.text[:]=b'A'*27+b'!';d.line=1
            self.assertEqual(run('DONE'),3)
            self.assertFalse(d.finished)
            d=Draft();d.text[:]=b'A'*14+b' '*14;d.line=1
            self.assertEqual(run('BACKSPACE'),1)
            self.assertEqual((d.line,d.cursor),(0,13))
            self.assertEqual(d.text[13],ord(' '))


if __name__=='__main__':unittest.main()
