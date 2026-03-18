# Real-Time Communication System - Design Document

## Overview

The real-time communication system enables bidirectional, event-driven communication between the Django backend and mobile clients. This system uses WebSocket technology to deliver instant updates during language learning lessons, allowing the AI tutor to send messages, feedback, and updates in real-time.

---

## Architecture Overview

```
┌─────────────────┐
│  Mobile Client  │
│ (React Native)  │
└────────┬────────┘
         │ WebSocket (Socket.io)
         │
┌────────▼────────────────────────┐
│   Realtime Microservice         │
│   (Node.js + Express)           │
│   - Socket.io Server            │
│   - Connection Management       │
│   - Room Management             │
│   - Authentication              │
└────────┬────────────────────────┘
         │ Redis PubSub
         │ (Subscribe)
┌────────▼────────────────────────┐
│   Redis Server                  │
│   - PubSub Channel              │
│   - Message Broker              │
└────────▲────────────────────────┘
         │ Redis PubSub
         │ (Publish)
┌────────┴────────────────────────┐
│   Django Backend                │
│   - API Endpoints               │
│   - Lesson Coordinator          │
│   - AI Agent                    │
└─────────────────────────────────┘
```

---

## System Components

### 1. Django Backend (Publisher)

**Responsibility**: Generate and publish real-time events

**Key Functions**:
- Execute lesson logic and AI interactions
- Publish events to Redis PubSub channels
- Manage lesson state and progression
- Generate AI responses and feedback

**Event Types to Publish**:
- Lesson messages from AI tutor
- Task updates and feedback
- Progress notifications
- Score updates
- Error notifications

### 2. Redis Server (Message Broker)

**Responsibility**: Route messages between Django and Realtime service

**Key Functions**:
- Act as PubSub broker
- Handle multiple channels per user/lesson
- Ensure message delivery
- Support pattern-based subscriptions

**Channel Structure**:
- User-specific channels: `user:{user_id}`
- Lesson-specific channels: `lesson:{lesson_id}`
- Broadcast channels: `broadcast:all`

### 3. Realtime Microservice (Subscriber & WebSocket Server)

**Responsibility**: Bridge between Redis and WebSocket clients

**Key Functions**:
- Maintain WebSocket connections with clients
- Subscribe to Redis PubSub channels
- Route messages to appropriate client connections
- Manage connection lifecycle
- Handle authentication and authorization
- Implement room-based messaging

**Technology Stack**:
- Node.js runtime
- Express.js for HTTP endpoints
- Socket.io for WebSocket management
- TypeScript for type safety
- Redis client for PubSub subscription

### 4. Mobile Client (WebSocket Consumer)

**Responsibility**: Receive and display real-time updates

**Key Functions**:
- Establish WebSocket connection
- Authenticate connection with API token
- Listen for specific event types
- Handle reconnection automatically
- Display messages in UI

---

## Communication Flow

### Message Flow Pattern

#### 1. Client Connection Flow
1. Mobile app authenticates with Django API
2. Mobile app receives API token
3. Mobile app connects to Realtime service via Socket.io
4. Mobile app sends authentication token
5. Realtime service validates token with Django/Redis
6. Connection established and client joins user room

#### 2. Message Publishing Flow
1. User action triggers Django logic (e.g., starts lesson)
2. Django processes request and generates response
3. Django publishes event to Redis channel
4. Redis broadcasts to subscribers
5. Realtime service receives event
6. Realtime service identifies target client(s)
7. Realtime service emits event via Socket.io
8. Mobile client receives and processes event

#### 3. Lesson Message Flow (Primary Use Case)
1. User sends message in lesson
2. Django API processes message through AI agent
3. AI generates response
4. Django publishes `lesson:message` event to Redis
5. Realtime service receives event
6. Realtime service emits to user's active connection
7. Mobile app displays AI tutor message
8. Process repeats for conversation

---

## Event Types & Message Format

### Standard Event Structure

All events follow a consistent structure:

**Fields**:
- `event_type`: String identifier for event category
- `event_name`: Specific event name
- `user_id`: Target user ID
- `lesson_id`: Related lesson ID (optional)
- `data`: Event-specific payload
- `timestamp`: ISO 8601 timestamp
- `message_id`: Unique message identifier

### Core Event Categories

