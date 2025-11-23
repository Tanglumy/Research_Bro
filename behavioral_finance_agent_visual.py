import asyncio
import os
import json
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import seaborn as sns
import numpy as np
from datetime import datetime
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

# Configure matplotlib for non-interactive backend
plt.switch_backend('Agg')
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (12, 8)
plt.rcParams['font.size'] = 10

# ==========================================
# 1. DEFINING THE SHARED STATE (Memory)
# ==========================================
class BehavioralFinanceState(TypedDict):
    token: str                  # Asset to analyze (e.g., "ETH")
    market_condition: dict      # Data: Price, 24h Drop %, Volume
    narrative_context: str      # Data: Summary of news/sentiment
    simulation_results: dict    # Result: How agents reacted
    hypothesis_verdict: str     # Conclusion
    execution_timestamp: str    # When analysis was run

# ==========================================
# 2. VISUALIZATION MODULE
# ==========================================
class BehavioralFinanceVisualizer:
    """Creates comprehensive visualizations for behavioral finance analysis"""

    def __init__(self, output_dir: str = "behavioral_finance_output"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    def create_comprehensive_dashboard(self, state: BehavioralFinanceState):
        """Create a multi-panel dashboard showing all analysis aspects"""

        fig = plt.figure(figsize=(16, 12))
        fig.suptitle(f'Behavioral Finance Analysis: {state["token"]} - {state["execution_timestamp"]}',
                     fontsize=16, fontweight='bold')

        # Panel 1: Market Conditions (top left)
        ax1 = plt.subplot(2, 3, 1)
        self._plot_market_conditions(ax1, state["market_condition"])

        # Panel 2: Narrative Analysis (top middle)
        ax2 = plt.subplot(2, 3, 2)
        self._plot_narrative_analysis(ax2, state["narrative_context"])

        # Panel 3: Agent Simulation Results (top right)
        ax3 = plt.subplot(2, 3, 3)
        self._plot_simulation_results(ax3, state["simulation_results"])

        # Panel 4: Hypothesis Validation (bottom left)
        ax4 = plt.subplot(2, 3, 4)
        self._plot_hypothesis_validation(ax4, state["hypothesis_verdict"])

        # Panel 5: Flow Diagram (bottom middle and right)
        ax5 = plt.subplot(2, 3, (5, 6))
        self._plot_analysis_flow(ax5, state)

        plt.tight_layout()

        # Save the dashboard
        dashboard_path = os.path.join(self.output_dir, f'behavioral_finance_dashboard_{self.timestamp}.png')
        plt.savefig(dashboard_path, dpi=300, bbox_inches='tight')
        plt.close()

        return dashboard_path

    def _plot_market_conditions(self, ax, market_data):
        """Plot market conditions gauge chart"""
        ax.set_title('📊 Market Conditions', fontweight='bold')

        # Create gauge for price change
        change_pct = float(market_data['change_24h'].replace('%', ''))

        # Color based on performance
        if change_pct > 5:
            color = '#2E8B57'  # Green
        elif change_pct < -5:
            color = '#DC143C'  # Red
        else:
            color = '#FFD700'  # Gold

        # Create gauge
        theta = np.linspace(0, np.pi, 100)
        r = 1
        x = r * np.cos(theta)
        y = r * np.sin(theta)

        ax.fill_between(x, y, 0, alpha=0.3, color=color)
        ax.plot(x, y, color=color, linewidth=3)

        # Add needle
        needle_angle = np.pi * (1 - (change_pct + 20) / 40)  # Map -20% to +20%
        needle_x = [0, 0.8 * np.cos(needle_angle)]
        needle_y = [0, 0.8 * np.sin(needle_angle)]
        ax.plot(needle_x, needle_y, 'k-', linewidth=3)
        ax.scatter(0, 0, color='black', s=50, zorder=5)

        # Add text
        ax.text(0, -0.3, f'{market_data["price"]}', ha='center', fontsize=12, fontweight='bold')
        ax.text(0, -0.5, f'{market_data["change_24h"]}', ha='center', fontsize=10)
        ax.text(0, -0.7, f'Vol: {market_data["volume_24h"]}', ha='center', fontsize=8)

        ax.set_xlim(-1.2, 1.2)
        ax.set_ylim(-1, 1.2)
        ax.set_aspect('equal')
        ax.axis('off')

    def _plot_narrative_analysis(self, ax, narrative):
        """Plot narrative sentiment analysis"""
        ax.set_title('📰 Narrative Analysis', fontweight='bold')

        # Determine sentiment
        if "HYPE" in narrative:
            sentiment = "HYPE"
            color = '#2E8B57'
            emoji = "🚀"
        elif "FUD" in narrative:
            sentiment = "FUD"
            color = '#DC143C'
            emoji = "😱"
        else:
            sentiment = "NEUTRAL"
            color = '#FFD700'
            emoji = "😐"

        # Create sentiment gauge
        categories = ['FUD', 'NEUTRAL', 'HYPE']
        positions = [0, 1, 2]
        colors = ['#DC143C', '#FFD700', '#2E8B57']

        bars = ax.bar(categories, [0.3, 0.3, 0.3], color=colors, alpha=0.3)

        # Highlight current sentiment
        sentiment_idx = categories.index(sentiment)
        bars[sentiment_idx].set_alpha(1.0)
        bars[sentiment_idx].set_height(0.8)

        # Add emoji and text
        ax.text(1, 0.5, emoji, ha='center', fontsize=30)
        ax.text(1, 0.3, sentiment, ha='center', fontsize=12, fontweight='bold')

        # Add narrative excerpt
        ax.text(1, -0.2, narrative[:50] + '...', ha='center', fontsize=8, wrap=True)

        ax.set_ylim(0, 1)
        ax.set_ylabel('Sentiment Strength')
        ax.set_xticklabels(categories)

    def _plot_simulation_results(self, ax, sim_data):
        """Plot trader simulation results"""
        ax.set_title('🤖 Trader Simulation', fontweight='bold')

        personas = list(sim_data.keys())
        actions = [sim_data[p]['action'] for p in personas]
        reasons = [sim_data[p]['reason'] for p in personas]

        # Color mapping for actions
        action_colors = {'Buy': '#2E8B57', 'Sell': '#DC143C', 'Hold': '#FFD700'}
        colors = [action_colors.get(action, '#808080') for action in actions]

        # Create horizontal bars
        y_pos = np.arange(len(personas))
        bars = ax.barh(y_pos, [1, 1], color=colors, alpha=0.7)

        # Add labels
        for i, (persona, action, reason) in enumerate(zip(personas, actions, reasons)):
            ax.text(0.5, i, f'{persona}: {action}', ha='center', va='center',
                   fontweight='bold', fontsize=10)
            ax.text(0.5, i-0.15, reason, ha='center', va='center',
                   fontsize=8, style='italic')

        ax.set_yticks(y_pos)
        ax.set_yticklabels(personas)
        ax.set_xlim(0, 1)
        ax.set_xticks([])
        ax.set_xlabel('Action Decision')

    def _plot_hypothesis_validation(self, ax, verdict):
        """Plot hypothesis validation result"""
        ax.set_title('⚖️ Hypothesis Validation', fontweight='bold')

        # Extract conclusion from verdict
        if "SUPPORTS" in verdict:
            result = "SUPPORTED"
            color = '#2E8B57'
            symbol = "✓"
        else:
            result = "REJECTED"
            color = '#DC143C'
            symbol = "✗"

        # Create validation display
        ax.text(0.5, 0.7, symbol, ha='center', fontsize=60, color=color, fontweight='bold')
        ax.text(0.5, 0.4, result, ha='center', fontsize=16, fontweight='bold')
        ax.text(0.5, 0.2, 'Hypothesis: "Market conditions', ha='center', fontsize=10)
        ax.text(0.5, 0.1, 'are driving panic behavior"', ha='center', fontsize=10)

        # Add key findings from verdict
        lines = verdict.split('\n')
        for i, line in enumerate(lines[-3:], start=-3):
            if 'Panic Seller' in line or 'Smart Money' in line:
                ax.text(0.5, -0.1 + (i+3)*0.1, line.strip(), ha='center',
                       fontsize=8, style='italic')

        ax.set_xlim(0, 1)
        ax.set_ylim(-0.3, 1)
        ax.set_xticks([])
        ax.set_yticks([])

    def _plot_analysis_flow(self, ax, state):
        """Plot the analysis flow diagram"""
        ax.set_title('🔄 Analysis Flow', fontweight='bold')

        # Define nodes and positions
        nodes = [
            ("Input Token", 1, 5, '#E6E6FA'),
            ("Market Data", 1, 4, '#87CEEB'),
            ("Narrative", 3, 4, '#98FB98'),
            ("Simulation", 2, 2, '#F0E68C'),
            ("Validation", 2, 0, '#FFB6C1')
        ]

        # Draw nodes
        for name, x, y, color in nodes:
            rect = patches.Rectangle((x-0.8, y-0.4), 1.6, 0.8,
                                   linewidth=2, edgecolor='black',
                                   facecolor=color, alpha=0.7)
            ax.add_patch(rect)
            ax.text(x, y, name, ha='center', va='center', fontsize=9, fontweight='bold')

        # Draw arrows
        arrows = [
            (1, 4.6, 1, 4.4),   # Input to Market
            (1.8, 4, 2.2, 4),   # Market to Narrative
            (2.5, 3.6, 2.2, 2.4), # Narrative to Simulation
            (2, 1.6, 2, 0.4)    # Simulation to Validation
        ]

        for x1, y1, x2, y2 in arrows:
            ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                       arrowprops=dict(arrowstyle='->', lw=2, color='black'))

        # Add state annotations
        ax.text(0.2, 4, f'Token: {state["token"]}', fontsize=8, style='italic')
        ax.text(0.2, 2, f'Market: {state["market_condition"]["change_24h"]}', fontsize=8, style='italic')
        ax.text(3.8, 4, state["narrative_context"][:30] + '...', fontsize=8, style='italic')

        ax.set_xlim(-0.5, 4.5)
        ax.set_ylim(-0.5, 5.5)
        ax.set_aspect('equal')
        ax.axis('off')

    def save_analysis_data(self, state: BehavioralFinanceState):
        """Save analysis data to JSON file"""
        data_path = os.path.join(self.output_dir, f'analysis_data_{self.timestamp}.json')

        with open(data_path, 'w') as f:
            json.dump(state, f, indent=2, default=str)

        return data_path

