from ultralytics import YOLO
import exiftool
import os

class WildlifeClassifier:
    def __init__(self, model_path="models/yolov8.onnx", conf=0.4, verbose=False):
        self.conf = conf
        self.verbose = verbose

        if self.verbose:
            print(f"Loading model: {model_path}")
            print(f"Confidence threshold: {self.conf}")

        self.model = YOLO(model_path)

    def classify(self, jpeg_path):
        if self.verbose:
            print(f"Running inference on {jpeg_path}")

        results = self.model(jpeg_path, conf=self.conf)

        tags = []
        for r in results:
            for box in r.boxes:
                cls = int(box.cls[0])
                tags.append(self.model.names[cls])

        if self.verbose:
            print(f"Detected tags: {tags}")

        return sorted(set(tags))

    def write_xmp(self, raw_path, tags):
        if not tags:
            if self.verbose:
                print("No tags detected, skipping XMP write")
            return

        if self.verbose:
            print(f"Writing XMP for {raw_path}: {tags}")

        xmp_args = [
            "-overwrite_original",
            f"-XMP:Subject={','.join(tags)}"
        ]

        with exiftool.ExifTool() as et:
            et.execute(*[arg.encode() for arg in xmp_args], raw_path.encode())
