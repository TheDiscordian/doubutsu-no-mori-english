/* The builder copies every original control and installs the summer row,
 * adding a relocation for each pointer in this complete 29-row directory. */
.section .rodata.af_v3_camper_controls,"a",@progbits
.balign 16
.globl af_v3_camper_controls
af_v3_camper_controls:
    .space 29 * 32
