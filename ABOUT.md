# About

## Why this role

I am interested in AgentCollect because the role combines full-stack engineering, AI-native workflows, automation, internal tooling, and real-world business operations. My recent work spans React, GraphQL, .NET, cloud deployments, DevOps workflows, and AI-integrated systems, including MCP-style tool orchestration for enterprise data access.

## How I work with AI tools

I use AI tools for repo mapping, implementation options, scaffolding, test-case generation, and review prompts. I do not treat model output as source of truth: I verify it against the codebase, product constraints, security boundaries, and actual runtime behavior, then override it when the architecture or failure mode needs a more conservative choice.

For this challenge, I used AI direction in the same way I would on a team: first to inspect the allowed planning context, then to draft a gated plan, then to adapt the implementation only after reading the clarifications.

## My last project

- **One ambiguity** I faced and how I resolved it: I recently worked on an MCP server for Capital IQ Pro to enable structured AI-driven data access and tool orchestration. The biggest ambiguity was deciding how much logic should live inside the MCP server versus existing GraphQL/backend services. I resolved it by treating the MCP server as an orchestration and tool-access layer, while keeping core business rules in the existing backend services.
- **One tradeoff** I made and why: I chose to avoid duplicating business logic in the MCP layer. That made the system easier to maintain and kept behavior consistent with existing APIs, but it required more careful schema design and tighter coordination between MCP tools and GraphQL contracts.
- **One mistake** I made and what I changed: Early on, I underestimated how important clear tool descriptions and response structures would be for AI reliability. The first version worked technically, but the outputs were not always easy for the AI layer to use predictably. I changed the tool design to be more explicit about naming, constraints, response shape, and failure cases.
- **One review comment** that made me change my mind: A reviewer said, "AI-facing APIs need to be designed like product interfaces, not just backend endpoints." That shifted how I approached MCP tools: I started treating them as interfaces an AI agent has to understand, not just transport wrappers around backend calls.

## Something I have shipped

Most of my recent shipped work was at S&P Global on Capital IQ Pro, an enterprise financial intelligence platform. Because this was enterprise/proprietary work, I cannot share internal repositories, screenshots, or production demos.

## Anything I would improve about this challenge or CLAUDE.md

I like the plan-first gate because it makes process visible. One small improvement I would make is to state whether the output CSV should include the original `company_name` and `mailing_address` fields in addition to the required contact fields; I included them so each result stays auditable without relying on row order.
