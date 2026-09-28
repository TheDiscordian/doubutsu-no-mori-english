"""Source bindings for the shared Tortimer conversation/attendance controller."""
import struct

from aflib import sha256
from v3_asset_loader import ROOT

REFERENCES = {
    'src/actor/npc/event/ac_ev_soncho2_talk.c_inc':
        '60269271c9d447cddb5145956e8316822e5d5d4494ed1aa95c79f37901ce1a8a',
    'src/actor/npc/ac_taisou_npc0_talk.c_inc':
        '13bf09a1d1aac78b8b7c30791e869c341a32c29257cd969b53f83334024abf47',
    'include/m_msg_data.h':
        'daf12151b738bcb7841faff53934948f9ba7a3ea5ca1c5a548e626cf6b0506e4',
}
FUNCTIONS = (
    (0x1B477C,'aES2_kinenhin_msg',36,'ac503352e21a511851e67c30552959e3bbf725eb61964c5cc3f5f5df51ac26cb','e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855'),
    (0x1B47A0,'aES2_LightHouse_set_free_str',164,'f9e5a67856796f23b6a6422eeb8c7b4c567f9fdcd50a4baedcc37a65b1e8aad0','86486c89ef6806e4ef06cbf4b8d2e5becef579e02ea4cbe04c13051bc3a85636'),
    (0x1B4844,'aES2_talk_before_give',180,'a3129746c1e60b877ecd74ae82f6861db8ef00509f0f15bfebe097324683bacc','11472c2e8fcda91a9e4a7d8bd26c86a0f61b418f26dbe5575e8fe58338df4192'),
    (0x1B48F8,'aES2_talk_give',172,'adb99cc52df75acb980d5f865c3c20f9778e223011b86d6f0b00d59aeec0d699','1ff0fdf3935ce72e6b80c453a9d3dad539d51c5059e27cd50c707dd8bde0f3e4'),
    (0x1B49A4,'aES2_change_talk_proc',12,'9e50b668002ad4eef5b84d24da1546c2d4774990e4437ad7c8ec50ca9c070195','e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855'),
    (0x1B49B0,'aES2_set_norm_talk_info',528,'1d3b94ee70c69a80574ba1ccdd59067eb1c19bd73ddd3679bade5af692a3a28e','d7c78aa70e97b19fa42765d64ccf07b1d96a499872298ae3b49962414b33dba8'),
    (0x1B4BC0,'aES2_norm_talk_request',72,'936c0d3f5aa4e85554d99d9ae7dec0e65b95be30ed7238c1d58e3c5fb11e2b9f','485c2cc72f1cede5f4363057df995806e5dc51e9c9bb82f5df26a539176894f9'),
    (0x1B4C08,'aES2_talk_init',164,'6e7d254653e58a7b937d09914bd760904523252b442a287e34cb6f5641d7b2a6','129fa3a8469b1c86476a9606275093942d38c8c03a70c4cd107981613280f5cd'),
    (0x1B4CAC,'aES2_talk_end_chk',172,'041d802ef8313165f280198b76e8ec5fc472612439338d85c1926fa9168b6bc8','0e6e5a09b0ff85d3d011f56ca5021483cf66887a14c1af966a510b4a71747287'),
    (0x21933C,'aTS0_talk_init',184,'2a2d4d791098405e7222b4d689653c9133904e6893d3c847b68534e7a5dd55da','8ed0b8c54bf64ded5e6fe1e1fabe115db004bc30af4ffd28f99dcca773634c6d'),
)


def discover(source):
    for path,digest in REFERENCES.items():
        if sha256((ROOT/'local/ac-decomp'/path).read_bytes())!=digest:
            raise ValueError('Changed Tortimer conversation reference: '+path)
    functions=[]
    for at,name,size,digest,reloc_digest in FUNCTIONS:
        raw,record=source.function(at)
        reloc=b''.join(struct.pack('>5I',p,*v) for p,v in sorted(record['relocations'].items()))
        if (record['symbol']!=name or len(raw)!=size or sha256(raw)!=digest or
                sha256(reloc)!=reloc_digest):
            raise ValueError('Changed complete Tortimer conversation: '+name)
        functions.append(record)
    return dict(format='AFV3-HOLIDAY-TALK-1',functions=functions,references=REFERENCES,
        holiday_events=28,vacation_events=[101,102],exercise_attendance_event=103,
        dialogue_source='GAFE01-r0 official message IDs; message resources not installed',
        attendance_trigger='actual Tortimer talk-init only',
        runtime_installed=False,actor_installed=False,messages_installed=False,
        exercise_card_conversation_installed=False,
        sources={p:sha256((ROOT/p).read_bytes()) for p in (
            'overlays/v3/holiday_talk.c','overlays/v3/holiday_talk.h',
            'overlays/v3/holiday_rewards.c','overlays/v3/holiday_rewards.h',
            'overlays/v3/diary_calendar.c','overlays/v3/diary.h')})
