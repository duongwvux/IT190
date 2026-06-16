import customtkinter as ctk
import tkintermapview as tkmv
import osmnx as ox
import math
import json

import func as f

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

C = {
    "bg":      "#F5F6FA",
    "panel":   "#FFFFFF",
    "border":  "#E2E5EE",
    "accent":  "#2563EB",
    "subtext": "#64748B",
    "text":    "#1E293B",
    "danger":  "#EF4444",
}

# Đọc file JSON trở lại thành List
with open('berlin_stations.json', 'r', encoding='utf-8') as j:
    STATION_NAMES = json.load(j)

ALGORITHMS = [
    "Dijkstra", "A* Search", "Bidirectional A*", "Uniform Cost Search (UCS)",
    "Greedy Best-First Search", "Bellman-Ford",
    "Breadth-First Search (BFS)", "Depth-First Search (DFS)",
]
RADIUS_OPTIONS = ["Không chặn", "500 m", "1000 m", "2000 m", "3000 m"]


def get_circle_polygon_points(lat, lng, radius_meters, num_points=36):
    R = 6371000.0
    pts = []
    for i in range(num_points):
        angle = math.radians(i * (360.0 / num_points))
        dlat = (radius_meters * math.cos(angle)) / R
        dlng = (radius_meters * math.sin(angle)) / (R * math.cos(math.radians(lat)))
        pts.append((lat + math.degrees(dlat), lng + math.degrees(dlng)))
    return pts


