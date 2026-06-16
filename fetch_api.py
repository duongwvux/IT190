import osmnx as ox
import json

ox.settings.log_console = True
ox.settings.use_cache = True


def load_berlin_rail_and_stations():
    place_name = "Berlin, Germany"

    # ==========================================
    # 1. LẤY VÀ LƯU MẠNG LƯỚI ĐƯỜNG TÀU (GRAPH)
    # ==========================================
    rail_filter = '["railway"~"subway|tram|rail|light_rail"]'
    G = ox.graph_from_place(place_name, custom_filter=rail_filter, simplify=True)

    filepath = "berlin_rail.graphml"
    ox.save_graphml(G, filepath)
    print(f"Đã lưu đồ thị đường ray vào {filepath}")

    # ==========================================
    # 2. LẤY TÊN CÁC GA TÀU RA MỘT LIST RIÊNG
    # ==========================================
    station_tags = {'railway': ['station', 'halt']}

    # Tải dữ liệu các ga (Lấy cả Node, Way, Relation)
    stations_gdf = ox.features_from_place(place_name, tags=station_tags)

    station_names_list = []

    # Kiểm tra xem cột 'name' có tồn tại không
    if 'name' in stations_gdf.columns:
        station_names_list = stations_gdf['name'].dropna().unique().tolist()
        station_names_list.sort()

        # LƯU RA FILE JSON Ở ĐÂY
        with open('berlin_stations.json', 'w', encoding='utf-8') as f:
            json.dump(station_names_list, f, ensure_ascii=False, indent=4)
        print("Đã xuất danh sách ga ra file berlin_stations.json")

    return G, station_names_list


if __name__ == "__main__":
    # Chạy hàm và nhận về đồ thị G cùng danh sách tên
    G, stations_list = load_berlin_rail_and_stations()

    # In kết quả kiểm tra
    print(f"\nTổng số ga/trạm dừng tìm thấy: {len(stations_list)}")
    for name in stations_list:
        print(f"- {name}")