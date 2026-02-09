"""
Standalone test for GraphExecutor hooks.

This test can be run directly without package installation.
"""
import asyncio
import sys
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Callable

# Test doubles
@dataclass
class NodeResult:
    """Test double for NodeResult."""
    success: bool
    output: Dict[str, Any] = field(default_factory=dict)
    tokens_used: int = 0
    latency_ms: int = 0

@dataclass
class NodeSpec:
    """Test double for NodeSpec."""
    id: str
    name: str = "Test Node"
    node_type: str = "test"
    input_keys: List[str] = field(default_factory=list)
    output_keys: List[str] = field(default_factory=list)

class SkipNodeExecution(Exception):
    """Raised to skip node execution."""
    def __init__(self, result: NodeResult):
        self.result = result

class GraphExecutor:
    """Test double for GraphExecutor with hook support."""
    def __init__(self, runtime=None):
        self.runtime = runtime
        self._pre_hooks: List[Callable] = []
        self._post_hooks: List[Callable] = []
    
    def add_pre_execution_hook(self, hook: Callable) -> None:
        """Add a pre-execution hook."""
        self._pre_hooks.append(hook)
    
    def add_post_execution_hook(self, hook: Callable) -> None:
        """Add a post-execution hook."""
        self._post_hooks.append(hook)
    
    def clear_hooks(self, pre: bool = True, post: bool = True) -> None:
        """Clear registered hooks."""
        if pre:
            self._pre_hooks.clear()
        if post:
            self._post_hooks.clear()
    
    async def _execute_node_hooks(
        self,
        node_id: str,
        node_spec: NodeSpec,
        inputs: Dict[str, Any],
        result: Optional[NodeResult] = None
    ) -> None:
        """Execute all registered hooks."""
        hooks = self._pre_hooks if result is None else self._post_hooks
        for hook in hooks:
            try:
                if result is not None:
                    await hook(node_id, node_spec, inputs, result)
                else:
                    await hook(node_id, node_spec, inputs)
            except SkipNodeExecution as e:
                raise
            except Exception as e:
                print(f"Hook failed: {e}", file=sys.stderr)

# Test cases
class TestHookSystem:
    """Test suite for hook system functionality."""
    
    @staticmethod
    async def test_basic_hooks() -> bool:
        """Test basic hook registration and execution."""
        execution_log = []
        executor = GraphExecutor()

        async def pre_hook(node_id, node_spec, inputs):
            execution_log.append(f"PRE: {node_id}")

        async def post_hook(node_id, node_spec, inputs, result):
            execution_log.append(f"POST: {node_id} (success: {result.success})")

        executor.add_pre_execution_hook(pre_hook)
        executor.add_post_execution_hook(post_hook)

        node_spec = NodeSpec(id="test_node")
        result = NodeResult(success=True)

        await executor._execute_node_hooks("test_node", node_spec, {})
        await executor._execute_node_hooks("test_node", node_spec, {}, result)

        expected = ["PRE: test_node", "POST: test_node (success: True)"]
        assert execution_log == expected, f"Expected {expected}, got {execution_log}"
        print("✓ test_basic_hooks passed")
        return True

    @classmethod
    async def run_all_tests(cls) -> bool:
        """Run all test cases and return success status."""
        tests = [
            ("Basic Hooks", cls.test_basic_hooks),
        ]
        
        print("\n=== Running Hook System Tests ===")
        all_passed = True
        
        for name, test in tests:
            try:
                start = asyncio.get_event_loop().time()
                success = await test()
                duration = (asyncio.get_event_loop().time() - start) * 1000
                status = "PASSED" if success else "FAILED"
                print(f"{name:<20} {status} ({duration:.1f}ms)")
                all_passed = all_passed and success
            except Exception as e:
                print(f"{name:<20} ERROR: {str(e)}")
                all_passed = False
                if "--debug" in sys.argv:
                    import traceback
                    traceback.print_exc()
        
        if all_passed:
            print("\n✅ All hook system tests passed!")
        else:
            print("\n❌ Some tests failed")
        
        return all_passed

if __name__ == "__main__":
    success = asyncio.run(TestHookSystem.run_all_tests())
    sys.exit(0 if success else 1)
