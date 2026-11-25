#!/usr/bin/env python3
"""
robot_validator.py
Công cụ dòng lệnh (CLI) kiểm tra tính đầy đủ, nhất quán của dữ liệu ghi nhận (recording episodes)
và nhãn ngôn ngữ tự nhiên phục vụ huấn luyện Robot.
"""

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Any, Dict, List

ALLOWED_ACTION_VERBS = {"pick", "place", "move", "open", "close", "sort", "push", "handover"}


def check_disk_space_gb(target_dir: Path) -> float:
    usage = shutil.disk_usage(target_dir)
    return round(usage.free / (1024 ** 3), 2)


def validate_episode(ep_path: Path) -> List[str]:
    errors: List[str] = []
    try:
        data: Dict[str, Any] = json.loads(ep_path.read_text(encoding="utf-8"))
    except Exception as exc:
        return [f"Không đọc được file JSON ({exc})"]

    required_fields = ["episode_id", "total_frames", "fps", "cameras", "robot_telemetry", "annotations"]
    for field in required_fields:
        if field not in data:
            errors.append(f"Thiếu trường bắt buộc: '{field}'")
    if errors:
        return errors

    total_frames = data["total_frames"]
    if not isinstance(total_frames, int) or total_frames <= 0:
        errors.append(f"total_frames không hợp lệ: {total_frames}")
        return errors

    # 1. Kiểm tra tín hiệu & số frame các camera trên robot
    cameras = data.get("cameras", {})
    if not cameras:
        errors.append("Không có dữ liệu camera ghi nhận")
    for cam_name, cam_info in cameras.items():
        recorded = cam_info.get("recorded_frames", 0)
        dropped = cam_info.get("dropped_frames", 0)
        blur_flag = cam_info.get("low_quality_signal", False)
        if recorded != total_frames:
            errors.append(
                f"Camera '{cam_name}' thiếu frame ({recorded}/{total_frames})"
            )
        if dropped > 0:
            errors.append(f"Camera '{cam_name}' bị rớt {dropped} frame tín hiệu")
        if blur_flag:
            errors.append(f"Camera '{cam_name}' cảnh báo chất lượng hình ảnh thấp / mờ")

    # 2. Kiểm tra trạng thái phần cứng robot (pin, lỗi khớp, bộ nhớ)
    telemetry = data.get("robot_telemetry", {})
    battery_pct = telemetry.get("battery_percent", 100)
    hw_error = telemetry.get("hardware_error", None)
    if battery_pct < 15:
        errors.append(f"Cảnh báo pin robot yếu trong ca ghi nhận ({battery_pct}%)")
    if hw_error:
        errors.append(f"Phát hiện lỗi phần cứng robot: {hw_error}")

    # 3. Kiểm tra nhãn hành động & ngôn ngữ tự nhiên (Data Annotation)
    annotations = data.get("annotations", [])
    if not annotations:
        errors.append("Chưa có nhãn hành động (annotations rỗng)")

    prev_end = -1
    for idx, ann in enumerate(annotations):
        seg_id = ann.get("segment_id", idx)
        start_f = ann.get("start_frame")
        end_f = ann.get("end_frame")
        action_type = str(ann.get("action_type", "")).strip().lower()
        instruction = str(ann.get("natural_language_label", "")).strip()
        ai_auto = ann.get("is_ai_prelabel", False)
        human_verified = ann.get("human_verified", False)

        if not isinstance(start_f, int) or not isinstance(end_f, int) or start_f < 0 or end_f >= total_frames or start_f > end_f:
            errors.append(f"Segment {seg_id}: Khoảng frame [{start_f}, {end_f}] nằm ngoài phạm vi [0, {total_frames - 1}]")
        elif start_f <= prev_end:
            errors.append(f"Segment {seg_id}: Bị chồng lấp thời gian với thao tác trước (start={start_f} <= prev_end={prev_end})")
        else:
            prev_end = end_f

        if action_type not in ALLOWED_ACTION_VERBS:
            errors.append(f"Segment {seg_id}: Loại hành động '{action_type}' ngoài danh mục chuẩn {sorted(ALLOWED_ACTION_VERBS)}")

        if len(instruction.split()) < 3:
            errors.append(f"Segment {seg_id}: Nhãn ngôn ngữ tự nhiên quá ngắn hoặc thiếu mô tả vật thể ('{instruction}')")

        if ai_auto and not human_verified:
            errors.append(f"Segment {seg_id}: Nhãn do AI tự động gán chưa được người kiểm duyệt xác nhận (human_verified=False)")

    return errors


def audit_directory(dataset_dir: Path, report_path: Path | None = None) -> int:
    episode_files = sorted(dataset_dir.glob("episode_*.json"))
    if not episode_files:
        print(f"[LỖI] Không tìm thấy file episode_*.json nào trong: {dataset_dir}")
        return 2

    free_gb = check_disk_space_gb(dataset_dir)
    print(f"=== KIỂM ĐỊNH DATASET ROBOT: {dataset_dir} ===")
    print(f"Dung lượng trống trên ổ lưu trữ hiện tại: {free_gb} GB")

    summary = {
        "dataset_dir": str(dataset_dir),
        "free_disk_gb": free_gb,
        "total_episodes": len(episode_files),
        "passed_episodes": 0,
        "failed_episodes": 0,
        "details": {},
    }

    for ep_file in episode_files:
        errs = validate_episode(ep_file)
        if not errs:
            summary["passed_episodes"] += 1
            print(f"  [PASS] {ep_file.name}: Đạt 100% chuẩn ghi nhận & nhãn ngôn ngữ")
        else:
            summary["failed_episodes"] += 1
            summary["details"][ep_file.name] = errs
            print(f"  [FAIL] {ep_file.name}: Phát hiện {len(errs)} vấn đề:")
            for e in errs:
                print(f"         - {e}")

    print(
        f"\n=> Tổng kết: {summary['passed_episodes']}/{summary['total_episodes']} episode đạt chuẩn | "
        f"{summary['failed_episodes']} episode cần xử lý lại."
    )

    if report_path:
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"=> Đã lưu báo cáo JSON tại: {report_path}")

    return 0 if summary["failed_episodes"] == 0 else 1


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Kiểm tra chất lượng bản ghi thao tác Robot (Data Collection) và nhãn ngôn ngữ tự nhiên (Annotation)."
    )
    parser.add_argument("dataset_dir", type=Path, help="Đường dẫn thư mục chứa các file episode_*.json")
    parser.add_argument("--report", type=Path, default=None, help="Đường dẫn xuất file báo cáo JSON")
    args = parser.parse_args()

    if not args.dataset_dir.exists():
        print(f"[LỖI] Thư mục không tồn tại: {args.dataset_dir}", file=sys.stderr)
        return 2

    return audit_directory(args.dataset_dir, args.report)


if __name__ == "__main__":
    sys.exit(main())
