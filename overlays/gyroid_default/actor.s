.section .native,"ax",@progbits
.incbin "native.bin"
.section .gyroid_default,"a",@progbits
.balign 16
.global af_gyroid_native_default
af_gyroid_native_default:
.incbin "saved-default.bin"
