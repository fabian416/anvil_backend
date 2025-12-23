# Module: [Module Name]

> **Technical Specification**: `FRONTEND_[USER|ADMIN]_[MODULE_NAME]`
> **Backend Controller**: `src/app/presentation/http/controllers/[path]/[controller].py`
> **Base Route**: `/[route-path]`
> **Package**: `[user|admin]/[module-package]`

---

## 📖 Overview

[Brief description of the module's purpose, key capabilities, and business value. 2-3 sentences.]

### Key Capabilities
1. **[Capability 1]**: [Description]
2. **[Capability 2]**: [Description]
3. **[Capability 3]**: [Description]

### Business Value
- **[Value Proposition 1]**
- **[Value Proposition 2]**

---

## 🎨 UX/UI Specifications

### Design Principles
- **User-Centric**: [How this module prioritizes user needs]
- **Accessibility**: WCAG 2.1 AA compliant
- **Responsive**: Mobile-first design approach
- **Performance**: [Performance targets]

### Visual Design

#### Layout Structure
```
┌─────────────────────────────────────────┐
│ Header / Navigation                     │
├─────────────────────────────────────────┤
│ ┌──────────┐  ┌──────────┐            │
│ │ Primary  │  │ Secondary│            │
│ │ Content  │  │ Panel    │            │
│ │          │  │          │            │
│ └──────────┘  └──────────┘            │
│                                         │
│ ┌──────────────────────────┐            │
│ │ Additional Content Area  │            │
│ └──────────────────────────┘            │
└─────────────────────────────────────────┘
```

#### Color Palette
- **Primary**: `#0ea5e9` (Sky Blue)
- **Secondary**: `#0284c7` (Blue)
- **Success**: `#10b981` (Green)
- **Warning**: `#f59e0b` (Amber)
- **Error**: `#ef4444` (Red)
- **Background**: `#ffffff` (White) / `#f9fafb` (Gray-50)
- **Text**: `#111827` (Gray-900)

#### Typography
- **Headings**: Inter, 600-700 weight
- **Body**: Inter, 400 weight
- **Code/Mono**: JetBrains Mono, 400 weight

#### Spacing System
- **Base Unit**: 4px
- **Container Padding**: 16px (mobile), 24px (tablet), 32px (desktop)
- **Component Gap**: 16px (mobile), 24px (desktop)

#### Component Specifications

##### Primary Action Button
```typescript
interface ButtonProps {
  variant: 'primary' | 'secondary' | 'ghost' | 'danger'
  size: 'sm' | 'md' | 'lg'
  disabled?: boolean
  loading?: boolean
  fullWidth?: boolean
}
```

**Visual States**:
- **Default**: Primary color background, white text
- **Hover**: Darker shade (10% darker)
- **Active**: Pressed state with shadow
- **Disabled**: 50% opacity, no interaction
- **Loading**: Spinner icon, disabled state

##### Form Inputs
```typescript
interface InputProps {
  label: string
  type: 'text' | 'email' | 'password' | 'number' | 'tel'
  placeholder?: string
  error?: string
  helpText?: string
  required?: boolean
  disabled?: boolean
}
```

**Visual States**:
- **Default**: Gray border, white background
- **Focus**: Primary color border, ring effect
- **Error**: Red border, error message below
- **Disabled**: Gray background, reduced opacity

##### Cards/Containers
- **Border Radius**: 8px (base), 12px (large)
- **Shadow**: `0 1px 3px rgba(0, 0, 0, 0.1)`
- **Padding**: 16px (mobile), 24px (desktop)

### Responsive Breakpoints
- **Mobile**: < 640px (1 column, stacked layout)
- **Tablet**: 640px - 1024px (2 columns, adjusted spacing)
- **Desktop**: > 1024px (Full layout, optimal spacing)
- **Large Desktop**: > 1280px (Max-width container, centered)

### Accessibility Requirements
- **Keyboard Navigation**: All interactive elements accessible via Tab
- **Screen Readers**: Proper ARIA labels and roles
- **Color Contrast**: Minimum 4.5:1 for text, 3:1 for UI components
- **Focus Indicators**: Visible focus rings on all focusable elements
- **Error Messages**: Descriptive, associated with inputs via `aria-describedby`

### Loading States
- **Skeleton Loaders**: For content-heavy sections
- **Spinner**: For button actions and small areas
- **Progress Bars**: For multi-step processes
- **Placeholder Content**: For images and media

### Empty States
- **Illustration**: Contextual illustration or icon
- **Message**: Clear explanation of empty state
- **Action**: Primary CTA to resolve empty state

### Error States
- **Inline Errors**: Below form fields with red text
- **Toast Notifications**: For system-level errors
- **Error Pages**: For critical failures (404, 500, etc.)

---

## 🔌 API Endpoints

### [Endpoint Name 1]

**Method**: `GET|POST|PUT|DELETE|PATCH`  
**Endpoint**: `/api/v1/[endpoint-path]`  
**Auth Required**: `Yes|No`  
**Role Required**: `[user|admin|super_admin]` (if applicable)

#### Request

##### Headers
```http
Authorization: Bearer {jwt_token}
Content-Type: application/json
```

##### Query Parameters (if applicable)
| Parameter | Type | Required | Description | Example |
|----------|------|----------|------------|---------|
| `param1` | `string` | No | Description | `value1` |
| `param2` | `integer` | Yes | Description | `42` |

##### Path Parameters (if applicable)
| Parameter | Type | Required | Description |
|----------|------|----------|------------|
| `id` | `UUID` | Yes | Resource identifier |

##### Request Body (if applicable)
```json
{
  "field1": "value1",
  "field2": 42,
  "field3": {
    "nested": "value"
  }
}
```

**Request Schema**:
| Field | Type | Required | Description | Validation |
|-------|------|----------|-------------|------------|
| `field1` | `string` | Yes | Description | Min: 1, Max: 255 |
| `field2` | `integer` | No | Description | Min: 0, Max: 100 |
| `field3` | `object` | No | Description | - |

#### Response

##### Success Response (200 OK)
```json
{
  "id": "uuid",
  "field1": "value1",
  "field2": 42,
  "created_at": "2024-01-01T12:00:00Z",
  "updated_at": "2024-01-01T12:00:00Z"
}
```

**Response Schema**:
| Field | Type | Description |
|-------|------|-------------|
| `id` | `UUID` | Resource identifier |
| `field1` | `string` | Description |
| `field2` | `integer` | Description |
| `created_at` | `datetime` | ISO 8601 timestamp |
| `updated_at` | `datetime` | ISO 8601 timestamp |

##### Error Responses

| Status | Error Code | Description | UI Behavior |
|--------|------------|-------------|-------------|
| `400` | `ValidationError` | Invalid request data | Show inline errors on form fields |
| `401` | `AuthenticationError` | Missing or invalid token | Redirect to login |
| `403` | `AuthorizationError` | Insufficient permissions | Show "Access Denied" message |
| `404` | `NotFoundError` | Resource not found | Show "Not Found" page |
| `409` | `ConflictError` | Resource conflict | Show conflict message with resolution |
| `422` | `DomainFieldError` | Business rule violation | Show field-specific error |
| `429` | `RateLimitError` | Too many requests | Show rate limit message with retry time |
| `500` | `InternalServerError` | Server error | Show generic error, log details |
| `503` | `ServiceUnavailableError` | Service unavailable | Show maintenance message |

**Error Response Format**:
```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": {
      "field": "Specific field error (if applicable)"
    },
    "timestamp": "2024-01-01T12:00:00Z"
  }
}
```

### [Endpoint Name 2]
[Repeat structure for each endpoint]

---

## 🔄 User Flows & Use Cases

### Use Case 1: [Primary Use Case Name]

**Actor**: [User Role]  
**Goal**: [What the user wants to achieve]  
**Preconditions**: [What must be true before starting]

#### Flow Steps

1. **Entry Point**: User navigates to `/[route]` or triggers action from `[location]`
2. **Initial State**: 
   - UI displays [initial content]
   - System loads [data] via `GET /api/v1/[endpoint]`
3. **User Action**: User [performs action]
4. **System Response**: 
   - UI shows [loading state]
   - System calls `POST /api/v1/[endpoint]`
5. **Success Path**:
   - System returns success response
   - UI updates to show [success state]
   - User sees [confirmation/result]
6. **Error Path**:
   - System returns error response
   - UI displays error message
   - User can [recovery action]

#### Flow Diagram
```
[User] → [Entry Point]
         ↓
    [Initial Load]
         ↓
    [User Action]
         ↓
    ┌────────┐
    │ Success│ → [Success State]
    └────────┘
         ↓
    ┌────────┐
    │ Error  │ → [Error State] → [Recovery]
    └────────┘
```

#### Success Criteria
- [ ] User completes action within [X] seconds
- [ ] Success feedback is clear and immediate
- [ ] Error recovery is intuitive
- [ ] Accessibility requirements met

### Use Case 2: [Secondary Use Case]
[Repeat structure]

---

## 🔌 WebSocket Implementation (if applicable)

### Connection Details

| Attribute | Value |
|-----------|-------|
| **URL (Dev)** | `ws://localhost:8000/api/v1/ws/[endpoint]` |
| **URL (Prod)** | `wss://api.anvil.com/api/v1/ws/[endpoint]` |
| **Auth** | Query Parameter: `?token=<jwt_access_token>` |
| **Optional** | Query Parameter: `?session_id=<uuid>` (for resuming sessions) |

### Connection Lifecycle

1. **Connect**: Client initiates WebSocket connection with JWT token
2. **Validate**: Server validates token (Close Code 1008 if invalid)
3. **Welcome**: Server sends `type: system` welcome message
4. **Subscribe**: Client sends subscription message
5. **Loop**: Bidirectional message flow
6. **Heartbeat**: Client sends `ping` every 30s, Server responds `pong`
7. **Disconnect**: Client closes connection or server terminates

### Client-to-Server Messages

#### Subscribe
```json
{
  "type": "subscribe",
  "subscriptions": ["event1", "event2"]
}
```

#### Send Action
```json
{
  "type": "action",
  "action": "action_name",
  "payload": {
    "field": "value"
  }
}
```

#### Heartbeat (Ping)
```json
{
  "type": "ping"
}
```

### Server-to-Client Messages

#### System/Welcome
```json
{
  "type": "system",
  "message": "Connected to [Service]",
  "user_id": "user_123",
  "session_id": "session_abc",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

#### Event Update
```json
{
  "type": "event",
  "event": "event_name",
  "data": {
    "field": "value"
  },
  "timestamp": "2024-01-01T12:00:00Z"
}
```

#### Progress Update
```json
{
  "type": "progress",
  "status": "processing",
  "message": "Processing request...",
  "progress": 0.5
}
```

#### Error
```json
{
  "type": "error",
  "error": "Error message",
  "code": "ERROR_CODE"
}
```

#### Heartbeat Response (Pong)
```json
{
  "type": "pong"
}
```

### Example Event Sequence

1. **Client**: Connects to WebSocket
2. **Server**: Sends `type: system` welcome
3. **Client**: Sends `type: subscribe` with subscriptions
4. **Server**: Sends `type: event` updates as they occur
5. **Client**: Sends `type: ping` every 30s
6. **Server**: Responds with `type: pong`
7. **Client**: Closes connection

### WebSocket Client Implementation

#### TypeScript/JavaScript Example
```typescript
class WebSocketClient {
  private ws: WebSocket | null = null
  private reconnectAttempts = 0
  private maxReconnectAttempts = 5
  private reconnectDelay = 1000

  connect(token: string, sessionId?: string): void {
    const url = `ws://localhost:8000/api/v1/ws/[endpoint]?token=${token}${sessionId ? `&session_id=${sessionId}` : ''}`
    
    this.ws = new WebSocket(url)

    this.ws.onopen = () => {
      console.log('WebSocket connected')
      this.reconnectAttempts = 0
      this.subscribe(['event1', 'event2'])
      this.startHeartbeat()
    }

    this.ws.onmessage = (event) => {
      const message = JSON.parse(event.data)
      this.handleMessage(message)
    }

    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error)
    }

    this.ws.onclose = () => {
      console.log('WebSocket disconnected')
      this.stopHeartbeat()
      this.attemptReconnect(token, sessionId)
    }
  }

  private subscribe(subscriptions: string[]): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({
        type: 'subscribe',
        subscriptions
      }))
    }
  }

  private startHeartbeat(): void {
    this.heartbeatInterval = setInterval(() => {
      if (this.ws?.readyState === WebSocket.OPEN) {
        this.ws.send(JSON.stringify({ type: 'ping' }))
      }
    }, 30000)
  }

  private stopHeartbeat(): void {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval)
    }
  }

  private handleMessage(message: any): void {
    switch (message.type) {
      case 'system':
        console.log('System message:', message.message)
        break
      case 'event':
        this.onEvent(message.event, message.data)
        break
      case 'progress':
        this.onProgress(message.status, message.progress)
        break
      case 'error':
        this.onError(message.error, message.code)
        break
      case 'pong':
        // Heartbeat acknowledged
        break
    }
  }

  private attemptReconnect(token: string, sessionId?: string): void {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++
      setTimeout(() => {
        console.log(`Reconnecting... (${this.reconnectAttempts}/${this.maxReconnectAttempts})`)
        this.connect(token, sessionId)
      }, this.reconnectDelay * this.reconnectAttempts)
    }
  }

  disconnect(): void {
    this.stopHeartbeat()
    if (this.ws) {
      this.ws.close()
      this.ws = null
    }
  }
}
```

### Error Handling

| Error Code | Description | Client Action |
|------------|-------------|---------------|
| `1008` | Invalid token | Re-authenticate and reconnect |
| `unknown_type` | Unknown message type | Log error, ignore message |
| `invalid_subscription` | Invalid subscription | Remove invalid subscription |
| `connection_error` | Connection failed | Attempt reconnection |

---

## 📱 Component Structure

### File Organization
```
src/
├── components/
│   └── [module-name]/
│       ├── [ModuleName].tsx          # Main component
│       ├── [ModuleName].types.ts     # TypeScript types
│       ├── [ModuleName].hooks.ts    # Custom hooks
│       ├── [ModuleName].utils.ts    # Utility functions
│       └── components/              # Sub-components
│           ├── [SubComponent].tsx
│           └── ...
├── hooks/
│   └── use[ModuleName].ts           # Module-specific hooks
├── services/
│   └── [moduleName]Service.ts        # API service
└── stores/
    └── [moduleName]Store.ts          # State management (if needed)
