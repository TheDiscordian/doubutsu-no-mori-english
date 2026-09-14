# V3 furniture pocket searches

`800B8128` and `800B8544` find the first matching pocket and count matching
pockets respectively. Requests for furniture type 1 include original furniture
and selected imported profiles. Other requested types execute the complete native
functions through unchanged prologue bridges. The requested type retains its
native 16-bit conversion; conditions retain the full argument comparison.

The adapter reads exactly 15 halfword pockets at private + `14` and their two-bit
conditions at private + `34`. It never writes the private data. A null private
pointer returns -1 for an index and zero for a count. Unavailable imports do not
match furniture searches. Searching raw type 3 retains native behaviour; this
query does not enable those IDs for gameplay or replace the save/profile guard.

Both complete native functions are hash-bound, including the unrolled original
count loop. Only their first two stack instructions change. The original index
body is 124 bytes and the count body is 424 bytes. Two sixteen-byte bridges at
`8046B100` and `8046B110` reproduce the original stack setup and resume the native
bodies at their third instruction. The compiled 372-byte helper at `8046B200`
uses the existing classifier at `80468000`. Each public helper has a 48-byte
stack frame. ABI 12 retains the 48-KiB resident reservation and all earlier helpers.

Four focused checks include sanitized host execution across all slots, rotations,
and conditions, complete native-body/bridge checks, exact composition, patch
reconstruction, guards/CRC, and unchanged import-free V2 output. The
[native checkpoint](../docs/checkpoints/V3_FURNITURE_POCKETS.md) records 28 complete
native query calls, including real original-type fallback execution.

Ordinary acquisition, catalogue collection/order lists, scoring, and save/profile
integration remain required. No complete item is enabled in the web patcher.
