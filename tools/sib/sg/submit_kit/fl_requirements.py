# Provenance: Project HERCULES | owner the owner | [id removed]
"""FL-01..FL-25: the First Letters requirements, each with a verbatim quote from the live
prize page (https://scrollprize.org/prizes, fetched 2026-09-25, raw sha256
2bc4b6df1d15008e50435169288fc76008ea1a5daf50e0eb4dc6fbd8df23ab44; rendered text in
logs/sib/sg/submit_kit/prizes_20260925_live.rendered.txt).

Numbering is this list's; FL-09, FL-14 and FL-15 keep the meanings they already have in
RULES.md (training/annotation separation, false-positive mitigation, held-out validation).
``answered_by`` names the generator section or package item that answers the requirement.
The quotes are checked against the saved page text by the unit tests.
"""

PAGE_SHA256 = "2bc4b6df1d15008e50435169288fc76008ea1a5daf50e0eb4dc6fbd8df23ab44"

FL = [
    ("FL-01", "Eligible volume", "Eligible scroll volumes (22)", "sheet.scroll_volume"),
    ("FL-02", "Deadline", "Deadline: June 25th, 2027 (11:59pm Pacific)", "owner (filing date)"),
    ("FL-03", "10 letters in one 4 cm2 area", "the first team that uncovers 10 letters within a single 4 cm² area of that scroll", "results table"),
    ("FL-04", "Open-source code, data, model weights and results after winning",
     "open sources their code, data, model weights and results (after winning the prize)", "methodology.open_source"),
    ("FL-05", "Mesh in tifxyz", "The submission must contain the mesh(es), in tifxyz format, of the surface region containing the letters", "manifest.meshes"),
    ("FL-06", "Low-distortion isometric flattening included",
     "already including a low-distortion isometric 2D parametrization (flattening)", "manifest.flattening"),
    ("FL-07", "Unwrapped image with >= 10 legible letters in 4 cm2",
     "Submissions must be an image of the virtually unwrapped segment, showing at least 10 visible and legible letters within a single 4 cm² area.", "manifest.image"),
    ("FL-08", "Single static image", "Submit a single static image showing the text region.", "manifest.image"),
    ("FL-09", "Programmatic image; no manual annotation; no training overlap",
     "Images must be generated programmatically from the reconstructed CT scan volume and the mesh(es) submitted in the same package, and should not contain manual annotations of characters or text.",
     "disclosure + FL-09 certificate"),
    ("FL-10", "Name the scroll; one submission per scroll",
     "Specify which scroll the image comes from. For multiple scrolls, please make multiple submissions.", "sheet.scroll_volume"),
    ("FL-11", "Scale bar and letter dimensions",
     "Include a scale bar showing the size of 1 cm on the submission image, and the pixel and millimeter dimensions of a few representative letters.",
     "manifest.scale_bar + letter_dimensions table"),
    ("FL-12", "Image named after the tifxyz mesh",
     "Name each image after the tifxyz mesh (from the same package) used to generate it", "manifest.image_name_check"),
    ("FL-13", "Annotate rows without obscuring letters", "Annotate the rows of text.", "manifest.row_annotation"),
    ("FL-14", "False-positive mitigation",
     "please let us know how you mitigated that risk. Tell us why you are confident that the results you are getting are real.", "fp_mitigation"),
    ("FL-15", "Held-out validation with known ground truth",
     "Run your method on the public input renders/volumes with known ground truth (using k-fold validation if you trained on them) and include the results.",
     "heldout_table"),
    ("FL-16", "Detailed, reproducible methodology",
     "A detailed technical description of how your solution works. We need to be able to reproduce your work", "methodology"),
    ("FL-17", "Docker image and system requirements (automated software)",
     "For fully automated software, consider a Docker image that we can easily run to reproduce your work, and please include system requirements.",
     "manifest.container"),
    ("FL-18", "Human-in-the-loop instructions and video", "For software with a human in the loop, please provide written instructions and a video",
     "methodology.human_in_loop"),
    ("FL-19", "Accessible download link", "Please include an easily accessible link from which we can download it.", "owner (hosting link)"),
    ("FL-20", "Other information", "Feel free to include any other things we should know.", "disclosure"),
    ("FL-21", "Review for technical validity and papyrological plausibility",
     "reviewed by the review teams to verify technical validity and papyrological plausibility and legibility", "disclosure"),
    ("FL-22", "No public disclosure before the official announcement",
     "you must not make your discovery public until the prize is officially announced", "owner (confidentiality)"),
    ("FL-23", "Submission through the Submission Form", "Submission Form", "owner (filing)"),
    ("FL-24", "Large model windows: show text is not hallucinated",
     "you must demonstrate that the text is not hallucinated", "fp_mitigation"),
    ("FL-25", "No overlap between training and prediction regions",
     "Do not include overlap between training and prediction regions", "fp_mitigation + FL-09 certificate"),
]
