# AI & LLM Integration

This project is configured to work seamlessly with AI coding assistants (like Antigravity, GitHub Copilot, etc.) and Large Language Models.

## 1. Documentation Context (`llms.txt`)

The file [`llms.txt`](../llms.txt) at the root of the project follows the [llmstxt.org](https://llmstxt.org/) specification. 
It serves as a vetted map for LLMs, pointing them to the most relevant documentation files to understand the project architecture, API, and deployment procedures.

## 2. Model Context Protocol (`docs.mcp.json`)

The file [`docs.mcp.json`](../docs.mcp.json) configures the **Model Context Protocol (MCP)** context for compatible agents (like Antigravity).
It explicitly exposes:
- The OpenAPI specification (`docs/api-docs.yaml`).
- The project documentation folder (`docs/`).

This allows the agent to "understand" the API structure and business logic without needing to index the entire codebase manually.

## 3. OpenAPI Schema Automation

To ensure that the AI agents always have an up-to-date view of the API, the OpenAPI schema (`docs/api-docs.yaml`) is synchronized automatically.

### Local Automation (Pre-commit)
We use `pre-commit` to regenerate the schema locally before every commit.

**Setup:**
```bash
pip install pre-commit
pre-commit install
```

**Workflow:**
1. Modify a Django View or Serializer.
2. `git commit`.
3. The hook runs `python manage.py spectacular`.
4. If the schema changes, the commit fails and the file is updated.
5. Simply `git add docs/api-docs.yaml` and commit again.

### Remote Enforcement (CI)
The CI pipeline contains a `check-schema` job. If a developer bypasses the pre-commit hook and pushes code with an out-of-sync schema, the CI will **fail**.
