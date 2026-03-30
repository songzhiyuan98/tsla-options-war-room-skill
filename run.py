#!/usr/bin/env python3
"""Entry point for TSLA Market Service."""

import asyncio
from market_service.service import main
from trade_memory.state_manager import init_empty_state

if __name__ == "__main__":
    init_empty_state()
    asyncio.run(main())
