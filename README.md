# 🚆 Berlin Rail Map

Ứng dụng tìm đường trên mạng lưới đường ray Berlin sử dụng nhiều thuật toán tìm đường khác nhau, với hệ thống đăng nhập phân quyền Admin / User.

---

## 📸 Demo

---

## ✨ Tính năng

- 🔐 **Đăng nhập phân quyền** — Admin và User có giao diện và quyền hạn khác nhau
- 🗺️ **Bản đồ tương tác** — hiển thị mạng lưới đường ray Berlin thời gian thực
- 🔍 **8 thuật toán tìm đường** — Dijkstra, A\*, Bidirectional A\*, UCS, Greedy Best-First, Bellman-Ford, BFS, DFS
- 🛑 **Thiết lập vùng cấm** *(chỉ Admin)* — chặn khu vực bán kính tuỳ chọn và tính lại đường đi
- 📏 **Hiển thị kết quả** — quãng đường (km) hoặc số bước, số node đi qua

---

## 🏗️ Cấu trúc project

```
IT190/
├── login/
│   ├── __init__.py         # Export LoginWindow
│   ├── role_select.py      # Màn hình chọn vai trò
│   ├── auth_window.py      # Màn hình đăng nhập / đăng ký
│   ├── auth.py             # Logic xác thực
│   ├── theme.py            # Màu sắc theo role
│   └── users.json          # Dữ liệu tài khoản
├── ui.py                   # Giao diện chính BerlinMapUI
├── func.py                 # Các thuật toán tìm đường
├── fetch_api.py            # Tải dữ liệu từ OpenStreetMap
├── berlin_rail.graphml     # Đồ thị mạng lưới đường ray
└── requirements.txt
```

---

## ⚙️ Cài đặt

**Yêu cầu:** Python 3.10+

```bash
# Clone repo
git clone https://github.com/your-username/IT190.git
cd IT190

# Cài dependencies
pip install -r requirements.txt
```

> Nếu chưa có file `berlin_rail.graphml`, chạy lệnh sau để tải dữ liệu từ OpenStreetMap:
> ```bash
> python fetch_api.py
> ```
> *(Cần kết nối internet, có thể mất vài phút)*

---

## 🚀 Chạy ứng dụng

```bash
python ui.py
```

---

## 👤 Tài khoản mặc định

| Username | Password | Role  |
|----------|----------|-------|
| admin    | 123      | Admin |
| bao      | 123      | User  |

> Có thể đăng ký tài khoản mới trực tiếp trong ứng dụng.

---

## 🔑 Phân quyền

| Tính năng              | Admin | User |
|------------------------|:-----:|:----:|
| Tìm đường              | ✅    | ✅   |
| Chọn thuật toán        | ✅    | ✅   |
| Thiết lập vùng cấm     | ✅    | ❌   |

---

## 🧠 Thuật toán

| Thuật toán | Đơn vị kết quả |
|---|---|
| Dijkstra | km |
| A\* Search | km |
| Bidirectional A\* | km |
| Uniform Cost Search (UCS) | km |
| Greedy Best-First Search | km |
| Bellman-Ford | km |
| Breadth-First Search (BFS) | bước |
| Depth-First Search (DFS) | bước |

---

## 🛠️ Công nghệ sử dụng

- [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter) — giao diện đồ họa
- [TkinterMapView](https://github.com/TomSchimansky/TkinterMapView) — hiển thị bản đồ
- [OSMnx](https://osmnx.readthedocs.io/) — tải và xử lý đồ thị OpenStreetMap
- [NetworkX](https://networkx.org/) — cấu trúc dữ liệu đồ thị
- [Shapely](https://shapely.readthedocs.io/) — xử lý hình học địa lý
