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


EXAMPLES

Measure: Payroll Credit/Debit Control Report​ Net a Payer (NEW)

Description: "Calculates the net payment amount for employees by summing 
all payment transactions, filtered by the current employee, company, and 
period context from the Dataset Unpivoted table."

Technical Notes: "Uses TREATAS to propagate filters from Dataset Unpivoted 
to the Payments fact table through the dim_personalinfo dimension. Ensures 
consistent filtering with other report measures by respecting employee key, 
period, and company filters."

Display Folder: "Payroll/Net Payments"

Issues: "None detected. Measure correctly uses TREATAS for cross-table 
filtering."



# Model Backup - 2026-02-09 15:30:00

## Changes Summary

Added new measure "Net a Payer (NEW)" to calculate employee net payment 
amounts. This measure improves upon the previous version by using TREATAS 
to ensure proper filter propagation from Dataset Unpivoted to the Payments 
table through the dim_personalinfo bridge table.

## Impact Assessment

**Affected Reports:**
- Company Payroll Tax Statement (uses new measure)
- Payroll Debit-Credit Control paginated report

**Benefits:**
- More accurate payment calculations when filtering by employee
- Consistent with other report measures
- Better performance than previous cross-filter approach

**Breaking Changes:** None
