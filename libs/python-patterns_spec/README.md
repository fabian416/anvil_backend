# Python Patterns Library Specification

## 1. Strategic Overview (CTO Perspective)
**Python Patterns** (from the `python-patterns` library) is our reference catalog for standardizing architectural implementations. While we use Hexagonal Architecture at the macro level, we need consistent micro-patterns for solving recurring design problems within those layers.

We are explicitly adopting specific patterns from this library to avoid "reinventing the wheel" and to ensure our code remains idiomatic and understandable to any senior Python engineer.

## 2. Use Cases & Adopted Patterns

### A. Creational Patterns (Object Construction)

1.  **Builder Pattern** (`creational/builder.py`)
    -   **Use Case**: Constructing complex `Agent` configurations or `Transaction` objects with many optional parameters.
    -   **Why**: To avoid constructors with 10+ arguments (`__init__(self, a, b, c, d...)`).
    -   **Application**: `AgentBuilder` for configuring LLM model, tools, and instructions.

2.  **Factory Method** (`creational/factory.py`)
    -   **Use Case**: Creating different types of `DeFiProvider` adapters based on configuration or chain ID.
    -   **Why**: Decouples the application code from specific adapter implementations.
    -   **Application**: `DeFiProviderFactory.get_provider("1inch")`.

3.  **Borg (Monostate)** (`creational/borg.py`)
    -   **Use Case**: Shared configuration state (like `SystemConfig`) that needs to be accessible everywhere but doesn't require a strict Singleton instance restriction (just shared state).
    -   **Why**: Pythonic alternative to Singleton.
    -   **Application**: Global `FeatureFlag` or `CircuitBreaker` state.

### B. Structural Patterns (Object Composition)

4.  **Adapter Pattern** (`structural/adapter.py`)
    -   **Use Case**: Integrating third-party libraries (like `1inch` API or `Agno` tools) into our Domain Ports.
    -   **Why**: Fundamental to Hexagonal Architecture.
    -   **Application**: `OneInchAdapter` implements `SwapProvider`.

5.  **Decorator Pattern** (`structural/decorator.py`)
    -   **Use Case**: Adding cross-cutting concerns like logging, caching, or rate-limiting to Interactors.
    -   **Why**: Keeps business logic clean (SRP).
    -   **Application**: `@cached(ttl=60)`, `@rate_limit(calls=10)`.

6.  **Proxy Pattern** (`structural/proxy.py`)
    -   **Use Case**: Lazy loading of heavy resources (like the `KnowledgeBase` vector index) or access control.
    -   **Why**: Performance optimization and security.
    -   **Application**: `LazyKnowledgeBase` that only connects to PgVector on first query.

### C. Behavioral Patterns (Object Interaction)

7.  **Strategy Pattern** (`behavioral/strategy.py`)
    -   **Use Case**: Swapping pricing algorithms or risk calculation models at runtime.
    -   **Why**: Allows us to A/B test different financial models without changing the core execution flow.
    -   **Application**: `PricingStrategy` (e.g., `UniswapV2Pricing` vs `CurvePricing`).

8.  **Observer Pattern** (`behavioral/observer.py`)
    -   **Use Case**: Event handling. When a `Transaction` is confirmed, notify the `User`, update `WalletBalance`, and log to `Audit`.
    -   **Why**: Decouples the trigger from the handlers.
    -   **Application**: `TransactionEventManager`.

9.  **Chain of Responsibility** (`behavioral/chain_of_responsibility.py`)
    -   **Use Case**: Processing a user message through multiple filters (Sanitization -> PII Redaction -> Intent Classification).
    -   **Why**: Dynamic pipeline construction.
    -   **Application**: `MessagePipeline`.

## 3. Integration Strategy
1.  **Reference, Don't Import**: We will treat `libs/python-patterns` primarily as a **Reference Library**. We won't inherit directly from its classes in production code (to avoid tight coupling to a demo repo), but we will **copy/adapt** the pattern implementations into our codebase where needed, using the library as the "Gold Standard" source.
2.  **Documentation**: When implementing a class using one of these patterns, add a docstring referencing the pattern: `See libs/python-patterns/patterns/behavioral/strategy.py`.
3.  **Utilities**: Specific generic helpers (like a `Borg` base class) can be moved to `src/app/application/common/patterns/`.
