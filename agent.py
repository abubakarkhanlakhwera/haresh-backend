from agents import WebSearchTool, Agent, ModelSettings, RunContextWrapper, TResponseInputItem, Runner, RunConfig, trace
from pydantic import BaseModel
from openai.types.shared.reasoning import Reasoning
from typing import List, Dict

# Tool definitions
web_search_preview = WebSearchTool(
  search_context_size="medium",
  user_location={
    "country": "AU",
    "type": "approximate"
  }
)
class ClassifierSchema(BaseModel):
  intent: str


classifier = Agent(
  name="classifier",
  instructions="""Goal: Determine whether the user’s question is about current public health trends or general health explanations.
Categories:
trend_query → The user asks about how things are going now / recently / this season / in a specific region or date (e.g., “How bad is flu this year?”, “Is COVID rising in Europe?”, “What are this week’s measles cases?”).
general_info → The user asks about concepts, definitions, comparisons, or non-time-sensitive info (e.g., “What is RSV?”, “How does flu spread?”, “Symptoms of malaria”).
Rules:
If the question mentions “this week”, “latest”, “today”, “season”, “trend”, “cases”, or numbers, classify as trend_query.
If it’s purely explanatory, classify as general_info.
If both appear, prefer trend_query.""",
  model="gpt-5-nano",
  output_type=ClassifierSchema,
  model_settings=ModelSettings(
    store=True,
    reasoning=Reasoning(
      effort="low",
      summary="auto"
    )
  )
)


class TrendQueryContext:
  def __init__(self, workflow_input_as_text: str):
    self.workflow_input_as_text = workflow_input_as_text
def trend_query_instructions(run_context: RunContextWrapper[TrendQueryContext], _agent: Agent[TrendQueryContext]):
  workflow_input_as_text = run_context.context.workflow_input_as_text
  return f"""Goal: Retrieve the most recent, trustworthy data about the public-health topic mentioned by the user.
Instructions to the model:
Search authoritative and official public-health sources only (CDC, WHO, ECDC, UKHSA, government health departments, etc.).
Prioritize recent data (past 30 days unless a longer range is explicitly asked).
Extract the following details:
Metric: infection rates, case counts, positivity rate, hospitalizations, etc.
Time range: make sure to include the latest week or report date.
Region or country (default to global or the user’s mentioned region).
Source and date of the information.
If multiple regions or diseases are mentioned, summarize each in a short section.
If no official data exists for the last 30 days, clearly state that and cite the most recent verified report.
Avoid giving medical advice or recommendations—report data only. {workflow_input_as_text}"""
trend_query = Agent(
  name="trend query",
  instructions=trend_query_instructions,
  model="gpt-5-nano",
  tools=[
    web_search_preview
  ],
  model_settings=ModelSettings(
    store=True,
    reasoning=Reasoning(
      effort="low",
      summary="auto"
    )
  )
)


class AgentContext:
  def __init__(self, workflow_input_as_text: str):
    self.workflow_input_as_text = workflow_input_as_text
def agent_instructions(run_context: RunContextWrapper[AgentContext], _agent: Agent[AgentContext]):
  workflow_input_as_text = run_context.context.workflow_input_as_text
  return f"""Goal: Provide a clear, easy-to-understand explanation of a public-health concept or question.
Instructions to the model:
Answer in plain English, suitable for everyday readers (no jargon).
Explain what the term, concept, or phenomenon means (e.g., “What is RSV?”, “How do vaccines work?”).
If relevant, describe:
Causes or mechanisms (briefly)
Why it matters for public health
How it’s monitored or measured
Include context when helpful (e.g., when the disease was first identified, global impact, etc.).
If data is mentioned, make clear it’s for illustration only, not current statistics.
Avoid giving medical or treatment advice — redirect to a healthcare provider if the user asks something personal.
If relevant, include reputable educational sources (WHO, CDC, NHS, etc.). {workflow_input_as_text}"""
agent = Agent(
  name="Agent",
  instructions=agent_instructions,
  model="gpt-5-nano",
  tools=[
    web_search_preview
  ],
  model_settings=ModelSettings(
    store=True,
    reasoning=Reasoning(
      effort="low",
      summary="auto"
    )
  )
)


