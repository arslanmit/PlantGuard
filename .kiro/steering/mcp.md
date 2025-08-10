---
inclusion: always
---

# MCP Integration Guidelines

## Core Principles

- **MCP First**: Always attempt MCP server integration before implementing custom solutions
- **Test Early**: Test MCP tools with sample calls before building features around them
- **Graceful Fallback**: Implement local alternatives when MCP services are unavailable
- **Security**: Never expose API keys or sensitive data in MCP configurations

## Configuration Locations

- **Workspace**: `.kiro/settings/mcp.json` (modify with file tools)
- **User Global**: `~/.kiro/settings/mcp.json` (modify with bash commands)
- Workspace settings override user settings for matching server names

## Project-Specific MCP Usage

### Plant Disease Detection (Core Feature)
- **Vision Analysis**: Use vision MCP servers for leaf image classification and disease detection
- **Model Inference**: Integrate ML MCP servers for plant diagnosis predictions
- **Image Processing**: MCP servers for image preprocessing, enhancement, and feature extraction

### Streamlit UI (`src/ui/app_streamlit.py`)
- **File Upload**: MCP servers for handling image uploads and validation
- **Real-time Updates**: Use MCP for live data streaming and UI state management
- **Session Management**: MCP-based user session and interaction tracking

### Audio Processing (`src/core/audio.py`)
- **Speech-to-Text**: MCP integration for voice input transcription
- **Audio Analysis**: Process plant care questions via audio MCP servers
- **Language Processing**: NLP MCP for understanding spoken plant queries

### Data Management
- **Storage**: Firebase MCP for plant data persistence and user history
- **Analytics**: MCP-based tracking of diagnosis accuracy and user interactions
- **Caching**: Local caching of MCP responses for offline capability

## Implementation Patterns

### Error Handling (Required)
```python
async def mcp_with_fallback(tool_name, params, fallback_func):
    try:
        return await mcp_client.call_tool(tool_name, params)
    except Exception as e:
        logger.warning(f"MCP {tool_name} failed: {e}")
        return fallback_func(params)
```

### Testing Pattern
```python
# Always test MCP tools before integration
def test_mcp_integration():
    sample_params = {"test": "data"}
    result = mcp_client.call_tool("tool-name", sample_params)
    assert result is not None
```

## Development Workflow

1. **Before Feature Development**: Test relevant MCP tools with sample calls
2. **During Implementation**: Use MCP servers for external integrations
3. **Error Scenarios**: Implement fallback functions for critical paths
4. **Testing**: Verify both MCP and fallback code paths work correctly

## Auto-Approval Recommendations

```json
{
  "mcpServers": {
    "vision-ai": {
      "autoApprove": ["analyze-image", "classify-plant", "detect-disease"]
    },
    "github": {
      "autoApprove": ["search-repositories", "get-file-contents", "create-issue"]
    },
    "firebase": {
      "autoApprove": ["firestore-get", "firestore-set", "auth-verify"]
    }
  }
}
```
