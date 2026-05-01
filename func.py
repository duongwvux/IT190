import osmnx as ox
import networkx as nx
import heapq
import math

def get_node_id_from_station(G, station_name):
    query = f"{station_name}, Berlin, Germany"
    try: 
        lat, lng = ox.geocode(query)
        nearest_node_id = ox.distance.nearest_nodes(G, X= lng, Y= lat)
        return nearest_node_id
    except Exception as e:
        print(f"❌ Không tìm thấy tọa độ cho ga: {station_name}")
        return None
    
def haversine_distance(lat1, lon1, lat2, lon2):
    """Tính khoảng cách (mét) giữa 2 tọa độ GPS"""
    R = 6371000  # Bán kính Trái Đất (mét)
    
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    
    a = math.sin(delta_phi / 2.0)**2 + \
        math.cos(phi1) * math.cos(phi2) * \
        math.sin(delta_lambda / 2.0)**2
        
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c
    
def get_all_candidate_nodes(G, station_name, radius_meters=150):
    """
    Trả về DANH SÁCH tất cả các Node ID nằm trong bán kính của nhà ga.
    """
    query = f"{station_name}, Berlin, Germany"
    
    try:
        lat_center, lng_center = ox.geocode(query)
        lat_center, lng_center = float(lat_center), float(lng_center)
        
        candidates = []
        
        # Quét và gom tất cả các Node hợp lệ
        for node_id, data in G.nodes(data=True):
            node_lat = data['y']
            node_lng = data['x']
            
            dist = haversine_distance(lat_center, lng_center, node_lat, node_lng)
            
            if dist <= radius_meters:
                candidates.append(node_id)
                
        # Nếu không có Node nào trong bán kính, dùng hàm nearest_nodes làm phương án dự phòng
        if not candidates:
            fallback_node = int(ox.distance.nearest_nodes(G, X=[lng_center], Y=[lat_center])[0])
            return [fallback_node]
            
        return candidates
        
    except Exception as e:
        print(f"❌ Không thể định vị ga '{station_name}': {e}")
        return []

def dijkstra(G: nx.MultiDiGraph, start_nodes, end_nodes):
    end_nodes_set = set(end_nodes)
    
    distances = {node: float('infinity') for node in G.nodes}
    previous_nodes = {node: None for node in G.nodes}
    
    pq = []
    
    # 1. Ném TẤT CẢ các điểm xuất phát vào hàng đợi với khoảng cách 0
    for start_node in start_nodes:
        distances[start_node] = 0
        heapq.heappush(pq, (0, start_node))
        
    best_end_node = None
    
    while pq:
        current_dist, current_node = heapq.heappop(pq)
        
        # 2. Nếu điểm đang xét nằm trong danh sách ĐÍCH -> DỪNG NGAY!
        # Nhờ hàng đợi ưu tiên, điểm đích đầu tiên chạm tới chính là khoảng cách ngắn nhất.
        if current_node in end_nodes_set:
            best_end_node = current_node
            break
            
        if current_dist > distances[current_node]:
            continue
            
        for neighbor in G.neighbors(current_node):
            edge_data = G[current_node][neighbor][0]
            
            # SỬA LỖI 2: Thêm giá trị mặc định 1.0 mét nếu không có length
            weight = float(edge_data.get('length', 1.0))
            dist = current_dist + weight

            if dist < distances[neighbor]:
                distances[neighbor] = dist
                previous_nodes[neighbor] = current_node 
                heapq.heappush(pq, (dist, neighbor))
                
    # 3. Rút trích đường đi từ best_end_node (Điểm đích tốt nhất vừa tìm được)
    if best_end_node is None:
        return None, float('infinity') # Không tìm thấy đường nào
        
    path = []
    current = best_end_node
    
    while current is not None:
        path.insert(0, current)
        current = previous_nodes[current]
        
    return path, distances[best_end_node]
  
# PL

def get_heuristic(node, target_nodes, G):
    """
    Tính h(n) cho A* và Bi A*
    """
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

