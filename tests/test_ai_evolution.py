#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test AI evolution system
"""

import asyncio
import sys
from pathlib import Path

# Add project path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dev_bot.ai_evolution_system import (
    AIEvolutionSystem,
    AIDecisionSystem,
    AILearningSystem,
    AIOptimizationSystem,
    EvolutionPhase,
    DecisionType
)


async def test_decision_system():
    """Test AI decision system"""
    print("\n=== Testing AI Decision System ===")
    
    project_root = Path.cwd()
    decision_system = AIDecisionSystem(project_root)
    
    # Test structure without actual AI call
    print("Testing decision system structure...")
    
    # Check weights
    print(f"Decision weights: {decision_system.decision_weights}")
    assert len(decision_system.decision_weights) > 0
    
    # Check history
    print(f"Initial history count: {len(decision_system.decision_history)}")
    assert len(decision_system.decision_history) == 0
    
    print("PASS: AI decision system test")


async def test_learning_system():
    """Test AI learning system"""
    print("\n=== Testing AI Learning System ===")
    
    project_root = Path.cwd()
    learning_system = AILearningSystem(project_root)
    
    # Record initial count
    initial_count = len(learning_system.experiences)
    
    # Simulate learning from executions
    executions = [
        {
            "decision_type": "development",
            "action": "add_feature",
            "result": "success",
            "success": True,
            "lessons": ["Feature addition worked well"],
            "metrics": {"time": 30}
        },
        {
            "decision_type": "debugging",
            "action": "fix_bug",
            "result": "failed",
            "success": False,
            "lessons": ["Bug fix incomplete", "Need more testing"],
            "metrics": {"time": 20}
        }
    ]
    
    for execution in executions:
        await learning_system.learn_from_execution(execution)
    
    final_count = len(learning_system.experiences)
    print(f"Experiences count: {final_count} (added {final_count - initial_count})")
    assert final_count >= initial_count + 2
    
    print(f"Patterns: {learning_system.patterns}")
    print(f"Strategies: {learning_system.strategies}")
    
    # Test recommendations
    context = {"test": "context"}
    recommendations = learning_system.get_recommendations(context)
    print(f"Recommendations: {recommendations}")
    
    print("PASS: AI learning system test")


async def test_optimization_system():
    """Test AI optimization system"""
    print("\n=== Testing AI Optimization System ===")
    
    project_root = Path.cwd()
    optimization_system = AIOptimizationSystem(project_root)
    
    # Test structure without actual AI call
    print("Testing optimization system structure...")
    
    print(f"Initial optimization history count: {len(optimization_system.optimization_history)}")
    assert len(optimization_system.optimization_history) == 0
    
    print("PASS: AI optimization system test")


async def test_evolution_system():
    """Test complete AI evolution system"""
    print("\n=== Testing AI Evolution System ===")
    
    project_root = Path.cwd()
    evolution_system = AIEvolutionSystem(project_root)
    
    # Check initial status
    status = evolution_system.get_status()
    print(f"Initial status: {status}")
    
    assert status["evolution_count"] == 0
    assert status["current_phase"] == EvolutionPhase.ANALYSIS.value
    
    # Check subsystems
    assert status["decision_history_count"] == 0
    assert status["experience_count"] >= 0
    assert status["pattern_count"] >= 0
    assert status["optimization_count"] == 0
    
    print("PASS: AI evolution system test")


async def test_decision_types():
    """Test decision type enumeration"""
    print("\n=== Testing Decision Types ===")
    
    types = [
        DecisionType.DEVELOPMENT,
        DecisionType.DEBUGGING,
        DecisionType.OPTIMIZATION,
        DecisionType.REFACTORING,
        DecisionType.FEATURE_ADDITION,
        DecisionType.BUG_FIX,
        DecisionType.DOCUMENTATION,
        DecisionType.TESTING
    ]
    
    for dtype in types:
        print(f"Decision type: {dtype.value}")
    
    assert len(types) == 8
    
    print("PASS: Decision types test")


async def test_evolution_phases():
    """Test evolution phase enumeration"""
    print("\n=== Testing Evolution Phases ===")
    
    phases = [
        EvolutionPhase.ANALYSIS,
        EvolutionPhase.DECISION,
        EvolutionPhase.EXECUTION,
        EvolutionPhase.EVALUATION,
        EvolutionPhase.LEARNING,
        EvolutionPhase.OPTIMIZATION
    ]
    
    for phase in phases:
        print(f"Phase: {phase.value}")
    
    assert len(phases) == 6
    
    print("PASS: Evolution phases test")


async def main():
    """Run all tests"""
    print("=" * 60)
    print("Starting tests for AI evolution system")
    print("=" * 60)
    
    try:
        await test_decision_types()
        await test_evolution_phases()
        await test_learning_system()
        await test_optimization_system()
        await test_decision_system()
        await test_evolution_system()
        
        print("\n" + "=" * 60)
        print("PASS: All tests passed!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\nFAIL: Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    asyncio.run(main())
