import json
from typing import Dict, Any, Optional

def get_transcript_from_json(json_data: Dict[str, Any]) -> Optional[str]:
    """
    Extract transcript from the JSON data
    
    Args:
        json_data: JSON data containing the transcript
        
    Returns:
        Extracted transcript or None if not found
    """
    if "speech_score" in json_data and "transcript" in json_data["speech_score"]:
        return json_data["speech_score"]["transcript"]
    
    if "transcript" in json_data:
        return json_data["transcript"]
    
    for key, value in json_data.items():
        if isinstance(value, dict):
            transcript = get_transcript_from_json(value)
            if transcript:
                return transcript
        elif key.lower() == "transcript" and isinstance(value, str):
            return value
    
    return None

def extract_transcript_features(transcript: str) -> Dict[str, Any]:
    """
    Extract features from the transcript for advanced analysis
    
    Args:
        transcript: Text transcript
        
    Returns:
        Dictionary of extracted features
    """
    # Calculate basic statistics
    word_count = len(transcript.split())
    sentence_count = len([s for s in transcript.split('.') if s.strip()])
    avg_words_per_sentence = word_count / sentence_count if sentence_count > 0 else 0
    
    # Calculate frequency of hesitation markers
    hesitation_markers = ["um", "uh", "er", "mm", "hmm", "like", "you know", "I mean"]
    hesitation_count = sum(transcript.lower().count(marker) for marker in hesitation_markers)
    
    # Calculate frequency of cohesive devices
    cohesive_devices = [
        "moreover", "furthermore", "in addition", "however", "nevertheless", 
        "on the other hand", "consequently", "therefore", "thus", "hence", 
        "as a result", "for instance", "for example", "specifically", 
        "to illustrate", "in conclusion", "to sum up", "finally"
    ]
    cohesive_count = sum(transcript.lower().count(device) for device in cohesive_devices)
    
    return {
        "word_count": word_count,
        "sentence_count": sentence_count,
        "avg_words_per_sentence": avg_words_per_sentence,
        "hesitation_count": hesitation_count,
        "hesitation_per_100_words": (hesitation_count / word_count) * 100 if word_count > 0 else 0,
        "cohesive_count": cohesive_count,
        "cohesive_per_100_words": (cohesive_count / word_count) * 100 if word_count > 0 else 0
    }

def extract_word_scores_from_json(json_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract word scores from the JSON data for pronunciation analysis
    
    Args:
        json_data: JSON data containing the word scores
        
    Returns:
        Dictionary of pronunciation statistics
    """
    try:
        if "speech_score" in json_data and "word_score_list" in json_data["speech_score"]:
            word_scores = json_data["speech_score"]["word_score_list"]
            
            # Calculate average pronunciation score
            quality_scores = [word.get("quality_score", 0) for word in word_scores if "quality_score" in word]
            avg_quality_score = sum(quality_scores) / len(quality_scores) if quality_scores else 0
            
            # Extract problematic pronunciations
            problem_words = [
                {
                    "word": word.get("word", ""),
                    "score": word.get("quality_score", 0)
                }
                for word in word_scores 
                if "quality_score" in word and word["quality_score"] < 70
            ]
            
            return {
                "avg_pronunciation_score": avg_quality_score,
                "problem_words": problem_words,
                "word_count": len(word_scores)
            }
    except Exception as e:
        print(f"Error extracting word scores: {str(e)}")
    
    return {} 