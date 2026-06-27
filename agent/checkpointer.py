from langgraph.checkpoint.memory import MemorySaver
from dotenv import load_dotenv

load_dotenv()  

def get_checkpointer(use_persistence: bool = True):
    if not use_persistence:
        return MemorySaver()