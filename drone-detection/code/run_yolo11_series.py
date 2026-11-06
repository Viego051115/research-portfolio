"""Sequentially: resume YOLO11s then train YOLO11m"""
import subprocess, sys

YOLO = r"yolo"
DATA = ".//drone.yaml"
PROJECT = ".//outputs"
BASE_ARGS = "imgsz=1280 device=0 lr0=0.01 lrf=0.01 warmup_epochs=3 cos_lr=True rect=True"

# Step 1: Resume YOLO11s from epoch 26
print("[1/2] Resuming YOLO11s...")
ret = subprocess.run([
    YOLO, "detect", "train",
    f"data={DATA}",
    f"model=.//outputs/yolo11s_train/weights/last.pt",
    "epochs=200", "batch=4", "resume=True",
    f"project={PROJECT}", "name=yolo11s_train",
] + BASE_ARGS.split(), cwd=r".").returncode
if ret != 0:
    print("[FAIL] YOLO11s crashed")
    sys.exit(1)
print("[DONE] YOLO11s finished!\n")

# Step 2: Fresh YOLO11m training
print("[2/2] Starting YOLO11m...")
ret = subprocess.run([
    YOLO, "detect", "train",
    f"data={DATA}",
    "model=yolo11m.pt",
    "epochs=200", "batch=2",
    f"project={PROJECT}", "name=yolo11m_train",
] + BASE_ARGS.split(), cwd=r".").returncode
if ret != 0:
    print("[FAIL] YOLO11m crashed")
    sys.exit(1)
print("[DONE] YOLO11m finished!\n")

print("\n=== ALL DONE ===")
print("YOLO11n ✅ (baseline)")
print("YOLO11s ✅ (completed)")
print("YOLO11m ✅ (completed)")
