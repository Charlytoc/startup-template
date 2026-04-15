# Real-Time Integration - Quick Reference

## Overview

This document provides a quick reference for integrating the real-time communication system across all components of Speaky.ai.

---

## Component Checklist

### ✅ Realtime Microservice (NodeJS + TypeScript)
**Location**: `/realtime`

**Key Responsibilities**:
- WebSocket server using Socket.io
- Subscribe to Redis PubSub channels
- Route messages to connected clients
- Manage connection authentication
- Handle rooms and namespaces

**Main Dependencies**:
- Express.js - HTTP server
- Socket.io - WebSocket management
- Redis client - PubSub subscription
- CORS - Cross-origin support

---

### ✅ Django Backend Integration
**Location**: `/django/core/`

**Integration Points**:

1. **Redis PubSub Publisher**
   - Add Redis client configuration
   - Create publisher service
   - Publish events from lesson coordinator
   - Publish events from AI agent

2. **Event Publishing Locations**:
   - `core/agent/lesson_coordinator.py` - AI messages
   - `core/tasks/generate_lesson.py` - Lesson events
   - `core/models/micro_task.py` - Task completion events
   - `core/models/skill_badge.py` - Badge earning events

3. **New Dependencies**:
   - `redis` Python package (already available for Celery)
   - Create `core/services/realtime_publisher.py`

---

### ✅ Mobile App Integration (React Native)
**Location**: `/mobile/`

**Integration Points**:

1. **Socket.io Client Manager**
   - Create `services/realtime.ts`
   - Singleton connection manager
   - Event subscription system
   - Automatic reconnection

2. **React Integration**:
   - Create `contexts/RealtimeContext.tsx`
   - Create `hooks/use-realtime.ts`
   - Connection state management
   - Event listeners in components

3. **Usage Locations**:
   - `app/learn/` - Lesson screens
   - `app/profile/` - Badge notifications
   - Global notification system

4. **New Dependencies**:
   - `socket.io-client` package

---

### ✅ Docker Compose Integration
**Location**: `/django/docker-compose.local.yml`

**Changes Needed**:

1. **Add Realtime Service**:
   - Service definition
   - Volume mounts for development
   - Environment variables
   - Network configuration
   - Port mapping

2. **Service Dependencies**:
   - Depends on Redis
   - Shares network with Django
   - Health check configuration

3. **Update Taskfile**:
   - Include realtime in `dev` command
   - Add realtime-specific commands
   - Log aggregation

---

## Communication Flow

### Lesson Message Example

```
1. User sends message in mobile app
   ↓ HTTP
2. Django API receives message
   ↓ Process
3. Django AI Agent generates response
   ↓ Redis PubSub Publish
4. Redis broadcasts to subscribers
   ↓ PubSub
5. Realtime service receives event
   ↓ Filter by user_id
6. Socket.io emits to client
   ↓ WebSocket
7. Mobile app displays message
```

---

## Redis Channel Naming Convention

### User Channels
- Pattern: `user:{user_id}`
- Purpose: User-specific messages
- Example: `user:123`

### Lesson Channels
- Pattern: `lesson:{lesson_id}`
- Purpose: Lesson-specific events
- Example: `lesson:456`

### Broadcast Channels
- Pattern: `broadcast:{scope}`
- Purpose: System-wide messages
- Example: `broadcast:all`, `broadcast:maintenance`

---

## Event Type Reference

### High Priority Events (Lesson Flow)
- `lesson:message` - AI tutor message
- `lesson:task_assigned` - New task
- `lesson:feedback` - Performance feedback
- `lesson:completed` - Lesson finished

### Medium Priority Events (Progress)
- `progress:skill_updated` - Skill change
- `progress:badge_earned` - Badge unlocked
- `progress:level_completed` - Level finished

### Low Priority Events (System)
- `system:notification` - General alert
- `system:error` - Error message
- `system:maintenance` - Maintenance notice

---

## Authentication Flow

### Mobile App → Realtime Service

1. **Connection Setup**:
   - Mobile app has API token from Django
   - Connect to Socket.io with token in handshake
   - Realtime validates token
   - Connection accepted/rejected

2. **Token Validation Options**:
   - **Option A**: HTTP call to Django `/auth/validate-token`
   - **Option B**: Redis cache lookup for active tokens
   - **Option C**: JWT validation if tokens are JWT

3. **Recommendation**: Use Redis cache for performance
   - Django caches valid tokens in Redis
   - Realtime service checks Redis first
   - Fallback to Django API if not cached

---

## Environment Variables

### Realtime Service
```
NODE_ENV=development
PORT=3001
REDIS_HOST=redis
REDIS_PASSWORD=
DJANGO_API_URL=http://django:8000
CORS_ORIGIN=*
LOG_LEVEL=debug
```

### Django
```
REDIS_REALTIME_HOST=redis
REDIS_REALTIME_PORT=6379
REDIS_REALTIME_DB=1
REALTIME_ENABLED=true
```

