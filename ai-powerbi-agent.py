# ai-powerbi-agent.py
import os
import json
from datetime import datetime
from pathlib import Path
from anthropic import Anthropic
import git
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

class PowerBIAIAgent:
    def __init__(self, anthropic_api_key):
        self.client = Anthropic(api_key=anthropic_api_key)
        self.repo = git.Repo('.')
        
    async def connect_to_model(self, model_path):
        """Connect to Power BI model via MCP"""
        server_params = StdioServerParameters(
            command="powerbi-mcp-server",
            args=[]
        )
        
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                
                # Connect to TMDL folder
                result = await session.call_tool(
                    "powerbi-model_connection_operations",
                    {
                        "request": {
                            "operation": "ConnectFolder",
                            "folderPath": model_path
                        }
                    }
                )
                
                return session
    
    def analyze_measure_with_ai(self, measure_name, dax_expression):
        """Use AI to analyze and document a DAX measure"""
        
        prompt = f"""Analyze this Power BI DAX measure and provide:
1. A concise business description (1-2 sentences)
2. Technical explanation of the logic
3. Any potential issues or improvements
4. Suggested display folder categorization

Measure Name: {measure_name}
DAX Expression:
{dax_expression}

Return as JSON with keys: description, technical_notes, issues, display_folder"""

        response = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            messages=[{
                "role": "user",
                "content": prompt
            }]
        )
        
        return json.loads(response.content[0].text)
    
    def analyze_tmdl_changes(self, diff_content):
        """AI analyzes what changed in TMDL files"""
        
        prompt = f"""Analyze these Power BI TMDL file changes and create:
1. A human-readable changelog summary
2. Impact assessment (what reports/measures are affected)
3. Suggested git commit message

Changes:
{diff_content}

Return as JSON with keys: changelog, impact, commit_message"""

        response = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2048,
            messages=[{
                "role": "user",
                "content": prompt
            }]
        )
        
        return json.loads(response.content[0].text)
    
    async def auto_document_measures(self, session, connection_name):
        """Automatically document all measures in the model"""
        
        # List all measures
        measures_result = await session.call_tool(
            "powerbi-model_measure_operations",
            {
                "request": {
                    "operation": "List",
                    "connectionName": connection_name
                }
            }
        )
        
        measures = json.loads(measures_result.content[0].text)
        
        documented_measures = []
        
        for measure in measures['data']['measures']:
            if not measure.get('description'):  # Only document if no description
                # Get measure details
                measure_detail = await session.call_tool(
                    "powerbi-model_measure_operations",
                    {
                        "request": {
                            "operation": "Get",
                            "connectionName": connection_name,
                            "tableName": measure['tableName'],
                            "measureName": measure['name']
                        }
                    }
                )
                
                details = json.loads(measure_detail.content[0].text)
                dax = details['data']['measure']['expression']
                
                # AI analyzes the measure
                ai_analysis = self.analyze_measure_with_ai(
                    measure['name'], 
                    dax
                )
                
                # Update measure with AI-generated description
                await session.call_tool(
                    "powerbi-model_measure_operations",
                    {
                        "request": {
                            "operation": "Update",
                            "connectionName": connection_name,
                            "tableName": measure['tableName'],
                            "measureName": measure['name'],
                            "updateDefinition": {
                                "name": measure['name'],
                                "description": ai_analysis['description'],
                                "displayFolder": ai_analysis.get('display_folder', ''),
                                "annotations": [
                                    {
                                        "key": "AI_Generated_Docs",
                                        "value": "true"
                                    },
                                    {
                                        "key": "Technical_Notes",
                                        "value": ai_analysis['technical_notes']
                                    }
                                ]
                            }
                        }
                    }
                )
                
                documented_measures.append({
                    "measure": measure['name'],
                    "description": ai_analysis['description']
                })
                
                print(f"✓ Documented: {measure['name']}")
        
        return documented_measures
    
    def create_backup_with_changelog(self):
        """Create TMDL backup with AI-generated changelog"""
        
        # Get git diff
        diff = self.repo.git.diff('HEAD~1', 'HEAD')
        
        if not diff:
            print("No changes to document")
            return
        
        # AI analyzes changes
        analysis = self.analyze_tmdl_changes(diff)
        
        # Create backup folder with timestamp
        backup_dir = Path(f"backups/{datetime.now():%Y%m%d_%H%M%S}")
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Copy TMDL files
        import shutil
        shutil.copytree(
            'Dataset.SemanticModel/definition',
            backup_dir / 'definition',
            dirs_exist_ok=True
        )
        
        # Create AI-generated changelog
        changelog_path = backup_dir / 'CHANGELOG.md'
        with open(changelog_path, 'w', encoding='utf-8') as f:
            f.write(f"# Model Backup - {datetime.now():%Y-%m-%d %H:%M:%S}\n\n")
            f.write("## Changes Summary\n\n")
            f.write(analysis['changelog'] + "\n\n")
            f.write("## Impact Assessment\n\n")
            f.write(analysis['impact'] + "\n\n")
            f.write("## Technical Details\n\n")
            f.write(f"```\n{diff}\n```\n")
        
        print(f"✓ Backup created: {backup_dir}")
        print(f"✓ Changelog: {changelog_path}")
        
        return analysis['commit_message']

async def main():
    agent = PowerBIAIAgent(
        anthropic_api_key=os.getenv('ANTHROPIC_API_KEY')
    )
    
    model_path = "c:/Users/Dell/Documents/Payroll Engine BI/payrollengine-powerbi-repo/Dataset.SemanticModel"
    
    # Connect to model
    print("Connecting to Power BI model...")
    session = await agent.connect_to_model(model_path)
    
    # Auto-document all measures
    print("Auto-documenting measures with AI...")
    documented = await agent.auto_document_measures(
        session, 
        f"TMDL-{model_path}/definition"
    )
    
    # Export updated TMDL
    await session.call_tool(
        "powerbi-model_database_operations",
        {
            "request": {
                "operation": "ExportToTmdlFolder",
                "tmdlFolderPath": f"{model_path}/definition"
            }
        }
    )
    
    # Create backup with AI changelog
    commit_message = agent.create_backup_with_changelog()
    
    # Commit with AI-generated message
    agent.repo.git.add('.')
    agent.repo.git.commit('-m', commit_message)
    
    print("✓ Complete! Model documented and backed up.")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
