# Pattern Specifications and Implementation Guide

## 1. Creational Patterns

### Builder Pattern
- **Source**: `libs/python-patterns/patterns/creational/builder.py`
- **Anvil Implementation**:
    ```python
    class AgentBuilder:
        def __init__(self):
            self.agent = Agent()
        
        def with_model(self, model: str):
            self.agent.model = model
            return self
        
        def with_tools(self, tools: List[Tool]):
            self.agent.tools = tools
            return self
            
        def build(self):
            return self.agent
    ```

### Factory Pattern
- **Source**: `libs/python-patterns/patterns/creational/factory.py`
- **Anvil Implementation**:
    ```python
    class ProviderFactory:
        def get_provider(self, chain: ChainType) -> WalletProvider:
            if chain == ChainType.ETHEREUM:
                return EthereumProvider()
            elif chain == ChainType.SOLANA:
                return SolanaProvider()
            raise ValueError(f"Unknown chain {chain}")
    ```

## 2. Behavioral Patterns

### Strategy Pattern
- **Source**: `libs/python-patterns/patterns/behavioral/strategy.py`
- **Anvil Implementation**:
    - Define `PricingStrategy(Protocol)` with method `get_price(token)`.
    - Implement `UniswapStrategy`, `CurveStrategy`.
    - Context: `PriceAggregator` takes a strategy in `__init__`.

### Chain of Responsibility
- **Source**: `libs/python-patterns/patterns/behavioral/chain_of_responsibility.py`
- **Anvil Implementation**:
    - Abstract Handler class with `successor`.
    - `SanitizationHandler` -> `IntentHandler` -> `ExecutionHandler`.

## 3. Structural Patterns

### Adapter Pattern
- **Source**: `libs/python-patterns/patterns/structural/adapter.py`
- **Anvil Implementation**:
    - Already heavily used in `src/app/infrastructure/adapters/`.
    - Ensure all Adapters explicitly state which Domain Port they adapt.

### Decorator Pattern
- **Source**: `libs/python-patterns/patterns/structural/decorator.py`
- **Anvil Implementation**:
    - Use Python's native `@decorator` syntax.
    - Create `src/app/application/common/decorators/` for reusable logic.

## 4. Implementation Task List
1.  Create `src/app/application/common/patterns/` directory.
2.  Implement a reusable `Borg` mixin for shared state configuration.
3.  Implement a generic `Observable` mixin for the Observer pattern.
4.  Review existing Interactors and refactor complex logic chains into `Chain of Responsibility` where applicable.
