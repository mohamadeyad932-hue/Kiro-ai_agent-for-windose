"""
label_decision_maker.py
Kiro — Automatic Folder Labeling Engine (Offline)

Generative Waterfall Logic:
  Level 1: OCR (EasyOCR) — extract dominant keywords from first 2 images
  Level 2: Context Matching — cosine similarity against user library vectors
  Level 3: Generative Labeling (BLIP) — caption → noun-phrase extraction

Author : Kiro AI Team
"""

import os
import sys
import re
import warnings
from typing import Dict, List, Optional, Tuple

import numpy as np
import arabic_reshaper
from bidi.algorithm import get_display
from rich import print as rprint

# ─── Suppress noisy library logs ───
warnings.filterwarnings("ignore")
os.environ["TOKENIZERS_PARALLELISM"] = "false"

sys.stdout.reconfigure(encoding="utf-8")

# ────────────────────────────────────────────────────────
# Paths
# ────────────────────────────────────────────────────────

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
BLIP_MODEL_DIR = os.path.join(PROJECT_ROOT, "clip_local_model", "blip_captioning")
PROCESSING_DIR = os.path.join(PROJECT_ROOT, "image_file_prossing")

if PROCESSING_DIR not in sys.path:
    sys.path.insert(0, PROCESSING_DIR)

# ────────────────────────────────────────────────────────
# Mock User Library Vectors  (Level 2 testing)
# ────────────────────────────────────────────────────────
# Each key is an existing folder name created by the user.
# Each value is the centroid vector (512-d CLIP embedding)
# of the images already inside that folder.
#
# In production, these are loaded from
#   image_file_prossing/*_images_vectors.py
# Here we provide a minimal mock so Level 2 can be tested
# without real user data.

_RNG = np.random.RandomState(42)

def _make_unit_vec(seed: int) -> List[float]:
    """Create a normalized random 512-d vector for mock data."""
    rng = np.random.RandomState(seed)
    v = rng.randn(512).astype(np.float32)
    v = v / np.linalg.norm(v)
    return v.tolist()

user_library_vectors: Dict[str, List[float]] = {
    # ── Nature / Landscape folders ──
    "Nature_Landscapes": _make_unit_vec(42),
    "Mountain_Photos":   _make_unit_vec(43),
    "Beach_Vacation":    _make_unit_vec(44),

    # ── Work / Office folders ──
    "Work_Invoices":     _make_unit_vec(45),
    "Meeting_Notes":     _make_unit_vec(46),

    # ── Personal folders ──
    "Family_Photos":     _make_unit_vec(47),
    "WhatsApp_Images":   _make_unit_vec(48),
    "Screenshots":       _make_unit_vec(49),
}


def load_real_user_library() -> Dict[str, List[float]]:
    """
    Attempt to load actual user vectors from the processing directory.
    Merges desktop / documents / downloads vectors into a single dict
    keyed by <source>_<image_name> → vector.

    Falls back to the mock ``user_library_vectors`` if imports fail.
    """
    merged: Dict[str, List[float]] = {}
    try:
        from documents_images_vectors import documents_images_vectors
        for name, vec in documents_images_vectors.items():
            merged[f"documents_{name}"] = vec
    except ImportError:
        pass
    try:
        from desktop_images_vectors import desktop_images_vectors
        for name, vec in desktop_images_vectors.items():
            merged[f"desktop_{name}"] = vec
    except ImportError:
        pass
    try:
        from downloads_images_vectors import downloads_images_vectors
        for name, vec in downloads_images_vectors.items():
            merged[f"downloads_{name}"] = vec
    except ImportError:
        pass

    return merged if merged else user_library_vectors


# ────────────────────────────────────────────────────────
# Utility: Sanitisation
# ────────────────────────────────────────────────────────

# Characters forbidden in Windows file / folder names
_FORBIDDEN_RE = re.compile(r'[\\/:*?"<>|]')


