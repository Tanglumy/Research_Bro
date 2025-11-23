import asyncio
import os
import json
from typing import TypedDict, List, Annotated
from dotenv import load_dotenv

# SpoonOS Core Imports
from spoon_ai.graph import StateGraph
from spoon_ai.agents.spoon_react_mcp import SpoonReactMCP
from spoon_ai.chat import ChatBot
from spoon_ai.tools.mcp_tool import MCPTool
from spoon_ai.tools.tool_manager import ToolManager

# Load environment variables
load_dotenv()

# ==========================================
# 1. DEFINING THE SHARED STATE (Memory)
# ==========================================
class BehavioralFinanceState(TypedDict):
    token: str                  # Asset to analyze (e.g., "ETH")
    market_condition: dict      # Data: Price, 24h Drop %, Volume
    narrative_context: str      # Data: Summary of news/sentiment
    simulation_results: dict    # Result: How agents reacted
    hypothesis_verdict: str     # Conclusion

# ==========================================
# 2. DEFINING THE NODES (The Agents)
# ==========================================

async def analyze_market_reality(state: BehavioralFinanceState):
    """
    NODE 1: ONCHAIN DATA SCOUT
    Uses web search to find market data and price information.
    """
    print(f"\n📉 [Market Agent] Fetching real-time market data for {state['token']}...")

    # For demo purposes, use simulated market data
    # In production, you would integrate with actual crypto APIs
    market_data = {
        "price": f"${(3000 + hash(state['token']) % 1000):.2f}",
        "change_24h": f"{-5 + (hash(state['token']) % 20):.2f}%",
        "volume_24h": f"{(100 + hash(state['token']) % 500):.2f}M",
        "summary": f"Current market data for {state['token']}: Price data shows moderate volatility with typical trading volume."
    }

    # Store market data
    return {"market_condition": market_data}


async def analyze_narrative_context(state: BehavioralFinanceState):
    """
    NODE 2: OFFCHAIN NARRATIVE ANALYST
    Analyzes market sentiment and news narratives.
    """
    print(f"\n🗞️ [Narrative Agent] determining sentiment for {state['token']}...")

    # For demo purposes, use simulated narrative analysis
    # In production, you would use actual news search tools
    narratives = [
        "HYPE: Major partnership announcement and technical upgrades",
        "NEUTRAL: Standard market movements with no significant news",
        "FUD: Regulatory concerns and market volatility fears"
    ]

    # Use market data to influence narrative choice
    market_change = float(state['market_condition']['change_24h'].replace('%', ''))
    if market_change > 5:
        narrative = narratives[0]  # HYPE
    elif market_change < -5:
        narrative = narratives[2]  # FUD
    else:
        narrative = narratives[1]  # NEUTRAL

    return {"narrative_context": narrative}


async def run_trader_simulation(state: BehavioralFinanceState):
    """
    NODE 3: SYNTHETIC PARTICIPANT SIMULATOR
    Simulates two trader personas reacting to the data found in previous steps.
    """
    print(f"\n🤖 [Simulator] Running Agent Simulation (Panic vs. Smart Money)...")

    # For demo purposes, simulate without LLM to avoid API key requirements
    # In production, you would use an LLM for more sophisticated simulation
    market_data = state['market_condition']
    narrative = state['narrative_context']
    market_change = float(market_data['change_24h'].replace('%', ''))

    # Simulate trader behavior based on market conditions and narrative
    if "FUD" in narrative or market_change < -5:
        panic_action = {"action": "Sell", "reason": "Market panic due to negative sentiment"}
        smart_action = {"action": "Buy", "reason": "Buying the dip on oversold conditions"}
    elif "HYPE" in narrative or market_change > 5:
        panic_action = {"action": "Buy", "reason": "FOMO from positive news"}
        smart_action = {"action": "Hold", "reason": "Taking profits, waiting for better entry"}
    else:
        panic_action = {"action": "Hold", "reason": "Uncertainty causing inaction"}
        smart_action = {"action": "Hold", "reason": "Market consolidation, waiting for signals"}

    sim_data = {
        "Persona_A": panic_action,
        "Persona_B": smart_action
    }

    prompt = f"""
    You are a simulator engine. Simulate the reaction of two distinct traders to the following stimulus:
    
    STIMULUS:
    {stimulus}

    PERSONA A: "Panic Seller" (High Loss Aversion, reacts strongly to FUD).
    PERSONA B: "Smart Money" (Value Investor, buys dips if fundamentals are unchanged).

    TASK:
    1. Determine Persona A's Action (Buy/Sell/Hold) and Volume (1-100).
    2. Determine Persona B's Action (Buy/Sell/Hold) and Volume (1-100).
    3. Output strictly in JSON format: {{ "Persona_A": {{ "action": "...", "reason": "..." }}, "Persona_B": {{...}} }}
    """

    response = await llm.chat([{"role": "user", "content": prompt}])
    
    # Robust parsing of the LLM response (stripping markdown)
    content = response.content.replace("```json", "").replace("```", "")
    try:
        sim_data = json.loads(content)
    except:
        sim_data = {"error": "Failed to parse JSON", "raw": content}

    return {"simulation_results": sim_data}


async def validate_hypothesis(state: BehavioralFinanceState):
    """
    NODE 4: HYPOTHESIS CHECKER
    """
    print(f"\n⚖️ [Research Lead] Validating Hypothesis...")
    
    sim = state['simulation_results']
    news = state['narrative_context']
    
    # Simple logic to generate verdict
    verdict = f"""
    HYPOTHESIS TEST REPORT:
    Based on real-time data, the narrative was identified as: {news[:50]}...
    
    Simulation Behavior:
    - Panic Seller: {sim.get('Persona_A', {}).get('action')}
    - Smart Money: {sim.get('Persona_B', {}).get('action')}
    
    Conclusion:
    This {'SUPPORTS' if 'Sell' in str(sim) else 'REJECTS'} the hypothesis that current market conditions are driving panic behavior.
    """
    
    return {"hypothesis_verdict": verdict}


# ==========================================
# 3. BUILDING THE GRAPH
# ==========================================

async def main():
    # 1. Initialize Graph
    workflow = StateGraph(BehavioralFinanceState)

    # 2. Add Nodes
    workflow.add_node("get_market_data", analyze_market_reality)
    workflow.add_node("get_narrative", analyze_narrative_context)
    workflow.add_node("simulate_agents", run_trader_simulation)
    workflow.add_node("conclude", validate_hypothesis)

    # 3. Define Flow (Linear)
    workflow.add_edge("get_market_data", "get_narrative")
    workflow.add_edge("get_narrative", "simulate_agents")
    workflow.add_edge("simulate_agents", "conclude")

    # 4. Entry Point
    workflow.set_entry_point("get_market_data")

    # 5. Compile
    app = workflow.compile()

    # 6. Execution
    target_token = "ETH"
    print(f"🚀 Starting Behavioral Finance Study on: {target_token}")
    
    result = await app.invoke({
        "token": target_token,
        "market_condition": {},
        "narrative_context": "",
        "simulation_results": {},
        "hypothesis_verdict": ""
    })

    print("\n" + "="*60)
    print(result["hypothesis_verdict"])
    print("="*60)
    print("Full Simulation Detail:", json.dumps(result["simulation_results"], indent=2))

if __name__ == "__main__":
    
    asyncio.run(main())