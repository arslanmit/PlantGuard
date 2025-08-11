---
inclusion: always
---

# MCP Integration Guidelines

## Core Constraints

**NEVER** use external APIs for core PlantGuard functionality:
- No cloud vision/ML services (Replicate, OpenAI Vision, etc.)
- No cloud speech services (use local Whisper-tiny only)
- No external inference APIs (maintain offline capability)
- No user data sent to external MCP services

## MCP Usage Patterns

### When to Use MCP
- GitHub operations: Repository management, documentation lookup
- Research: Library documentation via Context7
- Local operations: File management, dependency installation
- Project notes: Memory tool for project decisions

### Required Testing
Always test MCP tools before integration:
```python
# Test immediately when user requests MCP functionality
result = mcp_tool_name(sample_params)
```

### Configuration Management
- Workspace config: `.kiro/settings/mcp.json` (use file tools)
- User config: `~/.kiro/settings/mcp.json` (use bash commands)
- Only modify when explicitly requested
- Test tools after configuration changes

## Approved MCP Tools

**Production**: GitHub, Context7, Filesystem, Memory, Homebrew
**Research**: Brave Search (no user data)
**Local**: All local file and system operations

## Essential Configuration

```json
{
  "mcpServers": {
    "github": {
      "command": "uvx",
      "args": ["mcp-server-github"],
      "autoApprove": ["search-repositories", "get-file-contents"]
    },
    "context7": {
      "command": "uvx",
      "args": ["context7-mcp"],
      "autoApprove": ["resolve-library-id", "get-library-docs"]
    }
  }
}
```

## Production Workflow

1. Use MCP for auxiliary tasks only (not core features)
2. Maintain local fallbacks for all functionality
3. Keep plant detection pipeline completely local
4. Test MCP tools with sample calls before integration
