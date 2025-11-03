import google.generativeai as genai
from typing import List, Dict
import os

class GeminiRAG:
    def __init__(self, api_key: str = None):
        api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found")
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')
    
    def generate_answer(self, query: str, context: List[str], sources: List[Dict]) -> Dict:
        if not context:
            return {
                "answer": "No relevant information found. Try adding more sources.",
                "sources": [],
                "model": "gemini-1.5-flash"
            }
        
        context_text = ""
        for i, doc in enumerate(context, 1):
            context_text += f"\n[Source {i}]\n{doc}\n"
        
        prompt = f"""Answer based on these sources:
{context_text}

Question: {query}

Instructions:
- Answer based ONLY on the context
- Be concise and direct
- Mention source numbers [Source 1], [Source 2]
- If context doesn't have the answer, say so

Answer:"""
        
        try:
            response = self.model.generate_content(prompt)
            return {
                "answer": response.text,
                "sources": sources,
                "model": "gemini-1.5-flash"
            }
        except Exception as e:
            return {
                "answer": f"Error: {str(e)}",
                "sources": sources,
                "model": "gemini-1.5-flash",
                "error": True
            }
