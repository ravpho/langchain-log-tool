# Loki Log Query Agent with LangChain

A powerful tool that enables natural language querying of Grafana Loki logs using LangChain and Ollama's LLM. This project allows you to interact with your Loki instance using plain English, automatically translating your questions into LogQL queries.

## Features

- Natural language to LogQL translation
- Integration with Grafana Loki
- Support for complex log queries and aggregations
- Configurable time ranges and result limits
- Clean, markdown-formatted output
- Easy setup with Ollama for local LLM processing

## Prerequisites

- Python 3.8+
- Grafana Loki instance
- Ollama (for local LLM processing)
- Required Python packages (see [Installation](#installation))

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/langchain-log-tool.git
   cd langchain-log-tool
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install the required packages:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   Create a `.env` file in the project root with the following variables:
   ```
   LOKI_URL=http://your-loki-server:3100
   OLLAMA_BASE_URL=http://localhost:11434
   ```

5. Pull the Ollama model (if not already done):
   ```bash
   ollama pull llama3.2
   ```

## Usage

1. Run the agent:
   ```bash
   python agent.py
   ```

2. Enter your log query in natural language, for example:
   - "Show me error logs from the last hour"
   - "Count the number of 5xx errors in the last 30 minutes"
   - "What's the rate of requests per minute for the nginx service?"

## Configuration

### Environment Variables

- `LOKI_URL`: URL of your Loki instance (default: `http://localhost:3100`)
- `OLLAMA_BASE_URL`: URL of your Ollama server (default: `http://localhost:11434`)

### Customizing the LLM

Edit the `llm` initialization in `agent.py` to use a different model or adjust parameters:
```python
llm = ChatOllama(
    model="llama3.2",  # Change to your preferred model
    temperature=0,
    base_url=os.getenv("OLLAMA_BASE_URL")
)
```

## Project Structure

- `agent.py`: Main application script with the LangChain agent setup
- `loki_tool.py`: Tool implementation for querying Loki
- `.env.example`: Example environment variables (copy to `.env` and fill in your values)
- `requirements.txt`: Python dependencies

## Acknowledgments

- [LangChain](https://www.langchain.com/) for the agent framework
- [Ollama](https://ollama.ai/) for local LLM processing
- [Grafana Loki](https://grafana.com/oss/loki/) for log aggregation
