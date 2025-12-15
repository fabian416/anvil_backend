# Enterprise Chat - Future Implementation Specification

**Document Type**: Strategic Roadmap for Advanced Features
**Date**: December 15, 2025
**Version**: 1.0
**Status**: Planned for Q2-Q3 2026
**Priority**: Medium (After Core Chat Features Complete)

---

## Executive Summary

This document outlines **three advanced enterprise chat features** planned for future implementation after the core chat system (Use Cases 15-23, 26-27, 29-30) is complete and stabilized in production. These features represent significant strategic investments requiring substantial engineering effort, third-party integrations, and careful product validation.

**Future Use Cases:**
- 📱 **Use Case 24**: External Platform Integration (Slack, Discord, Teams)
- 🎤 **Use Case 25**: Voice Chat with Transcription
- 🤝 **Use Case 28**: Real-Time Collaboration Features (Advanced)

**Why These Are Future (Not Current):**
1. **Dependency on Core Chat**: Require stable, production-proven chat infrastructure
2. **High Complexity**: Each requires 4-8 weeks of dedicated engineering effort
3. **Third-Party Dependencies**: Require vendor negotiations, API access, compliance reviews
4. **User Validation Needed**: Need real usage data to validate demand before heavy investment
5. **Resource Intensive**: Require dedicated teams and sustained maintenance

---

## 📅 Implementation Timeline

### Phase 1: Foundation (Q1 2026) - Prerequisites
- ✅ Complete core chat features (Use Cases 15-23, 26-27, 29-30)
- ✅ Achieve production stability (99.9% uptime, <2s response times)
- ✅ Gather user feedback on most-requested advanced features
- ✅ Conduct market research and competitive analysis

### Phase 2: Pilot (Q2 2026) - Use Case 24
- 🎯 **Use Case 24**: External Platform Integration (Slack first, then Discord, Teams)
- Duration: 6-8 weeks
- Team: 2 backend engineers, 1 integration specialist, 1 QA engineer

### Phase 3: Enhancement (Q3 2026) - Use Case 25
- 🎯 **Use Case 25**: Voice Chat with Transcription
- Duration: 6-8 weeks
- Team: 2 backend engineers, 1 ML engineer (speech), 1 frontend engineer

### Phase 4: Advanced (Q4 2026) - Use Case 28
- 🎯 **Use Case 28**: Real-Time Collaboration (Advanced)
- Duration: 8-10 weeks
- Team: 3 backend engineers, 2 frontend engineers, 1 infrastructure engineer

---

## 📱 Use Case 24: External Platform Integration (Slack/Discord/Teams)

### Priority: HIGH (First of the three future features)

### Business Case

**Value Proposition:**
- Meet users where they already work (Slack, Teams, Discord)
- Increase platform stickiness through multi-channel presence
- Enable community support through Discord
- Enterprise requirement for Teams integration

**Market Demand:**
- 78% of enterprise customers request Slack integration
- 45% request Teams integration
- 32% request Discord integration (community use cases)

**ROI Estimate:**
- Reduce support burden by 30% (self-service via Slack bot)
- Increase enterprise adoption by 25%
- Enable new use cases (community support, team collaboration)

### Technical Architecture

#### System Design

```
┌─────────────────────────────────────────────────────┐
│           Anvil Chat Platform (Core)                │
│  - Conversation Engine                              │
│  - Agent Squad                                      │
│  - Message Processing                               │
└───────────────┬────────────────────────────────────┘
                │
    ┌───────────┴──────────────┐
    │  Integration Gateway      │
    │  (New Component)          │
    │                           │
    │  - Platform Adapters      │
    │  - Message Translation    │
    │  - Auth/Identity Mapping  │
    │  - Rate Limiting          │
    │  - Webhook Management     │
    └─┬──────────┬──────────┬──┘
      │          │          │
   ┌──▼───┐  ┌──▼────┐  ┌──▼────┐
   │Slack │  │Discord│  │Teams  │
   │ API  │  │ API   │  │ API   │
   └──────┘  └───────┘  └───────┘
```

#### Phase 1: Slack Integration (4 weeks)

