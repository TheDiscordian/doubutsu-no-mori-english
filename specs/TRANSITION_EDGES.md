# Building-transition screen edges

## V1-18

The user reports a thin strip of scene pixels along the top during the
silhouette-shaped building-entry transition. The native radial-wipe renderer
at `80083E08` loads one of three segmented models at `04004740`, `04004D60`,
and `04005360` from `gameplay_keep` (`00A22000`). Their outer vertices occupy
X ±16,000 and Y ±12,000 at Z zero. All three use the same projection and scale.

Startup at `80083C00` uses a 60-degree vertical field of view, 4:3 aspect, and
camera distance 400. The draw routine applies X/Y scale 0.019. After native
16.16 scale conversion, the outer bounds are approximately X 2.06–317.94 and
Y 1.55–238.45 on the 320×240 framebuffer. The fullscreen view/scissor is already
0,0–320,240: the geometry is too small, rather than the top rows being clipped
by a deliberately inset scissor.

## Correction

Change only the draw-scale float at RAM `80116D24` from 0.019 to 0.0195.
The `lwc1 f0,6D24(at)` at `80083F0C` binds this value. Fixed-point scale gives
outer bounds approximately X −2.00–322.00 and Y −1.50–241.50, safely beyond
all four screen edges. The shape is enlarged by about 2.6%; do not replace the
silhouette or add a permanent screen border. Retain the original projection,
mesh, texture, UVs, timing, directions, scene decisions, and allocation size.
The redundant comparison constant at `80116D20` remains untouched.

Require the exact combined font-edge candidate and verify the unchanged native
transition code, model ranges, scale-load instruction, and old float. The
cartridge rebuild changes only that four-byte range in main code; unrelated
resources and the font correction are retained. The complete UPS must reproduce
the 32-MiB output from the verified retail ROM. No saved format changes.

## Checks

Focused tests cover the exact changed range, every other resource, fixed-point
screen bounds, rejected unexpected inputs, and complete patch reconstruction.
The isolated native fixture calls the actual startup/type/draw routines and
samples a white framebuffer through the original and corrected meshes. It
checks guarded scratch, retained assets/code, unchanged saved data, and restored
checkpoint. A controlled wipe is not an ordinary building-entry playthrough or
original-hardware acceptance.
