import json
from typing import Dict, Any, List, Optional, TypedDict, Annotated, Union
from langchain_core.language_models import BaseChatModel
from langgraph.graph import MessagesState, StateGraph, END
from langgraph.graph.message import AnyMessage, add_messages
from langgraph.prebuilt import ToolNode
from langgraph.types import interrupt
import json

# Import this for our reducer function
from operator import itemgetter

from src.design_patterns.agent_factory import AgentFactory
from src.design_patterns.response_adapter import ResponseAdapter
from src.design_patterns.agent_observer import LoggingObserver, ReflectionObserver
from src.utils.transcript_processor import get_transcript_from_json

# Define a simple reducer that takes the last value
def take_last(current_value: Any, new_value: Any) -> Any:
    return new_value

# Define the state schema for the workflow - properly inheriting from MessagesState
class IELTSAssessmentState(MessagesState, total=False):
    transcript: Annotated[Optional[str], take_last]
    student_id: Annotated[Optional[int], take_last]
    fluency_coherence_result: Annotated[Optional[Dict[str, Any]], take_last]
    lexical_resource_result: Annotated[Optional[Dict[str, Any]], take_last]
    grammatical_range_result: Annotated[Optional[Dict[str, Any]], take_last]
    pronunciation_result: Annotated[Optional[Dict[str, Any]], take_last]
    feedback_result: Annotated[Optional[Dict[str, Any]], take_last]
    teacher_feedback: Annotated[Optional[str], take_last]
    history: Annotated[Optional[List[Dict[str, Any]]], take_last]
    error: Annotated[Optional[str], take_last]

# Define the default state
def get_default_state() -> IELTSAssessmentState:
    return {
        "messages": [],
        "transcript": None,
        "student_id": None,
        "fluency_coherence_result": None,
        "lexical_resource_result": None,
        "grammatical_range_result": None,
        "pronunciation_result": None,
        "feedback_result": None,
        "teacher_feedback": None,
        "history": [],
        "error": None
    }