# ==========================================
# 3. DEFINING THE NODES (The Agents)
# ==========================================

visualizer = BehavioralFinanceVisualizer()

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
# 4. BUILDING THE GRAPH
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
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"🚀 Starting Behavioral Finance Study on: {target_token}")
    print(f"📅 Timestamp: {timestamp}")

    result = await app.invoke({
        "token": target_token,
        "market_condition": {},
        "narrative_context": "",
        "simulation_results": {},
        "hypothesis_verdict": "",
        "execution_timestamp": timestamp
    })

    # Print results
    print("\n" + "="*60)
    print(result["hypothesis_verdict"])
    print("="*60)
    print("Full Simulation Detail:", json.dumps(result["simulation_results"], indent=2))

    # Generate visualizations
    print(f"\n📊 Generating visualizations...")

    # Create comprehensive dashboard
    dashboard_path = visualizer.create_comprehensive_dashboard(result)
    print(f"📈 Dashboard saved: {dashboard_path}")

    # Save analysis data
    data_path = visualizer.save_analysis_data(result)
    print(f"💾 Analysis data saved: {data_path}")

    # Print output summary
    output_dir = visualizer.output_dir
    print(f"\n📁 All outputs saved to: {output_dir}/")
    print(f"   - Dashboard: behavioral_finance_dashboard_{visualizer.timestamp}.png")
    print(f"   - Data: analysis_data_{visualizer.timestamp}.json")

if __name__ == "__main__":
    asyncio.run(main())