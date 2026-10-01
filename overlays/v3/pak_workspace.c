#include "pak_native.h"
#include "console_storage.h"
typedef __UINTPTR_TYPE__ address;
static const unsigned char binding[32]="AFV3-PASSPORT-PLAYER-1";
static int separate(const void *a,unsigned an,const void *b,unsigned bn) {
    address x=(address)a,y=(address)b;
    if(an>(address)-1-x || bn>(address)-1-y)return 0;
    return x<=y?y-x>=an:x-y>=bn;
}
int af_pi_workspace_acquire(AFPIWorkspace *out) {
    AFConsoleWorkspace loan;
    if(!out || !af_v3_save_workspace_acquire(&loan))return 0;
    if(loan.scratch_bytes<AF_PI_SCRATCH || loan.hash_bytes<AF_PAK_HASH_BYTES ||
       !separate(out,sizeof(*out),loan.data,loan.scratch_bytes) ||
       !separate(out,sizeof(*out),loan.index,loan.hash_bytes)) {
        (void)af_v3_save_workspace_release();return 0;
    }
    out->notes[0]=loan.data;out->notes[1]=loan.data+AF_PI_NOTE;
    out->raw=loan.data+2*AF_PI_NOTE;out->hash=loan.index;out->binding=binding;
    return 1;
}
int af_pi_workspace_release(void) {
    return af_v3_save_workspace_release()==AF_SAVE_OK;
}
