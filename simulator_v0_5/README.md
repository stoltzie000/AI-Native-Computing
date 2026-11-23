# AI-Native Computing — Simulator v0.5: equal-resource architecture falsification

**Evidence level: E1 — analytical and CPU-only correctness demonstrations.**
**Date:** 2026-11-23. **Nothing here is an actual fabricated or proven superior AI processor.**

## New evidence that changes the direction

NVIDIA's published 2026 **Rubin GPU** specification already lists 288 GB HBM4 at 22 TB/s. The former v0.4 8 x 36 GB HBM4 hypothesis supplied 288 GB and a theoretical sum of 22.4 TB/s. The former comparison against a single HBM3E MI355X (8 TB/s) therefore confounded *memory generation* with architectural superiority. The comparison is now **superseded**, not proof of a win.

Rather than treating the 2x4 mesh as the preferred new motherboard, v0.5 equalizes memory generation, memory stack count, total nominal memory bandwidth, total synthetic compute, batch and model precision across **1, 2, 4 and 8 logical compute packages**.

## Results: equal HBM4 resource envelope

**Workload:** Qwen2.5-32B **analytical proxy**, 32,768-token context, batch one, 4-bit weights with 10% metadata, 16-bit KV. **Total resources in *each* row:** 8 hypothetical 36 GB HBM4 stacks; 288 GB; 22.4 TB/s nominal peak; 70% assumed sustained; 1,600 TOPS assumed aggregate compute. **Same v0.3 scheduler** except for multi-module collective costs. Package bandwidth/compute are uniformly divided by package count. Interconnect uses v0.4 unverified parameters. Computational accuracy **not validated** for any Qwen model.

| Logical compute packages | HBM4 stacks per package | Conditional outputs/sec | Notes |
|---:|---:|---:|---|
| 1 | 8 | **569.70** | Ideal shared address space with no inter-package all-reduce; NOT an existing Rubin benchmark |
| 2 | 4 | 557.74 | One package pair with abstract ring collective |
| 4 | 2 | 546.27 | Mesh/recursive doubling |
| 8 | 1 | 507.99 | Earlier 2x4 mesh/recursive doubling |

**Finding:** The 8-node mesh is about 10.8% slower than the idealized single-domain configuration under **equalized resources**. This does not prove a centralized chip is manufacturable: central chip/package fan-out, HBM-controller layout, compute distribution, voltage delivery and heat flux remain unknown.

The centralized result is 569.70 vs 592.48 outputs/sec for a separate bandwidth-only bound; the scheduler is already at ~96.2% of its *assumed* bandwidth bound. Its large improvements cannot come from the same bytes at the same bandwidth unless the implementation is changed, the effective utilization improves, or the model's bytes-per-result are reduced.

Under a **purely hypothetical** power budget of 2,200 W aggregate compute and 20 W per HBM stack, and a *hypothetical* 1,400 W per-package thermal limit, one package is rejected (2,360 W partial package heat). Two packages are the fastest model surviving **this assumed screen** (1,180 W partial heat per package). The screen omits PHY and regulator heat and cannot establish practical cooling. Changing the thermal assumptions can reverse the choice.

On a severe **assumed** motherboard-link stress test (16 GB/s/link, 3 μs/hop, 1 μs injection), 8-package rate falls to 193.57, while the idealized single package remains 569.70. No board traces or PHY were built or measured.

## Tested computation alternative: exact zero-block skipping

New `sparse_reference.py` demonstrates a small 16×16 FP32 matrix with three of four 8×8 blocks provably zero. Its exact block-sparse computation equals the independent dense reference **bit-for-bit in the test**; stored weight+index+mask bytes fall from 1,024 to 261 (74.51% reduction). Randomized sparse matrices and zero/nonzero cases are tested. **This is an intentionally constructed mathematical test, not evidence that an existing LLM has 75% exact zero-block sparsity.** A dense model would pay more metadata overhead with no savings. No AI accuracy, training, inference latency, or power comparison has occurred.

For the 32K Qwen traffic proxy (17.875 GB/step 4-bit weights incl. metadata + 8.590 GB/step KV), a twofold decrease in traffic **at unchanged bandwidth and unchanged KV read traffic** would require eliminating at least **74.03% of weight traffic**, including necessary representation overhead. That cannot be equated to doubling an existing GPU's measured output rate. A 1-bit *weight-storage-only* scenario has a 2.03× theoretical byte advantage over this 4-bit case, **without established AI quality equivalence**.

## New tools and limitations

* `equal_resources.py`: equalized memory/compute layouts and topology-dependent overhead.
* `constraints.py`: explicitly assumed raw-lane counts, transmission overhead, thermal/power estimates and benchmark comparability blocking.
* `package_screen.py`: assume-and-reject per-package heat constraint, never a manufacturing approval.
* `sparse_reference.py`: exact numerical block-sparse matvec vs independent dense oracle.
* `run_experiments.py`: deterministic, labeled JSON evidence with uncertainty disclosures.
* `test_*.py`: 70 locally passed unit and correctness tests; see `results/test_run.txt`.
* `docs/DECISION_LEDGER.md`: rejected vs continuing candidates.
* `docs/PHYSICAL_AND_BASELINE_SOURCES.md`: verified primary vendor and benchmark references.
* `docs/RESEARCH_ROADMAP.md`: actionable next experiments.

## Reproduce

Run from repository root (Python >=3.11, standard library only):

```bash
python -m unittest discover -s simulator_v0_3 -p 'test_*.py' -v
python -m unittest discover -s simulator_v0_4 -p 'test_*.py' -v
python -m unittest discover -s simulator_v0_5 -p 'test_*.py' -v
python simulator_v0_5/run_experiments.py > /tmp/simulator_v0_5.json
cmp /tmp/simulator_v0_5.json simulator_v0_5/results/summary.json
```

**Important:** v0.5 depends on `simulator_v0_3` and `simulator_v0_4`. The ZIP deliverable includes these dependencies. The GitHub repository also retains historical v0.2 and v0.1 unchanged.

## Correct next engineering priority

**Stop selecting an HBM mesh solely for nominal aggregate bandwidth.** Evaluate ways to reduce *necessary weight/state transfers per quality-matched answer* while using a practical processor–memory package. Independently validate block sparsity or other conditional computation on actual trained models and workloads, not toy matrices. Fabricate/test a real package interconnect only after a physically grounded power, memory-controller, lane, and thermal budget passes. Obtain matched GPU software/hardware baselines; do not interpret vendor peak figures as benchmarks.
