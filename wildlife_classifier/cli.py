# wildlife_classifier/cli.py

import argparse
import json
from pathlib import Path
from typing import Optional, List, Dict, Any

from .deterministic import set_deterministic
from .model_downloader import download_inat_models, check_inat_prereqs
from .pipeline import run_single_image, run_batch


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    """
    CLI argument parser for the wildlife classifier pipeline.
    This is the ONLY place where user-facing parameters live.
    """
    p = argparse.ArgumentParser(
        description="Wildlife tagging pipeline (YOLO + offline iNat + XMP)."
    )

    # Mutually exclusive: single image or batch manifest
    mode = p.add_mutually_exclusive_group(required=False)
    mode.add_argument("--jpeg", type=str, help="Path to JPEG preview (single-image mode).")
    mode.add_argument("--manifest", type=str, help="Path to manifest JSON (batch mode).")

    # RAW required for single-image mode
    p.add_argument("--raw", type=str, help="Path to RAW file (single-image mode).")

    # Model paths
    p.add_argument("--yolo-model", type=str, default="yolov9c.pt",
                   help="Path to YOLO model.")
    p.add_argument("--inat-model", type=str, default="models/inat_classifier.pt",
                   help="Path to offline iNat model.")
    p.add_argument("--inat-taxonomy", type=str, default="models/inat_taxonomy.json",
                   help="Path to taxonomy JSON.")

    # Thresholds
    p.add_argument("--conf", type=float, default=0.25,
                   help="YOLO confidence threshold.")
    p.add_argument("--inat-conf", type=float, default=0.5,
                   help="iNat species classifier confidence threshold.")

    # Device override
    p.add_argument("--device", type=str, default=None,
                   help="Device for models (e.g. 'cuda', 'cpu').")

    # Verbose logging
    p.add_argument("--verbose", action="store_true",
                   help="Enable verbose logging to stderr.")

    # Bootstrap: download iNat model + taxonomy
    p.add_argument(
        "--download-inat",
        action="store_true",
        help="Download offline iNat model + taxonomy into ./models and exit.",
    )

    args = p.parse_args(argv)

    # Validation rules
    if not args.download_inat:
        if not args.jpeg and not args.manifest:
            p.error("One of --jpeg or --manifest is required (unless using --download-inat).")

        if args.jpeg and not args.raw:
            p.error("--raw is required when using --jpeg")

    return args


def main(argv: Optional[List[str]] = None) -> int:
    """
    Main entry point for the wildlife classifier CLI.
    """
    set_deterministic(42)
    args = parse_args(argv)

    # ---------------------------------------------------------
    # Handle model download bootstrap
    # ---------------------------------------------------------
    if args.download_inat:
        download_inat_models(Path("models"))
        return 0

    # ---------------------------------------------------------
    # Validate iNat prereqs before running pipeline
    # ---------------------------------------------------------
    model_path = Path(args.inat_model)
    taxonomy_path = Path(args.inat_taxonomy)

    if not check_inat_prereqs(model_path, taxonomy_path):
        print(json.dumps({
            "status": "error",
            "error": (
                "iNat model or taxonomy missing. "
                "Run: python -m wildlife_classifier.cli --download-inat"
            )
        }))
        return 1

    # ---------------------------------------------------------
    # Dispatch to single or batch mode
    # ---------------------------------------------------------
    if args.jpeg:
        result = run_single_image(
            jpeg_path=Path(args.jpeg),
            raw_path=Path(args.raw),
            yolo_model=args.yolo_model,
            inat_model=model_path,
            taxonomy_path=taxonomy_path,
            yolo_conf=args.conf,
            inat_conf=args.inat_conf,
            device=args.device,
            verbose=args.verbose,
        )
        print(json.dumps(result, ensure_ascii=False))
        return 0

    if args.manifest:
        result = run_batch(
            manifest_path=Path(args.manifest),
            yolo_model=args.yolo_model,
            inat_model=model_path,
            taxonomy_path=taxonomy_path,
            yolo_conf=args.conf,
            inat_conf=args.inat_conf,
            device=args.device,
            verbose=args.verbose,
        )
        print(json.dumps(result, ensure_ascii=False))
        return 0

    # Should never reach here
    print(json.dumps({"status": "error", "error": "Invalid CLI state"}))
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
