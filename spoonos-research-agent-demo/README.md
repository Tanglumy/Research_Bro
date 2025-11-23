# 🧠 SpoonOS Research Agent Demo: Behavioral Finance Analysis

> **A sophisticated AI-powered system that tests market psychology hypotheses using SpoonOS graph orchestration and MCP integration**

## 🎯 Demo Overview

This demo showcases how SpoonOS enables the creation of advanced research agents that combine Web3 data, MCP (Model Context Protocol) tools, and graph orchestration to solve complex financial research problems.

### **Core Research Question**
> *"Are market conditions driving panic behavior among traders?"*

---

## 🚀 Key Features Demonstrated

### **🔄 SpoonOS StateGraph Orchestration**
- **Multi-agent coordination** with shared state management
- **4-agent pipeline**: Market → Narrative → Simulation → Validation
- **Error handling** and async execution capabilities

### **🛠️ MCP Integration**
- **Standardized tool interfaces** across AI agents
- **Seamless crypto API integration** (OKX, Tavily)
- **Real-time data** from multiple Web3 sources

### **🌐 Web3 Data Capabilities**
- **Market Data**: OKX, Binance, crypto exchanges
- **Sentiment Analysis**: News search and social media
- **Blockchain Analytics**: On-chain data integration ready

---

## 📊 Demo Files

### **Core Implementations**
- **`behavioral_finance_agent.py`** - Original implementation with MCP tools
- **`behavioral_finance_agent_fixed.py`** - Simplified version for testing
- **`behavioral_finance_agent_visual.py`** - Enhanced version with visualizations

### **Analysis Outputs**
- **`behavioral_finance_output/`** - Generated analysis results and dashboards
  - **Dashboard** - 5-panel visualization with market gauges
  - **Data JSON** - Complete analysis traceability
  - **Presentations** - 1-minute demo presentation deck

### **Configuration**
- **`.env`** - Environment variables and API keys template

---

## 🏃‍♂️ Quick Start

### **1. Clone and Navigate**
```bash
git clone https://github.com/Tanglumy/Research_Bro.git
cd Research_Bro/spoonos-research-agent-demo
```

### **2. Set Up Environment**
```bash
# Edit environment file
nano .env

# Add your API keys
OPENAI_API_KEY=your_openai_key
OKX_API_KEY=your_okx_api_key
OKX_SECRET_KEY=your_okx_secret
OKX_PASSPHRASE=your_okx_passphrase
TAVILY_API_KEY=your_tavily_key
```

### **3. Run the Demo**
```bash
# Basic version (no API keys required)
python behavioral_finance_agent_fixed.py

# Enhanced version with visualizations
python behavioral_finance_agent_visual.py
```

---

## 📈 Demo Results (ETH Analysis)

### **Market Conditions Analyzed:**
- **Token**: ETH (Ethereum)
- **Price**: $3,676.00 (+11.00%)
- **Volume**: 276M
- **Narrative**: HYPE - Major partnership announcements

### **Behavioral Simulation:**
- **Panic Seller**: BUY (FOMO from positive news)
- **Smart Money**: HOLD (Taking profits, waiting for better entry)

### **Scientific Verdict:**
## ❌ HYPOTHESIS REJECTED
*No panic behavior detected in current market conditions*

---

## 🎨 Visualization Dashboard

The demo generates a comprehensive 5-panel dashboard:

1. **Market Conditions Gauge** - Price visualization with color coding
2. **Narrative Analysis** - Sentiment classification (FUD/HYPE/NEUTRAL)
3. **Trader Simulation** - Persona actions and reasoning
4. **Hypothesis Validation** - Clear SUPPORTED/REJECTED verdict
5. **Analysis Flow** - Visual pipeline diagram with state annotations

### **Sample Output:**
- **Dashboard**: `behavioral_finance_output/behavioral_finance_dashboard_*.png`
- **Data**: `behavioral_finance_output/analysis_data_*.json`

---

## 🛠️ Technical Architecture

### **SpoonOS Components Utilized**
```python
# StateGraph for multi-agent orchestration
from spoon_ai.graph import StateGraph

# MCP integration for standardized tools
from spoon_ai.tools.mcp_tool import MCPTool
from spoon_ai.agents.spoon_react_mcp import SpoonReactMCP

# Web3 data integration tools
from spoon_ai.tools.crypto_tools import get_crypto_tools
```

### **State Management**
```python
class BehavioralFinanceState(TypedDict):
    token: str                  # Asset to analyze
    market_condition: dict      # Price, volume, change data
    narrative_context: str      # Sentiment analysis
    simulation_results: dict    # Trader behavior simulation
    hypothesis_verdict: str     # Final validation result
```

### **Agent Pipeline Flow**
```
Input Token → Market Reality → Narrative Analysis → Behavioral Simulation → Hypothesis Validation → Dashboard + Verdict
```

---

## 🎓 Research Applications

### **Academic Use Cases**
- **Behavioral Finance Studies** - Test market psychology theories
- **Sentiment Analysis Research** - News-driven price movements
- **Risk Management Models** - Early panic detection systems
- **Academic Paper Generation** - Automated research reports

### **Commercial Applications**
- **Trading Psychology** - Understand market emotions
- **Risk Assessment** - Quantify market fear/greed levels
- **Portfolio Optimization** - Psychology-driven allocation strategies
- **Market Timing** - Identify optimal entry/exit points

---

## 📊 Presentation Materials

### **1-Minute Demo Script**
- **Location**: `behavioral_finance_output/1_minute_presentation.md`
- **Timing**: 30s system overview, 15s SpoonOS strengths, 15s results
- **Visual Cues**: Slide transitions and key impact points

### **Slide Deck**
- **Location**: `behavioral_finance_output/slides.md`
- **Format**: 11-slide comprehensive presentation
- **Audience**: Technical, business, and academic viewers

---

## 🔬 Innovation Highlights

### **Novel Contributions**
- **First-of-its-kind** multi-agent behavioral analysis pipeline
- **Real-time market psychology** with live sentiment integration
- **Scientific rigor** with hypothesis testing methodology
- **Reproducible research** with complete analysis traceability

### **SpoonOS Differentiators**
- **Graph Orchestration** - Seamless multi-agent coordination
- **MCP Standardization** - Unified tool interface
- **Web3 Integration** - Native blockchain data support
- **Production Ready** - Scalable and deployable architecture

---

## 🎉 Conclusion

This SpoonOS Research Agent Demo represents the **future of AI-powered financial research**:

✅ **Multi-Agent Intelligence** - Coordinated research team
✅ **Real-time Web3 Data** - Live blockchain intelligence
✅ **Scientific Methodology** - Rigorous hypothesis testing
✅ **Actionable Insights** - Trading and research applications
✅ **Open Source** - Collaborative development

**Built with SpoonOS - Enabling the next generation of AI research agents!**

---

## 🚀 Next Steps

1. **Run the demo** and explore the visualizations
2. **Add your API keys** for real-time data integration
3. **Customize hypotheses** for your research questions
4. **Extend the system** with new analysis agents
5. **Share your findings** and contribute to the project

**Ready to revolutionize behavioral finance research? Let's get started!** 🚀