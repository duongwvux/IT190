import customtkinter as ctk
import tkintermapview as tkmv
import osmnx as ox
import func as f

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

# ── Palette ──────────────────────────────────
C = {
    "bg":       "#F5F6FA",
    "panel":    "#FFFFFF",
    "border":   "#E2E5EE",
    "accent":   "#2563EB",
    "subtext":  "#64748B",
    "text":     "#1E293B",
    "tag_bg":   "#DBEAFE",
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


class BerlinMapUI(ctk.CTk):
    G = ox.load_graphml("berlin_rail.graphml")
    def __init__(self):
        super().__init__()
        self.title("Berlin Rail — Shortest Path Finder")
        self.geometry("1280x820")
        self.minsize(960, 600)
        self.configure(fg_color=C["bg"])

        self.columnconfigure(0, weight=0)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)

        self._build_sidebar()
        self._build_map()

    # ── Sidebar ──────────────────────────────
    def _build_sidebar(self):
        sb = ctk.CTkFrame(self, width=290, corner_radius=0,
                          fg_color=C["panel"],
                          border_width=1, border_color=C["border"])
        sb.grid(row=0, column=0, sticky="nsew")
        sb.grid_propagate(False)
        sb.columnconfigure(0, weight=1)

        # Header
        hdr = ctk.CTkFrame(sb, fg_color=C["accent"], corner_radius=0, height=60)
        hdr.grid(row=0, column=0, sticky="ew")
        hdr.grid_propagate(False)
        ctk.CTkLabel(
            hdr, text="🚆  Berlin Rail Pathfinder",
            font=ctk.CTkFont("Arial", 15, "bold"),
            text_color="#FFFFFF"
        ).place(relx=0.5, rely=0.5, anchor="center")

        p = dict(padx=18, pady=6)

        # Start station
        ctk.CTkLabel(sb, text="Ga khởi đầu (Start)",
                     font=ctk.CTkFont("Arial", 12, "bold"),
                     text_color=C["text"]
                     ).grid(row=1, column=0, sticky="w", padx=18, pady=(20, 2))
        self.cb_start = ctk.CTkComboBox(
            sb, values=STATION_NAMES, width=254, height=36,
            font=ctk.CTkFont("Arial", 12),
            state="normal"
        )
        self.cb_start.set(STATION_NAMES[0])
        self.cb_start.grid(row=2, column=0, **p)

        # End station
        ctk.CTkLabel(sb, text="Ga đích (End)",
                     font=ctk.CTkFont("Arial", 12, "bold"),
                     text_color=C["text"]
                     ).grid(row=3, column=0, sticky="w", padx=18, pady=(12, 2))
        self.cb_end = ctk.CTkComboBox(
            sb, values=STATION_NAMES, width=254, height=36,
            font=ctk.CTkFont("Arial", 12),
            state="normal"
        )
        self.cb_end.set(STATION_NAMES[-1])
        self.cb_end.grid(row=4, column=0, **p)

        # Find button (placeholder)
        self.btn_find = ctk.CTkButton(
            sb, text="🔍  Tìm đường ngắn nhất",
            height=42, corner_radius=8,
            font=ctk.CTkFont("Arial", 13, "bold"),
            fg_color=C["accent"], hover_color="#1D4ED8",
            command=self._on_find          # wire backend here later
        )
        self.btn_find.grid(row=5, column=0, padx=18, pady=(18, 4), sticky="ew")

        # Clear button (placeholder)
        self.btn_clear = ctk.CTkButton(
            sb, text="✕  Xóa tuyến đường",
            height=36, corner_radius=8,
            font=ctk.CTkFont("Arial", 12),
            fg_color="#F1F5F9", text_color=C["subtext"],
            hover_color=C["border"],
            command=self._on_clear         # wire backend here later
        )
        self.btn_clear.grid(row=6, column=0, padx=18, pady=(0, 8), sticky="ew")

        # Divider
        ctk.CTkFrame(sb, height=1, fg_color=C["border"]
                     ).grid(row=7, column=0, sticky="ew", padx=18, pady=10)

        # Result area (placeholder)
        self.result_box = ctk.CTkScrollableFrame(
            sb, fg_color=C["bg"], corner_radius=8, height=260
        )
        self.result_box.grid(row=8, column=0, padx=18, pady=(0, 10), sticky="nsew")
        sb.rowconfigure(8, weight=1)

        self.lbl_result = ctk.CTkLabel(
            self.result_box,
            text="Chọn ga đi và ga đến,\nrồi bấm Tìm đường…",
            font=ctk.CTkFont("Arial", 12),
            text_color=C["subtext"],
            justify="left"
        )
        self.lbl_result.pack(anchor="w", padx=4, pady=8)

        # Legend
        leg = ctk.CTkFrame(sb, fg_color=C["tag_bg"], corner_radius=8)
        leg.grid(row=9, column=0, padx=18, pady=(0, 18), sticky="ew")
        ctk.CTkLabel(
            leg,
            text="🔵 Ga trên mạng   🟢 Ga đầu   🔴 Ga cuối\n🟦 Tuyến đường ngắn nhất",
            font=ctk.CTkFont("Arial", 10),
            text_color=C["accent"],
            justify="left"
        ).pack(padx=10, pady=8, anchor="w")

    # ── Map ──────────────────────────────────
    def _build_map(self):
        wrapper = ctk.CTkFrame(self, corner_radius=0, fg_color=C["bg"])
        wrapper.grid(row=0, column=1, sticky="nsew", padx=(1, 0))
        wrapper.columnconfigure(0, weight=1)
        wrapper.rowconfigure(0, weight=1)

        self.map_widget = tkmv.TkinterMapView(wrapper, corner_radius=0)
        self.map_widget.grid(row=0, column=0, sticky="nsew")

        # Centre on Berlin
        self.map_widget.set_position(52.520, 13.405)
        self.map_widget.set_zoom(11)
        self.map_widget.set_tile_server(
            "https://a.tile.openstreetmap.org/{z}/{x}/{y}.png"
        )

    # ── Stub callbacks — replace with real logic later ──
    def _on_find(self):
        start_station = self.cb_start.get()
        end_station = self.cb_end.get()
        
        self.lbl_result.configure(text= "Đang định vị và tính toán...", text_color=C["text"])
        self.update()
        
        start_node = f.get_all_candidate_nodes(self.G, start_station)
        end_node = f.get_all_candidate_nodes(self.G, end_station)
        
        path_nodes, total_length = f.dijkstra(self.G, start_node, end_node)
        if path_nodes:
            km_length = round(total_length/1000, 2)
            self.lbl_result.configure(
                text=f"✅ Tìm thấy tuyến đường!\n\n📏 Quãng đường: {km_length} km\n🚉 Đi qua: {len(path_nodes)} điểm (nodes)", 
                text_color="green"
            )
            
            coordinates = []
            for node_id in path_nodes:
                lat = self.G.nodes[node_id]['y']
                lng = self.G.nodes[node_id]['x']
                coordinates.append((lat, lng))
            self.current_map_path = self.map_widget.set_path(
                coordinates,
                color= C["accent"],
                width= 5
            )
            start_node = coordinates[0]
            self.start_marker = self.map_widget.set_marker(
                start_node[0], start_node[1], 
                text="Điểm xuất phát",
                marker_color_circle="#10B981", # Màu xanh lá
                text_color="#065F46"
            )

            end_node = coordinates[-1]
            self.end_marker = self.map_widget.set_marker(
                end_node[0], end_node[1], 
                text="Điểm đến",
                marker_color_circle="#EF4444", # Màu đỏ
                text_color="#991B1B"
            )
            print(path_nodes)
            self.map_widget.set_position(coordinates[0][0], coordinates[0][1])
        

    def _on_clear(self):
        self.lbl_result.configure(
            text="Chọn ga đi và ga đến,\nrồi bấm Tìm đường…",
            text_color=C["subtext"]
        )


if __name__ == "__main__":
    app = BerlinMapUI()
    app.mainloop()