#### Lesson Events
- `lesson:started` - Lesson begins
- `lesson:message` - AI tutor message
- `lesson:task_assigned` - New task available
- `lesson:task_completed` - Task finished
- `lesson:feedback` - Performance feedback
- `lesson:completed` - Lesson finished
- `lesson:paused` - Lesson paused

#### Progress Events
- `progress:skill_updated` - Skill progress change
- `progress:badge_earned` - New badge awarded
- `progress:level_completed` - Level finished

#### System Events
- `system:notification` - General notification
- `system:error` - Error occurred
- `system:maintenance` - Maintenance alert

---

## Authentication & Authorization

### Connection Authentication

**Flow**:
1. Client provides API token during Socket.io handshake
2. Realtime service validates token
3. Token validation options:
   - **Option A**: HTTP request to Django API
   - **Option B**: Redis cache lookup
   - **Option C**: JWT verification (if tokens are JWT)

**Security Measures**:
- Require authentication for all connections
- Validate token on every connection
- Implement token refresh mechanism
- Support token revocation
- Rate limit connection attempts

### Message Authorization

**Principles**:
- Only send messages to authorized users
- Implement room-based access control
- Validate lesson participation
- Prevent cross-user message leaking

---

## Scalability Considerations

### Horizontal Scaling

**Realtime Service**:
- Multiple instances can run simultaneously
- Use Redis adapter for Socket.io
- Implement sticky sessions (optional)
- Share connection state via Redis

**Load Balancing**:
- WebSocket-aware load balancer
- Session affinity recommended
- Health check endpoints

### Connection Management

**Strategies**:
- Connection pooling
- Automatic reconnection on client
- Heartbeat/ping-pong mechanism
- Graceful disconnection handling
- Connection timeout policies

---

## Room & Namespace Strategy

### Room Structure

**User Rooms**:
- Each user joins: `user:{user_id}`
- Private messages to specific user
- Persistent across app usage

**Lesson Rooms**:
- Active lesson: `lesson:{lesson_id}`
- User joins when lesson starts
- User leaves when lesson ends
- Allows for multi-user lessons (future)

**Broadcast Room**:
- All connected clients
- System-wide announcements
- Maintenance notifications

### Namespace Organization

**Namespaces**:
- `/` - Default namespace (general)
- `/lessons` - Lesson-specific events
- `/notifications` - System notifications
- `/admin` - Admin-only events (future)

---

## Error Handling & Resilience

### Connection Failures

**Client Side**:
- Automatic reconnection with exponential backoff
- Queue messages during disconnection
- Retry failed message delivery
- Fallback to polling if WebSocket fails

**Server Side**:
- Graceful degradation
- Circuit breaker pattern
- Dead letter queue for failed messages
- Logging and monitoring

### Message Delivery Guarantees

**Strategies**:
- At-least-once delivery for critical events
- Idempotent message handlers
- Message deduplication using message_id
- Acknowledgment system for important events

---

## Monitoring & Observability

### Key Metrics

**Connection Metrics**:
- Active connections count
- Connection/disconnection rate
- Authentication success/failure rate
- Average connection duration

**Message Metrics**:
- Messages published per second
- Message delivery latency
- Failed message count
- Message queue depth

**Performance Metrics**:
- CPU and memory usage
- Redis connection pool status
- Event loop lag
- WebSocket frame rate

### Logging Strategy

**Log Levels**:
- Connection events (info)
- Message routing (debug)
- Errors and failures (error)
- Authentication attempts (warn)

---

## Docker Integration

### Service Definition

**New Service**: `realtime`

**Dependencies**:
- Redis (must be available)
- Django (for authentication)

**Network**:
- Same Docker network as Django and Redis
- Exposed port for WebSocket connections
- Internal communication with Redis

**Environment Variables**:
- Redis connection details
- Django API URL
- Port configuration
- Authentication settings

### Development Setup

**Docker Compose Integration**:
- Add realtime service to docker-compose.local.yml
- Configure service dependencies
- Set up volume mounts for development
- Enable hot reload for TypeScript

**Task Integration**:
- Include realtime service in `./taskfile dev`
- Ensure proper startup order
- Handle service health checks
- Aggregate logs from all services

---

## Mobile App Integration

### Socket.io Client Implementation

**Client Manager**:
- Singleton pattern for connection management
- Automatic reconnection logic
- Event subscription interface
- Connection state management
- Token refresh integration

