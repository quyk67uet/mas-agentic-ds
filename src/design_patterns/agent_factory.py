from langchain_openai import ChatOpenAI
from typing import Dict, Any, Optional

class AgentFactory:
    """
    Factory Pattern implementation for creating different types of agents
    """
    
    @staticmethod
    def create_agent(agent_type: str, model_name: str = "gpt-4", temperature: float = 0.0, **kwargs) -> Any:
        """
        Create an agent of the specified type
        
        Args:
            agent_type: Type of agent to create (fc, lr, gr, pr, feedback)
            model_name: Name of the LLM model to use
            temperature: Temperature setting for the LLM
            kwargs: Additional arguments to pass to the agent
            
        Returns:
            The created agent
        """
        # Create base LLM for all agents
        llm = ChatOpenAI(
            model_name=model_name,
            temperature=temperature
        )
        
        # Create the specific agent type
        if agent_type == "fc":
            from src.agents.criteria_agents import FluencyCoherenceAgent
            return FluencyCoherenceAgent(llm=llm, **kwargs)
        
        elif agent_type == "lr":
            from src.agents.criteria_agents import LexicalResourceAgent
            return LexicalResourceAgent(llm=llm, **kwargs)
        
        elif agent_type == "gr":
            from src.agents.criteria_agents import GrammaticalRangeAgent
            return GrammaticalRangeAgent(llm=llm, **kwargs)
        
        elif agent_type == "pr":
            from src.agents.criteria_agents import PronunciationAgent
            return PronunciationAgent(llm=llm, **kwargs)
        
        elif agent_type == "feedback":
            from src.agents.feedback_agent import FeedbackAgent
            return FeedbackAgent(llm=llm, **kwargs)
        
        else:
            raise ValueError(f"Unknown agent type: {agent_type}") 