"""
OMNICUS Agent Test Suite
========================
Tests for all cognitive components of the OMNICUS trading agent.
"""

import asyncio
import sys
import os

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent import (
    AIBrain, MemoryBank, EmotionTracker, SkillRegistry, ToolKit, WorkflowEngine,
    MarketContext, TradeSignal, DecisionType, MemoryType, PersonalityConfig,
    EmotionalState, SkillCategory, SkillLevel, ToolType, WorkflowType,
    create_omnicus_brain
)


def test_memory_bank():
    """Test Memory Bank functionality"""
    print("\n🧠 Testing Memory Bank...")
    
    memory = MemoryBank(db_path="/tmp/test_omnicus_memory.db")
    
    # Create a victory memory
    victory = memory.create_victory_memory(
        symbol="BTCUSDT",
        trade_id="test_001",
        profit=500.0,
        reasoning="RSI oversold with volume spike",
        confidence=0.75
    )
    assert victory.memory_type == MemoryType.VICTORY
    assert victory.profit_loss == 500.0
    print("  ✓ Victory memory created")
    
    # Create a mistake memory
    mistake = memory.create_mistake_memory(
        symbol="ETHUSDT",
        trade_id="test_002",
        loss=-200.0,
        reasoning="Chased pump without confirmation",
        confidence=0.60,
        mistake_type="chased_pump"
    )
    assert mistake.memory_type == MemoryType.MISTAKE
    assert mistake.profit_loss == -200.0
    print("  ✓ Mistake memory created")
    
    # Test pattern recording
    memory.record_pattern("volume_spike_breakout")
    assert memory.get_pattern_occurrences("volume_spike_breakout") >= 1
    print("  ✓ Pattern recorded")
    
    # Test hard lessons
    memory.add_lesson("Always wait for volume confirmation")
    lessons = memory.get_hard_lessons()
    assert len(lessons) > 0
    print("  ✓ Lesson added")
    
    # Test stats
    stats = memory.get_memory_stats()
    assert stats["total_memories"] >= 2
    print(f"  ✓ Memory stats: {stats['total_memories']} memories stored")
    
    print("  ✅ Memory Bank tests passed!")
    return True


def test_emotion_tracker():
    """Test Emotion Tracker functionality"""
    print("\n😊 Testing Emotion Tracker...")
    
    personality = PersonalityConfig()
    emotions = EmotionTracker(personality=personality)
    
    # Test initial state
    state = emotions.metrics.get_state()
    assert state in EmotionalState
    print(f"  ✓ Initial state: {state.value}")
    
    # Test trade impact - win
    emotions.update_from_trade(pnl=500.0, confidence=0.75, was_win=True)
    assert emotions.metrics.consecutive_wins == 1
    assert emotions.metrics.happiness > 0.75
    print("  ✓ Win processed - happiness increased")
    
    # Test trade impact - loss
    emotions.update_from_trade(pnl=-300.0, confidence=0.60, was_win=False)
    assert emotions.metrics.consecutive_losses == 1
    print("  ✓ Loss processed - stress tracked")
    
    # Test reward
    response = emotions.receive_reward("praise", "Great job on that BTC trade!")
    assert response and len(response) > 0  # Just check we got a response
    print(f"  ✓ Reward received: \"{response[:50]}...\"")
    
    # Test risk tolerance adjustment
    tolerance = emotions.get_risk_tolerance()
    assert 0.0 <= tolerance <= 1.0
    print(f"  ✓ Risk tolerance: {tolerance:.2f}")
    
    # Test state export
    state_dict = emotions.get_state()
    assert "happiness" in state_dict["metrics"]
    print("  ✓ State exported to dict")
    
    print("  ✅ Emotion Tracker tests passed!")
    return True


