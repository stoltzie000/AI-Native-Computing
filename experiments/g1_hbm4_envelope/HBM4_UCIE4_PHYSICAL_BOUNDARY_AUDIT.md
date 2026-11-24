# G1 HBM4 and UCIe4 interconnect physical boundary audit — 2026-11-24
Evidence: external published vendor/consortium specifications; E1 interface arithmetic only. No package feasibility or measured AI performance.

## Published primary sources
- Micron HBM4 36GB 12H, 2048-bit interface, greater than 2.8TB/s per stack (manufacturer specification, not achieved bandwidth in our platform): https://www.micron.com/products/memory/hbm/hbm4
- Rambus HBM4 controller IP maximum advertised 10Gbps/pin, independent PHY integration required: https://www.rambus.com/interface-ip/hbm/hbm4-controller/
- Rambus HBM4E controller announced up to 16Gbps/pin, ~4.1TB/s per stack, distinct generation/controller/PHY; not an assembled proof: https://www.rambus.com/interface-ip/hbm/hbm4e-controller/
- UCIe Consortium 4.0 specification announced November 12, 2026, enabling standardized **on-package memory** connectivity. It is **not** a motherboard/backplane PHY guarantee: https://www.uciexpress.org/specifications and https://www.uciexpress.org/press-releases
- Siemens EDA 2026 advanced packaging IC design guide reports HBM4 signaling and supply integrity and interface redesign requirements, secondary technical industry source: https://blogs.sw.siemens.com/semiconductor-packaging/2026/04/24/hbm3e-hbm4-ic-design-guide/

## Scope boundaries
Eight hypothetical 36GB stacks yield 288GB. Eight 2048-bit HBM4 controller data interfaces at 10Gbps/pin yield 20.48TB/s raw nominal. This is package-local data width, not a board routing requirement or verified full-chip I/O.
HBM4E 16Gbps/pin would nominally yield 4.096TB/s/stack and 32.768TB/s across eight **if independently compatible high-rate PHY, stack, package and thermal envelope exist**. HBM4E does not automatically increase performance of HBM4 memory/controller previously modeled. Compare equal-generation candidates only. No such physical system validated.
UCIe 4.0 may support package integration. Its on-package link characterization does not demonstrate PCB/backplane channel reach, BER, insertion loss, equalization, retiming, copper lengths, connector power, system topology or cooling.
Aggregate bandwidth arithmetic is a ceiling with no evidence for sustained application throughput, PVT margin, power, ECC, refresh, bank contention or capacity residency. No projection of GPU advantage is defensible from those peaks.

## Mandatory physical feasibility before gate acceptance
1. Controller/PHY/stack compatibility matrix with exact speed bins, external data-rate and ECC/refresh overhead, IP licenses and PDK availability
2. Interposer or advanced substrate floorplan, PHY footprint, stack placement, DQ lanes/bump pitch, routing/crosstalk/return path, clocking, tolerances and SI/PI simulation under a selected manufacturing process
3. Realistic thermal resistance, heat flux, hot spots, stack cooling, power-delivery losses, pump/fan impact and full-system wall power
4. Source-backed service distribution under representative burst/row locality, concurrency, refresh and read/write mix; calibrated against actual attainable bandwidth
5. End-to-end model-quality-matched GPU and hardware baseline, not a memory-bandwidth-only proxy
6. Clarify board interconnect separately from UCIe package links; assess PCB PHY technology independently rather than transferring on-package lane numbers to motherboard assumptions.

## Research decision
ADOPT published component specifications as constraints. TEST package-compatible controller+PHY combinations; TEST low-data-movement computational approaches. REJECT motherboard-level UCIe extrapolation as unsupported and HBM4E bandwidth upgrades as proven system advantage. Continue practical FPGA proof with ordinary accessible memory, explicitly separate that experiment from HBM4 physical claims. Gate G1 OPEN.
