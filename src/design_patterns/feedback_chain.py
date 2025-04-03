from typing import Dict, Any, Optional
from abc import ABC, abstractmethod

class FeedbackHandler(ABC):
    """
    Abstract handler class for the Chain of Responsibility pattern
    """
    
    def __init__(self):
        self._next_handler = None
    
    def set_next(self, handler):
        """
        Set the next handler in the chain
        
        Args:
            handler: The next handler in the chain
            
        Returns:
            The next handler for method chaining
        """
        self._next_handler = handler
        return handler
    
    def handle(self, feedback: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle the feedback or pass it to the next handler
        
        Args:
            feedback: The feedback to handle
            
        Returns:
            The processed feedback
        """
        if self._next_handler:
            return self._next_handler.handle(feedback)
        return feedback
    
    @abstractmethod
    def process(self, feedback: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process the feedback
        
        Args:
            feedback: The feedback to process
            
        Returns:
            The processed feedback
        """
        pass


class FormatCheckHandler(FeedbackHandler):
    """
    Handler to check and fix feedback format
    """
    
    def handle(self, feedback: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle the feedback format
        """
        processed_feedback = self.process(feedback)
        return super().handle(processed_feedback)
    
    def process(self, feedback: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check and fix feedback format
        """
        if not isinstance(feedback, dict):
            feedback = {"overall_feedback": str(feedback)}
        
        if "overall_score" not in feedback:
            feedback["overall_score"] = 0.0
            
        if "overall_feedback" not in feedback:
            feedback["overall_feedback"] = "No feedback provided."
            
        if "detailed_feedback" not in feedback:
            feedback["detailed_feedback"] = {}
            
        return feedback


class ContentEnhancementHandler(FeedbackHandler):
    """
    Handler to enhance feedback content
    """
    
    def handle(self, feedback: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle the feedback content enhancement
        """
        processed_feedback = self.process(feedback)
        return super().handle(processed_feedback)
    
    def process(self, feedback: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enhance feedback content
        """
        overall_feedback = feedback.get("overall_feedback", "")
        
        if not overall_feedback.startswith("# ") and not overall_feedback.startswith("## "):
            feedback["overall_feedback"] = f"## Overall Assessment\n\n{overall_feedback}"
        
        detailed_feedback = feedback.get("detailed_feedback", {})
        
        for criterion, criterion_feedback in detailed_feedback.items():
            if not criterion_feedback.startswith("# ") and not criterion_feedback.startswith("## "):
                detailed_feedback[criterion] = f"### {criterion.replace('_', ' ').title()}\n\n{criterion_feedback}"
        
        feedback["detailed_feedback"] = detailed_feedback
        
        return feedback


class PersonalizationHandler(FeedbackHandler):
    """
    Handler to personalize feedback based on student history
    """
    
    def __init__(self, student_history: Optional[Dict[str, Any]] = None):
        """
        Initialize the PersonalizationHandler
        
        Args:
            student_history: The student's history data
        """
        super().__init__()
        self.student_history = student_history
    
    def handle(self, feedback: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle the feedback personalization
        """
        processed_feedback = self.process(feedback)
        return super().handle(processed_feedback)
    
    def process(self, feedback: Dict[str, Any]) -> Dict[str, Any]:
        """
        Personalize feedback based on student history
        """
        if not self.student_history:
            return feedback
        
        # Add personalized context based on student history
        overall_feedback = feedback.get("overall_feedback", "")
        
        if "submissions" in self.student_history and len(self.student_history["submissions"]) > 1:
            current_score = feedback.get("overall_score", 0)
            previous_scores = [sub.get("overall", 0) for sub in self.student_history["submissions"]]
            avg_previous_score = sum(previous_scores) / len(previous_scores) if previous_scores else 0
            
            # Add personalized progress note
            if current_score > avg_previous_score:
                progress_note = f"\n\n## Progress Tracking\n\nGreat job! You've shown improvement compared to your previous submissions (average score: {avg_previous_score:.1f})."
                feedback["overall_feedback"] = overall_feedback + progress_note
            elif current_score < avg_previous_score:
                progress_note = f"\n\n## Progress Tracking\n\nYou've scored slightly lower than your previous submissions (average score: {avg_previous_score:.1f}). Let's focus on the areas for improvement."
                feedback["overall_feedback"] = overall_feedback + progress_note
        
        # Add personalized learning path based on weakest area
        detailed_feedback = feedback.get("detailed_feedback", {})
        criterion_scores = {
            "Fluency and Coherence": feedback.get("fc_score", 0),
            "Lexical Resource": feedback.get("lr_score", 0),
            "Grammatical Range": feedback.get("gr_score", 0),
            "Pronunciation": feedback.get("pr_score", 0)
        }
        
        if criterion_scores:
            weakest_criterion = min(criterion_scores, key=criterion_scores.get)
            
            learning_path = f"\n\n## Personalized Learning Path\n\nBased on your performance, we recommend focusing on improving your **{weakest_criterion}**. "
            
            # Add specific recommendations for each criterion
            if weakest_criterion == "Fluency and Coherence":
                learning_path += "Try practicing with conversation partners and focus on speaking without long pauses."
            elif weakest_criterion == "Lexical Resource":
                learning_path += "Work on expanding your vocabulary by learning topic-specific words and phrases."
            elif weakest_criterion == "Grammatical Range":
                learning_path += "Review complex grammatical structures and practice using them in your speaking."
            elif weakest_criterion == "Pronunciation":
                learning_path += "Focus on specific sounds that are difficult for you and practice stress and intonation patterns."
                
            feedback["overall_feedback"] = feedback["overall_feedback"] + learning_path
            
        return feedback 