def a_star_search(G: nx.MultiDiGraph, start_nodes, end_nodes):
    end_nodes_set = set(end_nodes)
    
    distances = {node: float('infinity') for node in G.nodes}
    previous_nodes = {node: None for node in G.nodes}
    
    pq = []
    
    for start_node in start_nodes:
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
            edge_data = G[current_node][neighbor][0]
            weight = float(edge_data.get('length', 1.0))
            
            tentative_g = g_current + weight

            if tentative_g < distances[neighbor]:
                distances[neighbor] = tentative_g
                previous_nodes[neighbor] = current_node
                
                h = get_heuristic(neighbor, end_nodes, G)
                f_score = tentative_g + h
                heapq.heappush(pq, (f_score, tentative_g, neighbor))
                
    if best_end_node is None:
        return None, float('infinity')
        
    path = []
    current = best_end_node
    
    while current is not None:
        path.insert(0, current)
        current = previous_nodes[current]
        
    return path, distances[best_end_node]

def bidirectional_a_star(G: nx.MultiDiGraph, start_nodes, end_nodes):
    g_forward = {node: float('infinity') for node in G.nodes}
    g_backward = {node: float('infinity') for node in G.nodes}
    
    parent_forward = {node: None for node in G.nodes}
    parent_backward = {node: None for node in G.nodes}
    
    pq_forward = []
    pq_backward = []
    
    for start_node in start_nodes:
        g_forward[start_node] = 0
        h = get_heuristic(start_node, end_nodes, G)
        heapq.heappush(pq_forward, (h, 0, start_node))
        
    for end_node in end_nodes:
        g_backward[end_node] = 0
        h = get_heuristic(end_node, start_nodes, G)
        heapq.heappush(pq_backward, (h, 0, end_node))
        
    best_meeting_node = None
    best_total_dist = float('infinity')
    
    while pq_forward and pq_backward:
        if pq_forward[0][0] + pq_backward[0][0] >= best_total_dist:
            break
            
        # Đi tiến
        f_f, current_g_f, u = heapq.heappop(pq_forward)
        if current_g_f <= g_forward[u]:
            for neighbor in G.neighbors(u):
                weight = float(G[u][neighbor][0].get('length', 1.0))
                dist = current_g_f + weight
                
                if dist < g_forward[neighbor]:
                    g_forward[neighbor] = dist
                    parent_forward[neighbor] = u
                    h = get_heuristic(neighbor, end_nodes, G)
                    heapq.heappush(pq_forward, (dist + h, dist, neighbor))
                    
                    if g_forward[neighbor] + g_backward[neighbor] < best_total_dist:
                        best_meeting_node = neighbor
                        best_total_dist = g_forward[neighbor] + g_backward[neighbor]

        # Đi lùi
        f_b, current_g_b, v = heapq.heappop(pq_backward)
        if current_g_b <= g_backward[v]:
            for pred in G.predecessors(v):
                weight = float(G[pred][v][0].get('length', 1.0))
                dist = current_g_b + weight
                
                if dist < g_backward[pred]:
                    g_backward[pred] = dist
                    parent_backward[pred] = v
                    h = get_heuristic(pred, start_nodes, G)
                    heapq.heappush(pq_backward, (dist + h, dist, pred))
                    
                    if g_forward[pred] + g_backward[pred] < best_total_dist:
                        best_meeting_node = pred
                        best_total_dist = g_forward[pred] + g_backward[pred]
                        
    if best_meeting_node is None:
        return None, float('infinity')
        
    path = []
    curr = best_meeting_node
    while curr is not None:
        path.insert(0, curr)
        curr = parent_forward[curr]
        
    curr = parent_backward[best_meeting_node]
    while curr is not None:
        path.append(curr)
        curr = parent_backward[curr]
        
    return path, best_total_dist
  
# Hiển
  
from collections import deque
import heapq
import networkx as nx

