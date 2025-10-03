<!--
Sync Impact Report:
- Version change: [NONE] → 1.0.0
- New principles added:
  1. Code Quality & Maintainability (includes dependency inversion principle)
  2. Testing Standards (Test-First Discipline)
  3. User Experience Consistency
  4. Library-First & Code Reuse
- New sections added: Development Standards, Governance
- Templates status:
  ✅ plan-template.md - reviewed, Constitution Check section aligns
  ✅ spec-template.md - reviewed, requirements alignment confirmed
  ✅ tasks-template.md - reviewed, task categorization aligns
- Follow-up TODOs: None
-->

# LangChain-Drasi Constitution

## Core Principles

### I. Code Quality & Maintainability

Code MUST be written for humans first, machines second. Every module, function, and class MUST have a clear, single responsibility. Variable and function names MUST be descriptive and reveal intent without requiring comments.

**Non-negotiable rules:**
- Functions MUST do one thing and do it well (single responsibility principle)
- Depend on abstractions, not concrete implementations (dependency inversion principle)
- Components MUST depend on interfaces/protocols/abstract base classes, not concrete types
- Complexity MUST be justified in writing before implementation
- Magic numbers and hardcoded values are FORBIDDEN - use named constants or configuration
- Code duplication beyond 3 lines MUST be refactored into shared functions
- Public APIs MUST have comprehensive documentation following the language's standard convention

**Rationale:** Maintainable code reduces technical debt, accelerates onboarding, and prevents bugs. Depending on abstractions enables testing with mocks, allows implementations to change without breaking clients, and supports dependency injection. Hardcoded examples in documentation or code create brittle systems that fail when environments change.

### II. Testing Standards (Test-First Discipline)

Test-Driven Development (TDD) is MANDATORY for all features. Tests MUST be written before implementation code, approved by stakeholders, and MUST fail initially to prove they test real behavior.

**Non-negotiable rules:**
- RED phase: Write failing tests that specify behavior
- GREEN phase: Implement minimum code to pass tests
- REFACTOR phase: Improve code while keeping tests green
- Contract tests REQUIRED for all API boundaries and library interfaces
- Integration tests REQUIRED for: new library contracts, contract changes, inter-service communication, shared schemas
- Unit tests MUST cover edge cases, error paths, and boundary conditions
- Test data MUST be generated or parameterized - no hardcoded test values

**Rationale:** TDD ensures requirements are testable, catches regressions early, and documents intended behavior. Hardcoded test data creates false positives and masks environment-specific failures.

### III. User Experience Consistency

User-facing interfaces (CLI, API, UI) MUST be predictable, consistent, and well-documented. Changes to existing interfaces MUST maintain backward compatibility or follow a documented deprecation process.

**Non-negotiable rules:**
- CLI tools MUST use standard conventions: stdin/args for input, stdout for results, stderr for errors
- JSON and human-readable output formats MUST be supported
- Error messages MUST be actionable (explain what failed and how to fix it)
- All user-facing features MUST include usage examples in documentation
- Examples MUST use configuration variables or environment variables - never hardcoded paths or credentials
- API responses MUST follow consistent structure: success/error status, data payload, error details
- Breaking changes REQUIRE major version bump and migration guide

**Rationale:** Consistent interfaces reduce cognitive load, enable automation, and prevent user frustration. Hardcoded examples in documentation fail when users operate in different environments.

### IV. Library-First & Code Reuse

Prefer existing, well-maintained libraries over custom implementations. When reinventing the wheel is proposed, justification MUST be documented and reviewed.

**Non-negotiable rules:**
- Before implementing functionality, MUST search for existing libraries in the ecosystem
- Custom implementations ONLY when: no suitable library exists, existing libraries have critical bugs/security issues, performance requirements cannot be met
- Justification MUST document: libraries evaluated, why each was unsuitable, performance/security/functionality requirements
- All dependencies MUST be pinned to specific versions or ranges
- Security vulnerabilities in dependencies MUST be addressed within 7 days of disclosure
- Shared code MUST be extracted into reusable modules or libraries

**Rationale:** Mature libraries have been battle-tested, have community support, and receive security updates. Reinventing the wheel wastes time and introduces bugs. Configuration-driven code is more reusable than hardcoded implementations.

## Development Standards

### Observability & Debugging

All components MUST be observable in production. Logging, metrics, and tracing MUST be built-in from the start.

**Requirements:**
- Structured logging REQUIRED (JSON format preferred)
- Log levels MUST be configurable via environment variables
- Sensitive data MUST NOT appear in logs (credentials, tokens, PII)
- Performance-critical paths MUST emit timing metrics
- Errors MUST include context (request ID, user ID, operation, parameters)

### Configuration Management

Configuration MUST be separate from code. All environment-specific values MUST be externalized.

**Requirements:**
- Use environment variables or configuration files for all deployment-specific values
- Configuration schema MUST be documented and validated at startup
- Secrets MUST be stored in secure vaults, never in code or configuration files
- Default values MUST work for local development without external dependencies
- Examples MUST use placeholder values (e.g., `YOUR_API_KEY_HERE`, `${API_ENDPOINT}`)

### Versioning & Breaking Changes

Follow semantic versioning (MAJOR.MINOR.PATCH):
- MAJOR: Breaking changes to public APIs or behavior
- MINOR: New features, backward-compatible additions
- PATCH: Bug fixes, performance improvements, documentation

**Process for breaking changes:**
1. Document the change, rationale, and migration path
2. Deprecate old behavior with warnings (minimum one MINOR version)
3. Provide migration tools or scripts when feasible
4. Update all examples and documentation
5. Announce in release notes and changelog

## Governance

### Constitutional Authority

This constitution supersedes all other development practices. When conflicts arise between this document and other guidance, the constitution takes precedence.

### Amendment Process

1. Proposed changes MUST be documented with rationale
2. Team review and approval REQUIRED
3. Update all dependent templates and documentation
4. Increment version following semantic versioning rules
5. Announce in project communication channels

### Compliance & Review

- All code reviews MUST verify constitutional compliance
- Pull requests that violate principles MUST include written justification in the PR description
- Unjustified violations MUST be rejected
- Complexity and custom implementations MUST be justified before implementation, not after

### Living Document

This constitution evolves with the project. When patterns emerge that improve quality, consistency, or developer experience, they should be proposed as amendments.

**Version**: 1.0.0 | **Ratified**: 2025-09-30 | **Last Amended**: 2025-09-30
