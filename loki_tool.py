# loki_tool.py
import os
import requests
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv
from langchain_core.tools import tool
from typing import Optional

load_dotenv()

LOKI_URL = os.getenv("LOKI_URL", "http://localhost:3100") # Default Loki URL

@tool
def query_loki_logs(
    query: str,
    time_range_minutes: int = 60,
    limit: int = 100,
    direction: str = "backward"
) -> str:
    """
    Queries logs from Grafana Loki using LogQL.

    Args:
        query (str): The LogQL query string. Examples:
                     - '{job="system_logs"}' to get all system logs.
                     - '{job="system_logs"} |= "error"' to filter for lines containing "error".
                     - '{app="nginx", level="error"} | json | status_code=~"5.."' to query specific app logs, parse JSON, and filter by status code.
                     - 'sum by (app) (count_over_time({job="system_logs"}[5m]))' for aggregation.
        time_range_minutes (int): How many minutes back from now to query. Default is 60 minutes.
        limit (int): Maximum number of log lines to return. Default is 100.
        direction (str): Order of logs, "forward" for oldest first, "backward" for newest first. Default is "backward".

    Returns:
        str: A JSON string of the log results, or an error message.
             If query is for streams, returns log lines. If for metrics, returns aggregated data.
             The output might be truncated if the limit is exceeded.
    """
    try:
        end_time_ns = datetime.now().timestamp() * 1e9
        start_time_ns = (datetime.now() - timedelta(minutes=time_range_minutes)).timestamp() * 1e9

        # Loki query_range API endpoint
        api_url = f"{LOKI_URL}/loki/api/v1/query_range"
        params = {
            "query": query,
            "limit": limit,
            "start": int(start_time_ns),
            "end": int(end_time_ns),
            "direction": direction,
            "interval": "1m" # For matrix queries (e.g., rate, count_over_time), allows step.
                             # For stream queries, it limits the resolution.
        }

        print(f"DEBUG: Making Loki API call to {api_url} with query: {query}, time_range_minutes: {time_range_minutes}, limit: {limit}")

        response = requests.get(api_url, params=params)
        response.raise_for_status() # Raise an HTTPError for bad responses (4xx or 5xx)

        data = response.json()

        # Check if the query returned a stream (log lines) or a matrix/vector (metrics)
        if data["data"]["resultType"] == "streams":
            if not data["data"]["result"]:
                return "No log streams found for the given query and time range."
            
            # Format stream results into a more readable string or JSON list
            formatted_logs = []
            for stream in data["data"]["result"]:
                labels = ", ".join([f'{k}="{v}"' for k, v in stream["stream"].items()])
                for entry in stream["values"]:
                    timestamp_ns = int(entry[0])
                    # Convert nanoseconds to datetime
                    dt_object = datetime.fromtimestamp(timestamp_ns / 1e9)
                    log_line = entry[1]
                    formatted_logs.append(f"[{dt_object.strftime('%Y-%m-%d %H:%M:%S')}] {{{labels}}} {log_line}")
            
            return json.dumps({"type": "streams", "logs": formatted_logs}, indent=2)

        elif data["data"]["resultType"] in ["matrix", "vector"]:
            if not data["data"]["result"]:
                return "No metric data found for the given query and time range."
            
            # Format matrix/vector results
            formatted_metrics = []
            for item in data["data"]["result"]:
                labels = ", ".join([f'{k}="{v}"' for k, v in item["metric"].items()])
                values = [{"timestamp": datetime.fromtimestamp(float(v[0])).strftime('%Y-%m-%d %H:%M:%S'), "value": v[1]} for v in item["values"]]
                formatted_metrics.append({"labels": labels, "values": values})
            
            return json.dumps({"type": "metrics", "data": formatted_metrics}, indent=2)
            
        else:
            return f"Loki query returned unsupported result type: {data['data']['resultType']}"

    except requests.exceptions.RequestException as e:
        return f"Error connecting to Loki or API error: {e}. Check if Loki is running at {LOKI_URL}."
    except json.JSONDecodeError:
        return f"Error: Loki returned invalid JSON response. Response: {response.text}"
    except Exception as e:
        return f"An unexpected error occurred: {e}"

# Example usage (for testing the tool directly)
if __name__ == "__main__":
    # Ensure Loki is running at http://localhost:3100
    print("--- Testing basic stream query ---")
    result = query_loki_logs(query='{job="system_logs"} |= "error"', time_range_minutes=10)
    print(result)

    print("\n--- Testing aggregated query (count errors over time) ---")
    # This requires Promtail to be sending logs to Loki and having some error logs.
    # Note: For `rate` or `count_over_time`, you generally need a range selector (e.g., [5m])
    # within the LogQL query itself for it to return a matrix.
    result_agg = query_loki_logs(query='sum by (filename) (count_over_time({job="system_logs"} |= "error" [5m]))', time_range_minutes=60, limit=10)
    print(result_agg)

    print("\n--- Testing non-existent query ---")
    result_no_data = query_loki_logs(query='{job="nonexistent_app"}', time_range_minutes=1)
    print(result_no_data)