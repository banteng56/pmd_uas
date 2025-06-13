import json
import re
import string
from typing import Optional, Set
from pathlib import Path

class TextCleaner:
    def __init__(self, stopwords_path: str = './indonesian_stopwords.json'):
        self.stopwords = self._load_stopwords(stopwords_path)
        self.patterns = self._compile_patterns()
    
    def _load_stopwords(self, path: str) -> Set[str]:
        try:
            stopwords_file = Path(path)
            with open(stopwords_file, 'r', encoding='utf-8') as f:
                return set(json.load(f))
        except (FileNotFoundError, json.JSONDecodeError):
            return set()
    
    def _compile_patterns(self):
        return [
            (r'&\w+;', ''),
            (r'^\s*[\w]+\.\s*[\w]+\s*,\s*[\w]+\s*(?:-|–|&nbsp;|\||\s)*\s*', ''),
            (r'\b[\w\s]+\bberkontribusi\b[\w\s]*', ''),
            (r'simak\s*(?:juga\s*)?video\s*[:\-]?\s*.*?(?:$|(?=\s+[A-Z]))', ''),
            (r'saksikan\s*(?:live|langsung)\s*[:\-]?\s*.*?(?:$|(?=\s+[A-Z]))', ''),
            (r'pilihan editor\s*:.*$', ''),
            (r'(?:simak\s*(?:juga\s*)?video|saksikan\s*(?:live|langsung)|tonton\s*(?:video|tayangan)|lihat\s*(?:juga\s*)?video|baca\s*(?:berita\s*)?selengkapnya)\s*[:\-]?\s*.*?(?:$|(?=\s+[A-Z]|\.))', ''),
            (r'simak (?:juga |)(?:video|berita).*?(?:\.|$)', ''),
            (r'saksikan (?:live|langsung).*?(?:\.|$)', ''),
            (r'baca (?:juga|selengkapnya).*?(?:\.|$)', ''),
            (r'tonton (?:video|tayangan).*?(?:\.|$)', ''),
            (r'lihat (?:selengkapnya|juga|lebih detail).*?(?:\.|$)', ''),
            (r'http[s]?://\S+', ''),
            (r'@\w+|#\w+', ''),
            (r'©\s*\d{4}\s*[\w\s]+\.?\s*all rights? reserved\.?', ''),
            (r'[^\w\s.,!?-]', ' '),
            (r'([.,!?-])\1+', r'\1')
        ]
    
    def clean(self, text: Optional[str]) -> str:
        if not text:
            return ""
        
        text = text.lower()
        
        for pattern, replacement in self.patterns:
            text = re.sub(pattern, replacement, text)
        
        text = re.sub(f"[{re.escape(string.punctuation)}]", "", text)
        tokens = [
            token for token in text.strip().split() 
            if token not in self.stopwords and len(token) > 1
        ]
        
        return " ".join(tokens)
