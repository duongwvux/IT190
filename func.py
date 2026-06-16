import osmnx as ox
import networkx as nx
import heapq
import math
from collections import deque
import numpy as np
from scipy.spatial import cKDTree

# ── 1. CÁC HÀM TRỢ GIÚP ĐỊNH VỊ VÀ TÍNH TOÁN GPS ───────────────────

def haversine_distance(lat1, lon1, lat2, lon2):
    """Tính khoảng cách thực tế bằng mét giữa 2 tọa độ GPS"""
    R = 6371000  # Bán kính Trái Đất (mét)
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = math.sin(delta_phi / 2.0) ** 2 + \
        math.cos(phi1) * math.cos(phi2) * \
        math.sin(delta_lambda / 2.0) ** 2

    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


def get_all_station_names(G) -> list[str]:
    """
    Trả về list tên ga duy nhất, có tên, sắp xếp theo alphabet.
    Ưu tiên node có railway = station/stop/halt.
    """
    seen   = set()
    result = []

    for _, data in G.nodes(data=True):
        name    = data.get("name", "")
        railway = data.get("railway", "")

        # Đôi khi OSMnx lưu list thay vì string
        if isinstance(name, list):
            name = name[0]

        name = name.strip()

        # Chỉ lấy node là ga (có tên + có tag railway)
        if name and railway and name not in seen:
            seen.add(name)
            result.append(name)

    return sorted(result)


def get_all_candidate_nodes(G, station_name, radius_meters=700):
    """Tìm tất cả các nút thuộc nhà ga"""
    candidates = []
    for node_id, data in G.nodes(data=True):
        name_attr = data.get('name', '')
        if isinstance(name_attr, list):
            name_attr = " ".join(name_attr)
        
        if station_name.lower() in name_attr.lower():
            candidates.append(node_id)
            
    if candidates:
        return candidates

    query = f"{station_name}, Berlin, Germany"
    try:
        lat_center, lng_center = ox.geocode(query)
        lat_center, lng_center = float(lat_center), float(lng_center)

        for node_id, data in G.nodes(data=True):
            dist = haversine_distance(lat_center, lng_center, data['y'], data['x'])
            if dist <= radius_meters:
                candidates.append(node_id)

        if not candidates:
            fallback = int(ox.distance.nearest_nodes(G, X=[lng_center], Y=[lat_center])[0])
            return [fallback]
        return candidates
    except Exception as e:
        print(f"❌ Không thể định vị ga '{station_name}': {e}")
        return []


def is_node_in_avoid_zone(G, node_id, avoid_zones):
    """Kiểm tra nút có nằm trong vùng cấm không"""
    if not avoid_zones:
        return False
    
    n_lat = G.nodes[node_id]['y']
    n_lng = G.nodes[node_id]['x']
    
    for z_lat, z_lng, radius in avoid_zones:
        if haversine_distance(z_lat, z_lng, n_lat, n_lng) <= radius:
            return True
    return False


def is_edge_in_avoid_zone(G, u, v, avoid_zones):
    """Kiểm tra cạnh nội suy thông minh (u, v và trung điểm)"""
    if not avoid_zones:
        return False

    u_lat, u_lng = G.nodes[u]['y'], G.nodes[u]['x']
    v_lat, v_lng = G.nodes[v]['y'], G.nodes[v]['x']
    mid_lat = (u_lat + v_lat) / 2
    mid_lng = (u_lng + v_lng) / 2
    
    for z_lat, z_lng, radius in avoid_zones:
        if (haversine_distance(z_lat, z_lng, u_lat, u_lng) <= radius or
            haversine_distance(z_lat, z_lng, v_lat, v_lng) <= radius or
            haversine_distance(z_lat, z_lng, mid_lat, mid_lng) <= radius):
            return True
            
    return False


def get_heuristic(node, target_nodes, G):
    """Tính toán h(n) khoảng cách chim bay nhỏ nhất tới tập đích"""
    lat1 = G.nodes[node]['y']
    lon1 = G.nodes[node]['x']
    min_dist = float('infinity')
    for target in target_nodes:
        lat2 = G.nodes[target]['y']
        lon2 = G.nodes[target]['x']
        dist = haversine_distance(lat1, lon1, lat2, lon2)
        if dist < min_dist:
            min_dist = dist
    return min_dist


