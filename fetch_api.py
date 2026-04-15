import osmnx as ox

ox.settings.log_console =  True
ox.settings.use_cache = True

def load_berlin_rail_network():
    place_name = "Berlin, Germany"
    
    rail_filter = '["railway"~"subway|tram|rail|light_rail"]'
    
    G = ox.graph_from_place(place_name, custom_filter= rail_filter, simplify= False)
    
    filepath = "berlin_rail.graphml"
    
    ox.save_graphml(G, filepath)
    
if __name__ == "__main__":
    load_berlin_rail_network();