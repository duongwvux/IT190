import osmnx as ox
import networkx as nx

G = ox.load_graphml("berlin_rail.graphml")

# Kiểm tra số component
components = list(nx.weakly_connected_components(G))
print(f"Số component: {len(components)}")
print(f"Component lớn nhất: {max(len(c) for c in components)} nodes")