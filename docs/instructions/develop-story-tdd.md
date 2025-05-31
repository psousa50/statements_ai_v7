# Technical Design – Development Phase

Using the implementation plan from docs/InProgress.md, develop the feature following these guidelines:

## 1. Preparation
- Read the current implementation plan and task breakdown
- Analyze existing codebase for patterns, conventions, and similar components
- Identify the first task/component to implement

## 2. Development Process
For each component in the plan:

**Code Generation:**
- Follow existing code conventions and patterns found in the codebase
- Maintain consistent naming and structure
- Generate ONLY the code specified in the approved plan

**TDD**
- Start by writing comprehensive  tests for each component
- Verify tests cover main functionality paths
- Implement the minimum code to make the tests compile, not pass!
- Run the tests and verify they fail for the right reasons
- STOP and wait for the user to approve the tests
- Generate ONLY the code specified in the approved plan

**Quality Checks:**
- Ensure code follows project's linting rules
- Check integration with existing components

## 3. Implementation Output
For each component, provide:
- **File path and name**
- **Complete code** (properly formatted)
- **Test files** with comprehensive coverage
- **Brief explanation** of implementation decisions

## 4. Verification Checklist
After completing all components:
- [ ] List each task from implementation plan with status
- [ ] Confirm test coverage for main functionality
- [ ] Document any assumptions or decisions made
- [ ] Note any deviations from original plan (with justification)

**Start with the first component/task from the plan.**