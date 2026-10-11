# Session 4 verification log — 2026-10-11 (UTC)

Status: **NOT OK TO SUBMIT — DO NOT SUBMIT** (unchanged). No new TIFF was generated, no experiment was run, no slot was used, nothing was uploaded.
Machine-readable record: [`evidence/session4_verification_20261011.json`](../../evidence/session4_verification_20261011.json).

## 1. Can you download the TIF and submit it?

**No, not yet.** The file exists and its format is correct, but the uniqueness gate is closed.

| Question | Answer | Evidence |
|---|---|---|
| Is there a downloadable TIF? | Yes: [`gems58-ribbon-sigma-adaptive-40768-20261011T052942Z.tif`](../downloads/gems58-ribbon-sigma-adaptive-40768-20261011T052942Z.tif), sha256 `ecf833f8…2711dd`, 433,419 B | re-hashed this session |
| Does it pass the format check that caused "Predicted values must be in range [0, 1]"? | Yes. float32, EPSG:32611, same shape and transform as the organizer's [`sample_submission.tif`](../../data/official/sample_submission.tif). Values are 0.0 or 1.0 only, with no value outside [0,1]. NaN appears only outside the footprint, in the same cells as the sample. | rasterio recheck, [`session4 JSON`](../../evidence/session4_verification_20261011.json) |
| Is it unique under the protocol? | **No, not cleared.** The literal 3 px rule fires 81 times against the registry (gate G3). The chance-corrected reading also fails (G3i) until the owner ratifies a rule. | `scripts/build_site.py --strict` → exit 2 |
| Is there an organizer receipt? | No. | G6 fails |

The earlier sessions' full reasoning is in [`REMAINING_WORK.md`](../../REMAINING_WORK.md) and [`README.md`](../../README.md). The key point: the literal stop fires on every ridge-based emitter in this repository family, because dense registry rasters cover nearly the whole footprint. The owner decides whether to change that rule. A new file made the same way would hit the same gate.

**Why no new TIFF this session.** `PROMPT.md` item 6 and `REMAINING_WORK.md` forbid starting another candidate experiment while the literal uniqueness stop is open. Making another file would mean manufacturing a candidate that the gate cannot clear. I did not do that.

## 2. Why 0.2778 — and is the attribution right?

The request says the GEMSDOE32 H33 file scored 0.2778. **The evidence does not support that.**

- The official board row at **0.2778 is `extradr19`, rank 23** (fetched 2026-10-11): <https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/>
- The GEMSDOE32 owner page says, verbatim, "NO ORGANISER SCORE EXISTS for this or any artifact in this repository", and gives **0.2747 as a model projection**: <https://buffedlizard55-lab.github.io/GEMSDOE32/docs/index.html>
- No receipt or hash ties 0.2778 to `gemsdoe32-h33-…e5eb6e7e-zeros.tif`.

So "why did H33 score highest" has no verified answer. The owner page's own explanation (thinning a thick surface raises credit per emitted pixel) is a hypothesis from that page, not an organizer result. The official metric formula is in the [problem page](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/) and the [rules](https://docs.nlr.gov/docs/fy26osti/96647.pdf) §1.1 (distance-weighted Tversky index).

## 3. The leaderboard, line by line (fetched 2026-10-11)

| Rank | Participant | Public DTI | Note |
|---:|---|---:|---|
| 1 | xiaofanhu | 0.4133 | matches repo record |
| 2 | cfld__ | 0.3585 | |
| 3 | JerryDataWorks | 0.3418 | |
| 4 | alexoktaba | 0.3361 | |
| 5 | joeyfezster | 0.3333 | |
| 6 | Batik Shirt Brothers | 0.3300 | |
| 7 | nchuzhoy | 0.3262 | |
| 8 | kinghorton42 | 0.3261 | |
| 9 | DARD | 0.3195 | **repo says rank 8 — irregularity IR-58-S4-02** |
| 23 | extradr19 | 0.2778 | the row the 0.2778 figure belongs to |

- The **0.3774** figure in the request does **not** appear anywhere in ranks 1–49 on the official board. It may be a figure from a site page, not the official board. Not verified.
- The board is dynamic: ranks and times change. Treat this table as a dated snapshot only.

## 4. Irregularities flagged for review

See [`docs/IRREGULARITIES.md`](../IRREGULARITIES.md) (entries IR-58-S4-01 to 04).

## 5. What would change the answer

1. The owner ratifies a chance-corrected uniqueness rule (REMAINING_WORK S3.1 item 1). Then the existing file's gate G3 can be re-read under that rule. That is an owner decision, not a session decision.
2. A verified organizer receipt for an exact file hash. Nothing in this repository has one.
3. Owner selection of a weekly slot, separate from any qualification step. Not done here.

## 6. Run card

Included in the JSON file. Verdict: **negative** (no promotion).
