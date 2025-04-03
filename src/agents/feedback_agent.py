import json
from typing import Dict, Any, List, Optional
from langchain_core.language_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser

from src.design_patterns.agent_observer import AgentSubject
from src.design_patterns.tool_proxy import DatabaseToolProxy
from src.design_patterns.feedback_chain import (
    FeedbackHandler, FormatCheckHandler, ContentEnhancementHandler, PersonalizationHandler
)
from src.database.db_connector import DatabaseConnector

class FeedbackAgent(AgentSubject):
    """
    Agent responsible for combining individual criteria assessments and providing
    personalized overall feedback to the student
    """
    
    def __init__(self, llm: BaseChatModel):
        """
        Initialize the feedback agent
        
        Args:
            llm: Language model to use
        """
        super().__init__()
        self.llm = llm
        self.confidence = 1.0
        
        # Create database connection through proxy
        db_connector = DatabaseConnector()
        self.fetch_student_history = DatabaseToolProxy(db_connector.fetch_student_history)
        self.save_feedback = DatabaseToolProxy(db_connector.save_feedback)
        
        self._init_feedback_chain()
        
        self._init_prompt_template()
        
        self.output_parser = JsonOutputParser()
    
    def _init_feedback_chain(self):
        """
        Initialize the feedback processing chain using Chain of Responsibility pattern
        """
        format_handler = FormatCheckHandler()
        content_handler = ContentEnhancementHandler()
        
        # Link the handlers in a chain
        format_handler.set_next(content_handler)
        
        # Store the first handler
        self.feedback_chain = format_handler
    
    def _init_prompt_template(self):
        """
        Initialize the prompt template for the feedback agent
        """
        self.prompt_template = ChatPromptTemplate.from_messages([
            ("system", "You are an expert IELTS speaking examiner responsible for providing overall "
                      "feedback to students. Based on the individual criteria assessments, you need to "
                      "calculate an overall score and provide comprehensive personalized feedback."),
            ("user", "Transcript: {transcript}\n\n"
                    "Fluency and Coherence Assessment:\n"
                    "Score: {fc_score}\n"
                    "Feedback: {fc_feedback}\n\n"
                    "Lexical Resource Assessment:\n"
                    "Score: {lr_score}\n"
                    "Feedback: {lr_feedback}\n\n"
                    "Grammatical Range and Accuracy Assessment:\n"
                    "Score: {gr_score}\n"
                    "Feedback: {gr_feedback}\n\n"
                    "Pronunciation Assessment:\n"
                    "Score: {pr_score}\n"
                    "Feedback: {pr_feedback}\n\n"
                    "{student_history}\n\n"
                    "Based on these assessments, provide an overall IELTS speaking score (calculated as the average of "
                    "the four criteria scores, rounded to the nearest 0.5), and detailed overall feedback. "
                    "The feedback should summarize strengths and weaknesses across all criteria and offer "
                    "actionable advice for improvement.\n\n"
                    "Return the response as a JSON object with the following fields:\n"
                    "- overall_score (number): The overall IELTS speaking score\n"
                    "- overall_feedback (string): Comprehensive feedback with actionable advice\n"
                    "- detailed_feedback (object): An object with keys for each criterion ('fluency_coherence', "
                    "'lexical_resource', 'grammatical_range', 'pronunciation') containing the specific feedback for each")
        ])
    
    def generate_feedback(self, 
                         transcript: str, 
                         criteria_results: Dict[str, Dict[str, Any]], 
                         student_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Generate overall feedback based on individual criteria assessments
        
        Args:
            transcript: The student's speaking transcript
            criteria_results: Results from individual criteria agents
            student_id: Optional student ID for personalized feedback
            
        Returns:
            Overall feedback including score and detailed feedback
        """
        # Notify observers that agent is starting
        self.notify("agent_start", {"transcript": transcript, "student_id": student_id})
        
        # Get student history if student_id is provided
        student_history = None
        if student_id:
            self.notify("agent_tool_use", {"tool": "fetch_student_history", "student_id": student_id})
            student_history = self.fetch_student_history(student_id=student_id)
        
        # Extract scores and feedback from criteria results
        fc_result = criteria_results.get("fluency_coherence", {})
        lr_result = criteria_results.get("lexical_resource", {})
        gr_result = criteria_results.get("grammatical_range", {})
        pr_result = criteria_results.get("pronunciation", {})
        
        try:
            # Prepare prompt inputs
            prompt_inputs = {
                "transcript": transcript,
                "fc_score": fc_result.get("score", 0),
                "fc_feedback": fc_result.get("feedback", "No feedback available"),
                "lr_score": lr_result.get("score", 0),
                "lr_feedback": lr_result.get("feedback", "No feedback available"),
                "gr_score": gr_result.get("score", 0),
                "gr_feedback": gr_result.get("feedback", "No feedback available"),
                "pr_score": pr_result.get("score", 0),
                "pr_feedback": pr_result.get("feedback", "No feedback available"),
            }
            
            # Add student history context if available
            if student_history:
                history_summary = self._format_history_for_prompt(student_history)
                prompt_inputs["student_history"] = history_summary
            else:
                prompt_inputs["student_history"] = "No previous history available."
            
            # Create the prompt
            prompt = self.prompt_template.format_messages(**prompt_inputs)
            
            response = self.llm.invoke(prompt)
            
            # Parse the response
            feedback = self.output_parser.invoke(response.content)
            
            # Add confidence score
            feedback["confidence"] = self.confidence
            
            # Add individual scores for reference
            feedback["fc_score"] = fc_result.get("score", 0)
            feedback["lr_score"] = lr_result.get("score", 0)
            feedback["gr_score"] = gr_result.get("score", 0)
            feedback["pr_score"] = pr_result.get("score", 0)
            
            # Process the feedback through the chain of responsibility
            if student_history:
                # Add personalization handler with student history
                personalization_handler = PersonalizationHandler(student_history)
                
                # Get the last handler in the chain
                last_handler = self.feedback_chain
                while last_handler._next_handler:
                    last_handler = last_handler._next_handler
                
                # Add personalization handler to the end of the chain
                last_handler.set_next(personalization_handler)
            
            # Process the feedback through the chain
            processed_feedback = self.feedback_chain.handle(feedback)
            
            # Perform reflection if confidence is low
            if self.confidence < 0.8:
                processed_feedback = self._reflect_on_feedback(processed_feedback, transcript, criteria_results)
            
            # Notify observers about the output
            self.notify("agent_output", {"output": processed_feedback, "confidence": self.confidence})
            
            return processed_feedback
            
        except Exception as e:
            # Notify observers about the error
            self.notify("agent_error", {"error": str(e)})
            
            # Calculate a basic overall score as fallback
            scores = [
                fc_result.get("score", 0),
                lr_result.get("score", 0),
                gr_result.get("score", 0),
                pr_result.get("score", 0)
            ]
            avg_score = sum(scores) / len(scores) if scores else 0
            
            # Return a default feedback on error
            return {
                "overall_score": round(avg_score * 2) / 2,  # Round to nearest 0.5
                "overall_feedback": f"Error generating feedback: {str(e)}",
                "detailed_feedback": {
                    "fluency_coherence": fc_result.get("feedback", ""),
                    "lexical_resource": lr_result.get("feedback", ""),
                    "grammatical_range": gr_result.get("feedback", ""),
                    "pronunciation": pr_result.get("feedback", "")
                },
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
        
        # Format history entries
        history_entries = []
        for entry in history:
            overall = entry.get("overall", "N/A")
            date = entry.get("submitted_at", "Unknown date")
            fc = entry.get("fluency_coherence", "N/A")
            lr = entry.get("lexical_resource", "N/A")
            gr = entry.get("grammatical_range", "N/A")
            pr = entry.get("pronunciation", "N/A")
            
            history_entry = (
                f"- Date: {date}\n"
                f"  Overall: {overall}\n"
                f"  Fluency and Coherence: {fc}\n"
                f"  Lexical Resource: {lr}\n"
                f"  Grammatical Range: {gr}\n"
                f"  Pronunciation: {pr}"
            )
            
            history_entries.append(history_entry)
        
        # Combine into a single string
        history_summary = "Previous speaking test results:\n" + "\n\n".join(history_entries)
        return history_summary
    
    def _reflect_on_feedback(self, feedback: Dict[str, Any], transcript: str, 
                           criteria_results: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """
        Perform reflection on the feedback to improve it
        
        Args:
            feedback: The initial feedback
            transcript: The student's speaking transcript
            criteria_results: Results from individual criteria agents
            
        Returns:
            Improved feedback
        """
        self.notify("agent_reflection", {"feedback": feedback})
        
        # Create reflection prompt
        reflection_prompt = ChatPromptTemplate.from_messages([
            ("system", "You are an expert IELTS examiner reviewing feedback given to a student. "
                      "Carefully analyze the feedback and improve it for clarity, helpfulness, and actionability."),
            ("user", "Transcript: {transcript}\n\n"
                    "Individual criteria assessments:\n{criteria_summary}\n\n"
                    "Initial overall feedback:\n{overall_feedback}\n\n"
                    "Please review this feedback carefully. Is it clear, helpful, and actionable? "
                    "Does it accurately reflect the individual assessments? Provide improved feedback "
                    "that better addresses the student's strengths and weaknesses.")
        ])
        
        # Prepare criteria summary
        criteria_summary = "\n".join([
            f"- Fluency and Coherence: {criteria_results.get('fluency_coherence', {}).get('score', 0)}",
            f"- Lexical Resource: {criteria_results.get('lexical_resource', {}).get('score', 0)}",
            f"- Grammatical Range: {criteria_results.get('grammatical_range', {}).get('score', 0)}",
            f"- Pronunciation: {criteria_results.get('pronunciation', {}).get('score', 0)}"
        ])
        
        # Prepare prompt inputs
        prompt_inputs = {
            "transcript": transcript,
            "criteria_summary": criteria_summary,
            "overall_feedback": feedback.get("overall_feedback", "")
        }
        
        prompt = reflection_prompt.format_messages(**prompt_inputs)
        response = self.llm.invoke(prompt)
        
        # Update the feedback with reflected improvements
        try:
            improved_feedback = json.loads(response.content)
            if isinstance(improved_feedback, dict):
                if "overall_feedback" in improved_feedback:
                    feedback["overall_feedback"] = improved_feedback["overall_feedback"]
                if "detailed_feedback" in improved_feedback:
                    feedback["detailed_feedback"] = improved_feedback["detailed_feedback"]
        except:
            feedback["overall_feedback"] = response.content
        
        # Update confidence after reflection
        feedback["confidence"] = 0.9
        
        return feedback
    
    def save_to_database(self, student_id: int, feedback: Dict[str, Any], 
                        teacher_feedback: Optional[str] = None) -> Optional[int]:
        """
        Save the feedback to the database
        
        Args:
            student_id: The student's ID
            feedback: The feedback data
            teacher_feedback: Optional feedback from a teacher
            
        Returns:
            The submission ID if successful, None otherwise
        """
        try:
            self.notify("agent_tool_use", {"tool": "save_feedback", "student_id": student_id})
            
            # Extract scores and feedback
            fc_score = feedback.get("fc_score", 0)
            lr_score = feedback.get("lr_score", 0)
            gr_score = feedback.get("gr_score", 0)
            pr_score = feedback.get("pr_score", 0)
            overall_score = feedback.get("overall_score", 0)
            overall_feedback = feedback.get("overall_feedback", "")
            
            if teacher_feedback:
                overall_feedback += f"\n\n## Teacher's Additional Feedback\n\n{teacher_feedback}"
            
            # Save to database
            submission_id = self.save_feedback(
                student_id=student_id,
                fc=fc_score,
                lr=lr_score,
                gr=gr_score,
                pr=pr_score,
                overall=overall_score,
                overall_comment=overall_feedback
            )
            
            return submission_id
            
        except Exception as e:
            self.notify("agent_error", {"error": f"Error saving to database: {str(e)}"})
            return None 