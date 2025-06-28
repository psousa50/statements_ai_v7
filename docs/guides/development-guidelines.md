# Development Guidelines - Summary

## Core Philosophy

All code changes must be preceded by a **comprehensive test plan**. For each story or implementation task:
- Determine which test types are needed (unit, integration, end-to-end)
- Cover behavior at appropriate levels during story planning

## Testing Approach

Tests should focus on **behavior, not implementation details**. Always test through the public API - internal workings are invisible to tests. Aim for 100% coverage through business behavior rather than code coverage metrics. Use factory functions with optional overrides to create test data consistently.

A critical rule: **Never redefine schemas or types in test files**. Always import from the actual shared schema packages to ensure tests reflect real system behavior.

Use **BDD (Behavior-Driven Development) scenarios** to guide tests:
- Write Given–When–Then structured scenarios in stories
- Map scenarios to test levels: unit, integration, or E2E
- Generate tests that verify exact specified behavior

For end-to-end tests, use **Playwright** with a **domain-specific language (DSL)** that mirrors business language for readability.

Tests should never use sqlite or in-memory databases. Integration tests must run against real databases by using test containers. This ensures type safety and real-world behavior.
Repositories should use integration tests.

## Type Safety

Strong typing is non-negotiable. Avoid dynamic types, type casting without justification, or suppressing compiler warnings. This applies equally to production and test code. 

Follow **schema-first development** - define your data schemas first, then derive types from them. This ensures consistency across your application.

## Code Style Principles

Embrace **functional programming patterns**. Data should be immutable - no mutations allowed. Write pure functions wherever possible. Use functional methods like map, filter, and reduce instead of loops. Keep nesting shallow (maximum 2 levels).

Favor **named parameters or options objects** over positional parameters to make function calls self-documenting and less error-prone.

**Code should be self-documenting** - if you need comments, the code isn't clear enough. Focus on clear naming instead.

Always implement **production-grade patterns** - avoid quick prototyping shortcuts that aren't scalable. Use **modern library patterns** and current/recommended APIs, avoiding deprecated approaches.

Each type of test serves a specific role:

### Unit Tests
- Use dependency injection for all external dependencies
- Test small, isolated units (pure functions when possible)
- Mock all external services and systems

### Integration Tests
- Use test containers (e.g., Postgres) for real service integration
- Test FastAPI endpoints with real DBs
- Preserve type safety throughout

### End-to-End Tests
- Use Playwright to simulate user workflows
- Verify complete behavior from UI to DB
- DSL must reflect business terminology

## Error Handling

Use your language's idiomatic error handling patterns. Some languages favor exceptions, others prefer result types or explicit error returns. Follow the established conventions while maintaining clear error communication.

## Language Adaptation

While these principles are universal, adapt the specific patterns to your language's idioms. Follow established naming conventions, use appropriate testing frameworks, and leverage language-specific features for immutability and type safety.

The key is maintaining the core principles - strong typing, functional patterns, and behavior-focused testing - while expressing them in ways that feel natural in your chosen language.

## Working Philosophy

Think deeply before making changes. Ask clarifying questions when requirements are unclear. Keep changes small and incremental. 

The goal is clean, testable, maintainable code that clearly expresses business intent through its structure and behavior.

---

## Quick Reference

### Key Principles
- Test behavior, not implementation
- Strong typing (avoid dynamic/any types)
- Immutable data only
- Small, pure functions
- Strict compiler settings always
- Use real schemas/types in tests
- Follow BDD scenarios using Given–When–Then format

### Preferred Patterns
- Behavior-driven testing
- Functional programming principles
- Schema-first development
- Named parameters/options objects
- Self-documenting code (no comments)
