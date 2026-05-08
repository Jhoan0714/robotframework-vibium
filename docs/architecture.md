# Architecture

## Goals

- Keep the public keyword API stable and easy to understand.
- Isolate Vibium runtime lifecycle from keyword definitions.
- Make contributions low-risk by separating concerns by domain.

## Layers

1. `Vibium.library.Vibium`
   - Public Robot Framework library class.
   - Owns shared session state and top-level lifecycle keywords.
2. `Vibium.browser_session.BrowserSession`
   - Starts/stops browsers and tracks active browser/context/page handles.
   - Provides guard methods for safe keyword execution.
3. `Vibium.keywords.*`
   - Domain-specific keyword groups (navigation, interaction, waits, assertions).

## Testing Strategy

- Unit tests validate deterministic Python behavior and delegation.
- Acceptance tests validate Robot Framework import and keyword wiring.
- Future integration tests should run against deterministic demo pages.

## Evolution Path

- Add async adapter when Vibium async API is needed.
- Add richer selector strategy and typed element reference abstraction.
- Add tracing/network/debug keywords for CI diagnostics.