class BerlinMapUI(ctk.CTk):
    _G_raw = ox.load_graphml("berlin_rail.graphml")

    _G_raw = ox.distance.add_edge_lengths(_G_raw)

    _G_raw = _G_raw.to_undirected().to_directed()

    G = f.connect_broken_rails(_G_raw, radius_meters=50)

    def __init__(self, role="user", on_logout=None):
        super().__init__()
        self.role = role                          # "admin" hoặc "user"
        self.is_admin = (role == "admin")
        self.on_logout = on_logout

        self.title("Berlin Rail Pathfinder" + (" — Admin" if self.is_admin else " — User"))
        self.geometry("1300x850")

        self.columnconfigure(0, weight=0)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)

        self.current_map_path = None
        self.start_marker     = None
        self.end_marker       = None
        self.avoid_circle     = None

        self.algo_mapping = {
            "Dijkstra":                      f.dijkstra,
            "A* Search":                     f.a_star_search,
            "Bidirectional A*":              f.bidirectional_a_star,
            "Uniform Cost Search (UCS)":     f.ucs,
            "Greedy Best-First Search":      f.greedy_best_first_search,
            "Bellman-Ford":                  f.bellman_ford,
            "Breadth-First Search (BFS)":    f.bfs,
            "Depth-First Search (DFS)":      f.dfs,
        }

        self._build_sidebar()
        self._build_map()

    # ── SIDEBAR ───────────────────────────────────────────
    def _build_sidebar(self):
        sb = ctk.CTkScrollableFrame(
            self, width=300, corner_radius=0,
            fg_color=C["panel"],
            border_width=1, border_color=C["border"])
        sb.grid(row=0, column=0, sticky="nsew")

        # Header — màu khác nhau theo role
        hdr_color = "#1E3A5F" if self.is_admin else "#14532D"
        hdr = ctk.CTkFrame(sb, fg_color=hdr_color, corner_radius=0, height=60)
        hdr.pack(fill="x", ipady=5, pady=(0, 10))

        role_icon  = "🔐" if self.is_admin else "🚇"
        role_label = "Admin Portal" if self.is_admin else "User Portal"
        ctk.CTkLabel(
            hdr,
            text=f"{role_icon}  Berlin Rail Navigator",
            font=ctk.CTkFont("Arial", 15, "bold"),
            text_color="#FFFFFF"
        ).pack(pady=(10, 2))
        ctk.CTkLabel(
            hdr, text=role_label,
            font=ctk.CTkFont("Arial", 9),
            text_color="#94A3B8"
        ).pack()

        p = dict(padx=10, pady=4)

        # Ga đi
        ctk.CTkLabel(sb, text="Ga khởi đầu (Start)",
                     font=ctk.CTkFont("Arial", 12, "bold"),
                     text_color=C["text"]).pack(anchor="w", padx=10, pady=(10, 2))
        self.cb_start = ctk.CTkComboBox(sb, width=260, height=36)  # Đã xóa tham số values ở đây
        self.cb_start.set("Hauptbahnhof")
        self.cb_start.pack(**p)
        # Bật tính năng tìm kiếm
        self._enable_autocomplete(self.cb_start, STATION_NAMES)

        # Ga đến
        ctk.CTkLabel(sb, text="Ga đích (End)",
                     font=ctk.CTkFont("Arial", 12, "bold"),
                     text_color=C["text"]).pack(anchor="w", padx=10, pady=(10, 2))
        self.cb_end = ctk.CTkComboBox(sb, width=260, height=36)  # Đã xóa tham số values ở đây
        self.cb_end.set("Alexanderplatz")
        self.cb_end.pack(**p)
        # Bật tính năng tìm kiếm
        self._enable_autocomplete(self.cb_end, STATION_NAMES)

        # Thuật toán
        ctk.CTkLabel(sb, text="Thuật toán tìm đường",
                     font=ctk.CTkFont("Arial", 12, "bold"),
                     text_color=C["text"]).pack(anchor="w", padx=10, pady=(10, 2))
        self.cb_algo = ctk.CTkComboBox(sb, values=ALGORITHMS, width=260, height=36, state="readonly")
        self.cb_algo.set("Dijkstra")
        self.cb_algo.pack(**p)

        # ── Vùng cấm: CHỈ hiện với Admin ──────────────────
        if self.is_admin:
            ctk.CTkFrame(sb, height=1, fg_color=C["border"]).pack(fill="x", padx=10, pady=15)
            ctk.CTkLabel(sb, text="🛑 THIẾT LẬP VÙNG CẤM",
                         font=ctk.CTkFont("Arial", 12, "bold"),
                         text_color=C["danger"]).pack(anchor="w", **p)

            self.cb_avoid_center = ctk.CTkComboBox(sb, width=260, height=36)  # Đã xóa tham số values ở đây
            self.cb_avoid_center.set("Friedrichstraße")
            self.cb_avoid_center.pack(**p)
            # Bật tính năng tìm kiếm cho Admin
            self._enable_autocomplete(self.cb_avoid_center, STATION_NAMES)

            self.cb_avoid_radius = ctk.CTkComboBox(sb, values=RADIUS_OPTIONS, width=260, height=36, state="readonly")
            self.cb_avoid_radius.set("Không chặn")
            self.cb_avoid_radius.pack(**p)
        else:
            # User: tạo biến giả để _on_find không lỗi
            self.cb_avoid_center = None
            self.cb_avoid_radius = None

        # Divider trước nút
        ctk.CTkFrame(sb, height=1, fg_color=C["border"]).pack(fill="x", padx=10, pady=15)

        # Nút tìm đường
        self.btn_find = ctk.CTkButton(
            sb, text="🔍  Tìm Tuyến Đường",
            height=42, corner_radius=8,
            font=ctk.CTkFont("Arial", 13, "bold"),
            fg_color=C["accent"], hover_color="#1D4ED8",
            command=self._on_find)
        self.btn_find.pack(fill="x", padx=10, pady=(0, 5))

        self.btn_clear = ctk.CTkButton(
            sb, text="✕  Xóa Trạng Thái",
            height=36, corner_radius=8,
            fg_color="#F1F5F9", text_color=C["subtext"],
            hover_color=C["border"],
            command=self._on_clear)
        self.btn_clear.pack(fill="x", padx=10, pady=5)

        self.btn_logout = ctk.CTkButton(
            sb, text="🚪  Đăng xuất",
            height=36, corner_radius=8,
            fg_color="#EF4444", hover_color="#DC2626",
            command=self._on_logout)
        self.btn_logout.pack(fill="x", padx=10, pady=(0, 15))

        # Kết quả
        self.result_box = ctk.CTkFrame(sb, fg_color=C["bg"], corner_radius=8, height=140)
        self.result_box.pack(fill="x", padx=10, pady=15)
        self.result_box.pack_propagate(False)

        self.lbl_result = ctk.CTkLabel(
            self.result_box,
            text="Chọn thông số và\nbấm Tìm Tuyến Đường...",
            font=ctk.CTkFont("Arial", 12),
            text_color=C["subtext"], justify="left")
        self.lbl_result.pack(anchor="w", padx=12, pady=12)

    # ── MAP ───────────────────────────────────────────────
    def _build_map(self):
        wrapper = ctk.CTkFrame(self, fg_color=C["bg"])
        wrapper.grid(row=0, column=1, sticky="nsew")
        wrapper.columnconfigure(0, weight=1)
        wrapper.rowconfigure(0, weight=1)

        self.map_widget = tkmv.TkinterMapView(wrapper, corner_radius=0)
        self.map_widget.grid(row=0, column=0, sticky="nsew")
        self.map_widget.set_position(52.520, 13.405)
        self.map_widget.set_zoom(13)

    # ── BUILD PATH COORDINATES ────────────────────────────
    def _build_path_coordinates(self, path_nodes):
        coordinates = []
        for i in range(len(path_nodes) - 1):
            u, v = path_nodes[i], path_nodes[i + 1]

            # 1. Lưu điểm khởi đầu của tuyến (nếu mảng còn trống)
            if not coordinates:
                coordinates.append((self.G.nodes[u]["y"], self.G.nodes[u]["x"]))

            # 2. KHÔNG DÙNG [0] NỮA. Tìm cạnh có khoảng cách ngắn nhất giữa u và v
            best_edge = None
            min_length = float('infinity')
            if v in self.G[u]:
                for key, data in self.G[u][v].items():
                    length = float(data.get('length', 1.0))
                    if length < min_length:
                        min_length = length
                        best_edge = data

            if not best_edge:
                continue

            # 3. Trích xuất Geometry và XỬ LÝ NGƯỢC CHIỀU
            if "geometry" in best_edge:
                # coords của shapely có định dạng (lon, lat)
                coords = list(best_edge["geometry"].coords)

                # So sánh khoảng cách để xem mảng coords đang xuôi hay ngược so với hướng đi (u -> v)
                u_x, u_y = self.G.nodes[u]["x"], self.G.nodes[u]["y"]
                v_x, v_y = self.G.nodes[v]["x"], self.G.nodes[v]["y"]
                first_coord_x, first_coord_y = coords[0]

                dist_to_u = (first_coord_x - u_x) ** 2 + (first_coord_y - u_y) ** 2
                dist_to_v = (first_coord_x - v_x) ** 2 + (first_coord_y - v_y) ** 2

                # Nếu điểm đầu của chuỗi coords lại nằm gần đích (v) hơn là nguồn (u)
                # -> Chuỗi đang bị ngược chiều -> Cần đảo ngược lại mảng
                if dist_to_v < dist_to_u:
                    coords.reverse()

                # Cập nhật tọa độ vào danh sách vẽ (bỏ qua điểm đầu để tránh trùng lặp)
                for lon, lat in coords[1:]:
                    coordinates.append([lat, lon])  # tkmapview dùng [lat, lon]
            else:
                # Nếu chỉ là đoạn thẳng nối trực tiếp không có độ cong
                coordinates.append((self.G.nodes[v]["y"], self.G.nodes[v]["x"]))

        return coordinates

    # ── ON FIND ───────────────────────────────────────────
    def _on_find(self):
        self._clear_map_elements()

        start_station   = self.cb_start.get()
        end_station     = self.cb_end.get()
        selected_algo   = self.cb_algo.get()

        self.lbl_result.configure(text="🔄 Đang tính toán...", text_color=C["text"])
        self.update()

        # Vùng cấm — chỉ admin mới có widget, user luôn rỗng
        avoid_zones = []
        if self.is_admin:
            radius_str = self.cb_avoid_radius.get()
            if radius_str != "Không chặn":
                avoid_station = self.cb_avoid_center.get()
                avoid_nodes = f.get_all_candidate_nodes(self.G, avoid_station, radius_meters=200)
                if avoid_nodes:
                    lat_c = float(self.G.nodes[avoid_nodes[0]]["y"])
                    lng_c = float(self.G.nodes[avoid_nodes[0]]["x"])
                    radius_meters = int(radius_str.replace(" m", ""))
                    avoid_zones.append((lat_c, lng_c, radius_meters))
                    circle_pts = get_circle_polygon_points(lat_c, lng_c, radius_meters)
                    self.avoid_circle = self.map_widget.set_polygon(
                        circle_pts,
                        fill_color="#EF4444",
                        outline_color="#B91C1C",
                        border_width=1.5)

        start_nodes = f.get_all_candidate_nodes(self.G, start_station)
        end_nodes   = f.get_all_candidate_nodes(self.G, end_station)

        if not start_nodes or not end_nodes:
            self.lbl_result.configure(text="❌ Lỗi định vị vị trí nhà ga!", text_color="red")
            return

        search_func = self.algo_mapping[selected_algo]
        path_nodes, cost = search_func(self.G, start_nodes, end_nodes, avoid_zones=avoid_zones)

        if path_nodes and cost != float("infinity"):
            cost_text = f"📏 Quãng đường: {round(cost / 1000, 2)} km"

            self.lbl_result.configure(
                text=f"✅ Tìm đường thành công!\n🤖 Thuật toán: {selected_algo}\n"
                     f"{cost_text}\n🚉 Đi qua: {len(path_nodes)} nodes.",
                text_color="green")

            coordinates = self._build_path_coordinates(path_nodes)
            self.current_map_path = self.map_widget.set_path(
                coordinates, color=C["accent"], width=5)
            self.start_marker = self.map_widget.set_marker(
                coordinates[0][0], coordinates[0][1],
                text=f"Đi: {start_station}", marker_color_circle="#10B981")
            self.end_marker = self.map_widget.set_marker(
                coordinates[-1][0], coordinates[-1][1],
                text=f"Đến: {end_station}", marker_color_circle="#EF4444")
            self.map_widget.set_position(coordinates[0][0], coordinates[0][1])
        else:
            self.lbl_result.configure(
                text="❌ Thất bại!\nKhông tìm được đường đi hợp lệ.\nVùng cấm đã chặn các tuyến ray.",
                text_color="red")

    # ── CLEAR ─────────────────────────────────────────────
    def _clear_map_elements(self):
        if self.current_map_path: self.current_map_path.delete(); self.current_map_path = None
        if self.start_marker:     self.start_marker.delete();     self.start_marker     = None
        if self.end_marker:       self.end_marker.delete();       self.end_marker       = None
        if self.avoid_circle:     self.avoid_circle.delete();     self.avoid_circle     = None

    def _on_clear(self):
        self._clear_map_elements()
        if self.is_admin:
            self.cb_avoid_radius.set("Không chặn")
        self.lbl_result.configure(
            text="Chọn thông số và\nbấm Tìm Tuyến Đường...",
            text_color=C["subtext"])

    def _on_logout(self):
        self.destroy()
        if self.on_logout:
            self.on_logout()

    def _enable_autocomplete(self, combobox, all_values):
        """
        Biến CTkComboBox thành thanh tìm kiếm động.
        Hiển thị các kết quả BẮT ĐẦU BẰNG từ khóa đã gõ.
        """
        combobox.configure(values=[])

        def handle_typing(event):
            # Bỏ qua các phím điều hướng
            if event.keysym in ["Up", "Down", "Return", "Tab", "Escape"]:
                return

            typed_text = combobox.get().lower()

            if not typed_text:
                combobox.configure(values=[])
            else:
                # Dùng .startswith() để tìm những ga bắt đầu bằng chữ đã nhập
                matches = [station for station in all_values if station.lower().startswith(typed_text)]

                # Nạp danh sách kết quả phù hợp
                combobox.configure(values=matches)

        # Gắn sự kiện gõ phím
        combobox._entry.bind("<KeyRelease>", handle_typing)


# ── ENTRY POINT ───────────────────────────────────────────
from login import LoginWindow

def start_app(role):
    app = BerlinMapUI(role=role, on_logout=lambda: LoginWindow(start_app))
    app.mainloop()

if __name__ == "__main__":
    LoginWindow(start_app)