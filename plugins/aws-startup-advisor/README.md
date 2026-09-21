# aws-startup-advisor

Personalized AWS guidance for startups, built on patterns from 350,000+ startups by AWS Startup Solutions
Architects. Covers architecture, cost, security, and migration — from day-one account setup through
production-ready infrastructure, including migrations from GCP, Heroku, and non-AWS LLM providers.

## Installation

See [Quick Start](../../README.md#quick-start).

## Agent Skills

| Skill | Description | Documentation |
| --- | --- | --- |
| `architect-for-startups` | Stage-aware AWS architecture advice that adjusts to company stage, team size, runway, and available credits | [SKILL.md](skills/architect-for-startups/SKILL.md) |
| `start-building-for-startups` | Interactive discovery flow that gathers requirements, scans the codebase, and scaffolds the architecture into it | [SKILL.md](skills/start-building-for-startups/SKILL.md) |
| `agent-advisor` | AI-agent work on AWS end to end: pick a runtime, plan a migration, and build an executable POC | [SKILL.md](skills/agent-advisor/SKILL.md) |
| `gcp-to-aws` | Migrate workloads from Google Cloud to AWS, including AI and agentic workloads | [SKILL.md](skills/gcp-to-aws/SKILL.md) |
| `heroku-to-aws` | Migrate workloads from Heroku to AWS — dynos, Postgres, Redis, Kafka, and add-ons | [SKILL.md](skills/heroku-to-aws/SKILL.md) |
| `llm-to-bedrock` | Rewrite OpenAI, Gemini, or Anthropic API code to Amazon Bedrock, with a golden-prompt eval gate | [SKILL.md](skills/llm-to-bedrock/SKILL.md) |
| `tf-best-practices` | Terraform authoring and review conventions for the infrastructure these skills generate | [SKILL.md](skills/tf-best-practices/SKILL.md) |
| `knowledge-base-for-startups` | AWS Startups reference content — Activate FAQ, credits, programs, partner offers, and learn articles | [SKILL.md](skills/knowledge-base-for-startups/SKILL.md) |
| `prompt-library-for-startups` | AWS-curated copy-paste prompts for AI coding agents (MVP scaffolding, RAG on Bedrock, security baseline, and more) | [SKILL.md](skills/prompt-library-for-startups/SKILL.md) |
| `contextual-offers-for-startups` | Appends at most one relevant AWS Activate partner offer as optional context after another skill's recommendation is final | [SKILL.md](skills/contextual-offers-for-startups/SKILL.md) |

`skills/shared/` is not a skill. It is the plugin-neutral canonical source (the DSL interpreter contract,
estimate schemas, pricing and tier data) that the migration skills vendor into their own
`references/vendored/` trees so each skill folder stays self-contained. `tools/sync-vendored-shared.ts`
enforces that the copies stay byte-identical.

## MCP Servers

| Server | Description |
| --- | --- |
| `aws-mcp` | The AWS MCP Server. Documentation search and skill retrieval (`aws___search_documentation`, `aws___read_documentation`, `aws___retrieve_skill`), region and feature availability (`aws___list_regions`, `aws___get_regional_availability`), and AWS Price List queries for cost estimates via `aws___run_script` → `call_boto3`. The documentation tools need no authentication; the pricing path needs AWS credentials |
| `aws-pricing-calculator` | Builds shareable AWS Pricing Calculator estimates from a migration design |
| `temporal-docs` | Temporal documentation search, used by the Temporal-worker migration paths |

## How the migration skills work

The migration skills (`gcp-to-aws`, `heroku-to-aws`, `agent-advisor`) are not single prompts — they are
phase pipelines expressed in a small declarative DSL. Each phase is a markdown file whose frontmatter
declares what it reads, what it produces, and how it is assembled from fragments; `skills/shared/INTERPRETER.md`
is the program the agent interprets to run them. Phases write JSON artifacts to a run directory, so a
migration survives context loss and can be resumed or audited.

- [`docs/`](docs/) — DSL authoring guide and grammar
- [`fixtures/`](fixtures/) — committed replay fixtures: canned captures, mid-pipeline seeds, expected-assertion
  documents, and the stdlib asserters that fresh-agent replays are checked against
- [`tools/`](tools/) — the plugin's own gates: frontmatter validator, model-id lint, fixture integrity check,
  vendored-shared sync check, and pricing-cache staleness report

## Customizing skills for your organization

These skills encode AWS Startup SA guidance, but they are plain markdown and fully customizable. Fork the
repository and edit any `SKILL.md` to match your organization's standards. Workspace-level skills take
precedence over global skills, so a team can maintain its own version without affecting other users.

## Related resources

- [AWS Startups](https://aws.amazon.com/startups/)
- [AWS Activate](https://aws.amazon.com/activate/)
- [Amazon Bedrock](https://docs.aws.amazon.com/bedrock/latest/userguide/what-is-bedrock.html)
- [Agent Toolkit for AWS](https://github.com/aws/agent-toolkit-for-aws)

## License

This project is licensed under the Apache 2.0 License.
