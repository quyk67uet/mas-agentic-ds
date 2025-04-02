from typing import Dict, Any, Optional, List
import json

class ResponseAdapter:
    """
    Adapter Pattern implementation for standardizing responses from different sources
    This adapter converts various response formats into a standard format for the application
    """
    
    @staticmethod
    def adapt_llm_response(response: Any) -> Dict[str, Any]:
        """
        Adapt a response from an LLM into a standard format
        """
        try:
            # Handle string responses that might be JSON
            if isinstance(response, str):
                try:
                    response_dict = json.loads(response)
                    return ResponseAdapter._format_dict_response(response_dict)
                except json.JSONDecodeError:
                    # Not JSON, return as content
                    return {"content": response, "type": "text"}
            
            # Handle dictionary responses
            elif isinstance(response, dict):
                return ResponseAdapter._format_dict_response(response)
            
            # Handle other types
            else:
                return {"content": str(response), "type": "text"}
                
        except Exception as e:
            print(f"Error adapting LLM response: {e}")
            return {"error": str(e), "type": "error"}
    
    @staticmethod
    def _format_dict_response(response_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format a dictionary response into the standard format
        """
        # Check if it already has the expected format
        if "content" in response_dict and "type" in response_dict:
            return response_dict
        
        # Convert to standard format
        if "score" in response_dict and "feedback" in response_dict:
            # It's likely a criteria agent response
            return {
                "score": response_dict.get("score"),
                "feedback": response_dict.get("feedback"),
                "type": "assessment"
            }
        elif "overall_score" in response_dict and "overall_feedback" in response_dict:
            # It's likely a feedback agent response
            return {
                "overall_score": response_dict.get("overall_score"),
                "overall_feedback": response_dict.get("overall_feedback"),
                "detailed_feedback": response_dict.get("detailed_feedback", {}),
                "type": "feedback"
            }
        else:
            # Unknown format, return as is with a type
            return {**response_dict, "type": "unknown"}
    
    @staticmethod
    def adapt_database_response(response: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Adapt a response from the database into a standard format
        """
        if not response or not isinstance(response, list):
            return {"content": [], "type": "database_result"}
        
        # Convert database response to standard format
        return {
            "content": response,
            "type": "database_result"
        }
    
    @staticmethod
    def adapt_transcript_response(response_json: Dict[str, Any]) -> Dict[str, Any]:
        """
        Adapt a transcript response from the JSON file into a standard format
        """
        if not response_json or "speech_score" not in response_json:
            return {"error": "Invalid transcript format", "type": "error"}
        
        try:
            transcript = response_json.get("speech_score", {}).get("transcript", "")
            
            # Extract word scores and other relevant data if needed
            word_scores = response_json.get("speech_score", {}).get("word_score_list", [])
            
            return {
                "transcript": transcript,
                "word_scores": word_scores,
                "type": "transcript"
            }
        except Exception as e:
            print(f"Error adapting transcript response: {e}")
            return {"error": str(e), "type": "error"} 