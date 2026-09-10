OUTPUT_ARCH(mips)
ENTRY(af_birthday_draw)
af_birthday_scale = 0x800E041C;
af_birthday_translate = 0x800E0314;
af_birthday_matrix = 0x800E13C4;
af_birthday_number = 0x8009264C;
af_birthday_font = 0x80090E98;
SECTIONS {
    . = 0x8089A684;
    .draw : { *(.text .text.*) *(.rodata .rodata.*) }
    __birthday_end = .;
    /DISCARD/ : { *(.MIPS.abiflags) *(.reginfo) *(.pdr) *(.comment) *(.gnu.attributes) }
}
