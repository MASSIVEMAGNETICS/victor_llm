#!/usr/bin/env python3
"""
Victor Prime AGI - System Validation Test
Tests core functionality without requiring external dependencies
"""

import sys
import os
import asyncio

def run_tests():
    """Run all validation tests."""
    print("=" * 60)
    print("Victor Prime AGI - System Validation Test")
    print("=" * 60)
    print()

    # Test 1: Import core modules
    print("Test 1: Importing core modules...")
    try:
        from victor_core.config import ASIConfigCore
        from victor_core.logger import VictorLoggerStub
        from victor_core.messaging.pulse_exchange import BrainFractalPulseExchange
        print("✓ Core modules imported successfully")
    except Exception as e:
        print(f"✗ Failed to import core modules: {e}")
        return False

    # Test 2: Check configuration
    print("\nTest 2: Configuration validation...")
    try:
        config = ASIConfigCore()
        assert config.DIMENSIONS == 128
        assert config.PLUGIN_DIR == "victor_plugins"
        print(f"✓ Configuration loaded: {config.DIMENSIONS}D embeddings")
    except Exception as e:
        print(f"✗ Configuration error: {e}")
        return False

    # Test 3: Logger functionality
    print("\nTest 3: Logger functionality...")
    try:
        logger = VictorLoggerStub(component="TestComponent")
        logger.info("Test log message")
        print("✓ Logger working correctly")
    except Exception as e:
        print(f"✗ Logger error: {e}")
        return False

    # Test 4: Async message system
    print("\nTest 4: Async message system...")
    try:
        async def test_pulse():
            pulse = BrainFractalPulseExchange()
            await pulse.start_pulse()
            
            received = []
            def handler(msg, sender):
                received.append(msg)
            
            pulse.subscribe("test.topic", handler)
            await pulse.publish("test.topic", {"data": "test"}, "TestSender")
            await asyncio.sleep(0.1)
            await pulse.stop_pulse()
            
            return len(received) > 0
        
        result = asyncio.run(test_pulse())
        if result:
            print("✓ Message system working correctly")
        else:
            print("✗ Message system failed")
            return False
    except Exception as e:
        print(f"✗ Message system error: {e}")
        return False

    # Test 5: NLP Tokenizer
    print("\nTest 5: NLP Tokenizer...")
    try:
        from victor_core.nlp.fractal_tokenizer import FractalTokenKernel_v1_1_0
        
        tokenizer = FractalTokenKernel_v1_1_0()
        tokenizer.train(["hello world", "test message"])
        tokens = tokenizer.tokenize("hello world")
        
        assert len(tokens) > 0
        print(f"✓ Tokenizer working: {len(tokenizer.vocabulary)} tokens in vocab")
    except Exception as e:
        print(f"✗ Tokenizer error: {e}")
        return False

    # Test 6: VictorBrain initialization
    print("\nTest 6: VictorBrain initialization...")
    try:
        from victor_core.brain import VictorBrain
        
        async def test_brain():
            brain = VictorBrain(
                creator_signature_for_plk="test_creator",
                approved_entities_for_plk=["TestEntity"]
            )
            # Just test initialization, don't start
            assert brain.brain_instance_id is not None
            assert len(brain.sectors) > 0
            return True
        
        result = asyncio.run(test_brain())
        if result:
            print(f"✓ VictorBrain initialized successfully")
        else:
            print("✗ VictorBrain initialization failed")
            return False
    except Exception as e:
        print(f"✗ VictorBrain error: {e}")
        return False

    print()
    print("=" * 60)
    print("All tests passed! ✓")
    print("=" * 60)
    print()
    print("Victor Prime AGI is ready to use.")
    print()
    print("Quick Start:")
    print("  - Run core system: python -m victor_core.main")
    print("  - Run GUI interface: python VICTOR_AGI_LLM.py")
    print("  - See QUICKSTART.md for more information")
    print()
    
    return True

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
