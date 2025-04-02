# LingLooma - IELTS Speaking Assessment System

LingLooma is an advanced IELTS Speaking assessment system that uses AI agents to evaluate speaking performance and provide personalized feedback to students. The system implements various design patterns and agentic strategies to create a robust, efficient, and user-friendly application.

## Features

- Multi-agent assessment system based on IELTS Speaking criteria
- Personalized feedback based on student's speaking performance and history
- Human-in-the-loop capability for teacher intervention and feedback improvement
- Database integration for storing and retrieving student performance history
- Streamlit web interface for easy interaction

## Design Patterns Implemented

1. **Singleton Pattern** - For database connection and configuration management
2. **Factory Pattern** - For creating different types of agents
3. **Proxy Pattern** - For managing tool interactions securely
4. **Adapter Pattern** - For compatibility between different components
5. **Observer Pattern** - For monitoring agent states and triggering actions
6. **Chain of Responsibility Pattern** - For processing feedback through multiple stages

## Agentic Strategies

1. **Reflection Strategy** - Agents evaluate and improve their own output
2. **Tool Use** - Agents access external tools and databases
3. **Planning** - Agents break down complex tasks into smaller steps
4. **Multi-agent Collaboration** - Multiple specialized agents work together

## Getting Started

1. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Set up environment variables:
   Create a `.env` file with your OpenAI API key and database connection string.

3. Run the application:
   ```
   streamlit run src/app/main.py
   ```

## System Architecture

The system consists of:
- 4 Criteria Agents (one for each IELTS Speaking criterion)
- 1 Feedback Agent for aggregating and personalizing feedback
- Database connector for historical data retrieval
- Human feedback integration using LangGraph's interrupt feature

## License

MIT 