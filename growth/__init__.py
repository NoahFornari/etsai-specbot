"""
ETSAI Growth Bot — 5-Agent Autonomous Marketing System

Agents:
  - Scout: Lead discovery (Etsy search, Reddit, hashtag scraping)
  - Writer: Multi-channel outreach (email, Reddit, DMs)
  - Listener: Community monitoring (Reddit, RSS, forums)
  - Creator: Hum mascot video production (script → TTS → MoviePy → upload)
  - Commander: Brain — schedules, delegates, tracks ROI

All agents use ai_engine.call_claude() for intelligence.
Growth tables live alongside app tables in the same database.
"""
