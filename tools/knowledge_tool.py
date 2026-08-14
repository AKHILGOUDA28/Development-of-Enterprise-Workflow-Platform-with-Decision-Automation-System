import json
import os
from pydantic import BaseModel
from tools.base_tool import BaseTool

class KnowledgeToolSchema(BaseModel):
    query: str

class KnowledgeTool(BaseTool):
    name = "knowledge_base"
    description = "Searches the local knowledge base for troubleshooting steps related to an IT issue."
    args_schema = KnowledgeToolSchema

    _cache = {}

    def _execute(self, query: str) -> str:
        query_clean = query.strip().lower()
        if query_clean in self._cache:
            return self._cache[query_clean]

        kb_path = os.path.join(os.path.dirname(__file__), "..", "database", "knowledge_base.json")
        try:
            with open(kb_path, "r") as f:
                kb = json.load(f)
        except Exception:
            return "Error: knowledge_base.json not found or invalid."
        
        query_lower = query.lower()
        results = []
        for item in kb:
            if query_lower in item["issue"].lower() or any(query_lower in sol.lower() for sol in item["solution"]):
                results.append(f"Issue: {item['issue']}\nSolution:\n- " + "\n- ".join(item['solution']))
        
        if results:
            res_str = "\n\n".join(results)
        else:
            res_str = "No matching solutions found in the knowledge base."
            
        self._cache[query_clean] = res_str
        return res_str
