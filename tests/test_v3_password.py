"""One shared password codec, checked against the pinned donor implementation."""
import copy
import json
from pathlib import Path
import re
import struct
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import sha256
from v3_furniture_pipeline import Source
import v3_password as password

OUTPUT=ROOT/'build/v3-password-prepared-02'


def oracle_source():
    """Compile local CC0 reference unchanged; never commit donor tables/strings."""
    source=(ROOT/password.SOURCE_FILE).read_bytes()
    header=(ROOT/'local/ac-decomp/include/m_mail_password_check.h').read_bytes()
    font=(ROOT/'local/ac-decomp/include/m_font.h').read_bytes()
    if (sha256(source)!=password.SOURCE_SHA
            or sha256(header)!='060f66ac33e46176b5b09bd3dfec3bb5869ba93e5fc0dcd8049a8f58128bf2dc'
            or sha256(font)!='7a6354cc7d29d0d8fef7579d26fe40e58a19b0bbde40ca8c20f604f1b4134ded'):
        raise ValueError('Changed reference password implementation or headers')
    defines='\n'.join(re.findall(r'^#define CHAR_\w+ [^\n]+',font.decode(),re.M))
    header=re.sub(r'^#include[^\n]+','',header.decode(),flags=re.M)
    source=source.decode().split('static u8 usable_to_fontnum',1)[1].split(
        'static int mMpswd_check_present_famicom',1)[0]
    prefix='''#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <strings.h>
#include "overlays/v3/password.h"
typedef uint8_t u8;
typedef uint16_t u16;
typedef uint32_t u32;
typedef u16 mActor_name_t;
#define PLAYER_NAME_LEN 8
#define TRUE 1
#define FALSE 0
#define ABS abs
#define __abs abs
'''
    wrappers='''
void ref_encode(const af_v3_password *v,u8 *text,unsigned *coverage) {
    u8 raw[28]={0};
    mMpswd_make_password(text,v->type,v->hit_rate_index,(u8 *)v->str0,(u8 *)v->str1,
                        v->item,v->npc_type,v->npc_code);
    /* Observe actual transform keys, without changing the reference encoder. */
    mMpswd_make_passcode(raw,v->type,v->hit_rate_index,(u8 *)v->str0,(u8 *)v->str1,
                        v->item,v->npc_type,v->npc_code);
    mMpswd_substitution_cipher(raw);coverage[0]|=1u<<(raw[18]&15);
    mMpswd_transposition_cipher(raw,1,0);coverage[1]|=1u<<(raw[13]&3);
    mMpswd_bit_shuffle(raw,0);coverage[2]|=1u<<(raw[15]>>4);
    mMpswd_chg_RSA_cipher(raw);coverage[3]|=1u<<(raw[1]&15);
    mMpswd_bit_mix_code(raw);coverage[4]|=1u<<(raw[2]&3);
    mMpswd_bit_shuffle(raw,1);coverage[5]|=1u<<(raw[9]&15);
    for(int i=0;i<28;i++) if(text[i]==CHAR_HASHTAG) text[i]='#';
}
int ref_decode(const u8 *text,af_v3_password *out) {
    u8 input[28],payload[21];mMpswd_password_c value={0};
    memcpy(input,text,28);
    for(int i=0;i<28;i++) if(input[i]=='#') input[i]=CHAR_HASHTAG;
    if(!mMpswd_decode_code(payload,input)) return 0;
    mMpswd_password(payload,&value);
    if(mMpswd_password_zuru_check(&value)) return 0;
    memset(out,0,sizeof(*out));
    out->item=value.item;out->type=value.type;out->hit_rate_index=value.hit_rate_index;
    out->npc_type=value.npc_type;out->npc_code=value.npc_code;out->checksum=value.checksum;
    memcpy(out->str0,value.str0,8);memcpy(out->str1,value.str1,8);
    return 1;
}
void ref_raw(const u8 *payload,u8 *text) {
    u8 work[28]={0};memcpy(work,payload,20);
    mMpswd_substitution_cipher(work);mMpswd_transposition_cipher(work,1,0);
    mMpswd_bit_shuffle(work,0);mMpswd_chg_RSA_cipher(work);mMpswd_bit_mix_code(work);
    mMpswd_bit_shuffle(work,1);mMpswd_transposition_cipher(work,0,1);
    mMpswd_chg_6bits_code(text,work);mMpswd_chg_common_font_code(text);
    for(int i=0;i<28;i++) if(text[i]==CHAR_HASHTAG) text[i]='#';
}
'''
    return prefix+defines+'\n'+header+'\nstatic u8 usable_to_fontnum'+source+wrappers


class PasswordTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
            (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
        cls.data,cls.report=password.discover(cls.source)

    def test_complete_prepared_packet_and_mips_kernel(self):
        self.assertEqual(self.data,(OUTPUT/'password-tables.bin').read_bytes())
        report=json.loads((OUTPUT/'password.json').read_bytes())
        self.assertEqual(report['sha256'],sha256(self.data))
        self.assertEqual(self.report['tables'],report['tables'])
        self.assertEqual(len(report['tables']),48)
        self.assertFalse(any(report[k] for k in ('runtime_installed','keyboard_installed',
                                               'eligibility_installed','acquisition_installed')))
        self.assertFalse(report['kernel']['linked'])
        self.assertIsNone(report['kernel']['resident_address'])
        obj=(OUTPUT/'password.o').read_bytes()
        self.assertEqual(obj[:6],b'\x7fELF\x01\x02')
        self.assertEqual(struct.unpack_from('>HH',obj,16),(1,8))
        self.assertEqual(sha256(obj),report['kernel']['sha256'])
        for path,digest in report['sources'].items():
            self.assertEqual(sha256((ROOT/path).read_bytes()),digest,path)
        self.assertEqual([len(r['source_items']) for r in report['source_lists']],[5,1,1])

    def test_changed_code_tables_and_directories_reject(self):
        bad=copy.copy(self.source);bad.rel=bytearray(self.source.rel)
        bad.rel[bad.sections[1][0]+password.CODE_END-1]^=1
        with self.assertRaisesRegex(ValueError,'complete source password codec'):password.discover(bad)
        for symbol in ('usable_to_fontnum','mMpswd_chg_code_table','mMpswd_prime_number','key_idx$688'):
            bad=copy.copy(self.source);bad.data=bytearray(self.source.data)
            bad.data[self.source.symbol(symbol)[0]]^=1
            with self.assertRaises(ValueError):password.discover(bad)
        for symbol in ('mMpswd_transposition_cipher_char_table','mMpswd_transposition_cipher_char0_table',
                       'mMpswd_transposition_cipher_char1_table','mMpswd_select_idx_table'):
            bad=copy.copy(self.source);bad.relocations=dict(self.source.relocations)
            at=self.source.symbol(symbol)[0];kind,local,section,target=bad.relocations[at]
            bad.relocations[at]=(kind,local,section,target+4)
            with self.assertRaises(ValueError):password.discover(bad)

    def test_donor_reference_and_bounds_under_sanitizers(self):
        (ROOT/'build').mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(prefix='v3-password-test-',dir=ROOT/'build') as tmp:
            temporary=Path(tmp);oracle=temporary/'reference.c';binary=temporary/'test'
            oracle.write_text(oracle_source())
            subprocess.run(['cc','-std=c11','-O1','-g','-Wall','-Wextra',
                '-ftrivial-auto-var-init=zero','-fsanitize=address,undefined','-fno-omit-frame-pointer',
                '-I',str(ROOT),str(oracle),str(ROOT/'tests/v3_password_test.c'),
                '-o',str(binary)],check=True,capture_output=True,text=True,timeout=30)
            result=subprocess.run([str(binary),str(OUTPUT/'password-tables.bin')],check=True,
                capture_output=True,text=True,timeout=30)
            self.assertIn('All six types, donor agreement, aliases, and transactional bounds pass',result.stdout)
            print(result.stdout.strip())