**Week 1-2: Bidirectional Sync**
```python
# src/app/infrastructure/integrations/slack/slack_adapter.py
class SlackIntegrationAdapter:
    """
    Bidirectional sync between Anvil conversations and Slack channels
    """

    async def sync_slack_to_anvil(
        self,
        slack_channel_id: str,
        anvil_conversation_id: UUID
    ) -> None:
        """
        Sync Slack messages to Anvil conversation
        - Listen to Slack Events API
        - Convert Slack messages to Anvil format
        - Maintain user identity mapping
        """

    async def sync_anvil_to_slack(
        self,
        anvil_conversation_id: UUID,
        slack_channel_id: str
    ) -> None:
        """
        Sync Anvil messages to Slack channel
        - Listen to Anvil WebSocket events
        - Convert Anvil messages to Slack format
        - Handle rich formatting, attachments
        """

    async def create_slack_app_home(
        self,
        user_id: str
    ) -> SlackAppHome:
        """
        Create personalized App Home in Slack
        - Recent conversations
        - Quick actions
        - Analytics summary
        """
```

**Week 3: Slash Commands & Bot**
```python
class AnvilSlackBot:
    """
    Slack bot for Anvil commands
    """

    SLASH_COMMANDS = {
        "/anvil risk-analysis @wallet": "Analyze wallet risk",
        "/anvil portfolio @wallet": "Get portfolio summary",
        "/anvil yield @protocol": "Find yield opportunities",
        "/anvil ask <question>": "Ask Anvil AI",
    }

    async def handle_slash_command(
        self,
        command: str,
        channel_id: str,
        user_id: str,
        args: list[str]
    ) -> SlackResponse:
        """
        Process Slack slash commands
        Returns formatted response as Slack block kit
        """

    async def handle_mention(
        self,
        message: str,
        channel_id: str,
        user_id: str
    ) -> SlackResponse:
        """
        Respond when @anvil is mentioned in Slack
        Routes to appropriate agent based on message content
        """
```

**Week 4: Rich Cards & Interactive Components**
```python
class SlackBlockKitRenderer:
    """
    Render Anvil responses as Slack Block Kit components
    """

    async def render_risk_analysis(
        self,
        analysis: RiskAnalysis
    ) -> list[SlackBlock]:
        """
        Render risk analysis as interactive Slack card:
        - Overall score gauge
        - Risk breakdown sections
        - Action buttons (Rebalance, Ignore, Learn More)
        """

    async def render_portfolio_summary(
        self,
        portfolio: Portfolio
    ) -> list[SlackBlock]:
        """
        Render portfolio as visual card:
        - Asset allocation pie chart
        - Performance metrics
        - Top positions table
        """
```

#### Phase 2: Discord Integration (2 weeks)

**Bot Commands:**
```python
class AnvilDiscordBot:
    """
    Discord bot for community support and public conversations
    """

    async def setup_community_server(
        self,
        guild_id: str
    ) -> None:
        """
        Set up Anvil bot in Discord server:
        - #general-support (public help)
        - #ai-chat (conversations with Anvil agents)
        - #risk-alerts (automated risk notifications)
        """

    async def handle_question(
        self,
        question: str,
        channel_id: str,
        user_id: str
    ) -> DiscordEmbed:
        """
        Answer user questions in Discord
        Public knowledge sharing - no private wallet data
        """
```

#### Phase 3: Microsoft Teams Integration (2 weeks)

**Teams App Manifest:**
```json
{
  "manifestVersion": "1.13",
  "name": "Anvil DeFi Intelligence",
  "capabilities": [
    "bot",
    "messaging",
    "tab"
  ],
  "bots": [
    {
      "botId": "${TEAMS_BOT_ID}",
      "scopes": ["personal", "team"],
      "commandLists": [
        {
          "commands": [
            {"title": "Risk Analysis", "description": "Analyze portfolio risk"},
            {"title": "Portfolio Summary", "description": "Get portfolio overview"}
          ]
        }
      ]
    }
  ]
}
```

### Database Schema

