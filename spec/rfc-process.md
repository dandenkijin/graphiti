# RFC Process for Graphiti

This document outlines the Request for Comments (RFC) process for Graphiti, which ensures that major changes to the project are properly discussed, designed, and reviewed before implementation.

## When is an RFC Required?

An RFC is required for:

- **New database drivers** (e.g., adding support for PostgreSQL, ArangoDB)
- **New LLM provider clients** (e.g., adding Cohere, Groq support)
- **New embedding provider clients** (e.g., adding Voyage AI, Jina AI)
- **New API endpoints or capabilities** in the REST server
- **Any major architectural change** that affects the core library
- **Any PR over 500 LOC** regardless of type

## RFC Lifecycle

### 1. RFC Creation
- Create an issue using the "[RFC] Request for Comments" template
- Fill out all sections thoroughly
- Tag with `rfc` label
- Assign appropriate reviewers if known

### 2. Discussion Period
- Minimum 7-day discussion period for community feedback
- Core team review and feedback
- Address concerns and refine the proposal
- May require multiple iterations

### 3. Approval Process
- RFCs are approved by core maintainers
- Approval is indicated by `approved` label
- Rejected RFCs get `rejected` label with reasoning
- Major changes may require a new RFC

### 4. Implementation
- Once approved, implementation can begin
- PR must reference the approved RFC issue
- Implementation must follow the approved design
- Significant deviations require a new RFC

## RFC Status Labels

- `rfc` - New RFC awaiting discussion
- `rfc-discussion` - Active discussion period
- `rfc-review` - Under core team review
- `approved` - RFC approved for implementation
- `rejected` - RFC rejected
- `implemented` - RFC has been implemented
- `superseded` - RFC replaced by a newer version

## RFC Categories

### Database Drivers
- New graph database support
- Driver architecture changes
- Query optimization strategies

### AI/ML Integrations
- LLM provider integrations
- Embedding service integrations
- Model-specific optimizations

### Core Architecture
- API design changes
- Data model modifications
- Performance improvements
- Security enhancements

### Developer Experience
- Tooling and utilities
- Documentation improvements
- Testing frameworks

## Writing a Good RFC

### Be Specific
- Include concrete code examples
- Provide clear API signatures
- Show before/after comparisons where applicable

### Consider Alternatives
- Discuss multiple approaches
- Explain trade-offs clearly
- Justify your chosen solution

### Think About Migration
- How will existing users migrate?
- What breaking changes are expected?
- How can we minimize disruption?

### Include Testing Strategy
- How will you test this change?
- What performance benchmarks are needed?
- How will you ensure backward compatibility?

## RFC Review Criteria

Core maintainers evaluate RFCs based on:

1. **Alignment with project goals** - Does this fit Graphiti's vision?
2. **Technical soundness** - Is the design robust and scalable?
3. **Developer experience** - Will this improve or complicate usage?
4. **Maintainability** - Can the team reasonably maintain this?
5. **Security implications** - Does this introduce security risks?
6. **Performance impact** - What are the performance implications?
7. **Breaking changes** - Are breaking changes justified and well-planned?

## Emergency Process

For critical security fixes or urgent bug fixes, the RFC process may be bypassed:

- Must be approved by at least 2 core maintainers
- Must include a post-mortem RFC explaining the change
- Should be rare and well-justified

## RFC Archive

Implemented RFCs are moved to the `spec/implemented/` directory for reference. Each RFC includes:

- Original issue number and title
- Final approved design
- Implementation notes
- Migration guide (if applicable)

## Getting Help

- Join discussions in the `#rfc` channel on Discord
- Tag core maintainers for specific questions
- Review past RFCs for examples
- Ask for feedback early in the process
