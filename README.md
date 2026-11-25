# Robot Episode & Annotation Validator CLI

Công cụ dòng lệnh Python (chạy trên **Linux Terminal**) hỗ trợ kiểm tra nhanh chất lượng các bản ghi thao tác Robot (*Data Collection*) và bộ nhãn hành động bằng ngôn ngữ tự nhiên (*Robot Data Annotation*) trước khi đồng bộ lên server huấn luyện AI.

## Tính năng chính

1. **Giám sát dữ liệu ghi nhận từ Camera & Thiết bị Robot:**
   - Phát hiện camera bị thiếu frame, rớt tín hiệu (`dropped_frames`) hoặc cảnh báo chất lượng hình ảnh thấp.
   - Cảnh báo các ca thu thập dữ liệu khi pin robot xuống thấp (`< 15%`), có mã lỗi phần cứng hoặc dung lượng ổ đĩa lưu trữ sắp đầy.
2. **Kiểm duyệt nhãn ngôn ngữ tự nhiên & phân loại hành động:**
   - Kiểm tra phân loại hành động chuẩn (`pick`, `place`, `move`, `sort`, `open`, `close`, `push`, `handover`).
   - Phát hiện khoảng frame bị chồng lấp hoặc vượt quá tổng số frame của video.
   - Chặn các nhãn do AI tự động gán (`is_ai_prelabel: true`) nhưng chưa qua bước con người rà soát xác nhận (`human_verified: false`).
   - Xuất báo cáo tổng hợp trực tiếp ra màn hình Terminal và file `report.json`.

## Cấu trúc thư mục

```text
robot-episode-validator/
├── robot_validator.py                 # Script CLI kiểm định chính (chỉ dùng Python Standard Library)
├── sample_episodes/                   # Dữ liệu mẫu mô phỏng các ca thu thập trên robot
│   ├── episode_001_valid.json         # Bản ghi chuẩn 100%
│   └── episode_002_defective.json     # Bản ghi giả lập lỗi rớt frame camera, pin yếu & nhãn chưa duyệt
├── tests/
│   └── test_validator.py              # Unit tests kiểm thử với pytest
└── README.md
```

## Cách chạy trên Linux Terminal

```bash
# 1. Chạy kiểm tra thư mục dữ liệu mẫu và xuất báo cáo JSON
python3 robot_validator.py sample_episodes --report outputs/qc_report.json

# 2. Chạy bộ kiểm thử tự động (nếu máy có cài pytest)
PYTHONPATH=. pytest -v
```

## Tác giả

- **Đặng Thanh Tiến** — [github.com/dangtienvn](https://github.com/dangtienvn)
- Giấy phép: MIT License