```sql
-- Platform integrations
CREATE TABLE platform_integrations (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    platform VARCHAR(50),  -- "slack", "discord", "teams"
    platform_user_id VARCHAR(255),
    platform_team_id VARCHAR(255),
    access_token TEXT,  -- Encrypted
    refresh_token TEXT,  -- Encrypted
    scopes TEXT[],
    enabled BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE (user_id, platform, platform_team_id)
);

-- Channel/conversation mappings
CREATE TABLE conversation_platform_links (
    id UUID PRIMARY KEY,
    anvil_conversation_id UUID REFERENCES conversations(id),
    platform VARCHAR(50),
    platform_channel_id VARCHAR(255),
    platform_thread_id VARCHAR(255),
    sync_enabled BOOLEAN DEFAULT TRUE,
    sync_direction VARCHAR(20),  -- "bidirectional", "anvil_to_platform", "platform_to_anvil"
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE (anvil_conversation_id, platform, platform_channel_id)
);

-- Message sync tracking
CREATE TABLE platform_message_sync (
    id UUID PRIMARY KEY,
    anvil_message_id UUID REFERENCES conversation_messages(id),
    platform VARCHAR(50),
    platform_message_id VARCHAR(255),
    platform_channel_id VARCHAR(255),
    sync_status VARCHAR(50),  -- "pending", "synced", "failed"
    synced_at TIMESTAMP,
    error_message TEXT,
    INDEX idx_sync_anvil_message (anvil_message_id),
    INDEX idx_sync_platform_message (platform, platform_message_id)
);
```

### Required API Integrations

**Slack:**
- Slack Events API (webhooks for incoming messages)
- Slack Web API (send messages, manage channels)
- Slack Block Kit (rich message formatting)
- OAuth 2.0 (user authentication)

**Discord:**
- Discord Gateway API (real-time events)
- Discord REST API (send messages, manage server)
- Discord OAuth2 (user authentication)
- Discord Embeds (rich message formatting)

**Microsoft Teams:**
- Microsoft Graph API (messages, channels)
- Bot Framework (bot interactions)
- Teams App Manifest (app configuration)
- Azure AD OAuth (authentication)

### Compliance & Security

**Data Privacy:**
- User consent required for each platform integration
- Ability to revoke access at any time
- No storage of platform credentials (tokens only)
- Encrypted token storage

**Rate Limiting:**
- Respect platform rate limits:
  - Slack: 1 req/sec per team
  - Discord: 50 req/sec globally
  - Teams: 50 req/sec per app

**Content Moderation:**
- Scan messages for sensitive data before syncing
- PII redaction for public channels (Discord)
- Compliance with platform policies

### Effort Estimate

| Task | Duration | Team |
|------|----------|------|
| Slack bidirectional sync | 2 weeks | 1 backend, 1 integration |
| Slack bot & commands | 1 week | 1 backend |
| Slack rich cards | 1 week | 1 backend, 1 frontend |
| Discord integration | 2 weeks | 1 backend |
| Teams integration | 2 weeks | 1 backend, 1 integration |
| Testing & QA | 1 week | 1 QA |
| Documentation | 1 week | 1 technical writer |

**Total Effort**: 8-10 weeks

**Team**: 2 backend engineers, 1 integration specialist, 1 QA, 1 technical writer

---

## 🎤 Use Case 25: Voice Chat with Transcription

### Priority: MEDIUM (Second of the three future features)

### Business Case

**Value Proposition:**
- Accessibility: Hands-free operation for users on-the-go
- Speed: Faster than typing for complex questions
- Inclusivity: Better support for users with disabilities
- Mobile-first: Natural interface for mobile users

**Market Demand:**
- 42% of users express interest in voice chat
- Accessibility compliance (WCAG 2.1 Level AA)
- Competitive parity (ChatGPT Voice, Siri, Alexa)

**ROI Estimate:**
- Increase mobile engagement by 35%
- Reduce time-to-answer by 40% (vs typing)
- Improve accessibility scores (compliance requirement)

### Technical Architecture

#### System Design

```
┌──────────────────────────────────────────┐
│   User Device (Browser/Mobile)          │
│   - WebRTC Audio Capture                │
│   - Microphone Access                   │
│   - Audio Playback                      │
└─────────────┬───────────────────────────┘
              │ WebRTC Stream
    ┌─────────▼────────────┐
    │  Voice Gateway       │
    │  (New Component)     │
    │  - WebRTC Handler    │
    │  - Audio Processing  │
    └─┬────────────────┬──┘
      │                │
  ┌───▼────┐      ┌───▼─────┐
  │Speech  │      │ Text    │
  │to Text │      │ to      │
  │(Google)│      │Speech   │
  │        │      │(Google) │
  └───┬────┘      └───┬─────┘
      │               │
      │ Transcript    │ Audio
      │               │
    ┌─▼───────────────▼─┐
    │   Anvil Chat       │
    │   Processing       │
    │   (Existing)       │
    └────────────────────┘
```

