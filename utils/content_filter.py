import re
import spacy
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from typing import List, Dict, Union
import logging
from config.config import ContentFilterConfig

# Download required NLTK data
nltk.download('punkt')
nltk.download('stopwords')
nltk.download('averaged_perceptron_tagger')

# Initialize spaCy
nlp = spacy.load('en_core_web_sm')

class ContentFilter:
    def __init__(self):
        self.config = ContentFilterConfig()
        self.stop_words = set(stopwords.words('english'))
        self.profanity_patterns = self._load_profanity_patterns()
        self.sensitive_patterns = self._load_sensitive_patterns()
        self.logger = logging.getLogger(__name__)

    def _load_profanity_patterns(self) -> Dict[str, re.Pattern]:
        """Load and compile regex patterns for profanity detection"""
        patterns = {}
        for category, words in self.config.PROFANITY_WORDS.items():
            pattern = r'\b(' + '|'.join(map(re.escape, words)) + r')\b'
            patterns[category] = re.compile(pattern, re.IGNORECASE)
        return patterns

    def _load_sensitive_patterns(self) -> Dict[str, re.Pattern]:
        """Load and compile regex patterns for sensitive content detection"""
        patterns = {}
        for category, phrases in self.config.SENSITIVE_PHRASES.items():
            pattern = r'\b(' + '|'.join(map(re.escape, phrases)) + r')\b'
            patterns[category] = re.compile(pattern, re.IGNORECASE)
        return patterns

    def filter_content(self, text: str) -> Dict[str, Union[bool, List[str]]]:
        """
        Filter content for inappropriate or sensitive material
        Returns dict with filtering results and reasons
        """
        result = {
            'is_safe': True,
            'reasons': []
        }

        # Check for profanity
        for category, pattern in self.profanity_patterns.items():
            if pattern.search(text):
                result['is_safe'] = False
                result['reasons'].append(f'Contains {category} profanity')

        # Check for sensitive content
        for category, pattern in self.sensitive_patterns.items():
            if pattern.search(text):
                result['is_safe'] = False 
                result['reasons'].append(f'Contains sensitive {category} content')

        # NLP-based checks
        doc = nlp(text)
        
        # Check for personal attacks
        if self._contains_personal_attack(doc):
            result['is_safe'] = False
            result['reasons'].append('Contains personal attack')

        # Check for hate speech indicators
        if self._contains_hate_speech(doc):
            result['is_safe'] = False
            result['reasons'].append('Contains hate speech indicators')

        return result

    def _contains_personal_attack(self, doc) -> bool:
        """Check if text contains patterns indicating personal attacks"""
        # Look for combinations of personal pronouns and negative adjectives
        personal_pronouns = {'you', 'your', 'you\'re', 'yours'}
        
        for token in doc:
            if (token.text.lower() in personal_pronouns and 
                any(child.pos_ == 'ADJ' and child.text.lower() in self.config.NEGATIVE_ADJECTIVES 
                    for child in token.children)):
                return True
        return False

    def _contains_hate_speech(self, doc) -> bool:
        """Check if text contains patterns indicating hate speech"""
        # Look for demographic terms combined with negative verbs/adjectives
        for ent in doc.ents:
            if (ent.label_ in {'NORP', 'ORG'} and 
                any(token.pos_ in {'ADJ', 'VERB'} and 
                    token.text.lower() in self.config.NEGATIVE_TERMS 
                    for token in doc)):
                return True
        return False

    def filter_suggestions(self, suggestions: List[str]) -> List[str]:
        """Filter a list of autocomplete suggestions"""
        filtered_suggestions = []
        for suggestion in suggestions:
            filter_result = self.filter_content(suggestion)
            if filter_result['is_safe']:
                filtered_suggestions.append(suggestion)
            else:
                self.logger.warning(f"Filtered out suggestion: {suggestion}, "
                                  f"reasons: {filter_result['reasons']}")
        return filtered_suggestions

    def sanitize_input(self, text: str) -> str:
        """Sanitize input text by removing potentially harmful characters"""
        # Remove special characters and excessive whitespace
        sanitized = re.sub(r'[^\w\s-]', '', text)
        sanitized = ' '.join(sanitized.split())
        return sanitized.strip()
