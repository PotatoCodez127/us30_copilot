import networkx as nx
import matplotlib.pyplot as plt
import json
import os

def draw_research_graph():
    memory_file = "results/research_memory.json"
    
    if not os.path.exists(memory_file):
        print("❌ No research memory found. Let autoresearch.py run a few times first!")
        return
        
    with open(memory_file, 'r', encoding='utf-8') as f:
        runs = json.load(f)

    print(f"📊 Loaded {len(runs)} configurations from Research Memory. Building Map...")
    
    G = nx.Graph()
    
    # Outcome nodes (Gravity Wells)
    G.add_node("WINNING_SCORE", color='lightgreen')
    G.add_node("LOSING_SCORE", color='salmon')
    
    for run in runs:
        score = run.get('score', 0)
        outcome = "WINNING_SCORE" if score > 0 else "LOSING_SCORE"
        
        sl = run.get('sl', 0)
        tp = run.get('tp', 0)
        buf = run.get('buffer', 0)
        
        # Create categorical buckets just like in autoresearch.py
        sl_node = f"SL: {int(sl//50)*50}-{int(sl//50)*50+50}"
        tp_node = f"TP: {int(tp//50)*50}-{int(tp//50)*50+50}"
        buf_node = f"Buf: {int(buf//5)*5}-{int(buf//5)*5+5}"
        
        # Connect parameters to their outcomes
        for node in [sl_node, tp_node, buf_node]:
            G.add_node(node, color='lightblue')
            if G.has_edge(node, outcome):
                G[node][outcome]['weight'] += 1
            else:
                G.add_edge(node, outcome, weight=1)

    # Render the Graph
    plt.figure(figsize=(14, 9))
    
    # The physics engine: pushes unrelated nodes apart, pulls connected nodes together
    pos = nx.spring_layout(G, k=0.9, iterations=100) 
    
    colors = [nx.get_node_attributes(G, 'color').get(node, 'gray') for node in G.nodes()]
    weights = [G[u][v]['weight'] * 2.5 for u, v in G.edges()] # Scale edge thickness by frequency
    
    nx.draw(
        G, pos, 
        with_labels=True, 
        node_color=colors, 
        node_size=4000, 
        font_size=10, 
        font_weight='bold', 
        width=weights, 
        edge_color='gray',
        alpha=0.9
    )
    
    plt.title("Autoresearch Parameter Topology (GraphRAG Map)", fontsize=18)
    plt.show()

if __name__ == "__main__":
    draw_research_graph()