**Usage Pattern**:
- Initialize on app startup
- Connect when user authenticated
- Disconnect on logout
- Reconnect on app resume

### Event Handling

**Handler Registration**:
- Type-safe event handlers
- Subscribe/unsubscribe methods
- Event filtering by context
- Error boundary for handlers

**UI Integration**:
- React hooks for event subscription
- Context provider for connection state
- Component-level event listeners
- Notification system integration

---

## Security Considerations

### Transport Security

**WebSocket Security**:
- Use WSS (WebSocket Secure) in production
- TLS/SSL certificate management
- Prevent man-in-the-middle attacks

### Data Security

**Message Encryption**:
- End-to-end encryption (optional)
- Sensitive data filtering
- PII handling compliance

### Access Control

**Authorization**:
- Token-based authentication
- Rate limiting per user
- IP-based restrictions (optional)
- Connection limits per user

---

## Performance Optimization

### Connection Optimization

**Strategies**:
- Connection pooling
- Binary protocol for Socket.io
- Compression for large payloads
- Efficient serialization (MessagePack)

### Message Optimization

**Techniques**:
- Batch similar events
- Debounce rapid updates
- Delta updates vs full state
- Pagination for large datasets

---

## Testing Strategy

### Unit Testing

**Components to Test**:
- Redis PubSub integration
- Socket.io event handlers
- Authentication logic
- Room management

### Integration Testing

**Scenarios**:
- End-to-end message flow
- Connection lifecycle
- Error handling
- Reconnection logic

### Load Testing

**Metrics**:
- Concurrent connections
- Messages per second
- Latency under load
- Resource usage

---

## Migration Path

### Phase 1: Foundation (Current Goal)
- Set up realtime microservice
- Implement basic WebSocket server
- Configure Redis PubSub
- Create client connection manager
- Integrate with docker-compose

### Phase 2: Lesson Integration
- Implement lesson message events
- Connect Django lesson coordinator
- Update mobile lesson UI
- Test real-time lesson flow

### Phase 3: Enhanced Features
- Add progress events
- Implement notification system
- Add admin monitoring
- Performance optimization

### Phase 4: Advanced Features
- Multi-user lessons
- Typing indicators
- Read receipts
- Message history sync

---

## Alternative Approaches Considered

### Alternative 1: Direct WebSocket in Django
**Pros**: Simpler architecture, fewer services
**Cons**: Poor scalability, blocks Django workers, complex to maintain

### Alternative 2: Server-Sent Events (SSE)
**Pros**: Simpler than WebSocket, HTTP-based
**Cons**: Unidirectional only, less efficient, browser limitations

### Alternative 3: Long Polling
**Pros**: Maximum compatibility, simple fallback
**Cons**: High latency, resource intensive, not true real-time

**Selected Approach**: Dedicated microservice with Socket.io provides the best balance of performance, scalability, and maintainability.

---

## Success Criteria

### Technical Metrics
- WebSocket connection latency < 100ms
- Message delivery latency < 200ms
- Support 1000+ concurrent connections
- 99.9% message delivery success
- Automatic reconnection within 5 seconds

### User Experience
- Seamless real-time lesson conversations
- No noticeable lag in AI responses
- Reliable connection across network changes
- Graceful degradation on poor connections

---

## Next Steps

1. **Review and Approve**: Validate design with team
2. **Create Realtime Service**: Implement TypeScript server
3. **Update Docker Compose**: Add realtime service
4. **Django Redis Integration**: Implement PubSub publisher
5. **Mobile Client**: Implement Socket.io client manager
6. **Testing**: Integration and load testing
7. **Documentation**: API documentation and usage guides

---

## Appendix

### Technology Choices Rationale

**Socket.io vs Native WebSocket**:
- Socket.io provides automatic reconnection
- Fallback to polling
- Built-in room support
- Better mobile support

**Redis PubSub vs Message Queue**:
- PubSub is lightweight for real-time
- No persistence needed
- Lower latency
- Simpler implementation

**TypeScript vs JavaScript**:
- Type safety reduces bugs
- Better IDE support
- Easier maintenance
- Self-documenting code

**Microservice vs Monolith**:
- Independent scaling
- Technology flexibility
- Fault isolation
- Easier deployment

