.section .native,"ax",@progbits
.incbin "native.bin"
/* Original 48-byte state, then 16 bytes reserved for the draw callback. */
.space 64,0
.section .hboard_defaults,"a",@progbits
.balign 16
.global af_hboard_native_default
af_hboard_native_default:
.incbin "saved-default.bin"
.global af_hboard_english_default
af_hboard_english_default:
.incbin "english-default.bin"
