#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ai_detector.py
~~~~~~~~~~~~~~
Lightweight wrapper around the open-source model
`roberta-base-openai-detector` to estimate the probability that a text
snippet was machine-generated.

Adapted for the thesis helper system.
"""

from __future__ import annotations

import logging
from typing import Optional, Tuple
import os

try:
    import torch
    from transformers import AutoModelForSequenceClassification, AutoTokenizer
    DEPENDENCIES_AVAILABLE = True
except ImportError:
    DEPENDENCIES_AVAILABLE = False
    torch = None
    AutoModelForSequenceClassification = None
    AutoTokenizer = None

logger = logging.getLogger(__name__)

class AIDetector:
    """AI content detection service for thesis helper system."""
    
    def __init__(self):
        self.model = None
        self.tokenizer = None
        self.model_name = "roberta-base-openai-detector"
        self._initialized = False
        
        if DEPENDENCIES_AVAILABLE:
            self._initialize_model()
    
    def _initialize_model(self):
        """Initialize the AI detection model."""
        try:
            logger.info(f"Loading AI detection model: {self.model_name}")
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModelForSequenceClassification.from_pretrained(self.model_name)
            self._initialized = True
            logger.info("AI detection model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load AI detection model: {e}")
            self._initialized = False
    
    def detect_ai_content(self, text: str) -> Tuple[float, str]:
        """
        Return the probability (0–1) that *text* was generated by an LLM.
        
        Args:
            text: The text to analyze
            
        Returns:
            Tuple of (probability, explanation)
        """
        if not DEPENDENCIES_AVAILABLE:
            return 0.0, "AI detection dependencies not available"
            
        if not self._initialized:
            return 0.0, "AI detection model not initialized"
            
        if not text or not text.strip():
            return 0.0, "Empty text provided"
        
        try:
            inputs = self.tokenizer(
                text, 
                return_tensors="pt",
                truncation=True, 
                max_length=512
            )
            
            with torch.no_grad():
                logits = self.model(**inputs).logits
                probability = torch.softmax(logits, dim=1)[0, 1].item()
            
            # Generate explanation based on probability
            if probability > 0.8:
                explanation = "Very likely AI-generated content"
            elif probability > 0.6:
                explanation = "Likely AI-generated content"
            elif probability > 0.4:
                explanation = "Possibly AI-generated content"
            else:
                explanation = "Likely human-written content"
                
            return probability, explanation
            
        except Exception as e:
            logger.error(f"Error during AI detection: {e}")
            return 0.0, f"Error during analysis: {str(e)}"

# Global instance
_detector = AIDetector()

def detect_ai_content(text: str, ai_service=None) -> Tuple[float, str]:
    """
    Detect if text is AI-generated.
    
    Args:
        text: The text to analyze
        ai_service: Optional AI service for analysis when ML models unavailable
        
    Returns:
        Tuple of (probability, explanation)
    """
    # Try ML-based detection first if available
    if DEPENDENCIES_AVAILABLE and _detector._initialized:
        try:
            return _detector.detect_ai_content(text)
        except Exception as e:
            logger.error(f"ML-based AI detection failed: {e}")
    
    # Fallback to AI-powered analysis if ML dependencies not available
    if ai_service and hasattr(ai_service, 'provider'):
        try:
            return _analyze_with_ai_service(text, ai_service)
        except Exception as e:
            logger.error(f"AI service detection failed: {e}")
    
    # Final fallback - heuristic analysis
    return _heuristic_ai_analysis(text)

def _analyze_with_ai_service(text: str, ai_service) -> Tuple[float, str]:
    """Use the AI service to analyze text for AI generation patterns."""
    prompt = f"""Analyze this text to assess if it was likely generated by AI or written by a human:

Text: "{text[:500]}{'...' if len(text) > 500 else ''}"

Consider these factors:
- Writing style and patterns
- Vocabulary and phrasing
- Structure and flow
- Common AI language patterns

Respond with a probability score (0.0 to 1.0) and brief explanation:
Probability: [0.0-1.0]
Explanation: [brief reasoning]"""

    response = ai_service.provider.generate_content(prompt)
    
    if response:
        lines = response.split('\n')
        probability = 0.5  # Default
        explanation = "AI analysis completed"
        
        for line in lines:
            line = line.strip()
            if line.startswith('Probability:'):
                try:
                    prob_str = line.split(':', 1)[1].strip()
                    probability = float(prob_str)
                    probability = max(0.0, min(1.0, probability))  # Clamp to [0,1]
                except (ValueError, IndexError):
                    pass
            elif line.startswith('Explanation:'):
                explanation = line.split(':', 1)[1].strip()
        
        return probability, explanation
    
    return 0.5, "AI analysis inconclusive"

def _heuristic_ai_analysis(text: str) -> Tuple[float, str]:
    """Simple heuristic analysis when no AI services are available."""
    if len(text) < 10:
        return 0.0, "Text too short for meaningful analysis"
    
    # Basic heuristics for AI-generated text patterns
    ai_indicators = 0
    total_checks = 0
    
    # Check for overly perfect grammar (simplified)
    sentences = text.split('.')
    if len(sentences) > 2:
        total_checks += 1
        avg_sentence_length = sum(len(s.split()) for s in sentences if s.strip()) / len([s for s in sentences if s.strip()])
        if 15 <= avg_sentence_length <= 25:  # AI often generates medium-length sentences
            ai_indicators += 0.3
    
    # Check for repetitive patterns
    words = text.lower().split()
    if len(words) > 10:
        total_checks += 1
        unique_words = len(set(words))
        word_diversity = unique_words / len(words)
        if word_diversity < 0.6:  # Lower diversity might indicate AI
            ai_indicators += 0.2
    
    # Check for common AI phrases
    ai_phrases = [
        "it's important to note", "it's worth noting", "in conclusion", 
        "furthermore", "moreover", "in addition", "as mentioned",
        "overall", "in summary", "to summarize"
    ]
    total_checks += 1
    phrase_count = sum(1 for phrase in ai_phrases if phrase in text.lower())
    if phrase_count > len(text.split()) * 0.02:  # More than 2% AI phrases
        ai_indicators += 0.3
    
    probability = min(ai_indicators, 1.0) if total_checks > 0 else 0.5
    
    if probability < 0.3:
        explanation = "Text shows human-like characteristics"
    elif probability > 0.7:
        explanation = "Text shows potential AI generation patterns"
    else:
        explanation = "Mixed indicators - inconclusive analysis"
    
    return probability, f"{explanation} (heuristic analysis)" 