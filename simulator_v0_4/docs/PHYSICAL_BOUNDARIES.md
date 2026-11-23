# Hardware evidence vs assumptions — v0.4

All dates checked 2026-11-23. Sources: supplier and consortium primary documents.

| Quantity | Basis | What we may infer | What remains unknown |
|---|---|---|---|
| Micron HBM4 >2.8 TB/s per 36GB 12H stack | [Micron HBM4](https://www.micron.com/products/memory/hbm/hbm4) | Published per-stack bandwidth envelope, not a realized combined module | Sustained effective bandwidth, signals, memory controller, package, ECC, temperature, controller silicon, cost |
| UCIe 3.0 supports 48 and 64 GT/s at the package interface | [UCIe 3.0](https://www.uciexpress.org/specifications/ucie-3-0) | High-rate die-to-die chiplet links are standard-defined | Any actual package PHY, lane count, encoding overhead, usable protocol rate, trace length, power, board-level capability |
| AMD MI355X 288GB HBM3E and 8TB/s peak, 1400W TBP | [AMD MI355X](https://www.amd.com/en/products/accelerators/instinct/mi350/mi355x.html) | Verified vendor *specifications* for comparison boundary | Matched Qwen decoding throughput, power during identical workload, software tuning |
| 8 x 36GB HBM4 = 288GB aggregate, 8 x 2.8TB/s = 22.4TB/s nominal per-stack sum | Arithmetic from Micron inputs | Naive theoretical capacity and bandwidth *before* application/PHY/controller overhead | Whether a new processor can actually access it at 70% sustained, or whether an 8-stack layout works physically |
| 128GB/s per physical fabric link, 4 compute ports per module, 1,024GB/s total physical link budget | **Explicit design assumptions** | Test rejection/latency under equal wire-capacity budget | Not independently demonstrated or quoted as real product |
| 120ns per hop, 80ns injection, 85% protocol efficiency | **Explicit design assumptions** | Test sensitivity to serialization and contention | Need measured electrical/package-level and runtime protocol results |
| 200 TOPS per 8-way computing module | **Explicit design assumption** | Schedule compute as conditional upper bound | ALU design, die area, clocks, arithmetic format, power, cooling, accuracy |
| Link energy in pJ/bit | **Unknown** by default | No claim of relative energy efficiency | Need PHY energy measurements plus HBM and compute power, wall measurement |

## Physical design boundary

A 128GB/s per-direction payload link does not follow automatically from any UCIe transfer-rate figure. Real product bandwidth depends on number of lanes, modulation, protocol encoding, direction, package materials, reach, routing margin and error management. Do not transfer an on-package UCIe specification to a removable board or cable without independent electrical evidence.

A full mesh of eight compute modules requires seven independent neighbor connections per module. The current assumed four-port PHY blocks reject this before performance modeling. An eight-port version is only a topology sensitivity study, not an implementable reference floorplan.

A custom motherboard remains an available option, but it may be better as a carrier for multiple *pre-integrated* memory-compute packages rather than carrying a massive die-to-die mesh across removable connectors. Packaging and motherboard are separate optimization variables, not synonyms.

## Comparability rule

Eight HBM4 modules against a *single* MI355X is not equal processor area, memory generation, power budget or delivered throughput. An eight-GPU baseline with its own optimized interconnect is also relevant for whole-system comparisons. Neither numerical ratio from v0.4 can substantiate a superior chip claim.
