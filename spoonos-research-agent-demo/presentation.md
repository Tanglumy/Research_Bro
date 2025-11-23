# SpoonOS Research Agent: Crypto Price Analysis (Sample Demo)

## Slide 1: What We Built - A Foundational Research Agent

### **Goal:** Fetch real-time cryptocurrency prices using SpoonOS's agentic capabilities.

*   **User Query:** "What is the price of Solana right now?"
*   **AI Agent (MarketAnalystAgent) Process:**
    1.  **Understand Intent:** LLM interprets the query as a request for price information.
    2.  **Tool Selection:** Agent identifies `get_crypto_price` tool as relevant.
    3.  **Parameter Extraction:** Agent extracts `asset_id='solana'` for the tool.
    4.  **Tool Execution:** `CryptoPriceTool` attempts to fetch data from CoinCap API.
    5.  **Result & Synthesis:** (In a successful run) Tool returns price; LLM synthesizes into natural language.

---

## Slide 2: Leveraging SpoonOS Strengths

### **This simple sample highlights core SpoonOS advantages for building complex Research Agents:**

*   **1. Modular Tools & Data Access (via MCP Abstraction):**
    *   We created `CryptoPriceTool` – a custom "plugin" to access an **off-chain** data source (CoinCap API).
    *   **SpoonOS strength:** The underlying Model Context Protocol (MCP) allows seamless integration of diverse data sources. We could easily add tools for:
        *   **Web3 Data (On-chain):** Querying Neo blockchain RPC for transaction volumes, smart contract states (e.g., `GetTransactionCountTool` as seen in examples).
        *   **Other Off-chain Data:** Social media sentiment APIs, news feeds, traditional market data.

*   **2. Agentic Framework & Autonomous Reasoning:**
    *   The `MarketAnalystAgent` doesn't follow rigid instructions; it *reasons* about the user's intent and *autonomously decides* which tool to use.
    *   **SpoonOS strength:** Provides the ReAct-style architecture where LLMs act as the "brain," orchestrating tool use, contextual understanding (via BeVec), and response generation. This is crucial for a "Research Agent" that needs to explore and synthesize information dynamically.

*   **3. Coherence with "Research Agent" & Graph Workflows:**
    *   This price-fetching agent is a fundamental building block.
    *   **SpoonOS strength:** In a larger "Research Agent" system, this agent could be one **node in a graph-based workflow**. For example:
        *   **Node 1 (Our Agent):** Fetches crypto prices.
        *   **Node 2 (New Agent):** Analyzes price trends, perhaps integrating **on-chain data** like trading volume from a blockchain explorer tool.
        *   **Node 3 (New Agent):** Cross-references with **off-chain data** like news sentiment to provide a comprehensive market report.
    *   This modularity and orchestration enable highly complex, multi-source, multi-step research.

---

## Slide 3: Next Steps for a Comprehensive Research Agent

### **Building upon this foundation:**

*   **Integrate Web3 Data Tools:** Develop new `BaseTool` implementations to interact directly with blockchain data (e.g., using `web3.py` or Neo-specific SDKs). This connects our agent to the core of Web3.
*   **Expand Off-chain Sources:** Add tools for web search, social media monitoring, or specific data APIs relevant to research.
*   **Complex Workflow Orchestration:** Design multi-agent workflows using SpoonOS's graph capabilities. Imagine an agent that automatically:
    1.  Identifies trending tokens (off-chain news).
    2.  Retrieves their on-chain activity (Web3 data).
    3.  Compares against historical data (BeVec).
    4.  Generates a concise research summary.

---