def dfs(G: nx.MultiDiGraph, start_nodes, end_nodes):
    end_nodes_set = set(end_nodes)
    
    open_set = list(start_nodes) # Sử dụng List như một Stack (LIFO)
    closed = set()
    previous_nodes = {node: None for node in start_nodes}
    
    best_end_node = None

    while open_set:
        # Lấy phần tử ở ĐỈNH stack (phần tử được thêm vào gần nhất)
        current_node = open_set.pop()
        
        # 1. Nếu điểm đang xét nằm trong danh sách ĐÍCH -> DỪNG NGAY!
        if current_node in end_nodes_set:
            best_end_node = current_node
            break
            
        if current_node not in closed:
            closed.add(current_node) # Đánh dấu đã duyệt
            # Duyệt qua các hàng xóm
            for neighbor in G.neighbors(current_node):
                if neighbor not in closed:
                    previous_nodes[neighbor] = current_node
                    open_set.append(neighbor) # Đẩy vào Stack
                    
    # 2. Rút trích đường đi từ best_end_node về điểm xuất phát
    if best_end_node is None:
        return None, float('infinity') # Không tìm thấy đường nào
        
    path = []
    current = best_end_node
    
    while current is not None:
        path.insert(0, current) # Chèn vào đầu mảng để ra đúng thứ tự
        current = previous_nodes.get(current)
        
    return path, len(path) - 1

def bfs(G: nx.MultiDiGraph, start_nodes, end_nodes):
    end_nodes_set = set(end_nodes)
    
    open_set = deque(start_nodes) # Sử dụng Deque như một Queue (FIFO)
    closed = set(start_nodes)     # BFS đánh dấu closed ngay khi cho vào queue để tránh lặp
    previous_nodes = {node: None for node in start_nodes}
    
    best_end_node = None

    while open_set:
        # Lấy phần tử ở ĐẦU hàng đợi (phần tử vào sớm nhất)
        current_node = open_set.popleft()
        
        # 1. Nếu điểm đang xét nằm trong danh sách ĐÍCH -> DỪNG NGAY!
        if current_node in end_nodes_set:
            best_end_node = current_node
            break
            
        for neighbor in G.neighbors(current_node):
            if neighbor not in closed:
                closed.add(neighbor) # Đánh dấu duyệt ngay khi nhìn thấy
                previous_nodes[neighbor] = current_node
                open_set.append(neighbor) # Đẩy vào cuối Queue
                
    # 2. Rút trích đường đi từ best_end_node
    if best_end_node is None:
        return None, float('infinity') # Không tìm thấy đường nào
        
    path = []
    current = best_end_node
    
    while current is not None:
        path.insert(0, current)
        current = previous_nodes.get(current)
        
    return path, len(path) - 1

def ucs(G: nx.MultiDiGraph, start_nodes, end_nodes):
    end_nodes_set = set(end_nodes)
    
    distances = {node: float('infinity') for node in G.nodes}
    previous_nodes = {node: None for node in G.nodes}
    
    pq = [] # Priority Queue dùng heapq
    
    # 1. Ném TẤT CẢ các điểm xuất phát vào hàng đợi ưu tiên với chi phí 0
    for start_node in start_nodes:
        distances[start_node] = 0
        heapq.heappush(pq, (0, start_node))
        
    best_end_node = None

    while pq:
        # Lấy node có chi phí CỘNG DỒN nhỏ nhất hiện tại ra khỏi Priority Queue
        current_dist, current_node = heapq.heappop(pq)
        
        # 2. ĐIỀU KIỆN DỪNG: Với UCS, phải chờ khi node được POP RA khỏi hàng đợi ưu tiên 
        # mới được check đích, vì lúc này mới đảm bảo đó là đường ngắn nhất.
        if current_node in end_nodes_set:
            best_end_node = current_node
            break
            
        # Bỏ qua nếu ta đã tìm thấy một đường ngắn hơn đến node này trước đó (tối ưu hóa Priority Queue)
        if current_dist > distances[current_node]:
            continue
            
        for neighbor in G.neighbors(current_node):
            # FIXED: Do đồ thị là MultiDiGraph, giữa 2 node có thể có NGUYÊN MỘT TẬP CÁC CẠNH.
            # Ta cần duyệt qua các cạnh này và lấy cạnh có độ dài ngắn nhất.
            min_weight = float('infinity')
            for edge_key, edge_data in G[current_node][neighbor].items():
                w = float(edge_data.get('length', 1.0))
                if w < min_weight:
                    min_weight = w
                    
            dist = current_dist + min_weight
            
            # Nếu tìm được đường đi tới neighbor ngắn hơn đường cũ
            if dist < distances[neighbor]:
                distances[neighbor] = dist
                previous_nodes[neighbor] = current_node
                # Đẩy cập nhật mới vào hàng đợi ưu tiên
                heapq.heappush(pq, (dist, neighbor))
                
    # 3. Rút trích đường đi từ best_end_node
    if best_end_node is None:
        return None, float('infinity') # Không tìm thấy đường nào
        
    path = []
    current = best_end_node
    
    while current is not None:
        path.insert(0, current)
        current = previous_nodes[current] # Traceback lại đường đi
        
    return path, distances[best_end_node]