def create_assessment_workflow(model_name: str = "gpt-4") -> StateGraph:
    """
    Create a LangGraph workflow for IELTS speaking assessment
    
    Args:
        model_name: Name of the LLM model to use
        
    Returns:
        A StateGraph instance
    """
    # Use the TypedDict class instead of a direct dictionary
    workflow = StateGraph(IELTSAssessmentState)
    
    # Create agents via factory
    fc_agent = AgentFactory.create_agent("fc", model_name=model_name)
    lr_agent = AgentFactory.create_agent("lr", model_name=model_name)
    gr_agent = AgentFactory.create_agent("gr", model_name=model_name)
    pr_agent = AgentFactory.create_agent("pr", model_name=model_name)
    feedback_agent = AgentFactory.create_agent("feedback", model_name=model_name)
    
    # Add observers to agents
    logging_observer = LoggingObserver()
    reflection_observer = ReflectionObserver(reflection_threshold=0.7)
    
    for agent in [fc_agent, lr_agent, gr_agent, pr_agent, feedback_agent]:
        agent.attach(logging_observer)
        agent.attach(reflection_observer)
    
    # Define workflow nodes
    def extract_transcript(state: IELTSAssessmentState) -> IELTSAssessmentState:
        """
        Extract transcript from the input JSON
        """
        try:
            # Process messages to get transcript
            if state.get("transcript") is None:
                for message in state.get("messages", []):
                    # Use attribute access instead of dictionary-style access
                    if hasattr(message, 'content') and isinstance(message.content, str):
                        try:
                            # Try to parse as JSON
                            json_data = json.loads(message.content)
                            transcript = get_transcript_from_json(json_data)
                            if transcript:
                                state["transcript"] = transcript
                                break
                        except json.JSONDecodeError:
                            # Not a JSON, check if it's a transcript directly
                            if len(message.content) > 100:  # Assume it's a transcript if long enough
                                state["transcript"] = message.content
                                break
            
            # If still no transcript, return error
            if state.get("transcript") is None:
                state["error"] = "No transcript found in input"
            
            return state
        except Exception as e:
            state["error"] = f"Error extracting transcript: {str(e)}"
            return state
    
    def assess_fluency_coherence(state: IELTSAssessmentState) -> IELTSAssessmentState:
        """
        Assess fluency and coherence
        """
        try:
            if state.get("error"):
                return state
            
            transcript = state.get("transcript", "")
            student_id = state.get("student_id")
            
            result = fc_agent.assess(transcript, student_id)
            state["fluency_coherence_result"] = result
            
            return state
        except Exception as e:
            state["error"] = f"Error assessing fluency and coherence: {str(e)}"
            return state
    
    def assess_lexical_resource(state: IELTSAssessmentState) -> IELTSAssessmentState:
        """
        Assess lexical resource
        """
        try:
            if state.get("error"):
                return state
            
            transcript = state.get("transcript", "")
            student_id = state.get("student_id")
            
            result = lr_agent.assess(transcript, student_id)
            state["lexical_resource_result"] = result
            
            return state
        except Exception as e:
            state["error"] = f"Error assessing lexical resource: {str(e)}"
            return state
    
    def assess_grammatical_range(state: IELTSAssessmentState) -> IELTSAssessmentState:
        """
        Assess grammatical range
        """
        try:
            if state.get("error"):
                return state
            
            transcript = state.get("transcript", "")
            student_id = state.get("student_id")
            
            result = gr_agent.assess(transcript, student_id)
            state["grammatical_range_result"] = result
            
            return state
        except Exception as e:
            state["error"] = f"Error assessing grammatical range: {str(e)}"
            return state
    
    def assess_pronunciation(state: IELTSAssessmentState) -> IELTSAssessmentState:
        """
        Assess pronunciation
        """
        try:
            if state.get("error"):
                return state
            
            transcript = state.get("transcript", "")
            student_id = state.get("student_id")
            
            result = pr_agent.assess(transcript, student_id)
            state["pronunciation_result"] = result
            
            return state
        except Exception as e:
            state["error"] = f"Error assessing pronunciation: {str(e)}"
            return state
    
    def generate_feedback(state: IELTSAssessmentState) -> IELTSAssessmentState:
        """
        Generate overall feedback (không sử dụng interrupt)
        """
        try:
            if state.get("error"):
                return state
            
            transcript = state.get("transcript", "")
            student_id = state.get("student_id")
            
            # Combine criterion results
            criteria_results = {
                "fluency_coherence": state.get("fluency_coherence_result", {}),
                "lexical_resource": state.get("lexical_resource_result", {}),
                "grammatical_range": state.get("grammatical_range_result", {}),
                "pronunciation": state.get("pronunciation_result", {})
            }
            
            # Generate AI feedback
            result = feedback_agent.generate_feedback(transcript, criteria_results, student_id)
            state["feedback_result"] = result
            
            # Save to database if student_id is provided
            if student_id:
                submission_id = feedback_agent.save_to_database(
                    student_id,
                    result,
                    None  # No teacher feedback
                )
                if submission_id:
                    result["submission_id"] = submission_id
            
            # Return state normally, no interrupt
            return state
        except Exception as e:
            state["error"] = f"Error generating feedback: {str(e)}"
            return state
    
    def create_final_response(state: IELTSAssessmentState) -> IELTSAssessmentState:
        """
        Create the final response for the user
        """
        try:
            if state.get("error"):
                error_msg = state.get("error", "An unknown error occurred")
                # Use the correct approach to add a message to the message list
                return {"messages": [{"role": "assistant", "content": f"Error: {error_msg}"}]}
            
            # Get the assessment results
            feedback_result = state.get("feedback_result", {})
            
            if not feedback_result:
                # Use the correct approach to add a message to the message list
                return {"messages": [{"role": "assistant", "content": "No feedback generated. Please try again."}]}
            
            # Format the response
            overall_score = feedback_result.get("overall_score", 0)
            overall_feedback = feedback_result.get("overall_feedback", "")
            detailed_feedback = feedback_result.get("detailed_feedback", {})
            
            # Create a nicely formatted response
            response = f"# IELTS Speaking Assessment\n\n"
            response += f"## Overall Score: {overall_score}\n\n"
            response += f"{overall_feedback}\n\n"
            
            # Add detailed feedback for each criterion
            response += "## Detailed Feedback\n\n"
            
            for criterion, feedback in detailed_feedback.items():
                criterion_name = criterion.replace("_", " ").title()
                response += f"### {criterion_name}\n\n"
                response += f"{feedback}\n\n"
            
            # Add teacher feedback if available
            teacher_feedback = state.get("teacher_feedback")
            if teacher_feedback:
                response += f"## Teacher's Additional Feedback\n\n{teacher_feedback}\n\n"
            
            # Return a dict with the new message to append to messages list
            return {"messages": [{"role": "assistant", "content": response}]}
            
        except Exception as e:
            state["error"] = f"Error creating final response: {str(e)}"
            # Return a dict with the new message to append to messages list
            return {"messages": [{"role": "assistant", "content": f"Error: {str(e)}"}]}
    
    # Add nodes to the workflow
    workflow.add_node("extract_transcript", extract_transcript)
    workflow.add_node("assess_fluency_coherence", assess_fluency_coherence)
    workflow.add_node("assess_lexical_resource", assess_lexical_resource)
    workflow.add_node("assess_grammatical_range", assess_grammatical_range)
    workflow.add_node("assess_pronunciation", assess_pronunciation)
    workflow.add_node("generate_feedback", generate_feedback)
    workflow.add_node("create_final_response", create_final_response)
    
    # Define the workflow edges (updated to skip human-in-the-loop)
    workflow.set_entry_point("extract_transcript")
    workflow.add_edge("extract_transcript", "assess_fluency_coherence")
    workflow.add_edge("assess_fluency_coherence", "assess_lexical_resource")
    workflow.add_edge("assess_lexical_resource", "assess_grammatical_range")
    workflow.add_edge("assess_grammatical_range", "assess_pronunciation")
    workflow.add_edge("assess_pronunciation", "generate_feedback")
    workflow.add_edge("generate_feedback", "create_final_response") # Direct connection, no interrupt
    workflow.add_edge("create_final_response", END)
    
    # Define a mapping of nodes to their next nodes in the normal flow
    node_to_next = {
        "extract_transcript": "assess_fluency_coherence",
        "assess_fluency_coherence": "assess_lexical_resource",
        "assess_lexical_resource": "assess_grammatical_range",
        "assess_grammatical_range": "assess_pronunciation",
        "assess_pronunciation": "generate_feedback",
        "generate_feedback": "create_final_response",  # Updated to go directly to create_final_response
    }
    
    # Define error handling edges - improved version to avoid KeyError: None
    for node_name in ["extract_transcript", "assess_fluency_coherence", "assess_lexical_resource", 
                    "assess_grammatical_range", "assess_pronunciation", "generate_feedback"]:
        
        # Create a separate condition function for each node to avoid closure issues
        def create_error_checker(node):
            def error_check(state: IELTSAssessmentState) -> str:
                # Instead of returning None, return a string that represents the normal flow
                if state.get("error") is not None:
                    return "error"
                # Return a specific string we can map, not None
                return "continue"
            return error_check
        
        # Get the next node for this node
        next_node = node_to_next.get(node_name)
        
        # Create the mapping dictionary
        mapping = {"error": "create_final_response"}
        
        # Only add the continue mapping if there's a next node
        if next_node:
            mapping["continue"] = next_node
            
        # Add conditional edge that routes to error handler or continues normal flow
        workflow.add_conditional_edges(
            node_name,
            create_error_checker(node_name),
            mapping
        )
    
    # Compile the graph before returning
    compiled_workflow = workflow.compile()
    
    return compiled_workflow 