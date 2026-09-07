.set noreorder
.section .text
.balign 16
.globl af_mail_grade_entry
af_mail_grade_entry:
    j af_mail_grade
    nop
.globl af_mail_word_entry
af_mail_word_entry:
    j af_mail_word_rate
    nop
.word 0x41464D47, 1, 96, 1024
.space 0x24C-(.-af_mail_grade_entry)
.globl af_mail_legacy_entry
af_mail_legacy_entry:
    j af_mail_word_rate_native
    nop
.balign 16