# T.T
def heuristic(G, node, goal_node):
    lat1 = G.nodes[node]['y']
    lon1 = G.nodes[node]['x']
    lat2 = G.nodes[goal_node]['y']
    lon2 = G.nodes[goal_node]['x']
    return haversine_distance(lat1, lon1, lat2, lon2)

def greedy_best_first_search(G: nx.MultiDiGraph, start_nodes, end_nodes):
    end_nodes_set = set(end_nodes)
    visited = set()
    previous_node = {}
    pq = []
    for start_node in start_nodes:
        h = min(heuristic(G, start_node, goal_node) for goal_node in end_nodes_set)
        heapq.heappush(pq,(h, start_node))
        previous_node[start_node] = None
    best_end_node = None

    while pq:
        current_h, current_node = heapq.heappop(pq)
        if current_node in end_nodes_set:
            best_end_node = current_node
            break
        if current_node in visited:
            continue
        visited.add(current_node)
        for neighbor in G.neighbors(current_node):
            if neighbor not in visited:
                h = min(heuristic(G, neighbor, goal_node) for goal_node in end_nodes_set)
                heapq.heappush(pq, (h, neighbor))

                if neighbor not in previous_node:
                    previous_node[neighbor] = current_node
    if best_end_node is None:
        return None, float('infinity')
    path = []
    current = best_end_node

    while current is not None:
        path.insert(0, current)
        current = previous_node[current]
    total_length = 0
    for i in range(len(path) - 1):
        edge_data = G[path[i]][path[i + 1]]
        min_length = min(float(data.get('length', 1.0)) for data in edge_data.values())
        total_length += min_length

    return path, total_length

def bellman_ford(G:nx.MultiDiGraph, start_nodes, end_nodes):
    end_node_set = set(end_nodes)
    distances = {node: float('infinity') for node in G.nodes}
    previous_nodes = {node: None for node in G.nodes}

    for start_node in start_nodes:
        distances[start_node] = 0
    V = list(G.nodes)
    for _ in range(len(V) - 1):
        updated = False
        for u in G.nodes:
            if distances[u] == float('infinity'):
                continue
            for v in G.neighbors(u):
                for edge_key in G[u][v]:
                    edge_data = G[u][v][edge_key]
                    weight = float(edge_data.get('length', 1.0))
                    if distances[u] + weight < distances[v]:
                        distances[v] = distances[u] + weight
                        previous_nodes[v] = u
                        updated = True
        if not updated:
            break
    for u in G.nodes:
        if distances[u] == float('infinity'):
            continue
        for v in G.neighbors(u):
            for edge_key in G[u][v]:
                edge_data = G[u][v][edge_key]
                weight = float(edge_data.get('length', 1.0))
                if distances[u] + weight < distances[v]:
                    print("Đồ thị chứa chu trình âm")
                    return None, float('infinity')
    best_end_node = None
    best_distance = float('infinity')
    for end_node in end_nodes:
        if distances[end_node] < best_distance:
            best_distance = distances[end_node]
            best_end_node = end_node
    if best_end_node is None or best_distance == float('infinity'):
        return None, float('infinity')
    path = []
    current = best_end_node
    while current is not None:
        path.insert(0, current)
        current = previous_nodes[current]
    return path, best_distance