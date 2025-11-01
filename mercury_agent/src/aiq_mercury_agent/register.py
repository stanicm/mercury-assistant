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

from nat.builder.builder import Builder
from nat.builder.framework_enum import LLMFrameworkEnum
from nat.cli.register_workflow import register_function
from nat.data_models.component_ref import FunctionRef
from nat.data_models.component_ref import LLMRef
from nat.data_models.function import FunctionBaseConfig

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

logger.propagate = False  # Prevent propagation to the root logger

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
    logger.info("[LLM_INIT] LLM type: %s", type(llm))
    logger.info("[LLM_INIT] LLM class: %s", llm.__class__.__name__)
    logger.info("[LLM_INIT] LLM module: %s", llm.__class__.__module__)
    
    # Test the LLM directly
    logger.debug("[LLM_TEST] Testing LLM with simple query...")
    from langchain_core.messages import HumanMessage
    test_response = await llm.ainvoke([HumanMessage(content="Say 'test' and nothing else.")])
    logger.debug("[LLM_TEST] Test response type: %s", type(test_response))
    logger.debug("[LLM_TEST] Test response has content: %s", hasattr(test_response, 'content'))
    if hasattr(test_response, 'content'):
        logger.debug("[LLM_TEST] Test response content: %s", repr(test_response.content))
    
    research_tool = await builder.get_tool(fn_name=config.research_tool, wrapper_type=LLMFrameworkEnum.LANGCHAIN)
    rag_tool = await builder.get_tool(fn_name=config.rag_tool, wrapper_type=LLMFrameworkEnum.LANGCHAIN)
    chitchat_agent = await builder.get_tool(fn_name=config.chitchat_agent, wrapper_type=LLMFrameworkEnum.LANGCHAIN)

    chat_hist = ChatMessageHistory()

    # Define the routing prompt for classifying user queries
    router_prompt = """/no_think

You are a classifier. Your ONLY job is to output ONE word: Research, Retrieve, or General.

Classification rules:
- Research: Questions about people, places, history, science, or any factual topic
- Retrieve: Questions about SPH (Smoothed Particle Hydrodynamics) only
- General: Greetings, chitchat, math, or anything else

User query: {input}

Classification:"""  # noqa: E501

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
        
        print(f"\n========== ROUTER DEBUG ==========")
        print(f"1. User query: '{query}'")
        
        # Format the prompt to see what will be sent
        formatted_prompt = router_prompt.format(input=query)
        print(f"2. Formatted prompt being sent to model:")
        print(f"---")
        print(formatted_prompt)
        print(f"---")
        
        try:
            raw_response = (await supervisor_chain_with_message_history.ainvoke(
                {"input": query},
                {"configurable": {
                    "session_id": "unused"
                }},
            ))
            
            print(f"3. Raw response from model: '{raw_response}'")
            print(f"4. Type of response: {type(raw_response)}")
            print(f"5. Response repr: {repr(raw_response)}")
            
            # Extract just the classification word from the response
            # The model might output reasoning, so we need to find the actual classification
            response_lower = raw_response.lower().strip()
            
            # Look for the classification words in the response
            if 'general' in response_lower.split()[-10:]:  # Check last 10 words
                chosen_agent = 'general'
            elif 'research' in response_lower.split()[-10:]:
                chosen_agent = 'research'
            elif 'retrieve' in response_lower.split()[-10:]:
                chosen_agent = 'retrieve'
            else:
                # If we can't find a clear match, try to get the last word
                words = response_lower.split()
                last_word = words[-1] if words else ''
                if last_word in ['general', 'research', 'retrieve']:
                    chosen_agent = last_word
                else:
                    # Default to general for chitchat if unclear
                    chosen_agent = 'general'
                    print(f"⚠️  Could not find clear classification, defaulting to: {chosen_agent}")
            
            print(f"6. Extracted classification: '{chosen_agent}'")
            print(f"========== END ROUTER DEBUG ==========\n")
            
            logger.debug("Supervisor classified query as: %s", chosen_agent)
        except Exception as e:
            logger.error("Error in supervisor classification: %s", str(e))
            # Default to research agent if classification fails
            chosen_agent = "research"
            logger.info("Defaulting to research agent due to classification error")

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
            print(f"\n========== RESEARCH AGENT DEBUG ==========")
            print(f"1. Query received: '{query}'")
            try:
                # Get the Wikipedia page content and URL
                print(f"2. Calling Wikipedia search...")
                wiki_results = await research_tool.ainvoke(query)
                print(f"3. Wikipedia returned {len(wiki_results)} characters")
                print(f"4. First 300 chars: {wiki_results[:300]}")
                print(f"5. Last 100 chars: {wiki_results[-100:]}")
                
                # Create a prompt for summarizing Wikipedia results
                summary_prompt = PromptTemplate.from_template("""
                You are a helpful AI assistant. Your task is to summarize and then analyze the information in the found Wikipedia content and provide a clear response to the user's query.
                {detail_instructions}
                Do this in steps:
                First, focus on providing a comprehensive and informative summary that directly addresses the main topic of user's query.
                Include relevant details, examples, and key points from the content.
                Maintain a natural flow and ensure all information is accurate and well-organized.
                Make sure to complete all sentences and paragraphs - do not cut off mid-sentence.
                Second step: analyze the user query and realize if it is appropriate to provide an answer derived from the page or just provide a summary.
                Example 1: Tell me something about Batman. - you provide a simple summary.
                Example 2: What is the name of Batman's sidekick? - you find Batman's Wikipedia page, read through the content and provide the answer - Robin.
                Example 3: Do you know anything about Belgrade, Serbia? - you provide a simple summary.
                Example 4: When was Belgrade liberated in second world war? - you find the page of Belgrade, Serbia and provide the answer - 1944.
                Example 5: What can you tell me about Led Zeppelin? - you provide a simple summary.
                Example 6: Who was the guitarist of Led Zeppelin? - you find the page of Led Zeppelin and provide the answer - Jimmy Page.
                Do not include any meta-commentary or notes about the summary itself.
                Do not mention the word count in your response.
                Do not add any disclaimers or notes about the content.

                User Query: {query}

                Wikipedia Content:
                {content}

                Summary:""")

                # Create a chain for summarizing the content
                summary_chain = summary_prompt | llm

                # Process the research results
                try:
                    # First, check if the user is asking for more details
                    detail_prompt = PromptTemplate.from_template("""
                    Analyze if the following query is asking for more details or elaboration.
                    Return ONLY 'yes' or 'no'.

                    Query: {query}
                    Response:""")

                    detail_chain = detail_prompt | llm

                    try:
                        detail_response = await detail_chain.ainvoke({"query": query})
                        # Extract text content from AIMessage if needed
                        detail_text = str(detail_response.content) if hasattr(detail_response, 'content') else str(detail_response)
                        is_detail_request = detail_text.lower().strip() == 'yes'
                        logger.debug("Detail detection response: %s", detail_text)
                    except Exception as e:
                        logger.warning("Error in detail detection: %s", str(e))
                        # Default to detailed response if we can't determine
                        is_detail_request = True

                    # Determine the length and instructions based on whether it's a detail request
                    if is_detail_request:
                        target_length = 1000
                        detail_instructions = "The summary MUST be EXACTLY 1000 words long - this is a strict requirement. Provide a comprehensive and detailed summary."
                    else:
                        target_length = 250
                        detail_instructions = "The summary MUST be EXACTLY 300 words long - this is a strict requirement. Provide a concise summary focusing on key points."

                    logger.info("Target summary length: %d words", target_length)

                    print(f"6. Calling LLM to summarize...")
                    print(f"7. LLM will receive {len(wiki_results)} chars of Wikipedia content")
                    
                    summary = await summary_chain.ainvoke({
                        "query": query,
                        "content": wiki_results,
                        "length": target_length,
                        "detail_instructions": detail_instructions
                    })

                    print(f"8. LLM returned. Type: {type(summary)}")
                    print(f"9. Has 'content' attribute: {hasattr(summary, 'content')}")
                    
                    if hasattr(summary, 'content'):
                        print(f"10. summary.content type: {type(summary.content)}")
                        print(f"11. summary.content length: {len(str(summary.content))} chars")
                        print(f"12. summary.content value: '{summary.content}'")
                    else:
                        print(f"10. No 'content' attr. Full summary: {summary}")

                    # Extract text content from AIMessage if needed
                    summary_text = str(summary.content) if hasattr(summary, 'content') else str(summary)
                    print(f"13. Final summary_text length: {len(summary_text)} chars")
                    print(f"14. Final summary_text: '{summary_text}'")
                    print(f"========== END DEBUG ==========\n")

                    # Log the word count for monitoring
                    word_count = len(summary_text.split())
                    logger.info("[SUMMARIZE] Generated summary length: %d words", word_count)
                    logger.info("[SUMMARIZE] Summary text: %s", summary_text[:500])

                    # Return a dictionary with the required state fields
                    return {
                        'input': query,
                        'chosen_worker_agent': worker_choice,
                        'chat_history': chat_hist,
                        'final_output': summary_text
                    }

                except Exception as e:
                    logger.error("Error processing research results: %s", str(e))
                    return {
                        'input': query,
                        'chosen_worker_agent': worker_choice,
                        'chat_history': chat_hist,
                        'final_output': f"Error: {str(e)}"
                    }
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
