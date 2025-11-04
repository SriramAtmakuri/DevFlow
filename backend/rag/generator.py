import google.generativeai as genai
import os
from typing import List, Dict

class GeminiRAG:
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found")
        
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-flash-latest')  # ✅ CHANGED
    
    def generate_answer(self, query: str, context: List[str], sources: List[Dict]) -> Dict:
        if not context:
            return {
                "answer": "No relevant documents found.",
                "sources": [],
                "model": "gemini-flash-latest"  # ✅ CHANGED
            }
        
        context_text = "\n\n".join([f"Doc {i+1}: {doc}" for i, doc in enumerate(context[:5])])
        
        prompt = f"""Answer based on these documents:

{context_text}

Question: {query}

Answer:"""
        
        try:
            response = self.model.generate_content(prompt)
            answer = response.text
        except Exception as e:
            answer = f"Error: {str(e)}"
        
        return {
            "answer": answer,
            "sources": sources[:5],
            "model": "gemini-flash-latest"  # ✅ CHANGED
        }