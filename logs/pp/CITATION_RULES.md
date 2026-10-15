# Citation, licence and README rules for the Progress Prize repositories (DECL-PP-1)
Provenance: Project HERCULES | owner the owner | [id removed]

Source of the data rules: https://scrollprize.org/data, section "How to Cite" and "Licenses", fetched 2026-09-27 ~01:08Z. The copy is data/catalogue/sources/scrollprize.org_data_20260927.html, with its sha256 file beside it. The Progress Prize section of https://scrollprize.org/prizes has no separate citation rule. Its criteria are listed in section D below.

## A. Data citation (mandatory: "cite the dataset that corresponds to the scans you used")
Cite, in every README (a "Data and citation" section), each dataset whose scans the tool was run on, validated on, or shown with.
1. **Newer scans released directly by Vesuvius Challenge** (all 2025-2026 scans, e.g. PHerc0139, 0009B, 0841, 0800, 1447, 0172, and the 2026 ESRF scans of PHerc. Paris 4). Verbatim:
   > Giorgio Angelotti, Stephen Parsons, Sean Johnson, Elian Rafael Dal Prà, Johannes Rudolph, Paul Tafforeau, Alessandro Mirone, Paul Henderson, Hendrik Schilling, Forrest McDonald, David Josey, Youssef Nader, C. Seth Parker, W. Brent Seales. *Vesuvius Challenge - CT Scans of Herculaneum Papyri*. Vesuvius Challenge.
   Link: https://scrollprize.org/data
2. **EduceLab-Scrolls** (Scrolls 1-4 and Fragments 1-6 scanned at DLS before 2025). Verbatim reference:
   > Parsons, S., Parker, C. S., Chapman, C., Hayashida, M., & Seales, W. B. (2023). *EduceLab-Scrolls: Verifiable Recovery of Text from Herculaneum Papyri using X-ray CT*. ArXiv [Cs.CV]. https://doi.org/10.48550/arXiv.2304.02084
   Also include this sentence: "Data used in the preparation of this work were obtained from the EduceLab-Scrolls dataset [Parsons et al. 2023]." This data is copyrighted by EduceLab/The University of Kentucky.
3. Name every scroll and segment by its official ID (e.g. PHerc0139, segment 20260623141924-...), and link the Data Browser (https://scrollprize.org/data_browser).

## B. Licences
- Code: MIT (LICENSE file, copyright line as in the LICENSE the packager wrote).
- Vesuvius Challenge data and anything derived from it (tables of per-segment numbers, figures): **CC BY-NC 4.0**, unless noted otherwise. Put such files under data/ or results/, with a data/LICENSE-DATA.md stating "Derived from Vesuvius Challenge data, CC BY-NC 4.0" and the citation above. Never commit raw CT volumes, surface volumes or large meshes. Link to the official bucket instead.
- Never include the five EduceLab title-search meshes or anything derived from them (licence accepted for internal use only). Never include Paris 4 title-search data.

## C. Credit to methods and code used
Cite every algorithm and library the tool uses or compares against:
- SLIM: M. Rabinovich, R. Poranne, D. Panozzo, O. Sorkine-Hornung. "Scalable Locally Injective Mappings." ACM Transactions on Graphics 36(2), 2017.
- ARAP parametrisation: L. Liu, L. Zhang, Y. Xu, C. Gotsman, S. J. Gortler. "A Local/Global Approach to Mesh Parameterization." Computer Graphics Forum 27(5) (SGP), 2008.
- ABF++: A. Sheffer, B. Lévy, M. Mogilnitsky, A. Bogomyakov. "ABF++: Fast and Robust Angle Based Flattening." ACM Transactions on Graphics 24(2), 2005.
- libigl: A. Jacobson, D. Panozzo, et al. libigl: a simple C++ geometry processing library, https://libigl.github.io (MPL-2.0). State its licence if it is a dependency.
- VC3D / vc_flatten (Vesuvius Challenge, https://github.com/scrollprize/villa), and the tifxyz format.
- SciPy (cKDTree): P. Virtanen et al. "SciPy 1.0: fundamental algorithms for scientific computing in Python." Nature Methods 17, 261-272 (2020).
- Community tools compared against, e.g. the July 2026 progress-prize tool "that detects intersections in tifxyz patches": name its author and link its repository, as given in the organizers' post "$33.5K awarded in July" (Substack, 2026-08-06; title verified 02:35Z; the URL slug reads 335k). Say plainly what is new relative to it.
Only cite what is actually used or compared. Check each reference against its source before publishing.

## D. The Progress Prize criteria the README must visibly satisfy (quoted from the prizes page)
- "Address a specific challenge using Vesuvius Challenge scroll data"
- "Provide clear implementation path and a demonstration of its use"
- "Demonstrate significant advantages over existing solutions"
- "Include comprehensive documentation" and "Provide usage examples"
- "Accept standard community formats (e.g. OME-Zarr or Zarr arrays, tifxyz quadmeshes, triangular meshes)"
- "Maintain consistent output formats" and be "Designed for modular integration"
- They favour work that is: released early; actually used; quantitatively better on real data; reveals insightful, actionable information ("detecting failure-cases of existing methods on real scroll data"); well documented. Any contribution that makes an Open Problem (https://scrollprize.org/2026_open_problems) easier is eligible.

## E. README structure (all three repos)
1. Title and a one-sentence purpose. This sentence is also the GitHub "About" description (<= 120 characters).
2. Why it matters: the specific scroll-reading problem, and which Open Problem or prize requirement it serves.
3. Install (pip, requirements, Python version); tested platforms.
4. Quick start: one copy-paste command on public data, and its expected output.
5. CLI and API reference: inputs (tifxyz and others), outputs (the exact JSON/CSV schema), exit codes.
6. Validation: every number, how it was produced (the script and command in the repo) and on which public segment IDs; the tests (`pytest`), with the pass count.
7. Findings on real data: the actionable results (e.g. failure cases found), stated as measured, with the segment IDs.
8. Limitations and known failure modes (honest).
9. Data and citation (section A); licences (section B); credits (section C).
10. AI assistance, one line: "Developed with the help of AI coding agents; all numbers are produced by the scripts and tests in this repository."
11. Contributing and issues (GitHub issues).
Every claim must be reproducible from the repo, or labelled with its evidence. No marketing superlatives. Use metric units, and state voxel sizes in um.