def connect_broken_rails(G, radius_meters=50):
    """
    Tìm và nối các node nằm gần nhau (đi bộ chuyển tuyến) để tránh đồ thị bị vỡ.
    """
    print(f"🔄 Đang xây cầu nối ảo cho các ga bị đứt gãy (Bán kính: {radius_meters}m)...")

    nodes = list(G.nodes(data=True))
    node_ids = [n[0] for n in nodes]

    # Đưa hệ tọa độ cầu về hệ tọa độ phẳng xấp xỉ (mét) tại vĩ độ của Berlin
    # 1 độ vĩ ~ 111,320m. 1 độ kinh ~ 111,320m * cos(vĩ độ)
    lat_center = math.radians(52.52)
    coords_meters = np.array([
        (n[1]['y'] * 111320.0, n[1]['x'] * 111320.0 * math.cos(lat_center))
        for n in nodes
    ])

    # Dùng cây KDTree để truy vấn các cặp điểm gần nhau cực nhanh O(N log N)
    tree = cKDTree(coords_meters)
    pairs = tree.query_pairs(radius_meters)

    added = 0
    for i, j in pairs:
        u, v = node_ids[i], node_ids[j]

        # Nếu chưa có đường nối trực tiếp
        if not G.has_edge(u, v):
            # Tính khoảng cách thực tế làm trọng số (weight)
            dist = haversine_distance(nodes[i][1]['y'], nodes[i][1]['x'], nodes[j][1]['y'], nodes[j][1]['x'])

            # Thêm link kết nối 2 chiều (hành khách đi bộ)
            G.add_edge(u, v, length=dist, edge_type="transfer")
            G.add_edge(v, u, length=dist, edge_type="transfer")
            added += 2

    print(f"✅ Đã nối thành công! Bổ sung {added} đoạn ray ảo.")
    return G


def _compute_path_length(G: nx.MultiDiGraph, path, weight_attr='length'):
    """Hàm bổ sung: Tính toán tổng quãng đường thực tế dựa trên thuộc tính length"""
    total_distance = 0.0
    for i in range(len(path) - 1):
        u = path[i]
        v = path[i + 1]
        edge_data = G.get_edge_data(u, v)
        if edge_data:
            min_weight = min([float(data.get(weight_attr, 1.0)) for data in edge_data.values()])
            total_distance += min_weight
    return total_distance


# ── 2. DANH SÁCH THỰC TẾ ĐỘC LẬP CỦA 8 THUẬT TOÁN ─────────────────

# 1. DIJKSTRA
def dijkstra(G: nx.MultiDiGraph, start_nodes, end_nodes, avoid_zones=None):
    end_nodes_set = set(end_nodes)
    distances = {node: float('infinity') for node in G.nodes}
    previous_nodes = {node: None for node in G.nodes}
    pq = []

    for start_node in start_nodes:
        if is_node_in_avoid_zone(G, start_node, avoid_zones):
            continue
        distances[start_node] = 0
        heapq.heappush(pq, (0, start_node))

    best_end_node = None
    while pq:
        current_dist, current_node = heapq.heappop(pq)

        if current_node in end_nodes_set:
            best_end_node = current_node
            break

        if current_dist > distances[current_node]:
            continue

        for neighbor in G.neighbors(current_node):
            if is_node_in_avoid_zone(G, neighbor, avoid_zones) or is_edge_in_avoid_zone(G, current_node, neighbor, avoid_zones):
                continue

            edge_data = G[current_node][neighbor][0]
            weight = float(edge_data.get('length', 1.0))
            dist = current_dist + weight

            if dist < distances[neighbor]:
                distances[neighbor] = dist
                previous_nodes[neighbor] = current_node
                heapq.heappush(pq, (dist, neighbor))

    if best_end_node is None: return None, float('infinity')
    path = []
    curr = best_end_node
    while curr is not None:
        path.insert(0, curr)
        curr = previous_nodes[curr]
    return path, distances[best_end_node]


# 2. A* SEARCH
def a_star_search(G: nx.MultiDiGraph, start_nodes, end_nodes, avoid_zones=None):
    end_nodes_set = set(end_nodes)
    distances = {node: float('infinity') for node in G.nodes}
    previous_nodes = {node: None for node in G.nodes}
    pq = []

    for start_node in start_nodes:
        if is_node_in_avoid_zone(G, start_node, avoid_zones):
            continue
        distances[start_node] = 0
        h = get_heuristic(start_node, end_nodes, G)
        heapq.heappush(pq, (h, 0, start_node))

    best_end_node = None
    while pq:
        f_current, g_current, current_node = heapq.heappop(pq)

        if current_node in end_nodes_set:
            best_end_node = current_node
            break

        if g_current > distances[current_node]:
            continue

        for neighbor in G.neighbors(current_node):
            if is_node_in_avoid_zone(G, neighbor, avoid_zones) or is_edge_in_avoid_zone(G, current_node, neighbor, avoid_zones):
                continue

            edge_data = G[current_node][neighbor][0]
            weight = float(edge_data.get('length', 1.0))
            tentative_g = g_current + weight

            if tentative_g < distances[neighbor]:
                distances[neighbor] = tentative_g
                previous_nodes[neighbor] = current_node
                h = get_heuristic(neighbor, end_nodes, G)
                heapq.heappush(pq, (tentative_g + h, tentative_g, neighbor))

    if best_end_node is None: return None, float('infinity')
    path = []
    curr = best_end_node
    while curr is not None:
        path.insert(0, curr)
        curr = previous_nodes[curr]
    return path, distances[best_end_node]


