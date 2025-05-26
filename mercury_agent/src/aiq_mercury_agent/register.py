"""
This module implements the core registration and workflow logic for the Mercury Agent system.
It defines the main workflow configuration and orchestrates the interaction between different AI agents.

Key Components:
1. MercuryAgentWorkflowConfig: Configuration class that defines the workflow parameters
2. mercury_agent_workflow: Main workflow function that sets up and orchestrates the agent system
3. Agent State Management: Handles the state transitions between different agents
4. Router Logic: Directs queries to appropriate specialized agents

Related Components:
- haystack_agent: Handles general conversation and chitchat
- langchain_research_tool: Provides research capabilities using LangChain
- nvbp_rag_tool: Implements RAG (Retrieval Augmented Generation) functionality

The workflow follows a supervisor-worker pattern where:
1. A supervisor agent classifies incoming queries
2. A router directs queries to specialized worker agents
3. Worker agents process queries using their specific capabilities
"""

# SPDX-FileCopyrightText: Copyright (c) 2025, NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging

from aiq.builder.builder import Builder
from aiq.builder.framework_enum import LLMFrameworkEnum
from aiq.cli.register_workflow import register_function
from aiq.data_models.component_ref import FunctionRef
from aiq.data_models.component_ref import LLMRef
from aiq.data_models.function import FunctionBaseConfig

# Import related agent modules
from . import haystack_agent  # noqa: F401, pylint: disable=unused-import
from . import langchain_research_tool  # noqa: F401, pylint: disable=unused-import
from . import nvbp_rag_tool  # noqa: F401, pylint: disable=unused-import

# Configure logging
logger = logging.getLogger(__name__)

# Set up logging format
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)


class MercuryAgentWorkflowConfig(FunctionBaseConfig, name="mercury_agent"):
    """
    Configuration class for the Mercury Agent workflow.
    
    Attributes:
        llm: Reference to the LLM to be used (defaults to "nim_llm")
        data_dir: Directory containing data for RAG operations
        research_tool: Reference to the research tool function
        rag_tool: Reference to the RAG tool function
        chitchat_agent: Reference to the chitchat agent function
    """
    llm: LLMRef = "nim_llm"
    data_dir: str = "/home/coder/dev/ai-query-engine/aiq/mercury/data/"
    research_tool: FunctionRef
    rag_tool: FunctionRef
    chitchat_agent: FunctionRef