def sanitize_name(raw: str, max_len: int = 20) -> str:
    """
    Make *raw* safe for use as a Windows folder name.

    1. Strip leading / trailing whitespace.
    2. Remove Windows-forbidden characters:  \\ / : * ? " < > |
    3. Collapse runs of whitespace / underscores to a single underscore.
    4. Truncate to *max_len* characters (default 20).
    5. Strip any trailing underscores left by truncation.
    """
    name = raw.strip()
    name = _FORBIDDEN_RE.sub(" ", name)        # replace forbidden → space
    name = re.sub(r"[\s_]+", "_", name)        # collapse whitespace / _
    name = name.strip("_")                      # strip leading/trailing _
    name = name[:max_len].rstrip("_")
    return name if name else "Unnamed"


# ────────────────────────────────────────────────────────
# Utility: Noun-phrase extraction (regex, no spaCy)
# ────────────────────────────────────────────────────────

# Lightweight stop-words — enough to strip filler from BLIP captions
_STOP = frozenset(
    "a an the is are was were be been being am "
    "of in on at to for with by from into through "
    "and or but not no nor so yet "
    "it its this that these those "
    "i me my we our you your he she they them "
    "do does did has have had will would shall should "
    "can could may might must "
    "very much more most some any all each every "
    "there here where when how what which who whom "
    "up down out off over under about after before "
    "sitting standing laying lying next top side front back "
    "two three four several many few large small "
    "photo picture image view scene shot".split()
)


def extract_noun_phrases(caption: str) -> str:
    """
    Extract meaningful noun phrases from a BLIP-style caption.

    Strategy:
      1. Lowercase, strip punctuation.
      2. Remove stop-words.
      3. Keep the first 3 remaining content words.
      4. Join with underscores → title-cased.
    """
    words = re.findall(r"[a-zA-Z]+", caption.lower())
    content = [w for w in words if w not in _STOP]
    # Take up to 3 content words for a concise label
    chosen = content[:3]
    if not chosen:
        return "Misc"
    return "_".join(w.capitalize() for w in chosen)


# ────────────────────────────────────────────────────────
# Cosine Similarity (standalone, no sklearn needed)
# ────────────────────────────────────────────────────────

def cosine_sim(a: np.ndarray, b: np.ndarray) -> float:
    """Cosine similarity between two 1-D vectors."""
    dot = np.dot(a, b)
    norm = np.linalg.norm(a) * np.linalg.norm(b)
    if norm == 0:
        return 0.0
    return float(dot / norm)


# ════════════════════════════════════════════════════════
#  KiroLabelEngine
# ════════════════════════════════════════════════════════