# 3. UNIFORM COST SEARCH (UCS)
def ucs(G: nx.MultiDiGraph, start_nodes, end_nodes, avoid_zones=None):
    #UCS nguyên bản chính là thuật toán Dijkstra áp dụng tìm kiếm từ tập S đến tập T
    return dijkstra(G, start_nodes, end_nodes, avoid_zones)


# 4. GREEDY BEST-FIRST SEARCH
def greedy_best_first_search(G: nx.MultiDiGraph, start_nodes, end_nodes, avoid_zones=None):
    end_nodes_set = set(end_nodes)
    visited = set()
    previous_nodes = {node: None for node in G.nodes}
    pq = []  # Hàng đợi ưu tiên dựa hoàn toàn vào h(n)

    for start_node in start_nodes:
        if is_node_in_avoid_zone(G, start_node, avoid_zones):
            continue
        h = get_heuristic(start_node, end_nodes, G)
        heapq.heappush(pq, (h, start_node))

    best_end_node = None
    total_cost = 0

    while pq:
        _, current_node = heapq.heappop(pq)

        if current_node in end_nodes_set:
            best_end_node = current_node
            break

        if current_node in visited:
            continue
        visited.add(current_node)

        for neighbor in G.neighbors(current_node):
            if is_node_in_avoid_zone(G, neighbor, avoid_zones) or is_edge_in_avoid_zone(G, current_node, neighbor, avoid_zones):
                continue

            if neighbor not in visited:
                previous_nodes[neighbor] = current_node
                h = get_heuristic(neighbor, end_nodes, G)
                heapq.heappush(pq, (h, neighbor))

    if best_end_node is None: return None, float('infinity')
    
    # Khôi phục đường đi và tính độ dài thực tế
    path = []
    curr = best_end_node
    while curr is not None:
        path.insert(0, curr)
        curr = previous_nodes[curr]
        
    for i in range(len(path) - 1):
        total_cost += float(G[path[i]][path[i+1]][0].get('length', 1.0))
        
    return path, total_cost


# 5. BIDIRECTIONAL A* (A* Hai hướng)
def bidirectional_a_star(G: nx.MultiDiGraph, start_nodes, end_nodes, avoid_zones=None):
    start_set = set(start_nodes)
    end_set = set(end_nodes)
    
    # Khởi tạo dữ liệu cho 2 hướng: Tiến (F) và Lùi (B)
    g_f = {node: float('infinity') for node in G.nodes}
    g_b = {node: float('infinity') for node in G.nodes}
    prev_f = {node: None for node in G.nodes}
    prev_b = {node: None for node in G.nodes}
    
    pq_f, pq_b = [], []

    for s in start_nodes:
        if not is_node_in_avoid_zone(G, s, avoid_zones):
            g_f[s] = 0
            heapq.heappush(pq_f, (get_heuristic(s, end_nodes, G), s))
            
    for t in end_nodes:
        if not is_node_in_avoid_zone(G, t, avoid_zones):
            g_b[t] = 0
            heapq.heappush(pq_b, (get_heuristic(t, start_nodes, G), t))

    mu = float('infinity')
    intersect_node = None

    while pq_f and pq_b:
        # Hướng tiến
        if pq_f:
            f_f, u = heapq.heappop(pq_f)
            if g_f[u] < float('infinity'):
                for v in G.neighbors(u):
                    if is_node_in_avoid_zone(G, v, avoid_zones) or is_edge_in_avoid_zone(G, u, v, avoid_zones): continue
                    w = float(G[u][v][0].get('length', 1.0))
                    if g_f[u] + w < g_f[v]:
                        g_f[v] = g_f[u] + w
                        prev_f[v] = u
                        heapq.heappush(pq_f, (g_f[v] + get_heuristic(v, end_nodes, G), v))
                        if g_f[v] + g_b[v] < mu:
                            mu = g_f[v] + g_b[v]
                            intersect_node = v

        # Hướng lùi (Xét đồ thị ngược)
        if pq_b:
            f_b, v = heapq.heappop(pq_b)
            if g_b[v] < float('infinity'):
                # Tìm các nút u có đường đi đến v (u -> v)
                for u in G.predecessors(v):
                    if is_node_in_avoid_zone(G, u, avoid_zones) or is_edge_in_avoid_zone(G, u, v, avoid_zones): continue
                    w = float(G[u][v][0].get('length', 1.0))
                    if g_b[v] + w < g_b[u]:
                        g_b[u] = g_b[v] + w
                        prev_b[u] = v
                        heapq.heappush(pq_b, (g_b[u] + get_heuristic(u, start_nodes, G), u))
                        if g_f[u] + g_b[u] < mu:
                            mu = g_f[u] + g_b[u]
                            intersect_node = u

        # Điều kiện dừng tối ưu sớm của Bidirectional A*
        if pq_f and pq_b and (pq_f[0][0] + pq_b[0][0] >= mu):
            break

    if intersect_node is None or mu == float('infinity'): 
        return None, float('infinity')

    # Trộn lộ trình xuôi và ngược
    path_f = []
    curr = intersect_node
    while curr is not None:
        path_f.insert(0, curr)
        curr = prev_f[curr]

    path_b = []
    curr = prev_b[intersect_node]
    while curr is not None:
        path_b.append(curr)
        curr = prev_b[curr]

    return path_f + path_b, mu


