# P2P Network Architecture

## Overview
The P2P network consists of two main components:
1. **Supernode**: Central registry and task coordinator
2. **Worker Nodes**: Distributed analysis executors

## Communication Flow

### 1. Node Registration
```mermaid
sequenceDiagram
    Worker->>Supernode: POST /register (NodeRegistration)
    Supernode->>Worker: 200 OK (node_id confirmation)
    Worker->>Supernode: POST /heartbeat (every 30s)