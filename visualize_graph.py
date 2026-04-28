import networkx as nx
import matplotlib.pyplot as plt
import json
import os

def draw_memory_bank():
    memory_file = "results/master_memory_bank.json"
    
    if not os.path.exists(memory_file):
        print("❌ No memory bank found. Run a backtest first!")
        return
        
    with open(memory_file, 'r', encoding='utf-8') as f:
        memory_bank = json.load(f)

    print(f"📊 Loaded {len(memory_bank)} trades from Memory Bank. Building Graph...")
    
    G = nx.Graph()
    
    # 1. Build the graph from your historical trades
    for trade in memory_bank:
        # If your JSON uses different keys, change them here
        level = trade.get('level', 'Unknown_Level')
        pnl = float(trade.get('pnl_points', 0))
        
        outcome = "WIN" if pnl > 0 else "LOSS"
        
        # Add nodes with specific colors for the plot
        G.add_node(level, color='lightblue')
        G.add_node(outcome, color='lightgreen' if outcome == 'WIN' else 'salmon')
        
        # Draw edges and increase thickness for frequent occurrences
        if G.has_edge(level, outcome):
            G[level][outcome]['weight'] += 1
        else:
            G.add_edge(level, outcome, weight=1)

    # 2. Render the Graph using Matplotlib
    plt.figure(figsize=(12, 8))
    
    # Use a force-directed layout so winning setups pull towards the WIN node
    pos = nx.spring_layout(G, k=0.5, iterations=50) 
    
    # Extract colors and weights for rendering
    colors = [nx.get_node_attributes(G, 'color').get(node, 'gray') for node in G.nodes()]
    weights = [G[u][v]['weight'] * 1.5 for u, v in G.edges()] # Scale thickness
    
    nx.draw(
        G, pos, 
        with_labels=True, 
        node_color=colors, 
        node_size=3500, 
        font_size=9, 
        font_weight='bold', 
        width=weights, 
        edge_color='gray',
        alpha=0.9
    )
    
    plt.title("US30 GraphRAG Memory Topology", fontsize=16)
    plt.show()

if __name__ == "__main__":
    draw_memory_bank()