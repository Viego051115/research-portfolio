"""SAHI evaluation on test set for best model (YOLO11s)"""
import os, time, glob
import numpy as np
from PIL import Image
from sahi import AutoDetectionModel
from sahi.predict import get_sliced_prediction

MODEL_PATH = r".\outputs\yolo11s_train\weights\best.pt"
TEST_IMG_DIR = r".\dataset\images\test"
TEST_LBL_DIR = r".\dataset\labels\test"
OUT_DIR = r".\outputs\sahi_eval"
os.makedirs(os.path.join(OUT_DIR, "predictions"), exist_ok=True)

# Load model via SAHI
print("Loading model...")
model = AutoDetectionModel.from_pretrained(
    model_type="yolov8",
    model_path=MODEL_PATH,
    confidence_threshold=0.5,
    device="cuda:0",
)

# SAHI params
SLICE_H, SLICE_W = 640, 640
OVERLAP = 0.2

# Get all test images
images = sorted(glob.glob(os.path.join(TEST_IMG_DIR, "*.png")))
print(f"Running SAHI on {len(images)} test images...")
print(f"Slice: {SLICE_H}x{SLICE_W}, Overlap: {OVERLAP}")

total_time = 0
for i, img_path in enumerate(images):
    t0 = time.time()
    result = get_sliced_prediction(
        image=img_path,
        detection_model=model,
        slice_height=SLICE_H,
        slice_width=SLICE_W,
        overlap_height_ratio=OVERLAP,
        overlap_width_ratio=OVERLAP,
        perform_standard_pred=False,
        verbose=0,
    )
    elapsed = time.time() - t0
    total_time += elapsed

    # Save predictions in YOLO format
    name = os.path.splitext(os.path.basename(img_path))[0]
    out_path = os.path.join(OUT_DIR, "predictions", name + ".txt")
    with open(out_path, "w") as f:
        for pred in result.object_prediction_list:
            bbox = pred.bbox  # SAHI BoundingBox object
            # All our images are 1920x1080
            img_w, img_h = 1920, 1080
            x_center = (bbox.minx + bbox.maxx) / 2.0 / img_w
            y_center = (bbox.miny + bbox.maxy) / 2.0 / img_h
            width = (bbox.maxx - bbox.minx) / img_w
            height = (bbox.maxy - bbox.miny) / img_h
            conf = pred.score.value
            f.write(f"0 {x_center:.6f} {y_center:.6f} {width:.6f} {height:.6f} {conf:.6f}\n")

    if (i+1) % 100 == 0:
        print(f"  {i+1}/{len(images)} done, avg {total_time/(i+1)*1000:.0f} ms/img")

avg_ms = total_time / len(images) * 1000
print(f"\nSAHI complete!")
print(f"Total time: {total_time:.1f}s")
print(f"Avg inference: {avg_ms:.0f} ms/img")
print(f"Predictions saved to: {OUT_DIR}/predictions/")

# Count total detections
total_dets = 0
for f in glob.glob(os.path.join(OUT_DIR, "predictions", "*.txt")):
    with open(f) as fh:
        total_dets += sum(1 for _ in fh)
print(f"Total detections (SAHI): {total_dets}")
print(f"Baseline (no SAHI): 636 images x ~1 detection = ~636 detections")
