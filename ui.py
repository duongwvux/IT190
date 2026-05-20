import customtkinter as ctk
import tkintermapview as tkmv
import osmnx as ox
import func as f
import math

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

C = {
    "bg":       "#F5F6FA",
    "panel":    "#FFFFFF",
    "border":   "#E2E5EE",
    "accent":   "#2563EB",
    "subtext":  "#64748B",
    "text":     "#1E293B",
    "danger":   "#EF4444"
}

STATION_NAMES = [
    "Hauptbahnhof", "Friedrichstraße", "Alexanderplatz", "Ostbahnhof",
    "Ostkreuz", "Warschauer Str.", "Potsdamer Platz", "Zoologischer Garten",
    "Charlottenburg", "Westkreuz", "Spandau", "Gesundbrunnen",
    "Schönhauser Allee", "Prenzlauer Allee", "Lichtenberg", "Südkreuz",
    "Tempelhof", "Neukölln", "Hermannstraße", "Wannsee",
    "Messe Nord", "Jungfernheide", "Wedding", "Pankow", "Steglitz",
]
STATION_NAMES.sort()

ALGORITHMS = [
    "Dijkstra", "A* Search", "Bidirectional A*", "Uniform Cost Search (UCS)",
    "Greedy Best-First Search", "Bellman-Ford", "Breadth-First Search (BFS)", "Depth-First Search (DFS)"
]
RADIUS_OPTIONS = ["Không chặn", "500 m", "1000 m", "2000 m", "3000 m"]


def get_circle_polygon_points(lat, lng, radius_meters, num_points=36):
    earth_radius = 6371000.0
    points = []
    for i in range(num_points):
        angle = math.radians(float(i) * (360.0 / num_points))
        delta_lat = (radius_meters * math.cos(angle)) / earth_radius
        delta_lng = (radius_meters * math.sin(angle)) / (earth_radius * math.cos(math.radians(lat)))
        points.append((lat + math.degrees(delta_lat), lng + math.degrees(delta_lng)))
    return points


