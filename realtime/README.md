# Speaky.ai Realtime Service

Real-time communication microservice for Speaky.ai language learning platform.

## Purpose

This service provides WebSocket-based real-time communication between the Django backend and mobile clients, enabling instant delivery of lesson messages, progress updates, and notifications.

---

## Technology Stack

- **Runtime**: Node.js 20+
- **Language**: TypeScript
- **Framework**: Express.js
- **WebSocket**: Socket.io
- **Message Broker**: Redis PubSub
- **Container**: Docker

---

## Architecture

```
Mobile App → Socket.io Client → Realtime Service → Redis PubSub → Django
```

The realtime service acts as a bridge:
1. Maintains WebSocket connections with mobile clients
2. Subscribes to Redis PubSub channels
3. Routes messages from Django to appropriate clients

---

## Directory Structure

```
realtime/
├── src/
│   ├── server.ts              # Express server setup
│   ├── socket.ts              # Socket.io configuration
│   ├── redis.ts               # Redis PubSub client
│   ├── auth.ts                # Authentication logic
│   ├── handlers/              # Event handlers
│   │   ├── connection.ts      # Connection handling
│   │   ├── lesson.ts          # Lesson events
│   │   └── notification.ts    # Notification events
│   ├── services/              # Business logic
│   │   ├── validator.ts       # Token validation
│   │   └── router.ts          # Message routing
│   └── types/                 # TypeScript types
│       ├── events.ts          # Event type definitions
│       └── socket.ts          # Socket type extensions
├── tests/                     # Test files
├── Dockerfile                 # Production Dockerfile
├── Dockerfile.dev            # Development Dockerfile
├── package.json              # Dependencies
├── tsconfig.json             # TypeScript config
├── .env.example              # Environment template
└── README.md                 # This file
```

---

## Environment Variables

Create a `.env` file based on `.env.example`:

```env
NODE_ENV=development
PORT=3001
REDIS_HOST=redis
REDIS_PASSWORD=
DJANGO_API_URL=http://django:8000
CORS_ORIGIN=*
LOG_LEVEL=debug
```

---

## Development Setup

### Prerequisites
- Node.js 20+
- Redis (via Docker)
- Django backend running

### Local Development (Docker)

The realtime service is included in the main docker-compose setup:

```bash
# From django directory
./taskfile dev
```

This starts all services including realtime.

### Standalone Development (without Docker)

```bash
# Install dependencies
npm install

# Copy environment file
cp .env.example .env

# Run in development mode (with hot reload)
npm run dev

# Run tests
npm test

# Build for production
npm run build

# Run production build
npm start
```

---

## API Endpoints

### Health Check
```
GET /health
Response: { status: "ok", uptime: 123, connections: 45 }
```

### Metrics
```
GET /metrics
Response: Prometheus-style metrics
```

### Status
```
GET /status
Response: Detailed service status
```

---

## Socket.io Events

### Client → Server

**connect**
- Triggered on connection establishment
- Requires authentication token

**disconnect**
- Triggered on disconnection

### Server → Client

**lesson:message**
- AI tutor message during lesson
- Payload: `{ message: string, timestamp: string }`

**lesson:feedback**
- Performance feedback
- Payload: `{ feedback: object, score: number }`

**progress:badge_earned**
- New badge notification
- Payload: `{ badge: object, skill: object }`

**system:notification**
- General notification
- Payload: `{ title: string, message: string, type: string }`

---

## Authentication

### Token Validation

Clients must provide a valid API token during connection:

```typescript
// Client side
const socket = io('http://localhost:3001', {
  auth: {
    token: 'your-api-token'
  }
});
```

The server validates the token before accepting the connection.

---

## Redis Channels

### Subscription Pattern

The service subscribes to these channel patterns:

- `user:*` - User-specific messages
- `lesson:*` - Lesson-specific messages
- `broadcast:*` - System-wide broadcasts

### Message Format

All Redis messages follow this structure:

```json
{
  "event_type": "lesson",
  "event_name": "message",
  "user_id": 123,
  "lesson_id": 456,
  "data": { ... },
  "timestamp": "2024-01-01T12:00:00Z",
  "message_id": "unique-id"
}
```

---

## Testing

### Unit Tests
```bash
npm test
```

### Integration Tests
```bash
npm run test:integration
```

### Manual Testing

Use Socket.io client tester or create a simple HTML client:

```html
<!DOCTYPE html>
<html>
<head>
  <script src="https://cdn.socket.io/4.5.4/socket.io.min.js"></script>
</head>
<body>
  <script>
    const socket = io('http://localhost:3001', {
      auth: { token: 'test-token' }
    });
    
    socket.on('connect', () => {
      console.log('Connected:', socket.id);
    });
    
    socket.on('lesson:message', (data) => {
      console.log('Message:', data);
    });
  </script>
</body>
</html>
```

---

## Monitoring

### Logs

View realtime service logs:
```bash
docker-compose logs -f realtime
```

### Metrics

Access metrics endpoint:
```bash
curl http://localhost:3001/metrics
```

### Redis Monitor

Watch Redis PubSub activity:
```bash
docker-compose exec redis redis-cli monitor
```

---

## Deployment

### Docker Production Build

```bash
docker build -t speaky-realtime:latest .
docker run -p 3001:3001 --env-file .env speaky-realtime:latest
```

### Environment Considerations

**Development**:
- Hot reload enabled
- Verbose logging
- CORS: `*`

**Production**:
- Compiled TypeScript
- Error-only logging
- Specific CORS origins
- WSS (secure WebSocket)
- Load balancing support

---

## Troubleshooting

### Connection Issues

**Problem**: Clients can't connect
**Solutions**:
- Check if service is running: `curl http://localhost:3001/health`
- Verify CORS configuration
- Check token validation
- Review firewall rules

### Message Delivery Issues

**Problem**: Events not reaching clients
**Solutions**:
- Check Redis connection
- Verify channel names
- Confirm user is connected
- Check room membership

### Performance Issues

**Problem**: High latency or dropped connections
**Solutions**:
- Monitor Redis performance
- Check connection count
- Review event loop lag
- Scale horizontally if needed

---

## Contributing

### Code Style
- TypeScript strict mode
- ESLint for linting
- Prettier for formatting
- No comments in code (per project convention)

### Testing Requirements
- Unit tests for all services
- Integration tests for flows
- Minimum 80% coverage

---

## Resources

### Documentation
- [Main Design](./REALTIME_DESIGN.md)
- [Integration Guide](./INTEGRATION_SUMMARY.md)
- [Architecture Overview](../django/ARCHITECTURE.md)

### External Resources
- [Socket.io Documentation](https://socket.io/docs/)
- [Redis PubSub](https://redis.io/docs/manual/pubsub/)
- [TypeScript Handbook](https://www.typescriptlang.org/docs/)

---

## License

Proprietary - Speaky.ai

---

## Support

For questions or issues, contact the development team.

