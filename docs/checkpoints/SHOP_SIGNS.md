# English SOLD OUT and keyboard-label correction

`build/shop-signs-01/animal-forest-halfwidth.z64` retains the complete
Nookington/grid/artwork/conversation build, adds the exact English SOLD OUT
texture, and corrects the three keyboard-hint character bytes found during
the isolated screen check. ROM SHA-256:
`58e02d5ccc8807ce6adffbcfa20502a10df0f7b2639147956ae1a14e3ca3de74`.
UPS SHA-256:
`c986a1bdc50195fd6b0a352ce69bb6651b1f2fedb06453b4e9503edf94bf0efc`.
This 32-MiB, four-MiB-RAM candidate does not include the title and is not a new
recommended handoff. See the [specification](../../specs/SHOP_SIGNS.md).

Three focused checks pass in 7.019 seconds: exact English pixels, all twelve
native model vertices and visible palette colours, native hint glyph meanings,
rejection of unrelated code/source changes, strict current shared-editor
verification, complete previous-resource retention, and UPS reconstruction.
The SOLD OUT texture changes 197 stored bytes; the hint correction changes
three. Neither changes code, model geometry, palettes, memory use, or saved data.

The whole combined text counter passes on the preceding Nookington candidate;
the exact shop-sign ROM/report pair is registered for the same current-route
checks. This artwork/label batch does not introduce a new runtime text reader.
The keyboard's verified entry/clear/Q/q observations and remaining native-test
limits are recorded in [its checkpoint](KEYBOARD_GRID.md).

Continue the police station's English sign/wanted poster, other remaining
decorative artwork, and final title combination. Native ordinary shop display,
normal save/restart, and hardware acceptance remain unverified. Do not repeat
the completed keyboard setup batch; future checks must control frame duration.
