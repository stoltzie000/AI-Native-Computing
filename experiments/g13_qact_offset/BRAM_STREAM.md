# BRAM-backed QACT and matrix pipeline

The quantizer accepts 64 FP32 words and sends 64 signed Q8 bytes, eight group-offset bytes and four little-endian scale bytes. The input handshake updates the row and group maxima and writes the activation RAM. Once the reciprocal and group factors are ready, the quantizer reads one word per accepted Q8 result. Backpressure holds the RAM output and the index together. Reset abandons the current row. The next complete input overwrites every RAM location before replay.

The full pipeline accepts one frame of 152 little-endian 32-bit words and returns five FP32 words. Each interface transfers on a rising clock edge when valid and ready are asserted.

| Input word indices | Payload |
| --- | --- |
| 0–79 | 320 signed weight bytes, four per word, lowest byte first |
| 80–82 | Ten weight-offset bytes followed by two ignored pad bytes |
| 83–87 | Five FP32 weight scales |
| 88–151 | 64 raw FP32 activations |

The five output beats follow matrix row order. Only the fifth asserts `output_last`. The pipeline accepts the next frame after that beat transfers. Reset flushes input, compute and result state. The quantized codes and weights use local registers at the existing MXU interface. Activation replay uses block RAM. External DRAM and host DMA are separate work.

The streaming pipeline precomputes each signed INT48-to-FP32 conversion while the shared multiplier handles a different operation. The first conversion overlaps activation-factor generation. Each later conversion overlaps the preceding lane's final multiplication. This puts a register between conversion and weight multiplication and preserves the serial epilogue's 11-cycle schedule. Other callers can select the original direct conversion.

## Reproduce

With Icarus, Yosys/ABC, NumPy and the pinned openTPU checkout available, run from the repository root.

```sh
python3 experiments/g13_qact_offset/fpga/validate.py /path/to/openTPU /path/to/build
python3 experiments/g13_qact_offset/fpga/route.py /path/to/build
```

The first command checks both reference generators, compares every result, exercises reset and stalls, and requires a RAMB18E1 on the activation array. The second command uses nextpnr-xilinx and its part database. It returns a failure on an incomplete route or a missed 100 MHz target and retains the routing log and timing report in the build directory. CI downloads the checksum-pinned openXC7 release.

For a bench bring-up run, copy `frames.hex` and `results.hex` to a separate output directory and pass that directory to `route.py` with `--profile bringup`. The board's 100 MHz oscillator drives a PLLE2_BASE. Its 800 MHz VCO divided by 128 drives the complete data path at 6.25 MHz. The validator requires the routed report to name that derived constraint. The full profile retains the 100 MHz target. [AMD Artix-7 switching characteristics, DS181](https://docs.amd.com/v/u/en-US/ds181_Artix_7_Data_Sheet)

Adding `--bitstream` to the bring-up command requests FPGA assembly, conversion to configuration frames, image generation and offline decoding. The tool checks every decoded set bit against its source frame and records the image SHA-256. The board test itself still needs a physical Arty A7-100T rev D/E.

For AMD's timing analysis, use `vivado -mode batch -source experiments/g13_qact_offset/fpga/route_vivado.tcl -tclargs /path/to/build full` or select `bringup`. This creates timing, utilization, design-rule and route reports plus a routed checkpoint. Check setup, hold and unconstrained paths before physical testing.

## Reference board

The fixed-workload top targets Digilent Arty A7-100T rev D/E, part `xc7a100tcsg324-1`. The constraint file sets the E3 oscillator to 10 ns. Input and result buses are entirely on chip and use this clock. The only other pins are the asynchronous restart button D9 and the pass/fail LEDs H5/J5. Two reset synchronizer stages release the datapath. The fixture ROM feeds the same 24 frames as the external stream test. The separate result ROM checks all 120 words, lane boundaries and final transaction count. A watchdog latches failure if the run stalls. Board ownership and measured behavior are unknown. [Digilent board schematic](https://digilent.com/reference/_media/programmable-logic/arty-a7/arty-a7-e2-sch.pdf) · [Digilent master constraints](https://github.com/Digilent/digilent-xdc/blob/master/Arty-A7-100-Master.xdc)
