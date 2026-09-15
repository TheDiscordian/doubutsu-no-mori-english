OUTPUT_ARCH(mips)
ENTRY(af_v3_campsite_schedule)
SECTIONS {
    /* Proposed address only: this module is not installed by ABI 72. */
    . = 0x804A2100;
    .text : { *(.text.af_v3_campsite_schedule) *(.text*) }
    .rodata : { *(.rodata*) }
    .data : { *(.data*) *(.sdata*) }
    .bss : { *(.bss*) *(.sbss*) *(COMMON) }
    ASSERT(SIZEOF(.data) == 0 && SIZEOF(.bss) == 0, "Camper event state must have an explicit owner")
    ASSERT(. <= 0x804A4000, "Campsite event code exceeds proposed reservation")
    /DISCARD/ : { *(.MIPS.abiflags) *(.reginfo) *(.pdr) *(.comment) *(.gnu.attributes) }
}
