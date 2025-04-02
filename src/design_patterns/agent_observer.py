from typing import Dict, Any, List, Callable, Optional
from abc import ABC, abstractmethod

class AgentSubject(ABC):
    """
    Abstract Subject class for the Observer pattern
    """
    
    def __init__(self):
        self._observers = []
    
    def attach(self, observer):
        """
        Attach an observer to the subject
        """
        if observer not in self._observers:
            self._observers.append(observer)
    
    def detach(self, observer):
        """
        Detach an observer from the subject
        """
        try:
            self._observers.remove(observer)
        except ValueError:
            pass
    
    def notify(self, event_type: str, data: Dict[str, Any]):
        """
        Notify all observers about an event
        """
        for observer in self._observers:
            observer.update(self, event_type, data)


class AgentObserver(ABC):
    """
    Abstract Observer class for the Observer pattern
    """
    
    @abstractmethod
    def update(self, subject, event_type: str, data: Dict[str, Any]):
        """
        Update method called by the subject
        """
        pass


class ReflectionObserver(AgentObserver):
    """
    Concrete Observer that triggers reflections when needed
    
    This observer monitors agent outputs and triggers reflection
    when it detects potential issues or areas for improvement
    """
    
    def __init__(self, reflection_threshold: float = 0.7, 
                 reflection_callback: Optional[Callable] = None):
        """
        Initialize the ReflectionObserver
        
        Args:
            reflection_threshold: Confidence threshold below which reflection is triggered
            reflection_callback: Callback function to execute when reflection is needed
        """
        self.reflection_threshold = reflection_threshold
        self.reflection_callback = reflection_callback
    
    def update(self, subject, event_type: str, data: Dict[str, Any]):
        """
        Update method called by the subject
        
        Args:
            subject: The subject that triggered the update
            event_type: Type of event that occurred
            data: Data associated with the event
        """
        if event_type == "agent_output":
            # Check if reflection is needed based on confidence score
            confidence = data.get("confidence", 1.0)
            
            if confidence < self.reflection_threshold:
                print(f"Reflection triggered for {subject.__class__.__name__} with confidence {confidence}")
                
                # Create reflection data
                reflection_data = {
                    "original_output": data.get("output"),
                    "confidence": confidence,
                    "subject": subject
                }
                
                # If a callback is provided, execute it
                if self.reflection_callback:
                    self.reflection_callback(reflection_data)


class LoggingObserver(AgentObserver):
    """
    Concrete Observer that logs agent activities
    """
    
    def update(self, subject, event_type: str, data: Dict[str, Any]):
        """
        Update method called by the subject
        """
        subject_name = subject.__class__.__name__
        
        if event_type == "agent_start":
            print(f"[LOG] {subject_name} started processing")
        
        elif event_type == "agent_output":
            print(f"[LOG] {subject_name} generated output")
        
        elif event_type == "agent_error":
            error = data.get("error", "Unknown error")
            print(f"[ERROR] {subject_name} encountered an error: {error}")
        
        elif event_type == "agent_reflection":
            print(f"[LOG] {subject_name} is performing reflection")
        
        elif event_type == "agent_tool_use":
            tool = data.get("tool", "Unknown tool")
            print(f"[LOG] {subject_name} is using tool: {tool}") 