class KiroLabelEngine:
    """
    Determines the folder name for a cluster of images using a
    three-level generative waterfall:

        Level 1  →  OCR  (EasyOCR)
        Level 2  →  Context Matching  (Cosine Similarity ≥ 0.85)
        Level 3  →  Generative Labeling  (BLIP captioning)

    All models follow the **Singleton** pattern — loaded once at
    ``__init__`` and reused for every subsequent call.
    """

    # Class-level singletons (shared across instances)
    _ocr_reader = None
    _blip_model = None
    _blip_processor = None
    _models_loaded: bool = False

    # ── OCR dominant keywords ──
    OCR_KEYWORDS: Dict[str, str] = {
        # keyword (lowercase)  →  label
        "invoice":       "Invoices",
        "receipt":       "Receipts",
        "whatsapp":      "WhatsApp_Images",
        "screenshot":    "Screenshots",
        "certificate":   "Certificates",
        "passport":      "Passports",
        "resume":        "Resumes",
        "cv":            "Resumes",
        "ticket":        "Tickets",
        "boarding":      "Boarding_Passes",
        "license":       "Licenses",
        "diploma":       "Diplomas",
        "report":        "Reports",
        "menu":          "Menus",
        "bill":          "Bills",
        "contract":      "Contracts",
        "prescription":  "Prescriptions",
        "id card":       "ID_Cards",
        "identification":"ID_Cards",
    }

    CONTEXT_THRESHOLD: float = 0.85

    def __init__(
        self,
        user_vectors: Optional[Dict[str, List[float]]] = None,
        blip_model_path: Optional[str] = None,
        lazy_load: bool = True,
    ):
        """
        Parameters
        ----------
        user_vectors : dict
            ``{folder_name: centroid_vector}`` for Level 2 matching.
            Falls back to ``load_real_user_library()`` → mock data.
        blip_model_path : str
            Local path to the BLIP model weights directory.
            Defaults to ``clip_local_model/blip_captioning``.
        lazy_load : bool
            If *True* (default), models are loaded on first use.
            Set to *False* to load everything eagerly at init time.
        """
        self.user_vectors = user_vectors or load_real_user_library()
        self.blip_model_path = blip_model_path or BLIP_MODEL_DIR
        if not lazy_load:
            self._ensure_ocr()
            self._ensure_blip()

    # ────────────────────────────────────────────────
    # Singleton Model Loaders
    # ────────────────────────────────────────────────

    @classmethod
    def _ensure_ocr(cls):
        """Load EasyOCR reader once (Singleton)."""
        if cls._ocr_reader is not None:
            return
        try:
            import easyocr
            print("⏳ Loading EasyOCR model (first time only)...")
            cls._ocr_reader = easyocr.Reader(
                ["en"],
                gpu=False,
                verbose=False,
            )
            print("✅ EasyOCR loaded successfully.")
        except ImportError:
            print("⚠ EasyOCR not installed — Level 1 (OCR) will be skipped.")
            print("  Install with:  pip install easyocr")
            cls._ocr_reader = None
        except Exception as e:
            print(f"⚠ EasyOCR failed to load: {e}")
            cls._ocr_reader = None

    @classmethod
    def _ensure_blip(cls):
        """Load BLIP captioning model once (Singleton)."""
        if cls._blip_model is not None:
            return
        try:
            import torch
            from transformers import BlipProcessor, BlipForConditionalGeneration
            import transformers
            transformers.logging.set_verbosity_error()

            model_path = BLIP_MODEL_DIR

            # ── Try loading from local path first ──
            if os.path.isdir(model_path) and os.listdir(model_path):
                print(f"⏳ Loading BLIP model from local path: {model_path}")
                cls._blip_processor = BlipProcessor.from_pretrained(
                    model_path, local_files_only=True
                )
                cls._blip_model = BlipForConditionalGeneration.from_pretrained(
                    model_path, local_files_only=True
                ).to("cpu")
            else:
                # Download and cache locally for future offline use
                hub_name = "Salesforce/blip-image-captioning-base"
                print(f"⏳ Downloading BLIP model ({hub_name})...")
                print(f"   Will be saved to: {model_path}")
                cls._blip_processor = BlipProcessor.from_pretrained(hub_name)
                cls._blip_model = BlipForConditionalGeneration.from_pretrained(
                    hub_name
                ).to("cpu")
                # Save locally so next launch is fully offline
                os.makedirs(model_path, exist_ok=True)
                cls._blip_model.save_pretrained(model_path)
                cls._blip_processor.save_pretrained(model_path)
                print(f"💾 BLIP model saved locally for offline use.")

            cls._blip_model.eval()
            print("✅ BLIP captioning model loaded successfully.")

        except ImportError as e:
            print(f"⚠ BLIP dependencies missing: {e}")
            print("  Ensure: pip install transformers torch Pillow")
            cls._blip_model = None
            cls._blip_processor = None
        except Exception as e:
            print(f"⚠ BLIP failed to load: {e}")
            cls._blip_model = None
            cls._blip_processor = None

    # ────────────────────────────────────────────────
    # Level 1: OCR
    # ────────────────────────────────────────────────

    def _level1_ocr(
        self, image_paths: List[str]
    ) -> Optional[Dict[str, object]]:
        """
        Scan the **first 2** images with EasyOCR.
        If a dominant keyword is found, return the label immediately.
        """
        self._ensure_ocr()
        if self._ocr_reader is None:
            return None

        scan_paths = image_paths[:2]
        all_text: List[str] = []

        for path in scan_paths:
            if not os.path.isfile(path):
                continue
            try:
                results = self._ocr_reader.readtext(path, detail=0)
                all_text.extend(results)
            except Exception as e:
                print(f"  ⚠ OCR error on {os.path.basename(path)}: {e}")

        # Merge all detected text into one haystack
        merged = " ".join(all_text).lower()

        if not merged.strip():
            return None

        # Check for dominant keywords (longest match first)
        sorted_kw = sorted(self.OCR_KEYWORDS.keys(), key=len, reverse=True)
        for keyword in sorted_kw:
            if keyword in merged:
                count = merged.count(keyword)
                label = self.OCR_KEYWORDS[keyword]
                confidence = min(1.0, 0.70 + 0.10 * count)
                return {
                    "folder_name": sanitize_name(label),
                    "method": "OCR",
                    "confidence": round(confidence, 2),
                }

        return None

    # ────────────────────────────────────────────────
    # Level 2: Context Matching
    # ────────────────────────────────────────────────

    def _level2_context(
        self, cluster_centroid: np.ndarray
    ) -> Optional[Dict[str, object]]:
        """
        Compare *cluster_centroid* against every folder centroid in
        ``self.user_vectors`` using cosine similarity.

        Threshold: ``CONTEXT_THRESHOLD`` (default 0.85).
        """
        if not self.user_vectors:
            return None

        best_name: Optional[str] = None
        best_sim: float = -1.0

        for folder_name, vec in self.user_vectors.items():
            sim = cosine_sim(cluster_centroid, np.array(vec, dtype=np.float32))
            if sim > best_sim:
                best_sim = sim
                best_name = folder_name

        if best_sim >= self.CONTEXT_THRESHOLD and best_name is not None:
            return {
                "folder_name": sanitize_name(best_name),
                "method": "Context_Match",
                "confidence": round(best_sim, 4),
            }

        return None

    # ────────────────────────────────────────────────
    # Level 3: Generative Labeling (BLIP)
    # ────────────────────────────────────────────────

    def _level3_blip(
        self, image_paths: List[str]
    ) -> Optional[Dict[str, object]]:
        """
        Generate a caption for the first available image using BLIP,
        then extract noun phrases to form the folder label.
        """
        self._ensure_blip()
        if self._blip_model is None or self._blip_processor is None:
            return None

        import torch
        from PIL import Image

        for path in image_paths[:3]:
            if not os.path.isfile(path):
                continue
            try:
                image = Image.open(path).convert("RGB")
                inputs = self._blip_processor(
                    images=image, return_tensors="pt"
                ).to("cpu")

                with torch.no_grad():
                    output_ids = self._blip_model.generate(
                        **inputs,
                        max_new_tokens=30,
                        num_beams=3,
                    )

                caption = self._blip_processor.decode(
                    output_ids[0], skip_special_tokens=True
                ).strip()

                if not caption:
                    continue

                print(f"  📝 BLIP caption: \"{caption}\"")

                noun_label = extract_noun_phrases(caption)
                final_label = sanitize_name(noun_label)

                return {
                    "folder_name": final_label,
                    "method": "BLIP_Caption",
                    "confidence": round(0.55, 2),
                }

            except Exception as e:
                print(f"  ⚠ BLIP error on {os.path.basename(path)}: {e}")

        return None

    # ────────────────────────────────────────────────
    # Main Public API
    # ────────────────────────────────────────────────

    def decide_label(
        self,
        image_paths: List[str],
        cluster_centroid: Optional[np.ndarray] = None,
    ) -> Dict[str, object]:
        """
        Determine the best folder name for a cluster of images.

        Parameters
        ----------
        image_paths : list[str]
            Absolute paths to the images in the cluster.
        cluster_centroid : np.ndarray, optional
            The mean CLIP vector (512-d) of the cluster.
            Required for Level 2 matching. If not provided,
            Level 2 is skipped.

        Returns
        -------
        dict
            ``{"folder_name": str, "method": str, "confidence": float}``
        """
        print(f"\n{'─' * 50}")
        print(f"🏷  KiroLabelEngine — deciding label for {len(image_paths)} image(s)")
        print(f"{'─' * 50}")

        # ── Level 1: OCR ──
        print("\n  ▸ Level 1: OCR scan...")
        result = self._level1_ocr(image_paths)
        if result:
            print(f"  ✅ OCR matched → \"{result['folder_name']}\"  "
                  f"(confidence: {result['confidence']})")
            return result
        print("  ✗ No dominant keyword found.")

        # ── Level 2: Context Matching ──
        if cluster_centroid is not None:
            print("\n  ▸ Level 2: Context matching...")
            result = self._level2_context(cluster_centroid)
            if result:
                print(f"  ✅ Context matched → \"{result['folder_name']}\"  "
                      f"(similarity: {result['confidence']})")
                return result
            print("  ✗ No context match above threshold "
                  f"({self.CONTEXT_THRESHOLD}).")
        else:
            print("\n  ▸ Level 2: Skipped (no centroid provided).")

        # ── Level 3: BLIP Captioning ──
        print("\n  ▸ Level 3: BLIP captioning...")
        result = self._level3_blip(image_paths)
        if result:
            print(f"  ✅ BLIP label → \"{result['folder_name']}\"  "
                  f"(confidence: {result['confidence']})")
            return result
        print("  ✗ BLIP captioning failed.")

        # ── Fallback ──
        fallback = {
            "folder_name": "Unsorted",
            "method": "Fallback",
            "confidence": 0.0,
        }
        print(f"\n  ⚠ All levels failed → fallback: \"{fallback['folder_name']}\"")
        return fallback


