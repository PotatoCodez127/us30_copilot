import json
import os
import chromadb

class Color:
    GREEN, CYAN, YELLOW, RED, MAGENTA, WHITE, RESET = '\033[92m', '\033[96m', '\033[93m', '\033[91m', '\033[95m', '\033[97m', '\033[0m'

def build_vector_db():
    print(f"{Color.CYAN}🚀 Initializing Local RAG Knowledge Base...{Color.RESET}")
    
    memory_file = os.path.join('results', 'master_memory_bank.json')
    if not os.path.exists(memory_file):
        print(f"{Color.RED}No memory bank found at {memory_file}. Run batch_runner.py first!{Color.RESET}")
        return

    with open(memory_file, 'r', encoding='utf-8') as f:
        tapes = json.load(f)

    db_path = os.path.join(os.getcwd(), "data", "rag_db")
    client = chromadb.PersistentClient(path=db_path)
    
    collection = client.get_or_create_collection(name="us30_setups")
    
    documents = []
    metadatas = []
    ids = []
    
    added_count = 0
    
    for tape in tapes:
        if len(collection.get(ids=[tape['id']])['ids']) == 0:
            documents.append(tape['tape'])
            metadatas.append({"classification": tape['classification'], "pnl": tape['pnl']})
            ids.append(tape['id'])
            added_count += 1

    if added_count > 0:
        collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
        print(f"{Color.GREEN}✅ Successfully vectorized and stored {added_count} new historical setups.{Color.RESET}")
    else:
        print(f"{Color.YELLOW}⚠️ DB is already up to date. No new setups found.{Color.RESET}")
        
    print(f"Total Setups in Knowledge Base: {collection.count()}")

if __name__ == "__main__":
    build_vector_db()