@register_function(config_type=MercuryAgentWorkflowConfig, framework_wrappers=[LLMFrameworkEnum.LANGCHAIN])
async def mercury_agent_workflow(config: MercuryAgentWorkflowConfig, builder: Builder):
    """
    Main workflow function that sets up and orchestrates the Mercury Agent system.
    
    This function:
    1. Initializes the necessary tools and LLM
    2. Sets up the routing logic
    3. Defines the state management
    4. Creates the workflow graph
    5. Handles the execution of queries
    
    Args:
        config: Configuration object containing workflow parameters
        builder: Builder object for creating framework-specific components
    """
    from typing import TypedDict

    from colorama import Fore
    from langchain_community.chat_message_histories import ChatMessageHistory
    from langchain_core.messages import BaseMessage
    from langchain_core.output_parsers import StrOutputParser
    from langchain_core.prompts import PromptTemplate
    from langchain_core.runnables import RunnablePassthrough
    from langchain_core.runnables.history import RunnableWithMessageHistory
    from langgraph.graph import END
    from langgraph.graph import StateGraph

    # Initialize components using the builder
    logger.info("workflow config = %s", config)

    llm = await builder.get_llm(llm_name=config.llm, wrapper_type=LLMFrameworkEnum.LANGCHAIN)
    research_tool = builder.get_tool(fn_name=config.research_tool, wrapper_type=LLMFrameworkEnum.LANGCHAIN)
    rag_tool = builder.get_tool(fn_name=config.rag_tool, wrapper_type=LLMFrameworkEnum.LANGCHAIN)
    chitchat_agent = builder.get_tool(fn_name=config.chitchat_agent, wrapper_type=LLMFrameworkEnum.LANGCHAIN)

    chat_hist = ChatMessageHistory()

    # Define the routing prompt for classifying user queries
    router_prompt = """
    Given the user input below, classify it as either being about 'Research', 'Retrieve' or 'General' topic.
    Just use one of these words as your response. \
    'Research' - any question requiring factual knowledge on a specific topic from Wikipedia...etc
    'Retrieve' - any question related to the topic of SPH (Smoothed Particle Hydrodynamics). This agent is also triggered if the user query explicitly mentioned RAG or the use retrieve..etc
    'General' - answering small greeting or chitchat type of questions or everything else that does not fall into any of the above topics.
    User query: {input}
    Classifcation topic:"""  # noqa: E501

    # Set up the routing chain
    routing_chain = ({
        "input": RunnablePassthrough()
    }
                     | PromptTemplate.from_template(router_prompt)
                     | llm
                     | StrOutputParser())

    # Add message history to the routing chain
    supervisor_chain_with_message_history = RunnableWithMessageHistory(
        routing_chain,
        lambda _: chat_hist,
        history_messages_key="chat_history",
    )

    class AgentState(TypedDict):
        """
        TypedDict defining the state structure for the agent workflow.
        
        Attributes:
            input: The user's input query
            chat_history: List of previous messages in the conversation
            chosen_worker_agent: The selected agent for processing the query
            final_output: The final response generated by the system
        """
        input: str
        chat_history: list[BaseMessage] | None
        chosen_worker_agent: str | None
        final_output: str | None

    async def supervisor(state: AgentState):
        """
        Supervisor function that classifies incoming queries and determines which agent should handle them.
        
        Args:
            state: Current state of the agent workflow
            
        Returns:
            Updated state with chosen agent and chat history
        """
        query = state["input"]
        chosen_agent = (await supervisor_chain_with_message_history.ainvoke(
            {"input": query},
            {"configurable": {
                "session_id": "unused"
            }},
        ))
        logger.debug("Supervisor classified query as: %s", chosen_agent)

        return {'input': query, "chosen_worker_agent": chosen_agent, "chat_history": chat_hist}

    async def router(state: AgentState):
        """
        Router function that determines the next step in the workflow based on the current state.
        
        Args:
            state: Current state of the agent workflow
            
        Returns:
            String indicating the next node in the workflow
        """
        status = list(state.keys())
        logger.debug("Router processing state: %s", status)
        
        if 'final_output' in status:
            route_to = "end"
        elif 'chosen_worker_agent' not in status:
            logger.debug("Routing to supervisor")
            route_to = "supevisor"
        elif 'chosen_worker_agent' in status:
            logger.debug("Routing to workers")
            route_to = "workers"
        else:
            route_to = "end"
        return route_to

    async def workers(state: AgentState):
        """
        Worker function that processes queries using the appropriate specialized agent.
        
        Args:
            state: Current state of the agent workflow
            
        Returns:
            Updated state with the final output from the chosen agent
        """
        query = state["input"]
        worker_choice = state["chosen_worker_agent"]
        logger.debug("Worker processing query with agent: %s", worker_choice)
        
        if "retrieve" in worker_choice.lower():
            out = (await rag_tool.ainvoke(query))
            output = out
            logger.debug("RAG tool response received")
        elif "general" in worker_choice.lower():
            output = (await chitchat_agent.ainvoke(query))
            logger.debug("Chitchat response received")
        elif 'research' in worker_choice.lower():
            # Get the Wikipedia page content and URL
            wiki_results = await research_tool.ainvoke(query)
            
            # Create a prompt for summarizing the Wikipedia results
            summary_prompt = PromptTemplate.from_template(
                """You are a helpful assistant that summarizes information from Wikipedia articles.
                Please provide a clear and concise 500-word summary of the following Wikipedia content, focusing on answering the user's question: {question}

                Wikipedia content:
                {content}

                Please provide a well-structured summary that:
                1. Directly answers the user's question
                2. Uses complete sentences
                3. Ends with a proper concluding sentence
                4. Maintains a natural flow
                5. Includes the most relevant information

                If the Wikipedia content is not relevant to the question, please indicate that we should try another search.

                Summary:"""
            )
            
            # Create the summarization chain
            summary_chain = summary_prompt | llm | StrOutputParser()
            
            # Get the summary
            output = await summary_chain.ainvoke({
                "question": query,
                "content": wiki_results
            })
            
            logger.debug("Research response received and summarized")
        else:
            output = ("Apologies, I am not sure what to say, I can answer general questions retrieve info this "
                      "mercury_agent workflow and answer light coding questions, but nothing more.")
            logger.warning("Unknown worker choice: %s", worker_choice)

        return {'input': query, "chosen_worker_agent": worker_choice, "chat_history": chat_hist, "final_output": output}

    # Set up the workflow graph
    workflow = StateGraph(AgentState)
    workflow.add_node("supervisor", supervisor)
    workflow.set_entry_point("supervisor")
    workflow.add_node("workers", workers)
    workflow.add_conditional_edges(
        "supervisor",
        router,
        {
            "workers": "workers", "end": END
        },
    )
    workflow.add_edge("supervisor", "workers")
    workflow.add_edge("workers", END)
    app = workflow.compile()

    async def _response_fn(input_message: str) -> str:
        """
        Response function that processes input messages and returns the system's response.
        
        Args:
            input_message: The user's input query
            
        Returns:
            The system's response to the query
        """
        try:
            logger.debug("Processing input message")
            out = (await app.ainvoke({"input": input_message, "chat_history": chat_hist}))
            output = out["final_output"]
            logger.info("Response generated successfully")
            return output
        finally:
            logger.debug("Finished processing message")

    try:
        yield _response_fn
    except GeneratorExit:
        logger.exception("Exited early!", exc_info=True)
    finally:
        logger.debug("Cleaning up mercury_agent workflow.")