### Mobile App
```
REALTIME_URL=http://localhost:3001 (dev)
REALTIME_URL=wss://realtime.speaky.ai (prod)
```

---

## Port Configuration

### Development
- Django: `8000`
- Realtime: `3001`
- Redis: `6379`
- PostgreSQL: `5432`

### Production
- Django: Behind reverse proxy
- Realtime: Behind reverse proxy (WSS)
- Redis: Internal only
- PostgreSQL: Internal only

---

## Development Workflow

### Starting Services

```bash
# From django directory
./taskfile dev

# This should start:
# - PostgreSQL
# - Redis
# - Django
# - Celery
# - Realtime (NEW)
```

### Testing Realtime

1. **Health Check**: `curl http://localhost:3001/health`
2. **Socket.io Test**: Use Socket.io client tester
3. **Redis PubSub Test**: Use redis-cli to publish test events

### Debugging

**View Realtime Logs**:
```bash
docker-compose logs -f realtime
```

**View All Logs**:
```bash
docker-compose logs -f
```

**Redis Monitor**:
```bash
docker-compose exec redis redis-cli monitor
```

---

## Testing Strategy

### Unit Tests
- **Django**: Test event publishing
- **Realtime**: Test event routing
- **Mobile**: Test event handling

### Integration Tests
- End-to-end message flow
- Authentication flow
- Reconnection scenarios
- Error handling

### Manual Testing
1. Connect mobile app
2. Start lesson in Django
3. Verify messages arrive in mobile
4. Test disconnection/reconnection
5. Test multiple users

---

## Security Checklist

- ✅ Token-based authentication required
- ✅ CORS properly configured
- ✅ WSS (secure WebSocket) in production
- ✅ Rate limiting on connections
- ✅ Input validation on all events
- ✅ No sensitive data in logs
- ✅ Connection limits per user
- ✅ Token expiration handling

---

## Performance Targets

### Latency
- Connection establishment: < 100ms
- Message delivery: < 200ms
- Reconnection: < 5 seconds

### Capacity
- Concurrent connections: 1000+
- Messages per second: 10,000+
- Memory per connection: < 10KB

### Reliability
- Message delivery: 99.9%
- Uptime: 99.9%
- Reconnection success: 99%

---

## Monitoring Endpoints

### Realtime Service

**Health Check**: `GET /health`
- Returns: `{ status: "ok", uptime: seconds, connections: count }`

**Metrics**: `GET /metrics`
- Returns: Prometheus-style metrics

**Status**: `GET /status`
- Returns: Detailed service status

---

## Common Issues & Solutions

### Issue: Connection Fails
**Symptoms**: Mobile app can't connect
**Check**:
- Realtime service is running
- Port 3001 is accessible
- CORS configuration
- Token is valid

### Issue: Messages Not Delivered
**Symptoms**: Events published but not received
**Check**:
- Redis connection
- Channel names match
- User is connected
- Room membership

### Issue: High Latency
**Symptoms**: Slow message delivery
**Check**:
- Redis performance
- Network latency
- Connection count
- Event loop lag

---

## Rollout Plan

### Phase 1: Infrastructure (Week 1)
- ✅ Create realtime service
- ✅ Docker integration
- ✅ Basic WebSocket server
- ✅ Health checks

### Phase 2: Django Integration (Week 2)
- ✅ Redis publisher service
- ✅ Event publishing in lesson coordinator
- ✅ Token validation
- ✅ Testing

### Phase 3: Mobile Integration (Week 3)
- ✅ Socket.io client
- ✅ Connection manager
- ✅ React context
- ✅ Lesson UI integration

### Phase 4: Testing & Polish (Week 4)
- ✅ Integration testing
- ✅ Load testing
- ✅ Bug fixes
- ✅ Documentation

---

## Success Metrics

### Technical
- All messages delivered < 200ms
- 0 message loss
- < 1% disconnection rate
- Automatic reconnection works

### User Experience
- Real-time lesson conversations
- Instant feedback on tasks
- Immediate badge notifications
- No perceived lag

### Operational
- Easy to deploy
- Simple to monitor
- Clear logging
- Self-healing

---

## Next Actions

1. **Review Design**: Approve architecture and approach
2. **Setup Realtime**: Create TypeScript server structure
3. **Docker Integration**: Update docker-compose files
4. **Django Publisher**: Implement Redis publishing
5. **Mobile Client**: Create Socket.io manager
6. **Integration Test**: End-to-end testing
7. **Deploy**: Production deployment plan

---

## Support & Resources

### Documentation
- Main design: `REALTIME_DESIGN.md`
- Architecture: `/django/ARCHITECTURE.md`
- API docs: (to be created)

### Libraries
- Socket.io: https://socket.io/docs/
- Redis: https://redis.io/docs/
- Socket.io Client: https://socket.io/docs/v4/client-api/

### Monitoring
- Redis Monitor: `redis-cli monitor`
- Docker Logs: `docker-compose logs -f realtime`
- Health endpoint: `http://localhost:3001/health`

