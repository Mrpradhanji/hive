# Hooks System Guide

## Overview
The GraphExecutor's hook system allows you to inject custom logic before and after node execution. This enables:
- Custom logging and metrics
- Caching layers
- Observability integration
- Circuit breaking
- Debugging tools

## Available Hooks

### Pre-Execution Hooks
Run before a node executes. Can be used for:
- Input validation
- Cached result lookup
- Rate limiting
- Feature flag checks

```python
async def validate_inputs(node_id: str, node_spec: NodeSpec, inputs: Dict[str, Any]) -> None:
    if not inputs.get('required_field'):
        raise ValueError("Missing required field")

# Register the hook
executor.add_pre_execution_hook(validate_inputs)
```

### Post-Execution Hooks
Run after successful node execution. Can be used for:
- Metrics collection
- Result caching
- Logging
- Side effects

```python
async def log_metrics(node_id: str, node_spec: NodeSpec, inputs: Dict[str, Any], result: NodeResult) -> None:
    metrics.record_latency(node_id, result.latency_ms)
    metrics.record_tokens(node_id, result.tokens_used)

# Register the hook
executor.add_post_execution_hook(log_metrics)
```

## Advanced Usage

### Skipping Node Execution
Pre-execution hooks can skip node execution by raising `SkipNodeExecution`:

```python
from hive.core.framework.graph.executor import SkipNodeExecution

async def check_cache(node_id: str, node_spec: NodeSpec, inputs: Dict[str, Any]) -> None:
    cached = cache.get(node_id, inputs)
    if cached:
        raise SkipNodeExecution(NodeResult(
            success=True,
            output=cached,
            tokens_used=0,
            latency_ms=0
        ))
```

### Error Handling
Hooks should handle their own errors. Unhandled exceptions will be logged but won't stop execution.

### Performance Considerations
- Keep hooks fast and non-blocking
- Use `asyncio` for I/O operations
- Be mindful of memory usage in hooks
- Consider using `functools.lru_cache` for expensive computations

## Built-in Monitoring Hooks

### Execution Time Monitor
```python
class ExecutionTimeMonitor:
    def __init__(self, threshold_ms: int = 1000):
        self.threshold = threshold_ms
        self.slow_nodes = []

    async def __call__(self, node_id: str, node_spec: NodeSpec, inputs: Dict[str, Any], result: NodeResult) -> None:
        if result.latency_ms > self.threshold:
            self.slow_nodes.append((node_id, result.latency_ms))
            logging.warning(f"Slow node {node_id}: {result.latency_ms}ms")

# Usage
monitor = ExecutionTimeMonitor(threshold_ms=500)
executor.add_post_execution_hook(monitor)
```

## Best Practices
1. **Idempotency**: Make hooks idempotent when possible
2. **Error Handling**: Handle all expected exceptions
3. **Performance**: Profile hooks in production
4. **Testing**: Test hooks in isolation
5. **Documentation**: Document hook behavior and side effects

## Example: Full Integration
```python
# Initialize executor with monitoring
executor = GraphExecutor()

# Add monitoring hook
monitor = ExecutionTimeMonitor()
executor.add_post_execution_hook(monitor)

# Add caching hook
executor.add_pre_execution_hook(check_cache)
executor.add_post_execution_hook(cache_results)

# Add metrics collection
executor.add_post_execution_hook(send_to_metrics_system)

# Add logging
executor.add_post_execution_hook(log_to_elasticsearch)
```
