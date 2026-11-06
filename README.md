# Research portfolio — Nuozhou Wang

I am a Year 3 AIAC student at Xi’an Jiaotong-Liverpool University. This repository contains selected implementation work from two projects. My novelty-evaluation replication is maintained separately: https://github.com/Viego051115/novelty-eval-replication.

## Warehouse agents: prompt engineering and observation contracts

I improved the agent-facing layer of an existing LPB warehouse simulation system. The simulator, standard LPB configuration server and original infrastructure are inherited. I do not claim to have built the complete system.

The current snapshot comes from **lpb_mas_v7**. Four role prompts define semantic references, observation lookups and allowed command endpoints. The selected Python modules show static/dynamic observation slices and semantic task adaptation. They are excerpts for inspection, not a standalone simulator distribution.

The V7 report records fixes for arm preconditions conflicting with arrival timing, exposing only one shuttle, and scheduling that allowed packages to accumulate. It describes explicit target counts, multiple-device exposure, zone routing and capacity-triggered interleaving. Reported single-zone checks passed 6/6 in dry-run mock, simulator mock and real-LLM tests. Multi-zone post-fix execution remains pending; no measured throughput improvement is claimed.

## Drone detection: training and evaluation

I implemented the code, model training and comparisons. A classmate supplied the photographs. The repository does not include the image dataset, annotations, model weights or manuscript, and I do not claim manuscript authorship.

The selection includes the original dataset preparation procedure, the YOLO11s resume / YOLO11m training sequence, and a SAHI evaluation script. Local filesystem paths have been generalized. These are historical experiment scripts; inspect their constants and data paths before execution. The training sequence expects a YOLO11s checkpoint and does not start all variants from scratch.

Recorded test mAP50 in the project V3 comparison report: YOLO11n 0.786, YOLO11s 0.797, YOLO11m 0.791, at input resolution 1280 with a reported 636-image test set. These are local recorded results, not newly rerun benchmarks. Random image splitting does not establish independence between video sequences. Dataset preparation matches filenames across exports; check duplicates before reusing it on other datasets.

### Using the selected scripts

Install Python and the packages imported by the scripts, including Ultralytics, scikit-learn, OpenCV, NumPy, SAHI and PyTorch appropriate to the hardware. Adjust paths and checkpoints in `drone-detection/code/`. Place the dataset under the project dataset directory and update `drone.yaml` and script constants together. No training is triggered by publishing this repository. This curated snapshot was syntax-checked, not GPU-trained again.

## Provenance and scope

`provenance.json` records source and published SHA-256 hashes. The source folders contain the full research context; this repository intentionally contains a selected subset. The V7 documentation and drone V3 report support the summaries above. This upload does not establish exclusive authorship or redistribute the inherited simulator. No blanket open-source licence is asserted for inherited material. Contact the author regarding reuse.
