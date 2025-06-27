# Testing Strategy

## Unit Tests

- Use **dependency injection** for all external dependencies
- Test individual functions and components in isolation
- Mock all external services, databases, and APIs

## Integration Tests  

- Use **test containers** with real Postgres databases
- Test FastAPI endpoints with actual database connections
- Verify API behavior with real data persistence

## End-to-End Tests

- Use **Playwright** for browser automation
- Test complete user workflows from UI perspective
- Cover critical business paths end-to-end

## Story Planning & Test Strategy

- When planning stories, **determine which test types are needed** for each feature/component
- Consider the scope and dependencies of each scenario
- Plan test coverage across unit, integration, and E2E levels during story creation
- **MANDATORY**: Every implementation plan must include comprehensive test planning

## BDD Scenario Usage

- All tests should be **driven by BDD scenarios**
- Use Given-When-Then structure from user stories
- Map scenarios to appropriate test levels based on scope
- Generate tests that verify the exact behavior specified in scenarios
- Playwright tests should use a domain-specific language (DSL) for readability