def test_skill_registry():
    """Test Skill Registry functionality"""
    print("\n🎯 Testing Skill Registry...")
    
    skills = SkillRegistry()
    
    # Test initial skills
    assert len(skills._skills) > 0
    print(f"  ✓ {len(skills._skills)} initial skills loaded")
    
    # Get a skill
    tech_skill = skills.get_skill("technical_analysis")
    assert tech_skill is not None
    print(f"  ✓ Technical analysis skill: level {tech_skill.level.name}")
    
    # Use a skill
    accuracy = skills.use_skill("technical_analysis", success=True, pnl=100.0)
    assert accuracy > 0.5  # Should improve
    print(f"  ✓ Skill used, new accuracy: {accuracy:.3f}")
    
    # Test skill combination
    combined = skills.calculate_combined_accuracy([
        "technical_analysis",
        "volume_analysis",
        "trend_recognition"
    ])
    assert 0.0 <= combined <= 1.0
    print(f"  ✓ Combined accuracy: {combined:.3f}")
    
    # Test recommendations
    recommendations = skills.get_skill_recommendations({
        "volatility": "high",
        "trend": "bullish"
    })
    assert len(recommendations) > 0
    print(f"  ✓ Recommendations: {recommendations}")
    
    # Test stats
    stats = skills.get_registry_stats()
    assert stats["total_skills"] > 0
    print(f"  ✓ Registry stats: {stats['total_skills']} skills")
    
    print("  ✅ Skill Registry tests passed!")
    return True


async def test_toolkit():
    """Test Tool Kit functionality"""
    print("\n🔧 Testing Tool Kit...")
    
    toolkit = ToolKit()
    
    # Test available tools
    tools = toolkit.list_tools()
    assert len(tools) > 0
    print(f"  ✓ {len(tools)} tools available")
    
    # Test technical indicators
    prices = [100, 101, 102, 101, 103, 104, 105, 106, 105, 107,
              108, 107, 109, 110, 111, 112, 111, 113, 114, 115,
              114, 116, 117, 118, 119, 120, 119, 121, 122, 123]
    
    result = await toolkit.use_tool(
        "technical_indicators",
        prices=prices,
        indicators=["sma", "rsi"]
    )
    assert result.success
    assert "rsi" in result.data
    print(f"  ✓ Technical indicators: RSI={result.data['rsi']:.1f}")
    
    # Test position sizer
    result = await toolkit.use_tool(
        "position_sizer",
        capital=10000,
        risk_percent=2.0,
        entry_price=100.0,
        stop_loss_price=95.0
    )
    assert result.success
    print(f"  ✓ Position size: {result.data['quantity']:.2f} units")
    
    # Test stop loss calculator
    result = await toolkit.use_tool(
        "stop_loss_calculator",
        entry_price=50000.0,
        method="percentage",
        risk_percent=2.0
    )
    assert result.success
    print(f"  ✓ Stop loss: ${result.data['stop_loss_price']:.2f}")
    
    # Test pattern recognition
    result = await toolkit.use_tool(
        "pattern_recognition",
        prices=prices
    )
    assert result.success
    print(f"  ✓ Patterns detected: {result.data['pattern_count']}")
    
    # Test stats
    stats = toolkit.get_toolkit_stats()
    print(f"  ✓ Toolkit stats: {stats['total_uses']} uses")
    
    print("  ✅ Tool Kit tests passed!")
    return True


async def test_workflow_engine():
    """Test Workflow Engine functionality"""
    print("\n⚙️ Testing Workflow Engine...")
    
    engine = WorkflowEngine()
    
    # Test templates
    assert len(engine._templates) > 0
    print(f"  ✓ {len(engine._templates)} workflow templates loaded")
    
    # Create and run a market scan workflow
    workflow = engine.create_workflow(
        "market_scan",
        context={"symbols": ["BTCUSDT", "ETHUSDT"]}
    )
    assert workflow.workflow_type == WorkflowType.MARKET_SCAN
    print(f"  ✓ Workflow created: {workflow.workflow_id}")
    
    # Execute workflow
    result = await engine.execute_workflow(workflow)
    assert result["state"] == "completed"
    print(f"  ✓ Workflow executed: {result['steps_completed']} steps")
    
    # Test stats
    stats = engine.get_workflow_stats()
    assert stats["total_completed"] >= 1
    print(f"  ✓ Engine stats: {stats['total_completed']} completed")
    
    print("  ✅ Workflow Engine tests passed!")
    return True


