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
                causes = ", ".join(item.get("known_causes", []))
                syms = ", ".join(item.get("symptoms", []))
                steps = "\n- ".join(item.get("solution", []))
                
                art_str = (
                    f"Article ID: {item.get('id', 'N/A')}\n"
                    f"Category: {item.get('category', 'N/A')}\n"
                    f"Issue: {item.get('issue', 'N/A')}\n"
                    f"Symptoms: {syms}\n"
                    f"Known Causes: {causes}\n"
                    f"Solution Steps:\n- {steps}\n"
                    f"Historical Success: {item.get('historical_success_count', 0)} incidents\n"
                    f"Success Rate: {item.get('success_rate_pct', 0)}%\n"
                    f"Average Confidence: {item.get('avg_confidence_pct', 0)}%"
                )
                results.append(art_str)
        
        if results:
            res_str = "\n\n=== MATCHED KB ARTICLES ===\n\n" + "\n\n-------------------------\n\n".join(results)
        else:
            res_str = "No matching solutions found in the knowledge base."
            
        self._cache[query_clean] = res_str
        return res_str