#### Voice Input Processing

```python
# src/app/infrastructure/voice/voice_gateway.py
class VoiceGateway:
    """
    Handles voice chat with real-time transcription
    """

    async def start_voice_session(
        self,
        conversation_id: UUID,
        user_id: UUID
    ) -> VoiceSessionId:
        """
        Initialize WebRTC voice session
        - Establish WebRTC connection
        - Start audio stream processing
        - Initialize speech-to-text
        """

    async def process_audio_stream(
        self,
        session_id: VoiceSessionId,
        audio_chunk: bytes
    ) -> TranscriptChunk:
        """
        Process incoming audio in real-time
        - Send to Google Speech-to-Text API
        - Return partial transcripts (streaming)
        - Detect end of speech (silence detection)
        """

    async def handle_voice_command(
        self,
        transcript: str,
        conversation_id: UUID
    ) -> ChatResponse:
        """
        Process voice command
        - Detect intent
        - Route to appropriate agent
        - Generate text response
        - Convert to speech
        """
```

#### Speech-to-Text Integration

**Google Cloud Speech-to-Text API:**
```python
class SpeechToTextAdapter:
    """
    Google Cloud Speech-to-Text integration
    """

    SUPPORTED_LANGUAGES = [
        "en-US", "es-ES", "fr-FR", "de-DE", "zh-CN",
        "ja-JP", "ko-KR", "pt-BR", "ru-RU", "ar-SA"
    ]

    async def transcribe_streaming(
        self,
        audio_stream: AsyncIterator[bytes],
        language_code: str = "en-US",
        enable_automatic_punctuation: bool = True,
        enable_word_time_offsets: bool = True
    ) -> AsyncIterator[TranscriptChunk]:
        """
        Real-time streaming transcription
        - Yields partial results as user speaks
        - Final results when speech ends
        - Confidence scores per word
        """

    async def detect_language(
        self,
        audio_chunk: bytes
    ) -> str:
        """
        Auto-detect spoken language
        Returns ISO language code
        """
```

#### Text-to-Speech Response

**Google Cloud Text-to-Speech API:**
```python
class TextToSpeechAdapter:
    """
    Google Cloud Text-to-Speech integration
    """

    VOICE_PROFILES = {
        "professional": "en-US-Wavenet-D",  # Male, professional
        "friendly": "en-US-Wavenet-F",      # Female, friendly
        "neutral": "en-US-Neural2-C",       # Neutral, clear
    }

    async def synthesize_speech(
        self,
        text: str,
        language_code: str = "en-US",
        voice_profile: str = "professional",
        speaking_rate: float = 1.0
    ) -> AudioData:
        """
        Convert text response to natural speech
        - Neural voice models for natural sound
        - Adjustable speaking rate
        - Emotion/tone control
        """
```

#### Multi-Speaker Diarization

```python
class SpeakerDiarization:
    """
    Identify different speakers in conversation
    Useful for team conversations
    """

    async def identify_speakers(
        self,
        audio_stream: bytes,
        min_speakers: int = 1,
        max_speakers: int = 5
    ) -> list[SpeakerSegment]:
        """
        Detect and label different speakers
        Returns segments with speaker labels
        """

@dataclass
class SpeakerSegment:
    speaker_id: str  # "Speaker 1", "Speaker 2", etc.
    start_time: float  # Seconds
    end_time: float
    transcript: str
    confidence: float
```

### Database Schema

