# Conversation Log Export

Local export of conversation/session logs previously read from the Kayess bridge SQLite database.

- Source EC2 instance: `i-0025ebc4f220db762`
- Source database path: `/var/lib/kayyess-bridge/bridge.db`
- User email: `synth@kayesssquare.com`
- Conversation ID: `b0604d32-c0f3-43b6-b0a2-cc1698e53e43`
- Export location: `task_1/conversation_logs/b0604d32-c0f3-43b6-b0a2-cc1698e53e43`

Files:

- `metadata.json`: source metadata, counts, and conversation summary.
- `messages.jsonl`: persisted conversation messages.
- `turns.jsonl`: Safesurf turn/session records.
- `tool_calls.jsonl`: tool-call records for turns in the conversation.
- `findings.jsonl`: findings records for the conversation; empty for this export.
- `conversation_export.json`: combined export in one JSON document.

This is a point-in-time local export. New conversation activity after `2026-06-15T08:29:40.443Z` is not included.
