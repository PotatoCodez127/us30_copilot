import networkx as nx
import json
import os

def query_knowledge_graph(setup_payload: dict) -> str:
    """
    Builds an in-memory Graph from past trades and queries the current setup's historical path.
    """
    memory_file = "results/master_memory_bank.json"
    
    if not os.path.exists(memory_file):
        return "[GraphRAG Context] Graph is empty. No historical edges available yet."
        
    try:
        with open(memory_file, 'r', encoding='utf-8') as f:
            memory_bank = json.load(f)
    except Exception:
        return "[GraphRAG Context] Warning: Failed to parse memory bank JSON."

    # Initialize the Graph
    G = nx.Graph()
    
    # 1. Map the Historical Graph
    for trade in memory_bank:
        # Extract features (adjust these keys if your json uses different names)
        level = trade.get('level', 'Unknown_Level')
        
        # We determine the outcome node based on PnL
        pnl = float(trade.get('pnl_points', 0))
        outcome_node = "WIN_NODE" if pnl > 0 else "LOSS_NODE"
        
        # Create the nodes
        G.add_node(level, type="market_structure")
        G.add_node(outcome_node, type="trade_result")
        
        # Connect the structure to the result. If the edge exists, strengthen its weight.
        if G.has_edge(level, outcome_node):
            G[level][outcome_node]['weight'] += 1
        else:
            G.add_edge(level, outcome_node, weight=1)

    # 2. Traverse the Graph for the LIVE setup
    current_level = setup_payload.get('level', 'Unknown_Level')
    
    if current_level in G:
        edges = G[current_level]
        wins = edges.get("WIN_NODE", {}).get("weight", 0)
        losses = edges.get("LOSS_NODE", {}).get("weight", 0)
        total = wins + losses
        winrate = (wins / total) * 100 if total > 0 else 0
        
        return f"[GraphRAG Context] Path traversal for '{current_level}' -> Connected to {wins} WIN nodes and {losses} LOSS nodes. Historical Win Rate for this structure: {winrate:.1f}%."
    else:
        return f"[GraphRAG Context] Node '{current_level}' has no historical edges. This is uncharted territory."