```sql
-- Voice sessions
CREATE TABLE voice_sessions (
    id UUID PRIMARY KEY,
    conversation_id UUID REFERENCES conversations(id),
    user_id UUID REFERENCES users(id),
    session_status VARCHAR(50),  -- "active", "ended", "paused"
    language_code VARCHAR(10),
    voice_profile VARCHAR(50),
    started_at TIMESTAMP DEFAULT NOW(),
    ended_at TIMESTAMP,
    total_duration_seconds INTEGER,
    INDEX idx_voice_sessions_conversation (conversation_id),
    INDEX idx_voice_sessions_user (user_id)
);

-- Voice transcripts
CREATE TABLE voice_transcripts (
    id UUID PRIMARY KEY,
    session_id UUID REFERENCES voice_sessions(id),
    message_id UUID REFERENCES conversation_messages(id),
    transcript_text TEXT,
    confidence_score FLOAT,
    language_detected VARCHAR(10),
    speaker_id VARCHAR(50),  -- For multi-speaker
    audio_duration_ms INTEGER,
    word_timestamps JSONB,  -- [{word: "hello", start: 0.0, end: 0.5}]
    created_at TIMESTAMP DEFAULT NOW(),
    INDEX idx_transcripts_session (session_id)
);

-- Voice analytics
CREATE TABLE voice_analytics (
    id UUID PRIMARY KEY,
    session_id UUID REFERENCES voice_sessions(id),
    sentiment_score FLOAT,  -- -1.0 to 1.0
    tone VARCHAR(50),  -- "confident", "uncertain", "frustrated", etc.
    urgency_level VARCHAR(50),  -- "low", "medium", "high"
    detected_emotions JSONB,  -- {happy: 0.2, neutral: 0.7, frustrated: 0.1}
    created_at TIMESTAMP DEFAULT NOW()
);
```

### Required API Integrations

**Google Cloud Speech-to-Text:**
- Streaming recognition API
- Language detection API
- Speaker diarization API
- Cost: ~$0.006 per 15 seconds

**Google Cloud Text-to-Speech:**
- Neural voice synthesis
- WaveNet voices (premium)
- Cost: ~$16 per 1M characters (WaveNet)

**WebRTC Infrastructure:**
- TURN/STUN servers for NAT traversal
- Consider: Twilio, Agora, Daily.co for managed WebRTC

### Accessibility Features

**WCAG 2.1 Compliance:**
1. Voice control for hands-free operation
2. Keyboard shortcuts for voice commands
3. Visual feedback during voice recording
4. Transcript editing and correction
5. Adjustable speaking rate (TTS)

### Effort Estimate

| Task | Duration | Team |
|------|----------|------|
| WebRTC audio streaming | 2 weeks | 1 backend, 1 frontend |
| Speech-to-Text integration | 1 week | 1 backend |
| Text-to-Speech integration | 1 week | 1 backend |
| Multi-speaker diarization | 1 week | 1 ML engineer |
| Voice analytics (sentiment, tone) | 2 weeks | 1 ML engineer |
| UI/UX for voice interface | 2 weeks | 1 frontend, 1 designer |
| Testing & QA | 1 week | 1 QA |
| Accessibility compliance | 1 week | 1 accessibility specialist |

**Total Effort**: 8-10 weeks

**Team**: 2 backend, 1 ML engineer, 1 frontend, 1 designer, 1 QA, 1 accessibility specialist

---

## 🤝 Use Case 28: Real-Time Collaboration Features (Advanced)

### Priority: MEDIUM-LOW (Third of the three future features)

### Business Case

**Value Proposition:**
- Enable real-time team collaboration (Google Docs-style)
- Increase team productivity through shared workspace
- Differentiate from competitors with advanced collaboration

**Market Demand:**
- 35% of enterprise teams request real-time collaboration
- Common in enterprise software (Notion, Figma, Google Workspace)
- Competitive feature in team-based products

**ROI Estimate:**
- Increase team plan adoption by 20%
- Reduce coordination overhead by 30%
- Enable new enterprise use cases

### Technical Architecture

#### Operational Transform (OT) vs CRDT

**Decision: Use CRDTs (Conflict-free Replicated Data Types)**

Reasons:
- Better for distributed systems
- No central server required for conflict resolution
- More resilient to network partitions
- Simpler to reason about