# 6. BELLMAN-FORD
def bellman_ford(G: nx.MultiDiGraph, start_nodes, end_nodes, avoid_zones=None):
    distances = {node: float('infinity') for node in G.nodes}
    previous_nodes = {node: None for node in G.nodes}

    for start_node in start_nodes:
        if not is_node_in_avoid_zone(G, start_node, avoid_zones):
            distances[start_node] = 0

    # Relax các cạnh |V| - 1 lần
    num_nodes = len(G.nodes)
    for _ in range(num_nodes - 1):
        changed = False
        for u, v, data in G.edges(data=True):
            if is_node_in_avoid_zone(G, u, avoid_zones) or is_node_in_avoid_zone(G, v, avoid_zones): continue
            if is_edge_in_avoid_zone(G, u, v, avoid_zones): continue
            
            weight = float(data.get('length', 1.0))
            if distances[u] + weight < distances[v]:
                distances[v] = distances[u] + weight
                previous_nodes[v] = u
                changed = True
        if not changed:
            break

    # Tìm đích tối ưu nhất
    best_end_node = min(end_nodes, key=lambda n: distances[n], default=None)
    
    if best_end_node is None or distances[best_end_node] == float('infinity'):
        return None, float('infinity')

    path = []
    curr = best_end_node
    while curr is not None:
        path.insert(0, curr)
        curr = previous_nodes[curr]
    return path, distances[best_end_node]


# 7. BREADTH-FIRST SEARCH (BFS)
def bfs(G: nx.MultiDiGraph, start_nodes, end_nodes, avoid_zones=None):
    end_nodes_set = set(end_nodes)
    open_set = deque()
    closed = set()
    previous_nodes = {}

    for start_node in start_nodes:
        if is_node_in_avoid_zone(G, start_node, avoid_zones): continue
        open_set.append(start_node)
        closed.add(start_node)
        previous_nodes[start_node] = None

    best_end_node = None
    while open_set:
        current_node = open_set.popleft()
        if current_node in end_nodes_set:
            best_end_node = current_node
            break

        for neighbor in G.neighbors(current_node):
            if is_node_in_avoid_zone(G, neighbor, avoid_zones) or is_edge_in_avoid_zone(G, current_node, neighbor, avoid_zones):
                continue
                
            if neighbor not in closed:
                closed.add(neighbor)
                previous_nodes[neighbor] = current_node
                open_set.append(neighbor)

    if best_end_node is None: return None, float('infinity')
    path = []
    curr = best_end_node
    while curr is not None:
        path.insert(0, curr)
        curr = previous_nodes.get(curr)
    
    total_distance = _compute_path_length(G, path, weight_attr='length')
    return path, total_distance


# 8. DEPTH-FIRST SEARCH (DFS)
def dfs(G: nx.MultiDiGraph, start_nodes, end_nodes, avoid_zones=None):
    end_nodes_set = set(end_nodes)
    open_set = []
    previous_nodes = {}
    closed = set()

    for start_node in start_nodes:
        if is_node_in_avoid_zone(G, start_node, avoid_zones): continue
        open_set.append(start_node)
        previous_nodes[start_node] = None

    best_end_node = None
    while open_set:
        current_node = open_set.pop()
        if current_node in end_nodes_set:
            best_end_node = current_node
            break

        if current_node not in closed:
            closed.add(current_node)
            for neighbor in G.neighbors(current_node):
                if is_node_in_avoid_zone(G, neighbor, avoid_zones) or is_edge_in_avoid_zone(G, current_node, neighbor, avoid_zones):
                    continue
                    
                if neighbor not in closed:
                    previous_nodes[neighbor] = current_node
                    open_set.append(neighbor)

    if best_end_node is None: return None, float('infinity')
    path = []
    curr = best_end_node
    while curr is not None:
        path.insert(0, curr)
        curr = previous_nodes.get(curr)
        
    total_distance = _compute_path_length(G, path, weight_attr='length')
    return path, total_distance