class BerlinMapUI(ctk.CTk):
    G = ox.load_graphml("berlin_rail.graphml")
    
    def __init__(self):
        super().__init__()
        self.title("Berlin Rail Pathfinder — Fixed")
        self.geometry("1300x850")
        
        # Cấu hình grid phân chia layout chính của cửa sổ
        self.columnconfigure(0, weight=0)  # Sidebar cố định kích thước
        self.columnconfigure(1, weight=1)  # Bản đồ co giãn tự động
        self.rowconfigure(0, weight=1)
        
        self.current_map_path = None
        self.start_marker = None
        self.end_marker = None
        self.avoid_circle = None

        self.algo_mapping = {
            "Dijkstra": f.dijkstra, "A* Search": f.a_star_search,
            "Bidirectional A*": f.bidirectional_a_star, "Uniform Cost Search (UCS)": f.ucs,
            "Greedy Best-First Search": f.greedy_best_first_search, "Bellman-Ford": f.bellman_ford,
            "Breadth-First Search (BFS)": f.bfs, "Depth-First Search (DFS)": f.dfs
        }
        self._build_sidebar()
        self._build_map()

    def _build_sidebar(self):
        # Thiết lập khung Sidebar nằm ở ô (row=0, column=0)
        sb = ctk.CTkScrollableFrame(self, width=300, corner_radius=0, fg_color=C["panel"], border_width=1, border_color=C["border"])
        sb.grid(row=0, column=0, sticky="nsew")

        hdr = ctk.CTkFrame(sb, fg_color=C["accent"], corner_radius=0, height=60)
        hdr.pack(fill="x", ipady=5, pady=(0, 10))
        ctk.CTkLabel(hdr, text="🚆  Berlin Rail Navigator", font=ctk.CTkFont("Arial", 16, "bold"), text_color="#FFFFFF").pack(pady=12)

        p = dict(padx=10, pady=4)
        ctk.CTkLabel(sb, text="Ga khởi đầu (Start)", font=ctk.CTkFont("Arial", 12, "bold"), text_color=C["text"]).pack(anchor="w", padx=10, pady=(10, 2))
        self.cb_start = ctk.CTkComboBox(sb, values=STATION_NAMES, width=260, height=36); self.cb_start.set("Hauptbahnhof"); self.cb_start.pack(**p)

        ctk.CTkLabel(sb, text="Ga đích (End)", font=ctk.CTkFont("Arial", 12, "bold"), text_color=C["text"]).pack(anchor="w", padx=10, pady=(10, 2))
        self.cb_end = ctk.CTkComboBox(sb, values=STATION_NAMES, width=260, height=36); self.cb_end.set("Alexanderplatz"); self.cb_end.pack(**p)

        ctk.CTkLabel(sb, text="Thuật toán tìm đường", font=ctk.CTkFont("Arial", 12, "bold"), text_color=C["text"]).pack(anchor="w", padx=10, pady=(10, 2))
        self.cb_algo = ctk.CTkComboBox(sb, values=ALGORITHMS, width=260, height=36, state="readonly"); self.cb_algo.set("Dijkstra"); self.cb_algo.pack(**p)

        ctk.CTkFrame(sb, height=1, fg_color=C["border"]).pack(fill="x", padx=10, pady=15)
        ctk.CTkLabel(sb, text="🛑 THIẾT LẬP VÙNG CẤM", font=ctk.CTkFont("Arial", 12, "bold"), text_color=C["danger"]).pack(anchor="w", **p)
        
        self.cb_avoid_center = ctk.CTkComboBox(sb, values=STATION_NAMES, width=260, height=36); self.cb_avoid_center.set("Friedrichstraße"); self.cb_avoid_center.pack(**p)
        self.cb_avoid_radius = ctk.CTkComboBox(sb, values=RADIUS_OPTIONS, width=260, height=36, state="readonly"); self.cb_avoid_radius.set("Không chặn"); self.cb_avoid_radius.pack(**p)

        self.btn_find = ctk.CTkButton(sb, text="🔍  Tìm Tuyến Đường", height=42, corner_radius=8, font=ctk.CTkFont("Arial", 13, "bold"), fg_color=C["accent"], hover_color="#1D4ED8", command=self._on_find)
        self.btn_find.pack(fill="x", padx=10, pady=(15, 5))
        self.btn_clear = ctk.CTkButton(sb, text="✕  Xóa Trạng Thái", height=36, corner_radius=8, fg_color="#F1F5F9", text_color=C["subtext"], hover_color=C["border"], command=self._on_clear)
        self.btn_clear.pack(fill="x", padx=10, pady=5)

        # Hộp chứa kết quả hiển thị thông tin
        self.result_box = ctk.CTkFrame(sb, fg_color=C["bg"], corner_radius=8, height=140)
        self.result_box.pack(fill="x", padx=10, pady=15)
        self.result_box.pack_propagate(False) # Giữ nguyên chiều cao cố định của hộp thông báo
        
        # Đặt lbl_result vào TRONG result_box để không làm lệch giao diện bên ngoài
        self.lbl_result = ctk.CTkLabel(self.result_box, text="Chọn thông số và\nbấm Tìm Tuyến Đường...", font=ctk.CTkFont("Arial", 12), text_color=C["subtext"], justify="left")
        self.lbl_result.pack(anchor="w", padx=12, pady=12)

    def _build_map(self):
        # Khung bản đồ nằm ở ô bên phải (row=0, column=1)
        wrapper = ctk.CTkFrame(self, fg_color=C["bg"])
        wrapper.grid(row=0, column=1, sticky="nsew")
        wrapper.columnconfigure(0, weight=1); wrapper.rowconfigure(0, weight=1)
        
        self.map_widget = tkmv.TkinterMapView(wrapper, corner_radius=0)
        self.map_widget.grid(row=0, column=0, sticky="nsew")
        self.map_widget.set_position(52.520, 13.405); self.map_widget.set_zoom(13)

    def _on_find(self):
        self._clear_map_elements()
        start_station = self.cb_start.get()
        end_station = self.cb_end.get()
        selected_algo = self.cb_algo.get()
        avoid_station = self.cb_avoid_center.get()
        radius_str = self.cb_avoid_radius.get()

        self.lbl_result.configure(text="🔄 Đang tính toán...", text_color=C["text"])
        self.update()

        avoid_zones = []
        if radius_str != "Không chặn":
            avoid_nodes = f.get_all_candidate_nodes(self.G, avoid_station, radius_meters=200)
            if avoid_nodes:
                lat_c = float(self.G.nodes[avoid_nodes[0]]['y'])
                lng_c = float(self.G.nodes[avoid_nodes[0]]['x'])
                radius_meters = int(radius_str.replace(" m", ""))
                
                avoid_zones.append((lat_c, lng_c, radius_meters))
                
                circle_points = get_circle_polygon_points(lat_c, lng_c, radius_meters)
                self.avoid_circle = self.map_widget.set_polygon(circle_points, fill_color="#EF4444", outline_color="#B91C1C", border_width=1.5)
            else:
                print(f"⚠️ Không tìm thấy tọa độ cho ga vùng cấm: {avoid_station}")

        start_nodes = f.get_all_candidate_nodes(self.G, start_station)
        end_nodes = f.get_all_candidate_nodes(self.G, end_station)

        if not start_nodes or not end_nodes:
            self.lbl_result.configure(text="❌ Lỗi định vị vị trí nhà ga chính!", text_color="red")
            return

        search_func = self.algo_mapping[selected_algo]
        path_nodes, cost = search_func(self.G, start_nodes, end_nodes, avoid_zones=avoid_zones)

        if path_nodes and cost != float('infinity'):
            # Kiểm tra xem có phải BFS hoặc DFS không để hiển thị đơn vị "bước"
            if selected_algo in ["Breadth-First Search (BFS)", "Depth-First Search (DFS)"]:
                cost_text = f"📏 Chi phí: {int(cost)} bước"
            else:
                # Các thuật toán còn lại (Dijkstra, A*, UCS...) có cost là mét, đổi ra km
                cost_text = f"📏 Quãng đường: {round(cost / 1000, 2)} km"
                
            self.lbl_result.configure(text=f"✅ Tìm đường thành công!\n🤖 Thuật toán: {selected_algo}\n{cost_text}\n🚉 Đi qua: {len(path_nodes)} nodes.", text_color="green")

            coordinates = [(self.G.nodes[nid]['y'], self.G.nodes[nid]['x']) for nid in path_nodes]
            self.current_map_path = self.map_widget.set_path(coordinates, color=C["accent"], width=5)
            self.start_marker = self.map_widget.set_marker(coordinates[0][0], coordinates[0][1], text=f"Đi: {start_station}", marker_color_circle="#10B981")
            self.end_marker = self.map_widget.set_marker(coordinates[-1][0], coordinates[-1][1], text=f"Đến: {end_station}", marker_color_circle="#EF4444")
            self.map_widget.set_position(coordinates[0][0], coordinates[0][1])
        else:
            self.lbl_result.configure(text=f"❌ Thất bại!\nKhông tìm được đường đi hợp lệ.\nVùng cấm đã chặn các tuyến ray.", text_color="red")
    def _clear_map_elements(self):
        if self.current_map_path: self.current_map_path.delete(); self.current_map_path = None
        if self.start_marker: self.start_marker.delete(); self.start_marker = None
        if self.end_marker: self.end_marker.delete(); self.end_marker = None
        if self.avoid_circle: self.avoid_circle.delete(); self.avoid_circle = None

    def _on_clear(self):
        self._clear_map_elements(); self.cb_avoid_radius.set("Không chặn")
        self.lbl_result.configure(text="Chọn thông số và\nbấm Tìm Tuyến Đường...", text_color=C["subtext"])


if __name__ == "__main__":
    app = BerlinMapUI()
    app.mainloop()