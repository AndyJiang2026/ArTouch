#!/usr/bin/env python3
# AI-ASSISTED: Yes
# AI-TOOL: Claude Code
# PROMPT: Create FastAPI run script
# DATE: 2026-04-19
# ENGINEER: System
# RISK-LEVEL: P2

import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