async def test_ai_brain():
    """Test AI Brain functionality"""
    print("\n🧠 Testing AI Brain...")
    
    brain = AIBrain()
    
    # Create market context
    context = MarketContext(
        symbol="BTCUSDT",
        current_price=50000.0,
        prices=[48000, 48500, 49000, 49500, 50000, 50200, 50500, 50800, 51000, 51200,
                51500, 51800, 52000, 52200, 52500, 52800, 53000, 53200, 53500, 53800,
                54000, 54200, 54500, 54800, 55000, 55200, 55500, 55800, 56000, 56200],
        volumes=[1000, 1100, 1200, 1300, 1400, 1500, 1600, 1500, 1400, 1300,
                 1200, 1100, 1000, 1100, 1200, 1300, 1400, 1500, 1600, 1700,
                 1800, 1900, 2000, 2100, 2200, 2300, 2400, 2500, 2600, 2700],
        trend="bullish",
        momentum="up",
        volatility=0.03,
        sentiment_score=0.65
    )
    print(f"  ✓ Market context created for {context.symbol}")
    
    # Analyze market
    analysis = await brain.analyze_market(context)
    assert 0.0 <= analysis.overall_score <= 1.0
    print(f"  ✓ Analysis complete: score={analysis.overall_score:.3f}, rec={analysis.recommendation}")
    
    # Generate signal
    signal = await brain.generate_signal(context)
    assert signal.action in DecisionType
    assert 0.0 <= signal.confidence <= 1.0
    print(f"  ✓ Signal generated: {signal.action.value}, confidence={signal.confidence:.2%}")
    print(f"    Reasoning: {signal.reasoning[:80]}...")
    
    # Test learning
    await brain.learn_from_outcome(
        signal=signal,
        outcome_pnl=500.0,
        outcome_type="win",
        hold_duration=4.0,
        exit_reason="target_hit"
    )
    print("  ✓ Learning from outcome completed")
    
    # Test brain state
    state = brain.get_brain_state()
    assert "emotional_state" in state
    assert "memory_stats" in state
    assert "skill_stats" in state
    print(f"  ✓ Brain state exported")
    
    print("  ✅ AI Brain tests passed!")
    return True


async def test_full_integration():
    """Test full OMNICUS integration"""
    print("\n🚀 Testing Full Integration...")
    
    # Create complete OMNICUS brain
    brain = create_omnicus_brain(
        db_path="/tmp/test_omnicus_full.db",
        min_confidence=0.60,
        max_position_percent=5.0,
        risk_per_trade_percent=2.0
    )
    print("  ✓ OMNICUS brain created with custom config")
    
    # Test multiple trading scenarios
    scenarios = [
        ("BTCUSDT", "bullish", 50000),
        ("ETHUSDT", "bearish", 3000),
        ("SOLUSDT", "neutral", 100),
    ]
    
    for symbol, trend, price in scenarios:
        context = MarketContext(
            symbol=symbol,
            current_price=price,
            prices=[price - 100 + i*5 for i in range(30)],
            trend=trend,
            sentiment_score=0.5
        )
        
        signal = await brain.generate_signal(context)
        print(f"  ✓ {symbol}: {signal.action.value} (conf={signal.confidence:.2%})")
    
    # Get final status
    status = brain.get_brain_state()
    print(f"  ✓ Final status: {status['session_stats']['decisions_made']} decisions made")
    print(f"  ✓ Emotional state: {status['emotional_state']['state']}")
    
    print("  ✅ Full Integration tests passed!")
    return True


async def run_all_tests():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("   OMNICUS AGENT TEST SUITE")
    print("=" * 60)
    
    results = []
    
    # Sync tests
    results.append(("Memory Bank", test_memory_bank()))
    results.append(("Emotion Tracker", test_emotion_tracker()))
    results.append(("Skill Registry", test_skill_registry()))
    
    # Async tests
    results.append(("Tool Kit", await test_toolkit()))
    results.append(("Workflow Engine", await test_workflow_engine()))
    results.append(("AI Brain", await test_ai_brain()))
    results.append(("Full Integration", await test_full_integration()))
    
    # Summary
    print("\n" + "=" * 60)
    print("   TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {name}: {status}")
    
    print("=" * 60)
    print(f"   Total: {passed}/{total} tests passed")
    print("=" * 60)
    
    return passed == total


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)