# ════════════════════════════════════════════════════════
#  Self-Test / Demo
# ════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 60)
    print("  Kiro Label Decision Maker — Self-Test")
    print("=" * 60)

    # ── 1. Sanitization tests ──
    print("\n── sanitize_name tests ──")
    test_cases = [
        ('Invoice: Q3/2024 "Final"', "Invoice_Q3_2024_Fina"),  # : and / are forbidden → _
        ("My<Best>Photos*Ever",       "My_Best_Photos_Ever"),  # forbidden → _
        ("WhatsApp Image 2024-01-15", "WhatsApp_Image_2024-"),
        ("   spaces   everywhere   ", "spaces_everywhere"),
        ("a" * 30,                    "a" * 20),
        ('/:*?"<>|',                  "Unnamed"),
    ]
    all_pass = True
    for raw, expected in test_cases:
        got = sanitize_name(raw)
        status = "✅" if got == expected else "❌"
        if got != expected:
            all_pass = False
        print(f"  {status} sanitize_name({raw!r:40s}) → {got!r:25s}  (expected: {expected!r})")

    # ── 2. Noun-phrase extraction tests ──
    print("\n── extract_noun_phrases tests ──")
    captions = [
        "a group of people sitting at a table",
        "a beautiful mountain landscape with snow",
        "an invoice document on a white background",
        "a cat sitting on a couch next to a window",
    ]
    for cap in captions:
        print(f"  \"{cap}\"  →  {extract_noun_phrases(cap)}")

    # ── 3. Level 2 mock demo ──
    print("\n── Level 2 Context Matching demo ──")

    # Use mock vectors explicitly so the demo is deterministic
    engine = KiroLabelEngine(user_vectors=user_library_vectors, lazy_load=True)

    # Pull the first folder vector from the engine's own library
    first_folder = list(engine.user_vectors.keys())[0]
    first_vec = np.array(engine.user_vectors[first_folder], dtype=np.float32)

    # Add small noise so it's nearly identical but not exact
    noisy = first_vec + np.random.randn(512).astype(np.float32) * 0.01

    result_exact = engine._level2_context(first_vec)
    result_noisy = engine._level2_context(noisy)

    print(f"  Exact match ({first_folder}):  {result_exact}")
    print(f"  Noisy match ({first_folder}):  {result_noisy}")

    # Completely random vector should NOT match
    random_vec = np.random.randn(512).astype(np.float32)
    result_rand = engine._level2_context(random_vec)
    print(f"  Random vec:   {result_rand}")

    # ── 4. Full waterfall (only if images exist) ──
    HOME = os.path.expanduser("~")
    sample_dir = os.path.join(HOME, "Documents")
    sample_images = []
    if os.path.isdir(sample_dir):
        for fname in os.listdir(sample_dir):
            if os.path.splitext(fname)[1].lower() in {".png", ".jpg", ".jpeg"}:
                sample_images.append(os.path.join(sample_dir, fname))
            if len(sample_images) >= 3:
                break

    if sample_images:
        print(f"\n── Full waterfall demo with {len(sample_images)} image(s) ──")
        result = engine.decide_label(
            image_paths=sample_images,
            cluster_centroid=np.random.randn(512).astype(np.float32),
        )
        print(f"\n  🏷  Final result: {result}")
    else:
        print("\n  ℹ No sample images found in Documents — skipping full waterfall demo.")
        print("  To test the full pipeline, pass real image paths to engine.decide_label().")

    print("\n" + "=" * 60)
    print("  Self-test complete.")
    print("=" * 60)