```

### Component Example
```typescript
import React, { useState, useEffect } from 'react'
import { useQuery, useMutation } from '@tanstack/react-query'
import { [ModuleName]Service } from '@/services/[moduleName]Service'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'

interface [ModuleName]Props {
  // Props definition
}

export const [ModuleName]: React.FC<[ModuleName]Props> = (props) => {
  const [state, setState] = useState(/* initial state */)

  // Data fetching
  const { data, isLoading, error } = useQuery({
    queryKey: ['[moduleName]', /* params */],
    queryFn: () => [ModuleName]Service.getData(/* params */)
  })

  // Mutations
  const mutation = useMutation({
    mutationFn: [ModuleName]Service.createData,
    onSuccess: (data) => {
      // Handle success
    },
    onError: (error) => {
      // Handle error
    }
  })

  // WebSocket connection (if applicable)
  useEffect(() => {
    const ws = new WebSocketClient()
    ws.connect(token)
    
    ws.onEvent = (event, data) => {
      // Handle real-time updates
    }

    return () => {
      ws.disconnect()
    }
  }, [token])

  if (isLoading) return <LoadingSpinner />
  if (error) return <ErrorMessage error={error} />

  return (
    <div className="[module-name]-container">
      {/* Component JSX */}
    </div>
  )
}
```

---

## 🧪 Testing Requirements

### Unit Tests
- Component rendering
- User interactions
- State management
- Utility functions

### Integration Tests
- API calls
- WebSocket connections
- Error handling
- Loading states

### E2E Tests
- Complete user flows
- Cross-browser compatibility
- Mobile responsiveness

---

## 📚 References

- **Backend Controller**: `src/app/presentation/http/controllers/[path]/[controller].py`
- **Domain Entity**: `src/app/domain/[module]/entities/[entity].py`
- **Application Interactor**: `src/app/application/[module]/commands/[command].py`
- **Related Modules**: 
  - [Link to related module 1]
  - [Link to related module 2]

---

## 🔄 Changelog

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 1.0.0 | 2024-01-01 | Initial documentation | [Author] |