agent1 = Agent(
  name="Agent",
  instructions="",
  model="gpt-5-nano",
  model_settings=ModelSettings(
    store=True,
    reasoning=Reasoning(
      effort="low",
      summary="auto"
    )
  )
)


class WorkflowInput(BaseModel):
  input_as_text: str


# Main code entrypoint
async def run_workflow(workflow_input: WorkflowInput):
  with trace("New workflow"):
    state = {

    }
    workflow = workflow_input.model_dump()
    conversation_history: list[TResponseInputItem] = [
      {
        "role": "user",
        "content": [
          {
            "type": "input_text",
            "text": workflow["input_as_text"]
          }
        ]
      }
    ]
    classifier_result_temp = await Runner.run(
      classifier,
      input=[
        *conversation_history
      ],
      run_config=RunConfig(trace_metadata={
        "__trace_source__": "agent-builder",
        "workflow_id": "wf_6906f893bcd481909e88c4931d8b68d0012920c3898990bf"
      })
    )

    conversation_history.extend([item.to_input_item() for item in classifier_result_temp.new_items])

    classifier_result = {
      "output_text": classifier_result_temp.final_output.json(),
      "output_parsed": classifier_result_temp.final_output.model_dump()
    }
    if classifier_result["output_parsed"]["intent"] == "trend_query":
      trend_query_result_temp = await Runner.run(
        trend_query,
        input=[
          *conversation_history
        ],
        run_config=RunConfig(trace_metadata={
          "__trace_source__": "agent-builder",
          "workflow_id": "wf_6906f893bcd481909e88c4931d8b68d0012920c3898990bf"
        }),
        context=TrendQueryContext(workflow_input_as_text=workflow["input_as_text"])
      )

      conversation_history.extend([item.to_input_item() for item in trend_query_result_temp.new_items])

      trend_query_result = {
        "output_text": trend_query_result_temp.final_output_as(str)
      }
    elif classifier_result["output_parsed"]["intent"] == "general_info":
      agent_result_temp = await Runner.run(
        agent,
        input=[
          *conversation_history
        ],
        run_config=RunConfig(trace_metadata={
          "__trace_source__": "agent-builder",
          "workflow_id": "wf_6906f893bcd481909e88c4931d8b68d0012920c3898990bf"
        }),
        context=AgentContext(workflow_input_as_text=workflow["input_as_text"])
      )

      conversation_history.extend([item.to_input_item() for item in agent_result_temp.new_items])

      agent_result = {
        "output_text": agent_result_temp.final_output_as(str)
      }
    else:
      agent_result_temp = await Runner.run(
        agent1,
        input=[
          *conversation_history
        ],
        run_config=RunConfig(trace_metadata={
          "__trace_source__": "agent-builder",
          "workflow_id": "wf_6906f893bcd481909e88c4931d8b68d0012920c3898990bf"
        })
      )

      conversation_history.extend([item.to_input_item() for item in agent_result_temp.new_items])

      agent_result = {
        "output_text": agent_result_temp.final_output_as(str)
      }


# ChatAgent wrapper class for FastAPI integration
class ChatAgent:
    """
    Wrapper class for the medical assistant agent.
    Handles disease information queries with web search capabilities.
    """
    
