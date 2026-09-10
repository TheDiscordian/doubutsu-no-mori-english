# Published compiler inspection

The published libdragon OCI index is reachable at
`ghcr.io/dragonminded/libdragon@sha256:b68e8dfd393f76ba69c1ba62da6b42dcda8b5b52eaa8fb96adc5aab7865a2d40`.
Its Linux amd64 manifest is
`sha256:efa724f6fa703eadb04aa72e3af230d6b11e0a8cb7487faaa012f6714050b4d3`;
the index also references an attestation manifest at
`sha256:2d21c6dc17d38842e1b5c8026ebd42afaa2fe0a9ff3f3f385fbe30dbcd771cc4`.
The installed published image uses `/n64_toolchain/bin/`, identifies GCC 14.2.0,
and has exactly the same nine executable hashes documented in
[the compiler identity record](../TOOLCHAIN.md).

Its filesystem layers are:

- `sha256:351d919b2c06105efcb263b77e23bff2f166d23bcb487f5185d884bfada142f3`
- `sha256:d214b031b7133e262fbd7000b3cf8f028611570a86ba2f0b2259e8f6c0760da5`
- `sha256:ada4c3c28db9af4ab59554753f8d2331babf97565bcbb0aa5d3aca0c92fbf171`

The local development image has those same three layers plus
`sha256:603ed62100fcc5d2d64e5dfd4e1ef130920649e6f181b8ee7da6fbca41a01fb0`.
No existing image is modified or published by this inspection. The nine-file
comparison is not a claim that every file or host library in both images matches.

The [portable integration specification](../../specs/PORTABLE_TOOLCHAIN.md)
defines actual-image provenance, narrow compatibility with historical metadata
fingerprints, and the required complete clean build. Implementation and public-image
rebuild execution remain pending; the passing full source rebuild uses the existing
local image and is separately recorded in [the base](V0_REBUILD.md) and
[v1](V1_REBUILD.md) checkpoints.
