# Isolated event-artwork rendering fixture

Render the installed left stall, reflected right stall, and fortune table using
the emulator's actual N64 graphics path. This is a controlled model preview, not
ordinary scene, event, collision, shadow, or hardware acceptance. No diagnostic
code or assets are added to the playtest ROM.

Use the exact combined shared-stall cartridge, a fresh silent eight-MiB emulator,
and a checkpoint. Temporarily replace only the located title actor's drawing
callback. The fixture uses spare Expansion Pak RAM beyond the title reservation;
the normal heap ends at `80400000` and the title reservation at `80450000`.
Bind the actual cartridge and extracted building object by hash. Reject changed
owners, nonzero scratch space, missing title/heap guards, and wrong RAM sizes.

The independently compiled callback uses its own orthographic projection,
directional light, depth buffer, and model-view transform. It draws the installed
native display lists without rewriting them. The right entry therefore executes
its actual matrix push/reflection/pop and culling operations on the N64 graphics
path. Command space is checked against the actual static graphics pools at
`801540C0`, not the ordinary heap: pool stride `20410`, overlay offset `18F08`,
and overlay capacity 8192 bytes. Both depth clearing and command space remain
bounded. Compare complete
object/code data and outer guards after rendering, and reject native faults.

| Test range | Purpose |
| --- | --- |
| `80500000..80502000` | Callback and its constants |
| `80503000..805030C0` | Selection/counters and two native matrices |
| `80510000..805AAD80` | Complete installed building object |
| `80600000..80625800` | Separate 320×240 16-bit depth buffer |

Capture only the isolated emulator, without a desktop display window or audio.
Restore the complete checkpoint and verify the title callback and memory guards
before graceful shutdown. Never use or modify a user's save. Keep generated
assets, code binaries, scenarios, and captures ignored and local.

Allow one initial native attempt and one justified setup retry. Limit fixture
construction/debugging to thirty minutes for this batch. Record incomplete
evidence honestly; this budget does not waive actual graphics or memory defects.