# ChatAgent wrapper class for FastAPI integration
class ChatAgent:
    """
    Wrapper class for the medical assistant agent.
    Handles disease information queries with web search capabilities.
    """
    
    async def get_response(self, message: str, history: List[Dict[str, str]] = None) -> str:
        """
        Get a response from the agent based on user message and conversation history.
        
        Args:
            message: User's query
            history: Previous conversation messages (optional)
            
        Returns:
            Agent's response as a string
        """
        try:
            print(f"[DEBUG] ChatAgent.get_response called with message: {message}")
            
            # Use the existing run_workflow function
            workflow_input = WorkflowInput(input_as_text=message)
            print(f"[DEBUG] Created workflow_input: {workflow_input}")
            
            # Run the workflow (this doesn't return anything, it modifies state)
            await run_workflow(workflow_input)
            print(f"[DEBUG] run_workflow completed, but it doesn't return a value")
            
            # The issue is that run_workflow doesn't return anything!
            # Let's run the agents directly instead
            print(f"[DEBUG] Running agents directly...")
            
            with trace("Chat response"):
                conversation_history: list[TResponseInputItem] = [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "input_text",
                                "text": message
                            }
                        ]
                    }
                ]
                
                # First classify the query
                print(f"[DEBUG] Step 1: Classifying message")
                classifier_result_temp = await Runner.run(
                    classifier,
                    input=conversation_history,
                    run_config=RunConfig(trace_metadata={
                        "__trace_source__": "api",
                        "workflow_id": "chat_api"
                    })
                )
                
                print(f"[DEBUG] Classifier completed")
                print(f"[DEBUG] classifier_result_temp type: {type(classifier_result_temp)}")
                print(f"[DEBUG] classifier_result_temp.new_items: {len(classifier_result_temp.new_items) if hasattr(classifier_result_temp, 'new_items') else 'N/A'}")
                
                # Don't add classifier output to conversation history for the next agent
                # conversation_history.extend([item.to_input_item() for item in classifier_result_temp.new_items])
                
                classifier_result = classifier_result_temp.final_output.model_dump()
                print(f"[DEBUG] Step 2: Classifier result: {classifier_result}")
                intent = classifier_result.get("intent", "general_info")
                print(f"[DEBUG] Intent: {intent}")
                
                # Route based on intent
                print(f"[DEBUG] Step 3: Routing to appropriate agent")
                if intent == "trend_query":
                    print("[DEBUG] Routing to trend_query agent")
                    result_temp = await Runner.run(
                        trend_query,
                        input=conversation_history,  # Use original conversation without classifier output
                        run_config=RunConfig(trace_metadata={
                            "__trace_source__": "api",
                            "workflow_id": "chat_api"
                        }),
                        context=TrendQueryContext(workflow_input_as_text=message)
                    )
                elif intent == "general_info":
                    print("[DEBUG] Routing to general_info agent")
                    result_temp = await Runner.run(
                        agent,
                        input=conversation_history,  # Use original conversation without classifier output
                        run_config=RunConfig(trace_metadata={
                            "__trace_source__": "api",
                            "workflow_id": "chat_api"
                        }),
                        context=AgentContext(workflow_input_as_text=message)
                    )
                else:
                    print("[DEBUG] Routing to default agent")
                    result_temp = await Runner.run(
                        agent1,
                        input=conversation_history,
                        run_config=RunConfig(trace_metadata={
                            "__trace_source__": "api",
                            "workflow_id": "chat_api"
                        })
                    )
                
                print(f"[DEBUG] Step 4: Agent completed, extracting response")
                print(f"[DEBUG] Result type: {type(result_temp)}")
                
                # Extract the final text response
                try:
                    response = result_temp.final_output_as(str)
                    print(f"[DEBUG] SUCCESS: Extracted response: {response[:200]}..." if len(response) > 200 else f"[DEBUG] SUCCESS: Extracted response: {response}")
                    return response
                except Exception as e1:
                    print(f"[DEBUG] final_output_as(str) failed: {e1}")
                    # Try alternative extraction methods
                    try:
                        if hasattr(result_temp, 'new_items') and result_temp.new_items:
                            print(f"[DEBUG] Trying to extract from new_items (count: {len(result_temp.new_items)})")
                            last_item = result_temp.new_items[-1]
                            print(f"[DEBUG] Last item type: {type(last_item)}")
                            print(f"[DEBUG] Last item: {last_item}")
                            
                            if hasattr(last_item, 'content'):
                                response = str(last_item.content)
                            elif hasattr(last_item, 'text'):
                                response = str(last_item.text)
                            else:
                                response = str(last_item)
                            print(f"[DEBUG] Extracted from new_items: {response}")
                            return response
                        else:
                            print(f"[DEBUG] No new_items, converting result_temp to string")
                            response = str(result_temp)
                            print(f"[DEBUG] String conversion: {response}")
                            return response
                    except Exception as e2:
                        print(f"[ERROR] All extraction methods failed: {e2}")
                        return "I encountered an error processing your request. Please try again."
                
        except Exception as e:
            print(f"[ERROR] ChatAgent error: {str(e)}")
            import traceback
            traceback.print_exc()
            raise Exception(f"Error in ChatAgent: {str(e)}")
