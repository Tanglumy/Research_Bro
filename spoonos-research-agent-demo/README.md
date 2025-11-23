# SpoonOS Research Agent Demo

This repository contains a simple, self-contained demonstration of a data analysis agent built using the [SpoonOS framework](https://github.com/XSpoonAi/spoon-core).

The agent, `MarketAnalystAgent`, is designed to answer questions about cryptocurrency prices by fetching live, off-chain data from a public API.

This demo illustrates several core concepts of SpoonOS:
- **Agentic Framework:** The agent uses an LLM to reason about a user's query and autonomously decide which tool to use.
- **Modular Tools:** The `CryptoPriceTool` is a custom, self-contained class that extends the agent's capabilities to a new data source.
- **Robust Error Handling:** The included `run_output.txt` shows the agent gracefully handling an external network error and providing a coherent response to the user.

## How to Run This Demo

### 1. Prerequisites
- Python 3.11+
- A valid OpenAI API key with credits and access to the `gpt-4-turbo` model.

### 2. Setup
1.  **Clone this repository:**
    ```bash
    git clone <your-repo-url>
    cd spoonos-research-agent-demo
    ```

2.  **Create a virtual environment:**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Install dependencies:**
    The `requirements.txt` file contains all necessary packages.
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure your API key:**
    - Copy the example `.env.example` file to a new file named `.env`.
      ```bash
      cp .env.example .env
      ```
    - Open the `.env` file and replace `YOUR_OPENAI_API_KEY` with your actual OpenAI API key.

### 3. Execution
Run the main script:
```bash
python main.py
```

### Expected Output
If the script can successfully connect to the external CoinCap API, you will see the agent fetch the price and provide a response similar to:

```
--- SpoonOS Data Analysis Sample ... ---
...
--- Tool Log: Fetching price for 'solana'...
--- Tool Log: Found price $162.55
...
--- Agent's Final Response ---
The current price of Solana is $162.55.
------------------------------
```

If the script's execution environment has a network or DNS issue (as demonstrated in `run_output.txt`), you will see the agent's robust error-handling capability:

```
--- SpoonOS Data Analysis Sample ... ---
...
--- Tool Log: An unexpected error occurred: [Errno 8] nodename nor servname provided, or not known
...
--- Agent's Final Response ---
I am currently unable to retrieve the price of Solana due to a technical issue...
------------------------------
```
