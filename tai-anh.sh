#!/usr/bin/env bash
# Tải ảnh của trường (nguồn: hpu.edu.vn) vào thư mục frontend/img
# Chạy ở thư mục gốc của repo:  bash tai-anh.sh
set -e
mkdir -p frontend/img
cd frontend/img
curl -fsSL -o logo.png "https://theme.hstatic.net/1000215755/1001198208/14/logo.png?v=749" && echo "OK  logo.png" || echo "LOI logo"
curl -fsSL -o campus.jpg "https://file.hstatic.net/1000215755/file/ai_hoc_quan_ly_va_cong_nghe_hai_phong_6513b4e483274ababa4929c2043afd42_grande.jpg" && echo "OK  campus.jpg" || echo "LOI campus"
curl -fsSL -o library.jpg "https://file.hstatic.net/1000215755/file/thu_vien_mo_hpu__1__2ea6d1a7584a4ac380633468fd757ebf_grande.jpg" && echo "OK  library.jpg" || echo "LOI library"
curl -fsSL -o dance.jpg "https://file.hstatic.net/1000215755/file/a_ket_noi_dam_me_khi_tham_gia_clb__1__fae251ceb2124fe29796f4eabd1700dd_grande.jpg" && echo "OK  dance.jpg" || echo "LOI dance"
curl -fsSL -o hearts.png "https://cdn.hstatic.net/files/1000215755/article/dan_len_4ce603a8daa644f1a85d6f3585cdc96e_large.png" && echo "OK  hearts.png" || echo "LOI hearts"
curl -fsSL -o trees.jpg "https://cdn.hstatic.net/files/1000215755/article/1_be199b7f80114f87a060326cd473424e_large.jpg" && echo "OK  trees.jpg" || echo "LOI trees"
curl -fsSL -o class4kid.jpg "https://cdn.hstatic.net/files/1000215755/article/eng_dd2426622392450296ea4528a43a1e5b_large.jpg" && echo "OK  class4kid.jpg" || echo "LOI class4kid"
curl -fsSL -o exam.jpg "https://cdn.hstatic.net/files/1000215755/article/_f8a9160_10f84e05eb6a4d62aae949bfd4bbe8cb_large.jpg" && echo "OK  exam.jpg" || echo "LOI exam"
curl -fsSL -o startup.jpg "https://cdn.hstatic.net/files/1000215755/article/hpu_cafe_khoi_nghiep_so_15__9__c99a8d84a93e4132947abb90ee9c990e.jpg" && echo "OK  startup.jpg" || echo "LOI startup"
curl -fsSL -o digital.jpg "https://cdn.hstatic.net/files/1000215755/article/picture1_665a2e79a5f24ec19310a89f43dd7b6f_large.jpg" && echo "OK  digital.jpg" || echo "LOI digital"
curl -fsSL -o theory.jpg "https://cdn.hstatic.net/files/1000215755/article/_f8a7074_582b95d94e774a42be39763c2fe9354c_large.jpg" && echo "OK  theory.jpg" || echo "LOI theory"
curl -fsSL -o opening.jpg "https://cdn.hstatic.net/files/1000215755/article/0905_10__256dcbcd86f1490bbe640f8860b3c8a8.jpg" && echo "OK  opening.jpg" || echo "LOI opening"
curl -fsSL -o sport1.jpg "https://theme.hstatic.net/1000215755/1001198208/14/trainghiem-1-image_grande.jpg?v=749" && echo "OK  sport1.jpg" || echo "LOI sport1"
curl -fsSL -o sport2.jpg "https://theme.hstatic.net/1000215755/1001198208/14/trainghiem-2-image_grande.jpg?v=749" && echo "OK  sport2.jpg" || echo "LOI sport2"
ls -lh
