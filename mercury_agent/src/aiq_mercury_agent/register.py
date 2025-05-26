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
from colorama import Fore, Style, init

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

# Initialize colorama
init()

# Configure logging
logger = logging.getLogger(__name__)

# Set up logging format
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Add a custom formatter for color-coded output
class ColoredFormatter(logging.Formatter):
    def format(self, record):
        if hasattr(record, 'agent_type'):
            if record.agent_type == 'research':
                record.msg = f"{Fore.BLUE}[RESEARCH AGENT]{Style.RESET_ALL} {record.msg}"
            elif record.agent_type == 'retrieve':
                record.msg = f"{Fore.GREEN}[RAG AGENT]{Style.RESET_ALL} {record.msg}"
            elif record.agent_type == 'general':
                record.msg = f"{Fore.YELLOW}[CHITCHAT AGENT]{Style.RESET_ALL} {record.msg}"
        return super().format(record)

# Apply the colored formatter
handler = logging.StreamHandler()
handler.setFormatter(ColoredFormatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)


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
            logger.info("Processing with RAG agent", extra={'agent_type': 'retrieve'})
            out = (await rag_tool.ainvoke(query))
            output = out
            logger.debug("RAG tool response received")
        elif "general" in worker_choice.lower():
            logger.info("Processing with Chitchat agent", extra={'agent_type': 'general'})
            output = (await chitchat_agent.ainvoke(query))
            logger.debug("Chitchat response received")
        elif 'research' in worker_choice.lower():
            logger.info("Processing with Research agent", extra={'agent_type': 'research'})
            try:
                # Get the Wikipedia page content and URL
                wiki_results = await research_tool.ainvoke(query)
                
                # Check if the query is asking for more details
                detail_prompt = PromptTemplate.from_template("""
                Check if the query contains any of these expressions asking for more information:
                - "more details"
                - "elaborate"
                - "tell me more"
                - "explain further"
                - "more information"

                Query: {query}
                Return ONLY 'yes' if any of these expressions are present, otherwise 'no'.""")
                
                try:
                    detail_check = await llm.ainvoke(detail_prompt.format(query=query))
                    # Extract the text content from the AIMessage
                    detail_response = str(detail_check).strip().lower()
                    is_detail_request = 'yes' in detail_response
                    logger.debug("Detail detection response: %s", detail_response)
                except Exception as e:
                    logger.warning("Error in detail detection, defaulting to standard summary: %s", e)
                    is_detail_request = False
                
                # Create a prompt for summarizing the Wikipedia results
                summary_prompt = PromptTemplate.from_template(
                    """You are a helpful assistant that summarizes information from Wikipedia articles.
                    You MUST provide a summary of {length} words, but make sure you complete the last sentence.
                    Focus on answering the user's question: {question}

                    Wikipedia content:
                    {content}

                    Please provide a well-structured summary that:
                    1. Directly answers the user's question
                    2. Uses complete sentences
                    3. Ends with a proper concluding sentence
                    4. Maintains a natural flow
                    5. Includes the most relevant information
                    {detail_instructions}

                    Remember: Your summary should be approximately {length} words long, but make sure you complete the last sentence.
                    If the Wikipedia content is not relevant to the question, please indicate that we should try another search.

                    Summary:"""
                )
                
                # Create the summarization chain with word count verification
                summary_chain = summary_prompt | llm | StrOutputParser()
                
                # Get the summary with appropriate length and detail level
                output = await summary_chain.ainvoke({
                    "question": query,
                    "content": wiki_results,
                    "length": "1000" if is_detail_request else "500",
                    "detail_instructions": """
                    Since this is a request for more details, please:
                    1. Include more specific examples and facts
                    2. Provide deeper context and background information
                    3. Explain related concepts and their connections
                    4. Discuss implications and significance
                    5. Cover multiple aspects of the topic
                    6. Aim for approximately 1000 words while maintaining quality
                    """ if is_detail_request else ""
                })
                
                # Verify and adjust word count if needed
                word_count = len(output.split())
                target_count = 1000 if is_detail_request else 500
                logger.debug("Initial summary word count: %d (target: %d)", word_count, target_count)
                
                if word_count < target_count * 0.7:  # If we're more than 30% short
                    logger.warning("Summary is too short (%d words), regenerating with stronger length requirement", word_count)
                    # Try again with stronger emphasis on length
                    output = await summary_chain.ainvoke({
                        "question": query,
                        "content": wiki_results,
                        "length": str(target_count),
                        "detail_instructions": f"""
                        CRITICAL: Your previous response was too short. Please provide a more detailed summary.
                        Since this is a request for more details, please:
                        1. Include more specific examples and facts
                        2. Provide deeper context and background information
                        3. Explain related concepts and their connections
                        4. Discuss implications and significance
                        5. Cover multiple aspects of the topic
                        6. Aim for approximately {target_count} words while maintaining quality
                        """ if is_detail_request else f"CRITICAL: Your previous response was too short. Please provide a more detailed summary of approximately {target_count} words."
                    })
                
                # Final verification of word count
                final_word_count = len(output.split())
                logger.debug("Final summary word count: %d (target: %d)", final_word_count, target_count)
                
                if final_word_count < target_count * 0.7:
                    logger.warning("Summary is still shorter than desired (%d words), but proceeding with response", final_word_count)
                    # Instead of returning an error, we'll proceed with the shorter response
                    output = f"{output}\n\nNote: This summary is shorter than requested but contains the most relevant information available."
            except Exception as e:
                logger.error("Error in research processing: %s", e)
                output = f"Error processing research request: {str(e)}"
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
