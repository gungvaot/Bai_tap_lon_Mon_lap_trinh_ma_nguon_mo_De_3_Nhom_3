# Quản lý câu lạc bộ và sự kiện sinh viên

Đồ án nhóm (ĐG2) – Học phần Lập trình mã nguồn mở (POS02024) – Đề tài 3 – Nhóm 3

## Công nghệ
FastAPI · PostgreSQL · SQLAlchemy + Alembic · JWT · Docker Compose · Nginx · GitHub Actions · pytest/Postman

## Thành viên và phân công

| TT | Họ và tên | Vai trò | Nhiệm vụ chính | Đóng góp |
|----|-----------|---------|----------------|----------|
| 1 | Nguyễn Đức Duy | Trưởng nhóm, Front-end | Quản lý tiến độ; giao diện, gọi API, màn hình CLB/sự kiện, quét QR | 
| 2 | Phạm Văn Long Thành | Back-end | RESTful API, JWT, phân quyền, duyệt sự kiện, tính điểm rèn luyện | 
| 3 | Ngô Xuân Lộc | CSDL và QA | ERD, models, Alembic, seed data; test Postman và pytest | 
| 4 | Nguyễn Sỹ Duy Anh | DevOps | Máy chủ, Dockerfile, docker-compose, Nginx, CI/CD |

## Cấu trúc thư mục

~~~
├── backend/        # FastAPI, models, alembic, tests
├── frontend/       # Giao diện
├── nginx/          # Cấu hình Nginx
├── docs/           # ERD, tài liệu, bảng phân công
├── .github/workflows/
├── docker-compose.yml
└── .env.example
~~~

## Quy ước làm việc
- Nhánh: `main` (ổn định), `feat/<tên>-<việc>`, `fix/...`
- Làm việc qua Pull Request, ít nhất 1 người review
- Commit message: `feat:`, `fix:`, `docs:`, `chore:`, `test:`
- Không commit file `.env` hay mật khẩu
