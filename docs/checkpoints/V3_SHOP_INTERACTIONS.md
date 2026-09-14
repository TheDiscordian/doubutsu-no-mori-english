# V3 shop interaction checkpoint

The [interaction adapter](../../specs/V3_SHOP_INTERACTIONS.md) installs four
furniture decisions across all five native shopkeeper actors.
Cartridge: `build/v3-shop-actors-01/animal-forest-v3-asset-loader.z64`.

- ROM SHA-256: `403507d932dc64733a2422a1be59f665548f167581cd965e557c2e28d98cfd6f`.
- UPS SHA-256: `d6e84884a8549a1a4ee31f02f86363d8ab08bd70ddfd323d0482a4adc8c4b129`.
- Helper: 1,520 bytes, SHA-256 `0379530872ae3c1c3d1f8cba7fd8a613f1bdbc8e4ceef2126892f9f466ae9b80`.
- ABI 17; unchanged resident allocation and save/profile format.

```sh
python3 tools/v3_asset_loader.py --shop-actors --output build/v3-shop-actors-01
python3 -m unittest discover -s tests -p test_v3_shop_actors.py -v
```

Construction and all three focused tests pass. The tests check the complete
five installed actors and unchanged relocations/descriptors, exact twenty
windows, rejected descriptor mutation, compiled helper/query/guard boundaries,
full-width return-register instructions, startup CRC/ABI, current composition,
UPS reconstruction, and exact import-free V2.

## Native execution

```sh
python3 tools/emulator_smoke.py \
  --rom build/v3-shop-actors-01/animal-forest-v3-asset-loader.z64 \
  --output build/v3-shop-actors-native-02 \
  --scenario tests/scenarios/v3_shop_actors.json --expansion-pak \
  --no-initial-screenshot --seconds 180 \
  --xvfb /home/discordian/Games/OpenRSC/headless/vendor/usr/bin/Xvfb
```

The combined pass records 148 steps, 43 native calls, and 94 passing assertions.

- Native loading/relocation of each complete shop actor matches its independent
  image, including the twins' BSS and unchanged address-biased price constants.
- Forty live-register cases cover each changed window with an imported item
  and an original-category fallback. Both imports are represented. Full integer
  and floating registers, HI/LO, stack, return register, intended native outputs,
  and the actual continuation address match.
- Thirty complete native lottery-ticket decisions cover both imports, original
  furniture, an excluded original category, unknown imports, and disabled oil
  drum across all five actors.
- The delivery-only tail invokes the unchanged native pending-order loop with
  oil drum and haz-mat barrel at different shop levels. Both complete 164-byte
  letters match the independent reference, including all English captured-name
  bytes and real attachment IDs. The complete 1,040-byte reader outputs match.
- The expected whole live save matches: both pending item fields clear only
  after mailbox receipt, their other pending metadata stays intact, and no
  unrelated saved data changes. The creator detaches after delivery.
- Complete code, heap/stack/translation guards, and the fault pointer pass.
  Fixture globals/live data are restored; checkpoint restoration and graceful
  shutdown pass. No physical audio, FlashRAM/Pak write, or user save is involved.

This closes the two-letter/read-tail uncertainty recorded in
[the stock checkpoint](V3_SHOPS.md). Its already passing stock-selection prefix
is not replayed; unchanged catalogue/collection/FlashRAM evidence is reused.
Ordinary shop controls, payment confirmation, floor presentation/removal, full
item lifecycle, and original-hardware acceptance are not claimed.

## Setup failure

`v3-shop-actors-native-01` stops before actor loading because the fixture invokes
the generic relocation model without the shops' established address-biased
turnip-price constant. The existing `shop_units.PRICE_BIASES` records supply the
exact per-actor values. The fixture binds the complete current actor/relocation
hashes, passes that existing exception to the model, and retries once. The retry
passes actual native relocation and all remaining checks. No cartridge fix or
additional setup retry is needed; harness work remains within 30 minutes.

## Next implementation

The independent `Shop_Design` owner still rejects imported IDs when choosing
a reserve point, reading the floor item, and removing sold furniture. Its three
verified native `1ECD` upper-bound checks are the next implementation targets.
Continue scoring, ordinary placement/persistence, houses/selection, and Controller
Pak profile transport afterward. No import is selectable yet.

Development is version-tracked on `v3/optional-imports`; neither V2 web patcher,
the stable cartridge, the released trailer, nor user saves changes.
