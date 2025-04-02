import json
from typing import Dict, Any, List, Optional
from langchain_core.language_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser

from src.design_patterns.agent_observer import AgentSubject
from src.design_patterns.tool_proxy import DatabaseToolProxy
from src.database.db_connector import DatabaseConnector

class CriteriaAgent(AgentSubject):
    """
    Base class for all criteria agents
    """
    
    def __init__(self, llm: BaseChatModel, criterion_name: str):
        """
        Initialize the criteria agent
        
        Args:
            llm: Language model to use
            criterion_name: Name of the criterion to assess
        """
        super().__init__()
        self.llm = llm
        self.criterion_name = criterion_name
        self.confidence = 1.0
        
        # Create database connection through proxy
        db_connector = DatabaseConnector()
        self.fetch_student_history = DatabaseToolProxy(db_connector.fetch_student_history)
        
        # Initialize the prompt template
        self._init_prompt_template()
        
        # Initialize the output parser
        self.output_parser = JsonOutputParser()
    
    def _init_prompt_template(self):
        """
        Initialize the prompt template for the agent
        Override in subclasses
        """
        self.prompt_template = ChatPromptTemplate.from_messages([
            ("system", "You are an expert IELTS examiner specializing in assessing {criterion}. "
                      "Provide a detailed assessment of the speaking response."),
            ("user", "Transcript: {transcript}\n\n"
                    "Please assess this speaking response for {criterion} on a scale of 1-9 "
                    "according to the IELTS band descriptors. Provide a detailed feedback "
                    "explaining the score.")
        ])
    
    def _process_transcript(self, transcript: str) -> Dict[str, Any]:
        """
        Extract relevant features from the transcript for assessment
        Override in subclasses if needed
        """
        return {"transcript": transcript}
    
    def assess(self, transcript: str, student_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Assess the transcript for this criterion
        
        Args:
            transcript: The student's speaking transcript
            student_id: Optional student ID for personalized assessment
            
        Returns:
            Assessment result including score and feedback
        """
        # Notify observers that agent is starting
        self.notify("agent_start", {"transcript": transcript, "student_id": student_id})
        
        # Process the transcript to extract relevant features
        processed_data = self._process_transcript(transcript)
        
        # Get student history if student_id is provided
        student_history = None
        if student_id:
            self.notify("agent_tool_use", {"tool": "fetch_student_history", "student_id": student_id})
            student_history = self.fetch_student_history(student_id=student_id)
        
        # Generate assessment using the LLM
        try:
            # Prepare prompt inputs
            prompt_inputs = {
                "criterion": self.criterion_name,
                "transcript": transcript
            }
            
            # Add student history context if available
            if student_history:
                history_summary = self._format_history_for_prompt(student_history)
                prompt_inputs["student_history"] = history_summary
            
            # Create the prompt
            prompt = self.prompt_template.format_messages(**prompt_inputs)
            
            # Get the response from the LLM
            response = self.llm.invoke(prompt)
            
            # Parse the response
            assessment = self.output_parser.invoke(response.content)
            
            # Add confidence score
            assessment["confidence"] = self.confidence
            
            # Perform reflection if confidence is low
            if self.confidence < 0.8:
                assessment = self._reflect_on_assessment(assessment, transcript)
            
            # Notify observers about the output
            self.notify("agent_output", {"output": assessment, "confidence": self.confidence})
            
            return assessment
            
        except Exception as e:
            # Notify observers about the error
            self.notify("agent_error", {"error": str(e)})
            
            # Return a default assessment on error
            return {
                "score": 0,
                "feedback": f"Error assessing {self.criterion_name}: {str(e)}",
                "confidence": 0.0
            }
    
    def _format_history_for_prompt(self, history: List[Dict[str, Any]]) -> str:
        """
        Format student history for inclusion in the prompt
        
        Args:
            history: Student history data
            
        Returns:
            Formatted history string
        """
        if not history:
            return "No previous history available."
        
        # Extract relevant information from history
        criterion_key = self._get_criterion_key()
        
        # Format history entries
        history_entries = []
        for entry in history:
            score = entry.get(criterion_key, "N/A")
            date = entry.get("submitted_at", "Unknown date")
            history_entries.append(f"- Date: {date}, Score: {score}")
        
        # Combine into a single string
        history_summary = "Previous assessments for this criterion:\n" + "\n".join(history_entries)
        return history_summary
    
    def _get_criterion_key(self) -> str:
        """
        Get the database key for this criterion
        Override in subclasses
        """
        return "score"
    
    def _reflect_on_assessment(self, assessment: Dict[str, Any], transcript: str) -> Dict[str, Any]:
        """
        Perform reflection on the assessment to improve it
        
        Args:
            assessment: The initial assessment
            transcript: The student's speaking transcript
            
        Returns:
            Improved assessment
        """
        self.notify("agent_reflection", {"assessment": assessment})
        
        # Create reflection prompt
        reflection_prompt = ChatPromptTemplate.from_messages([
            ("system", "You are an expert IELTS examiner reviewing an assessment. "
                      "Carefully analyze the assessment and improve it if needed."),
            ("user", "Transcript: {transcript}\n\n"
                    "Initial assessment for {criterion}:\n"
                    "Score: {score}\n"
                    "Feedback: {feedback}\n\n"
                    "Please review this assessment carefully. Is the score justified? "
                    "Is the feedback detailed and helpful? Provide an improved assessment "
                    "with a score and detailed feedback.")
        ])
        
        # Prepare prompt inputs
        prompt_inputs = {
            "criterion": self.criterion_name,
            "transcript": transcript,
            "score": assessment.get("score", 0),
            "feedback": assessment.get("feedback", "")
        }
        
        # Get the response from the LLM
        prompt = reflection_prompt.format_messages(**prompt_inputs)
        response = self.llm.invoke(prompt)
        
        # Parse the response
        try:
            improved_assessment = self.output_parser.invoke(response.content)
            improved_assessment["confidence"] = 0.9  # Higher confidence after reflection
            return improved_assessment
        except:
            # If parsing fails, return the original assessment
            return assessment


class FluencyCoherenceAgent(CriteriaAgent):
    """
    Agent for assessing Fluency and Coherence
    """
    
    def __init__(self, llm: BaseChatModel):
        super().__init__(llm, "Fluency and Coherence")
    
    def _init_prompt_template(self):
        self.prompt_template = ChatPromptTemplate.from_messages([
            ("system", "You are an expert IELTS examiner specializing in assessing Fluency and Coherence. "
                      "Focus on how fluently the candidate speaks without repetition, self-correction, "
                      "hesitation, or slow speech. Also assess how coherent, relevant, and well-developed "
                      "their responses are, with appropriate use of cohesive devices and discourse markers."),
            ("user", "Transcript: {transcript}\n\n"
                    "{student_history}\n\n"
                    "Assess this speaking response for Fluency and Coherence on a scale of 1-9 "
                    "according to the IELTS band descriptors. Return a JSON with 'score' (number) and 'feedback' (string) fields. "
                    "The feedback should be detailed and include specific examples from the transcript.")
        ])
    
    def _get_criterion_key(self) -> str:
        return "fluency_coherence"


class LexicalResourceAgent(CriteriaAgent):
    """
    Agent for assessing Lexical Resource
    """
    
    def __init__(self, llm: BaseChatModel):
        super().__init__(llm, "Lexical Resource")
    
    def _init_prompt_template(self):
        self.prompt_template = ChatPromptTemplate.from_messages([
            ("system", "You are an expert IELTS examiner specializing in assessing Lexical Resource. "
                      "Focus on the range of vocabulary used by the candidate, including their ability "
                      "to use less common and idiomatic vocabulary. Also assess their accuracy in word "
                      "choice, formation, and collocation, as well as their ability to paraphrase."),
            ("user", "Transcript: {transcript}\n\n"
                    "{student_history}\n\n"
                    "Assess this speaking response for Lexical Resource on a scale of 1-9 "
                    "according to the IELTS band descriptors. Return a JSON with 'score' (number) and 'feedback' (string) fields. "
                    "The feedback should be detailed and include specific examples from the transcript.")
        ])
    
    def _get_criterion_key(self) -> str:
        return "lexical_resource"


class GrammaticalRangeAgent(CriteriaAgent):
    """
    Agent for assessing Grammatical Range and Accuracy
    """
    
    def __init__(self, llm: BaseChatModel):
        super().__init__(llm, "Grammatical Range and Accuracy")
    
    def _init_prompt_template(self):
        self.prompt_template = ChatPromptTemplate.from_messages([
            ("system", "You are an expert IELTS examiner specializing in assessing Grammatical Range and Accuracy. "
                      "Focus on the range and accuracy of grammatical structures used by the candidate. "
                      "Consider their ability to use both simple and complex structures flexibly, "
                      "and the frequency of grammatical errors."),
            ("user", "Transcript: {transcript}\n\n"
                    "{student_history}\n\n"
                    "Assess this speaking response for Grammatical Range and Accuracy on a scale of 1-9 "
                    "according to the IELTS band descriptors. Return a JSON with 'score' (number) and 'feedback' (string) fields. "
                    "The feedback should be detailed and include specific examples from the transcript.")
        ])
    
    def _get_criterion_key(self) -> str:
        return "grammatical_range"


class PronunciationAgent(CriteriaAgent):
    """
    Agent for assessing Pronunciation
    """
    
    def __init__(self, llm: BaseChatModel):
        super().__init__(llm, "Pronunciation")
    
    def _init_prompt_template(self):
        self.prompt_template = ChatPromptTemplate.from_messages([
            ("system", "You are an expert IELTS examiner specializing in assessing Pronunciation. "
                      "Focus on the candidate's ability to produce individual sounds, use appropriate "
                      "word stress, sentence stress, and intonation patterns. Also consider the "
                      "impact of pronunciation features on intelligibility."),
            ("user", "Transcript: {transcript}\n\n"
                    "{student_history}\n\n"
                    "Assess this speaking response for Pronunciation on a scale of 1-9 "
                    "according to the IELTS band descriptors. Return a JSON with 'score' (number) and 'feedback' (string) fields. "
                    "The feedback should be detailed and include specific examples from the transcript.")
        ])
    
    def _get_criterion_key(self) -> str:
        return "pronunciation" 