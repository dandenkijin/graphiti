# Graphiti Specifications

This directory contains technical specifications and design documents for Graphiti.

## Directory Structure

- `active/` - Currently active RFCs under discussion and review
- `implemented/` - Approved and implemented RFCs (archived for reference)
- `rfc-process.md` - Complete RFC process documentation
- `driver-operations-redesign.md` - Example of a detailed technical specification

## Active RFCs

Active RFCs are stored in the `active/` directory with the format:
`rfc-XXX-issue-title.md`

Where:
- `XXX` is the GitHub issue number
- `issue-title` is a kebab-cased version of the issue title

## Implemented RFCs

Once an RFC is implemented, it's moved to `implemented/` with the same naming convention. Each implemented RFC includes:

- Final approved design
- Implementation notes
- Migration guide (if applicable)
- Links to related PRs

## Contributing

All major changes to Graphiti require an RFC. See [RFC Process](rfc-process.md) for complete details.

## Quick Reference

### When to Create an RFC
- New database drivers
- New LLM/embedding provider clients  
- New API endpoints or capabilities
- Major architectural changes
- Any PR over 500 LOC

### RFC Status Flow
```
Draft → Discussion → Review → Approved → Implemented
```

### Getting Started
1. Use the [RFC issue template](../.github/ISSUE_TEMPLATE/rfc.md)
2. Follow the [RFC process documentation](rfc-process.md)
3. Join discussions in Discord `#rfc` channel
