.set noreorder
.set noat
.text

# These are call-site-specific tail shims, not independently callable APIs.
# The guarded board call's return address supplies its actual relocated base.
# Read mode is menu.data0 == 1, independently of its animation/procedure state.
.globl af_mail_body_hook
.ent af_mail_body_hook
af_mail_body_hook:
    lw      $t0, 0x38($a1)
    addiu   $t1, $zero, 1
    beq     $t0, $t1, 1f
    nop
    addiu   $t9, $ra, -0x60C
    jr      $t9
    nop
1:
    j       af_mail_read_body
    nop
.end af_mail_body_hook

.globl af_mail_footer_hook
.ent af_mail_footer_hook
af_mail_footer_hook:
    lw      $t0, 0x2C($a0)
    lui     $t1, 1
    addu    $t0, $t0, $t1
    lw      $t0, 0x420($t0)
    addiu   $t1, $zero, 1
    beq     $t0, $t1, 2f
    nop
    addiu   $t9, $ra, -0x6F8
    jr      $t9
    nop
2:
    j       af_mail_read_footer
    nop
.end af_mail_footer_hook
