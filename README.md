# Trang Web quản lý tệp

Ứng dụng web bằng Flask cho phép:
- Đăng ký tài khoản.
- Đăng nhập/đăng xuất.
- Tải tệp lên theo từng người dùng.
- Tải tệp xuống từ danh sách tệp đã tải lên.

## Cách chạy

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Mở trình duyệt tại: `http://127.0.0.1:5000`

## Chạy kiểm thử

```bash
python -m unittest discover -s tests -v
```
