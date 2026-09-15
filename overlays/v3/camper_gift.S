/* The two normal item-give paths store their full item before the callback.
 * Record that item, preserving callback arguments and the original return PC.
 * This is transient quest-manager state, never a saved item or town field. */
.set noreorder
.set noat
.set nomacro
.text
.globl af_v3_camper_gift
af_v3_camper_gift:
    lhu $t0, 0x1d8($a0)
    lui $t1, %hi(camper_last_gift)
    sh $t0, %lo(camper_last_gift)($t1)
    jr $t9
     nop

/* Called at the original constructor's native five-byte clear operation. */
.globl af_v3_camper_gift_reset
af_v3_camper_gift_reset:
    lui $t0, %hi(camper_last_gift)
    sh $zero, %lo(camper_last_gift)($t0)
    j native_clear
     nop
