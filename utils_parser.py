import json

def extract_tool_calls(text: str) -> list:
    """
    Scans the text and extracts any JSON objects that represent tool calls.
    Can handle nested JSON.
    Returns a list of dicts: [{"tool": "...", "args": {...}}]
    """
    tool_calls = []
    decoder = json.JSONDecoder()
    
    pos = 0
    while True:
        pos = text.find('{', pos)
        if pos == -1:
            break
            
        try:
            obj, index = decoder.raw_decode(text[pos:])
            if isinstance(obj, dict) and "tool" in obj:
                tool_calls.append(obj)
            pos += index
        except json.JSONDecodeError:
            pos += 1
            
    return tool_calls
