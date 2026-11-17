# Quản lý câu lạc bộ và sự kiện sinh viên

Đồ án nhóm (ĐG2) – Học phần Lập trình mã nguồn mở (POS02024) – Trường Đại học Quản lý và Công nghệ Hải Phòng
Đề tài 3 – Nhóm 3 – Lớp CT2802

Hệ thống thay cho việc đăng ký qua Google Form và điểm danh bằng giấy: sinh viên xin gia nhập câu lạc bộ, đăng ký sự kiện, điểm danh bằng mã QR và tích lũy điểm rèn luyện; ban chủ nhiệm quản lý sự kiện, duyệt thành viên, xuất danh sách điểm danh ra Excel.

- Kế hoạch và phân công: [GitHub Projects – ĐG2 Nhóm 3](https://github.com/users/duy646756-netizen/projects/1)
- Địa chỉ máy chủ: *(cập nhật sau khi triển khai)*

## Thành viên và phân công

| TT | Họ và tên | Vai trò | Phân hệ phụ trách | Đóng góp |
|----|-----------|---------|-------------------|----------|
| 1 | Nguyễn Đức Duy | Trưởng nhóm, Front-end | Kế hoạch trên GitHub Projects; giao diện, gọi API, màn hình CLB/sự kiện, quét QR | …% |
| 2 | Phạm Văn Long Thành | Back-end | RESTful API, JWT, phân quyền, tính điểm rèn luyện, upload poster, thống kê | …% |
| 3 | Ngô Xuân Lộc | CSDL và Kiểm thử | ERD, models, Alembic, seed; Postman, pytest | …% |
| 4 | Nguyễn Sỹ Duy Anh | DevOps | Dockerfile, docker-compose, Nginx, CI/CD, máy chủ | …% |

## Chức năng

| Vai trò | Chức năng |
|---------|-----------|
| Sinh viên | Xem danh sách CLB, xin gia nhập; xem, tìm kiếm, lọc sự kiện; đăng ký / hủy đăng ký; điểm danh bằng quét QR hoặc nhập mã; xem lịch sử tham gia và điểm rèn luyện |
| Ban chủ nhiệm CLB | Duyệt / từ chối thành viên; tạo sự kiện (thời gian, địa điểm, số lượng tối đa, ảnh poster); mở mã QR điểm danh; xuất Excel; thống kê theo học kỳ; xóa sự kiện, CLB |
| Đoàn – Hội (quản trị) | Toàn bộ quyền của ban chủ nhiệm trên mọi CLB |

**Tính năng nâng cao:** upload ảnh poster; tìm kiếm, lọc, phân trang; mã QR sinh phía server, hết hạn sau 10 phút; xuất danh sách điểm danh ra Excel; thống kê sự kiện theo học kỳ; logging.

## Công nghệ

| Thành phần | Công nghệ | Giấy phép |
|-----------|-----------|-----------|
| Back-end | Python 3.12, FastAPI, Uvicorn, Pydantic | MIT, BSD-3 |
| CSDL | PostgreSQL 16, SQLAlchemy 2, Alembic | PostgreSQL License, MIT |
| Bảo mật | PyJWT (HS256), bcrypt | MIT, Apache-2.0 |
| Tính năng | qrcode, openpyxl | BSD, MIT |
| Front-end | HTML/CSS/JavaScript thuần, html5-qrcode | Apache-2.0 |
| Hạ tầng | Docker, Docker Compose, Nginx | Apache-2.0, BSD-2 |
| Kiểm thử, CI | pytest, ruff, Postman, GitHub Actions | MIT |

Dự án phát hành theo giấy phép [MIT](LICENSE).

## Kiến trúc

```
Trình duyệt ──► Nginx (web, cổng 8080)
                 ├── /        → frontend/index.html
                 └── /api/... → FastAPI (api:8000) ──► PostgreSQL (db:5432)
                                     └── ảnh poster: volume uploads
```

Docker Compose gồm 3 service: `db` (PostgreSQL), `api` (FastAPI, chạy bằng user `appuser`, không phải root), `web` (Nginx).
Khi khởi động, `api` tự chạy `alembic upgrade head` rồi nạp dữ liệu mẫu.

## Cài đặt và chạy

Yêu cầu: Docker và Docker Compose.

```bash
git clone https://github.com/gungvaot/Bai_tap_lon_Mon_lap_trinh_ma_nguon_mo_De_3_Nhom_3.git
cd Bai_tap_lon_Mon_lap_trinh_ma_nguon_mo_De_3_Nhom_3
cp .env.example .env          # rồi đổi POSTGRES_PASSWORD, SECRET_KEY
bash tai-anh.sh               # (tùy chọn) tải ảnh của trường vào frontend/img
docker compose up -d --build
```

| Địa chỉ | Nội dung |
|---------|----------|
| http://localhost:8080 | Giao diện web |
| http://localhost:8080/api/docs | Swagger UI |

Dừng: `docker compose down` (thêm `-v` để xóa cả dữ liệu).

**Chạy test (không cần Docker):**

```bash
cd backend
pip install -r requirements-dev.txt
ruff check .
pytest -q
```

## Tài khoản demo

| Vai trò | Email | Mật khẩu |
|---------|-------|----------|
| Đoàn – Hội (admin) | admin@demo.vn | Admin@123 |
| Ban chủ nhiệm CLB (manager) | manager@demo.vn | Manager@123 |
| Sinh viên (student) | sv@demo.vn | Student@123 |

## API chính

Tất cả đường dẫn đi qua Nginx có tiền tố `/api`. Tài liệu đầy đủ ở Swagger UI.

| Phương thức | Đường dẫn | Quyền | Mô tả |
|-------------|-----------|-------|-------|
| POST | /auth/register | Công khai | Đăng ký tài khoản sinh viên |
| POST | /auth/login | Công khai | Đăng nhập, trả JWT |
| GET | /auth/me | Đã đăng nhập | Thông tin người dùng hiện tại |
| GET | /clubs | Đã đăng nhập | Danh sách CLB |
| POST | /clubs | manager, admin | Tạo CLB |
| DELETE | /clubs/{id} | Chủ nhiệm CLB đó, admin | Xóa CLB (409 nếu còn sự kiện) |
| POST | /clubs/{id}/join | student | Xin gia nhập CLB |
| GET | /clubs/{id}/members | Chủ nhiệm CLB đó, admin | Danh sách thành viên |
| PATCH | /memberships/{id} | Chủ nhiệm CLB đó, admin | Duyệt / từ chối thành viên |
| GET | /me/memberships | Đã đăng nhập | CLB của tôi |
| GET | /events | Đã đăng nhập | Danh sách sự kiện (tìm kiếm `q`, lọc `club_id`, phân trang `page`, `size`) |
| POST | /events | Chủ nhiệm CLB đó, admin | Tạo sự kiện |
| DELETE | /events/{id} | Chủ nhiệm CLB đó, admin | Xóa sự kiện (409 nếu đã có điểm danh) |
| POST | /events/{id}/poster | Chủ nhiệm CLB đó, admin | Upload ảnh poster (JPG/PNG/WEBP, ≤ 2 MB) |
| POST | /events/{id}/register | student | Đăng ký sự kiện (409 nếu hết chỗ hoặc đã đăng ký) |
| DELETE | /events/{id}/register | student | Hủy đăng ký |
| GET | /me/registrations | Đã đăng nhập | Sự kiện tôi đã đăng ký |
| POST | /events/{id}/qr | Chủ nhiệm CLB đó, admin | Sinh mã QR điểm danh, hết hạn sau 10 phút |
| POST | /events/{id}/checkin | student | Điểm danh bằng mã, chỉ trong giờ diễn ra sự kiện |
| GET | /events/{id}/attendances/export | Chủ nhiệm CLB đó, admin | Xuất Excel danh sách điểm danh |
| GET | /me/history | Đã đăng nhập | Sự kiện đã tham gia và tổng điểm rèn luyện |
| GET | /stats/semesters | manager, admin | Thống kê sự kiện theo học kỳ |

Mã trạng thái: `200/201/204` thành công · `401` chưa đăng nhập hoặc token hết hạn · `403` không đủ quyền · `404` không tìm thấy · `409` xung đột nghiệp vụ · `413` file quá lớn · `415` sai định dạng file · `422` dữ liệu không hợp lệ.

## Cơ sở dữ liệu

7 bảng: `users`, `clubs`, `memberships`, `events`, `registrations`, `attendances`, `activity_points`.

- 1:N – `clubs` → `events`; `users` → `clubs` (ban chủ nhiệm)
- N:N – `users` ↔ `clubs` qua `memberships`; `users` ↔ `events` qua `registrations`, `attendances`

ERD: `docs/` *(cập nhật)*

## Cấu trúc thư mục

```
├── backend/
│   ├── app/            # main, models, schemas, security, seed, routers/
│   ├── migrations/     # Alembic
│   ├── tests/          # pytest
│   └── Dockerfile
├── frontend/           # index.html (giao diện), img/
├── docs/               # bảng phân công, ERD
├── .github/workflows/  # CI: ruff + pytest mỗi PR
├── docker-compose.yml
├── nginx.conf
├── tai-anh.sh
└── .env.example
```

## Quy ước làm việc

- Nhánh: `main` luôn chạy được; làm việc trên `feat/...`, `fix/...`, `docs/...`, `test/...`, `chore/...`
- Mọi thay đổi qua Pull Request, có ít nhất 1 thành viên khác Approve rồi mới merge; không tự merge PR của mình
- Commit theo Conventional Commits: `feat:`, `fix:`, `docs:`, `test:`, `chore:`
- Không commit file `.env`, mật khẩu hay khóa bí mật

## Ghi nhận

Ảnh minh họa trong giao diện lấy từ website [hpu.edu.vn](https://hpu.edu.vn/), chỉ dùng cho mục đích học tập.
Nhóm có dùng công cụ AI (Claude) hỗ trợ; chi tiết từng phần được ghi trong báo cáo.
