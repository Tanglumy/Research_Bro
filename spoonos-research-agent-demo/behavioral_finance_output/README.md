# Behavioral Finance Analysis with SpoonOS

## Overview

This project implements a sophisticated behavioral finance analysis system using SpoonOS's graph orchestration and MCP (Model Context Protocol) capabilities. The system tests the hypothesis that market conditions are driving panic behavior among traders.

## 📊 Generated Outputs

### Current Analysis (2025-11-22 21:47:12)
- **Dashboard**: `behavioral_finance_dashboard_20251122_214712.png` (367KB)
- **Data**: `analysis_data_20251122_214712.json` (976 bytes)

### Analysis Results Summary
- **Token**: ETH
- **Market**: $3676.00 (+11.00%, 276M volume)
- **Narrative**: HYPE - Major partnership announcement
- **Hypothesis**: REJECTED (No panic behavior detected)

## 🎯 Core Hypothesis

**Primary Hypothesis**: *"Current market conditions are driving panic behavior among traders"*

### Validation Logic
- **SUPPORTS**: If Panic Seller sells AND Smart Money buys → panic behavior confirmed
- **REJECTS**: Any other combination → no clear panic behavior

## 📈 Data Architecture

### 1. Market Data (Node 1: Market Reality Analysis)
```
Input: Token symbol (e.g., "ETH")
Output: Price, 24h change %, 24h volume
Source: Simulated hash-based data → Production: OKX/Crypto APIs
Purpose: Quantify market volatility and direction
```

### 2. Narrative Data (Node 2: Offchain Narrative Analyst)
```
Input: Market condition from Node 1
Output: Sentiment classification (FUD/HYPE/NEUTRAL)
Source: Rule-based logic → Production: Tavily MCP news search
Purpose: Understand what's driving market movements
```

### 3. Simulation Data (Node 3: Synthetic Participant Simulator)
```
Input: Market + Narrative data
Output: Agent actions (Panic Seller vs Smart Money)
Source: Behavioral models
Purpose: Model how different trader personas react
```

### 4. Validation Data (Node 4: Hypothesis Checker)
```
Input: All previous node outputs
Output: Hypothesis verdict with reasoning
Source: Logic-based validation
Purpose: Determine if hypothesis is supported/rejected
```

## 🔄 SpoonOS Components Usage

### StateGraph (Orchestration Engine)
```python
workflow = StateGraph(BehavioralFinanceState)
```
- **Purpose**: Manages state flow between agents
- **State Type**: `BehavioralFinanceState` (shared memory)
- **Flow**: Linear pipeline with error handling
- **Benefits**: Async execution, checkpointing, state management

### Agent Architecture
- **Framework**: SpoonReactMCP
- **Production Tools**:
  - `CryptoPowerDataCEXTool` for market data
  - `MCPTool` with Tavily for news search
- **Current**: Simplified implementation (no external API dependencies)

### MCP Integration (Model Context Protocol)
```python
tavily_tool = MCPTool(
    name="tavily-search",
    mcp_config={
        "command": "npx",
        "args": ["-y", "tavily-mcp"],
        "env": {"TAVILY_API_KEY": os.getenv("TAVILY_API_KEY")}
    }
)
```
- **Purpose**: Standardized tool interface across AI agents
- **Benefits**: Tool discovery, parameter validation, async execution

## 📊 Visualizations Dashboard

The generated dashboard contains 5 panels:

### Panel 1: Market Conditions Gauge
- Visual representation of price changes
- Color-coded performance (Green: +, Red: -, Yellow: neutral)
- Current price, 24h change, and volume display

### Panel 2: Narrative Analysis
- Sentiment classification (FUD/HYPE/NEUTRAL)
- Color-coded sentiment strength
- Narrative context excerpt

### Panel 3: Trader Simulation
- Persona A: "Panic Seller" actions and reasoning
- Persona B: "Smart Money" actions and reasoning
- Color-coded actions (Buy: Green, Sell: Red, Hold: Yellow)

### Panel 4: Hypothesis Validation
- Clear SUPPORTED/REJECTED verdict
- Symbol indication (✓ for supported, ✗ for rejected)
- Key behavioral findings

### Panel 5: Analysis Flow Diagram
- Visual representation of the 4-node pipeline
- State annotations showing data flow
- Connection arrows between processing stages

## 🗂️ File Structure

```
behavioral_finance_output/
├── README.md                           # This file
├── behavioral_finance_dashboard_*.png  # Visual analysis dashboard
└── analysis_data_*.json               # Complete analysis data
```

## 🚀 Production Setup

To deploy this with real data sources:

### 1. Environment Configuration
```bash
# .env file
OPENAI_API_KEY=your_openai_key
OKX_API_KEY=your_okx_api_key
OKX_SECRET_KEY=your_okx_secret
OKX_PASSPHRASE=your_okx_passphrase
TAVILY_API_KEY=your_tavily_key
```

### 2. Real Data Integration
```python
# Replace simulated data with:
# - OKX API for market data
# - Tavily MCP for news search
# - OpenAI GPT-4 for LLM simulation
```

### 3. Tool Configuration
```python
# Production tools configuration
crypto_tool = CryptoPowerDataCEXTool()
tavily_tool = MCPTool(...)  # As shown above
```

## 🔧 Technical Implementation

### Key Dependencies
- **SpoonOS**: Graph orchestration and agent framework
- **MCP**: Model Context Protocol for tool integration
- **python-dotenv**: Environment variable management
- **matplotlib/seaborn**: Data visualization
- **asyncio**: Asynchronous execution

### State Management
```python
class BehavioralFinanceState(TypedDict):
    token: str                  # Asset to analyze
    market_condition: dict      # Price, volume, change data
    narrative_context: str      # Sentiment analysis
    simulation_results: dict    # Trader behavior simulation
    hypothesis_verdict: str     # Final validation result
    execution_timestamp: str    # Analysis timestamp
```

## 📈 Example Analysis Walkthrough

1. **Input**: ETH token analysis request
2. **Market Data**: $3676.00 (+11.00%, 276M volume)
3. **Narrative**: HYPE scenario detected from positive price action
4. **Simulation**:
   - Panic Seller: Buy (FOMO from positive news)
   - Smart Money: Hold (Taking profits)
5. **Validation**: Hypothesis REJECTED (no panic behavior)
6. **Visualization**: Dashboard generated with all insights

## 🔬 Research Applications

This system can be used for:
- **Academic Research**: Behavioral finance hypothesis testing
- **Trading Analysis**: Market sentiment and trader psychology
- **Risk Management**: Panic detection and early warning systems
- **Market Research**: Narrative-driven price analysis

## 📞 Contact and Support

Built with SpoonOS framework - enabling sophisticated AI agent orchestration for blockchain and financial analysis.

For questions about the implementation or deployment, refer to the SpoonOS documentation or the analysis data JSON files for complete traceability of the decision-making process.