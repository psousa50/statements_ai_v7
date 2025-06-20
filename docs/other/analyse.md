Please perform a comprehensive code analysis of this entire codebase. I want you to:

  1. Code Quality & Architecture Review:
  - Analyze the overall architecture and identify any architectural anti-patterns
  - Review adherence to the hexagonal architecture pattern in the backend
  - Check for proper separation of concerns between layers
  - Identify any violations of SOLID principles

  2. Bug Detection & Potential Issues:
  - Look for potential runtime errors, null pointer exceptions, or type mismatches
  - Identify race conditions or concurrency issues
  - Check for SQL injection vulnerabilities or other security issues
  - Find memory leaks or performance bottlenecks
  - Spot error handling gaps or improper exception management

  3. Code Consistency & Standards:
  - Check adherence to coding conventions and style guidelines
  - Identify inconsistent naming patterns
  - Find duplicate code that could be refactored
  - Review import organization and unused imports
  - Check for proper TypeScript typing throughout the frontend

  4. Performance Optimization Opportunities:
  - Identify inefficient database queries or N+1 problems
  - Find opportunities for caching or optimization
  - Check for unnecessary re-renders in React components
  - Look for bundle size optimization opportunities

  5. Testing & Coverage Gaps:
  - Identify areas with insufficient test coverage
  - Find missing edge case testing
  - Check for brittle or flaky tests
  - Review test organization and maintainability

  6. Security Analysis:
  - Check for exposed secrets or credentials
  - Review authentication and authorization patterns
  - Identify potential XSS or CSRF vulnerabilities
  - Check for proper input validation and sanitization

  7. Documentation & Maintainability:
  - Identify areas lacking proper documentation
  - Find complex code that needs better comments
  - Check for outdated comments or documentation

  8. Dependency Management:
  - Review for outdated or vulnerable dependencies
  - Identify unused dependencies
  - Check for dependency conflicts

  Please organize your findings by priority (Critical, High, Medium, Low) and provide specific file locations with line numbers where applicable. For each issue, suggest concrete solutions or improvements."