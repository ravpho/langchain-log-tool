# agent.py
import os
from dotenv import load_dotenv
from langchain_openai import AzureChatOpenAI # <--- CHANGED IMPORT FOR AZURE
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from loki_tool import query_loki_logs # Your Loki tool remains the same

load_dotenv()

# --- 1. Initialize your Azure OpenAI LLM ---
# The model name here refers to your DEPLOYMENT NAME on Azure.
llm = AzureChatOpenAI(
    openai_api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
    azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    openai_api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    temperature=0, # Keep temperature low for factual tasks like log querying
    # model_name="gpt-4o" # This is often used internally for prompt templating, but Azure uses deployment name for actual API calls
)

# --- 2. Define the Tools available to the agent ---
tools = [query_loki_logs]

# --- 3. Create the Prompt Template for the Agent ---
# This remains largely the same, as the prompt structure is LLM-agnostic
# but ensure your SystemMessage guides the Azure OpenAI model effectively.
prompt = ChatPromptTemplate.from_messages(
    [
        SystemMessage(
            "You are an expert log analyst connected to Grafana Loki. "
            "Your task is to understand user questions about logs, translate them into accurate LogQL queries, "
            "and use the 'query_loki_logs' tool to fetch results. "
            "Always include relevant labels in your LogQL queries (e.g., {job=\"your_job_name\"}, {namespace=\"your_namespace\"}). "
            "If the user asks for a time range, use `time_range_minutes`. Default time range is 60 minutes. "
            "If the user asks for aggregations (like 'count', 'rate', 'sum', 'top N'), form a LogQL query that includes the appropriate Loki aggregation functions (e.g., `count_over_time`, `rate`, `sum by`). "
            "Always try to provide specific examples of what labels are available in the logs (e.g., 'system_logs', 'nginx_app') if you are unsure, or ask the user for more context. "
            "If a query returns too many results, consider refining the query with more specific labels or filters. "
            "Present the results clearly to the user, summarizing key findings. If no logs are found, state that clearly. "
            "Always respond in Markdown format for readability. Ensure any LogQL queries you construct are valid."
        ),
        HumanMessage(content="{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ]
)

# --- 4. Create the Tool-Calling Agent ---
agent = create_tool_calling_agent(llm, tools, prompt)

# --- 5. Create the Agent Executor ---
# verbose=True is highly recommended for debugging agent's thought process
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

# --- 6. Run the Agent (main interaction loop) ---
if __name__ == "__main__":
    print("--- Loki Log Query Agent (Azure OpenAI) ---")
    print("I can help you query logs from Grafana Loki using natural language.")
    print("Examples: ")
    print("  - 'Show me the last 100 system logs from the last 30 minutes.'")
    print("  - 'Find all error messages in nginx logs from yesterday.'")
    print("  - 'Count errors by application in the last hour.'")
    print("Type 'exit' to quit.")

    while True:
        user_input = input("\nYour query: ")
        if user_input.lower() == 'exit':
            print("Goodbye!")
            break

        try:
            result = agent_executor.invoke({"input": user_input})
            print("\n--- Agent Response ---")
            print(result["output"])
            print("----------------------")
        except Exception as e:
            print(f"\n--- An error occurred ---")
            print(f"Error: {e}")
            print("-------------------------")