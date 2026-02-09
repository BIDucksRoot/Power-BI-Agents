Generates intelligent documentation (understanding what measures do)
Adds descriptions/annotations to measures, tables, columns
Creates changelogs with AI-generated summaries
Backs up with context about what changed and why
Here's how to build this:

Architecture: AI-Powered Power BI Documentation Agent

GitHub/Azure DevOps (Trigger)
    ↓
Azure Function / GitHub Action
    ↓
AI Agent (Claude/GPT/Azure OpenAI)
    ↓ (analyzes TMDL)
Power BI MCP Server (read model)
    ↓
AI generates docs + descriptions
    ↓
Writes back to TMDL files
    ↓
Commits with AI-generated summary