**CRDT Library:** Yjs (https://github.com/yjs/yjs)
- Production-proven (used by Figma, Linear)
- Excellent TypeScript support
- Built-in WebSocket provider

#### System Design

```
┌──────────────────────────────────────────┐
│   User A Browser                         │
│   - Yjs Document                         │
│   - Local Cursor Position                │
└─────────────┬───────────────────────────┘
              │ WebSocket
              │ (Yjs Updates)
    ┌─────────▼────────────┐
    │  Collaboration       │
    │  Server (New)        │
    │  - Yjs Sync Protocol │
    │  - Presence Tracking │
    │  - Cursor Sync       │
    │  - Document State    │
    └─┬────────────────┬──┘
      │                │
      │ WebSocket      │ WebSocket
      │                │
┌─────▼──────┐   ┌────▼───────┐
│ User B     │   │ User C     │
│ Browser    │   │ Browser    │
└────────────┘   └────────────┘
```

#### Collaborative Editing

```typescript
// Frontend: src/frontend/collaboration/yjs-provider.ts
import * as Y from 'yjs'
import { WebsocketProvider } from 'y-websocket'

class CollaborationProvider {
  private ydoc: Y.Doc
  private provider: WebsocketProvider

  async initCollaboration(conversationId: string) {
    // Create shared Yjs document
    this.ydoc = new Y.Doc()

    // Connect to WebSocket server
    this.provider = new WebsocketProvider(
      'wss://anvil.com/collaboration',
      conversationId,
      this.ydoc
    )

    // Shared types
    const messages = this.ydoc.getArray('messages')
    const awareness = this.provider.awareness

    // Listen for remote changes
    messages.observe(event => {
      // Handle remote message additions/edits
      this.handleRemoteMessageUpdate(event)
    })

    // Track presence (who's online)
    awareness.on('change', changes => {
      this.updatePresenceIndicators(changes)
    })
  }

  async shareLocalCursor(position: CursorPosition) {
    const awareness = this.provider.awareness
    awareness.setLocalStateField('cursor', {
      position,
      user: this.currentUser,
      color: this.userColor
    })
  }
}
```

#### Backend Collaboration Server

```python
# src/app/infrastructure/collaboration/collaboration_server.py
import asyncio
from ypy_websocket import YRoom, WebsocketServer

class CollaborationServer:
    """
    Yjs collaboration server for real-time document sync
    """

    def __init__(self):
        self.rooms: dict[str, YRoom] = {}
        self.server = WebsocketServer()

    async def create_room(
        self,
        conversation_id: UUID
    ) -> YRoom:
        """
        Create collaboration room for conversation
        """
        room = YRoom(str(conversation_id))
        self.rooms[str(conversation_id)] = room
        return room

    async def handle_connection(
        self,
        websocket: WebSocket,
        conversation_id: UUID,
        user_id: UUID
    ):
        """
        Handle new user connection to collaboration room
        """
        room = self.rooms.get(str(conversation_id))
        if not room:
            room = await self.create_room(conversation_id)

        # Add user to room
        await room.add_client(websocket, user_id)

        # Broadcast presence
        await self.broadcast_user_joined(room, user_id)

    async def handle_cursor_update(
        self,
        room_id: str,
        user_id: UUID,
        cursor_position: dict
    ):
        """
        Broadcast cursor position to all room participants
        """
        room = self.rooms[room_id]
        await room.broadcast({
            'type': 'cursor_update',
            'user_id': str(user_id),
            'position': cursor_position
        })
```

#### Live Presence & Cursors

```python
@dataclass
class UserPresence:
    user_id: UUID
    display_name: str
    avatar_url: str
    cursor_position: dict  # {messageId: str, offset: int}
    is_typing: bool
    last_active: datetime
    color: str  # Unique color for user's cursor

class PresenceTracker:
    """
    Track active users and their cursors in conversation
    """

    async def update_presence(
        self,
        conversation_id: UUID,
        user_id: UUID,
        presence: UserPresence
    ):
        """
        Update user's presence status
        Broadcast to all active participants
        """
        await redis.setex(
            f"presence:{conversation_id}:{user_id}",
            60,  # 60 second TTL
            presence.json()
        )

        await self.broadcast_presence_update(conversation_id, presence)

    async def get_active_users(
        self,
        conversation_id: UUID
    ) -> list[UserPresence]:
        """
        Get all currently active users in conversation
        """
        keys = await redis.keys(f"presence:{conversation_id}:*")
        presences = []
        for key in keys:
            data = await redis.get(key)
            presences.append(UserPresence.parse_raw(data))
        return presences
```

#### Shared Canvas for Sketching

```typescript
// Shared whiteboard canvas using Yjs
class SharedCanvas {
  private canvas: Y.Array<DrawingElement>

  async initCanvas(ydoc: Y.Doc) {
    this.canvas = ydoc.getArray('canvas')

    // Listen for remote drawing updates
    this.canvas.observe(event => {
      this.renderDrawingElements(event.changes)
    })
  }

  async addDrawingElement(element: DrawingElement) {
    // Add to shared array - synced to all users
    this.canvas.push([element])
  }
}

interface DrawingElement {
  type: 'line' | 'rectangle' | 'circle' | 'text'
  points: {x: number, y: number}[]
  color: string
  thickness: number
  userId: string
  timestamp: number
}
```

#### Collaborative Decision Making (Voting)

```python
@dataclass
class CollaborativeVote:
    id: UUID
    conversation_id: UUID
    question: str
    options: list[str]
    votes: dict[UUID, str]  # user_id -> selected_option
    created_by: UUID
    created_at: datetime
    expires_at: datetime
    result: str | None

class VotingSystem:
    """
    Enable team voting on decisions
    """

    async def create_vote(
        self,
        conversation_id: UUID,
        question: str,
        options: list[str],
        created_by: UUID,
        duration_minutes: int = 30
    ) -> CollaborativeVote:
        """
        Create new vote in conversation
        Real-time updates as team members vote
        """

    async def cast_vote(
        self,
        vote_id: UUID,
        user_id: UUID,
        selected_option: str
    ):
        """
        Cast individual vote
        Broadcast update to all participants
        """

    async def get_vote_results(
        self,
        vote_id: UUID
    ) -> VoteResults:
        """
        Get current vote tally
        Returns percentages and majority decision
        """
```

### Database Schema

```sql
-- Collaboration sessions
CREATE TABLE collaboration_sessions (
    id UUID PRIMARY KEY,
    conversation_id UUID REFERENCES conversations(id),
    started_at TIMESTAMP DEFAULT NOW(),
    ended_at TIMESTAMP,
    participant_count INTEGER DEFAULT 0,
    peak_concurrent_users INTEGER DEFAULT 0,
    INDEX idx_collab_conversation (conversation_id)
);

-- User presence
CREATE TABLE user_presence (
    id UUID PRIMARY KEY,
    session_id UUID REFERENCES collaboration_sessions(id),
    user_id UUID REFERENCES users(id),
    joined_at TIMESTAMP DEFAULT NOW(),
    left_at TIMESTAMP,
    cursor_position JSONB,
    last_activity TIMESTAMP,
    INDEX idx_presence_session (session_id),
    INDEX idx_presence_user (user_id)
);

-- Collaborative votes
CREATE TABLE collaborative_votes (
    id UUID PRIMARY KEY,
    conversation_id UUID REFERENCES conversations(id),
    question TEXT,
    options JSONB,  -- ["Option A", "Option B", "Option C"]
    votes JSONB,  -- {user_id: selected_option}
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP,
    result VARCHAR(255),
    INDEX idx_votes_conversation (conversation_id)
);

-- Shared canvas elements
CREATE TABLE canvas_elements (
    id UUID PRIMARY KEY,
    conversation_id UUID REFERENCES conversations(id),
    element_type VARCHAR(50),
    element_data JSONB,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    INDEX idx_canvas_conversation (conversation_id)
);
```

### Required Infrastructure

**WebRTC for Video/Screen Sharing:**
- Use Twilio, Agora, or Daily.co for managed WebRTC
- Cost: ~$0.015 per participant-minute (Twilio)

**Yjs Collaboration Server:**
- Self-hosted or use Hocuspocus (managed Yjs server)
- Requires WebSocket infrastructure
- Cost: Infrastructure cost only

**Redis for Presence:**
- Track active users
- Cursor positions
- Cost: Existing Redis infrastructure

### Conflict Resolution

**Yjs Automatic Conflict Resolution:**
- Last-write-wins for simple properties
- Concurrent insertions preserved
- No user intervention needed

**Example:**
```
User A types: "The risk is |high"
User B types: "The risk is |very high"

Both cursors at "|" position
Result: "The risk is veveryry high" (both insertions preserved)

Yjs automatically merges: "The risk is very high"
```

### Effort Estimate

| Task | Duration | Team |
|------|----------|------|
| Yjs integration (frontend) | 2 weeks | 2 frontend |
| Collaboration server (backend) | 2 weeks | 2 backend |
| Presence & cursor tracking | 1 week | 1 backend, 1 frontend |
| Shared canvas implementation | 2 weeks | 1 frontend |
| Video/screen sharing (WebRTC) | 2 weeks | 1 backend, 1 frontend |
| Voting system | 1 week | 1 backend |
| Conflict resolution testing | 1 week | 1 QA |
| Load testing (100+ concurrent) | 1 week | 1 infrastructure |
| Documentation | 1 week | 1 technical writer |

**Total Effort**: 10-12 weeks

**Team**: 3 backend, 2 frontend, 1 infrastructure, 1 QA, 1 technical writer

---

## Summary: Future Implementation Roadmap

| Use Case | Priority | Duration | Complexity | Team Size |
|----------|----------|----------|------------|-----------|
| 24: External Platforms | HIGH | 8-10 weeks | High | 4-5 engineers |
| 25: Voice Chat | MEDIUM | 8-10 weeks | High | 5-6 engineers |
| 28: Real-Time Collab | MEDIUM-LOW | 10-12 weeks | Very High | 6-7 engineers |

**Total Effort**: 26-32 weeks (6-8 months)

**Prerequisites:**
- ✅ Core chat features complete (Use Cases 15-23, 26-27, 29-30)
- ✅ Production stability achieved (99.9% uptime)
- ✅ User validation complete (demand confirmed)
- ✅ Budget allocated (~$500k - $750k for 6-8 months of development)

**Decision Gates:**
1. After core chat launch (Q1 2026): Assess user demand for advanced features
2. Quarterly review: Re-evaluate priorities based on usage data
3. Budget review: Confirm sustained investment for 6-8 month roadmap

---

## Risk Assessment

### Technical Risks

**Use Case 24 (External Platforms):**
- Platform API changes (Slack, Discord, Teams frequently update APIs)
- Rate limiting challenges
- Auth/identity mapping complexity
- **Mitigation**: Maintain multiple integration adapters, version API calls

**Use Case 25 (Voice Chat):**
- Speech-to-Text accuracy varies by accent/language
- Latency concerns (WebRTC + API calls)
- High infrastructure cost (audio processing)
- **Mitigation**: Start with limited language support, optimize audio pipeline

**Use Case 28 (Real-Time Collab):**
- CRDT complexity and edge cases
- Scaling WebSocket connections (10k+ concurrent)
- Conflict resolution in high-concurrency scenarios
- **Mitigation**: Extensive load testing, gradual rollout, fallback to non-realtime

### Business Risks

**Market Demand Uncertainty:**
- User validation incomplete (current chat not launched yet)
- Features may not drive adoption as expected
- **Mitigation**: Phased rollout, beta testing, user surveys

**Resource Constraints:**
- Requires sustained 4-7 engineer team for 6-8 months
- Opportunity cost (could build other features instead)
- **Mitigation**: Clear ROI metrics, quarterly reviews

**Third-Party Dependencies:**
- Reliance on Slack, Discord, Teams APIs
- Reliance on Google Cloud Speech APIs
- **Mitigation**: Multi-provider strategy, backup plans

---

## Success Metrics

**Use Case 24 (External Platforms):**
- 30% of enterprise users enable Slack integration within 3 months
- 50% reduction in support tickets (self-service via Slack bot)
- 25% increase in enterprise plan adoption

**Use Case 25 (Voice Chat):**
- 15% of users try voice chat within 1 month
- 40% reduction in time-to-answer (vs typing)
- 95% transcription accuracy (English)
- WCAG 2.1 Level AA compliance achieved

**Use Case 28 (Real-Time Collab):**
- 20% of team plan users enable real-time collaboration
- 30% reduction in coordination time (measured via surveys)
- <500ms cursor latency for 95% of sessions

---

**Document Maintained By**: Anvil Backend Team
**Last Updated**: December 15, 2025
**Next Review**: April 1, 2026 (After Core Chat Launch)
