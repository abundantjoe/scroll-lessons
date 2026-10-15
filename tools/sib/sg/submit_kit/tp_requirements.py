# Provenance: Project HERCULES | owner the owner | [id removed]
"""TP-01..TP-22: the PHerc. Paris 4 Title Prize requirements, each with a verbatim
requirement sentence from the live prize page (https://scrollprize.org/prizes, fetched
2026-09-26T00:47Z, raw sha256 7e653247be3e9390d23fafd56f293447e17def92291b56c83764fd7dcf635be4;
rendered text identical to the 2026-09-25 copy).  Only requirement sentences are quoted;
no title words exist on the page and none are ever written by the project.
"""

PAGE_SHA256 = "7e653247be3e9390d23fafd56f293447e17def92291b56c83764fd7dcf635be4"

TP = [
    ("TP-01", "Mesh in tifxyz with low-distortion flattening",
     "The submission must contain the mesh, in tifxyz format, of the surface region containing the title, already including a low-distortion isometric 2D parametrization (flattening).",
     "manifest.meshes + manifest.flattening"),
    ("TP-02", "Image of the unwrapped region showing the title",
     "Submissions must be an image of the virtually unwrapped region, showing the title visibly and legibly.", "manifest.image"),
    ("TP-03", "Ink predictions in the spatial context of the search",
     "Illustrate the ink predictions in the spatial context of the title search", "manifest.context_image"),
    ("TP-04", "The papyrologists read the title, not the entrant",
     "You do not have to read the title yourself", "disclosure"),
    ("TP-05", "Programmatic image; no manual annotation; no training overlap",
     "Images must be generated programmatically from the reconstructed CT scan volume and the mesh submitted in the same package, and should not contain manual annotations of characters or text.",
     "disclosure + training_overlap"),
    ("TP-06", "Name the scan", "Specify which scan the image comes from", "sheet.scan"),
    ("TP-07", "Scale bar and letter dimensions",
     "Include a scale bar showing the size of 1 cm on the submission image, and the pixel and millimeter dimensions of a few representative letters.",
     "manifest.scale_bar + letter_dimensions table"),
    ("TP-08", "Image named after the tifxyz mesh", "Name the image after the tifxyz mesh (from the same package) used to generate it",
     "manifest.image_name_check"),
    ("TP-09", "Detailed, reproducible methodology", "A detailed technical description of how your solution works.", "methodology"),
    ("TP-10", "Docker image and system requirements",
     "For fully automated software, consider a Docker image that we can easily run to reproduce your work, and please include system requirements.",
     "manifest.container"),
    ("TP-11", "Human-in-the-loop instructions and video",
     "For software with a human in the loop, please provide written instructions and a video", "methodology"),
    ("TP-12", "Accessible download link", "Please include an easily accessible link from which we can download it.", "owner (hosting link)"),
    ("TP-13", "False-positive mitigation",
     "please let us know how you mitigated that risk. Tell us why you are confident that the results you are getting are real.",
     "fp_mitigation"),
    ("TP-14", "Large windows: letters and words not hallucinated",
     "you must demonstrate the letters and words are not hallucinated", "fp_mitigation"),
    ("TP-15", "No training / prediction overlap", "Do not include overlap between training and prediction regions",
     "fp_mitigation + training_overlap"),
    ("TP-16", "Held-out validation",
     "Run your method on the public input renders/volumes with known ground truth (using k-fold validation if you trained on them) and include the results.",
     "heldout_table"),
    ("TP-17", "Other information", "Feel free to include any other things we should know.", "disclosure"),
    ("TP-18", "Review for technical validity and papyrological plausibility",
     "reviewed by the review teams to verify technical validity and papyrological plausibility and legibility", "disclosure"),
    ("TP-19", "Open until won", "Submissions remain open until the prize is won", "owner (filing)"),
    ("TP-20", "No public disclosure before the announcement",
     "you must not make your discovery public until the prize is officially announced", "owner (confidentiality)"),
    ("TP-21", "Submission through the Title Prize form", "Submission Form", "owner (filing)"),
    ("TP-22", "Deadline", "Deadline: June 25th, 2027 (11:59pm Pacific)", "owner (filing date)"),
]
