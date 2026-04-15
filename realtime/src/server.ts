import express from 'express';
import { createServer } from 'http';
import { Server } from 'socket.io';
import cors from 'cors';
import dotenv from 'dotenv';
import { initRedis } from './redis';

dotenv.config();

const app = express();
const httpServer = createServer(app);
const io = new Server(httpServer, {
  cors: {
    origin: '*',
    methods: ['GET', 'POST']
  },
  transports: ['websocket', 'polling'],
  allowEIO3: true,
  pingTimeout: 60000,
  pingInterval: 25000
});

app.use(cors());
app.use(express.json());

// Add detailed request logging
app.use((req, res, next) => {
  const timestamp = new Date().toISOString();
  console.log(`📡 [HTTP] ${req.method} ${req.url} - ${timestamp}`);
  console.log(`📡 [HTTP] Headers:`, JSON.stringify(req.headers, null, 2));
  console.log(`📡 [HTTP] Query:`, JSON.stringify(req.query, null, 2));
  if (req.body && Object.keys(req.body).length > 0) {
    console.log(`📡 [HTTP] Body:`, JSON.stringify(req.body, null, 2));
  }
  next();
});

const PORT = process.env.PORT || 3001;
const startTime = Date.now();

app.get('/health', (req, res) => {
  const uptime = Date.now() - startTime;
  console.log(`🏥 [HEALTH] Health check requested - Uptime: ${uptime}ms`);
  console.log(`🏥 [HEALTH] Request headers:`, JSON.stringify(req.headers, null, 2));
  res.json({ 
    status: 'ok', 
    uptime: `${uptime}ms`,
    timestamp: new Date().toISOString(),
    service: 'realtime-microservice',
    port: PORT,
    redis_host: process.env.REDIS_HOST || 'localhost',
    redis_port: 6379,
    connections: io.engine.clientsCount
  });
});

// Add a simple test endpoint
app.get('/test', (req, res) => {
  console.log(`🧪 [TEST] Test endpoint called`);
  console.log(`🧪 [TEST] Request headers:`, JSON.stringify(req.headers, null, 2));
  res.json({ 
    message: 'Test endpoint working',
    timestamp: new Date().toISOString(),
    client_ip: req.ip,
    user_agent: req.get('User-Agent')
  });
});

console.log('🚀 [REALTIME] Starting realtime microservice...');
console.log(`📡 [REALTIME] Environment: ${process.env.NODE_ENV || 'development'}`);
console.log(`🔧 [REALTIME] Configuration:`);
console.log(`  - Port: ${PORT}`);
console.log(`  - Redis Host: ${process.env.REDIS_HOST || 'localhost'}`);
console.log(`  - Redis Port: 6379`);
console.log(`  - All environment variables:`, JSON.stringify(process.env, null, 2));

// Initialize Redis connection
initRedis(io).then(() => {
  console.log('✅ [REALTIME] Redis connection initialized successfully');
}).catch((error) => {
  console.error('❌ [REALTIME] Failed to initialize Redis:', error);
  process.exit(1);
});

// Socket.io connection handling with detailed logging
io.on('connection', (socket) => {
  const connectionTime = new Date().toISOString();
  console.log(`🔌 [SOCKET] Client connected: ${socket.id} at ${connectionTime}`);
  
  socket.conn.on('upgrade', () => {
    console.log(`⬆️ [SOCKET] Transport upgraded for ${socket.id}: ${socket.conn.transport.name}`);
  });
  
  socket.on('join-lesson', (data) => {
    console.log(`🚪 [SOCKET] Client ${socket.id} joining lesson:`, data);
    const roomName = `lesson-${data.lessonId}`;
    socket.join(roomName);
    console.log(`✅ [SOCKET] Client ${socket.id} joined room: ${roomName}`);
    console.log(`📊 [SOCKET] Room ${roomName} now has ${io.sockets.adapter.rooms.get(roomName)?.size || 0} clients`);
    socket.emit('room-joined', { room: roomName, lessonId: data.lessonId });
  });

  socket.on('join-user', (data) => {
    console.log(`🚪 [SOCKET] Client ${socket.id} joining user room:`, data);
    const roomName = `user-${data.userId}`;
    socket.join(roomName);
    console.log(`✅ [SOCKET] Client ${socket.id} joined room: ${roomName}`);
    console.log(`📊 [SOCKET] Room ${roomName} now has ${io.sockets.adapter.rooms.get(roomName)?.size || 0} clients`);
    socket.emit('room-joined', { room: roomName, userId: data.userId });
  });
  
  socket.on('disconnect', (reason) => {
    console.log(`❌ [SOCKET] Client ${socket.id} disconnected: ${reason}`);
    console.log(`📊 [SOCKET] Total connected clients: ${io.sockets.sockets.size}`);
  });
  
  socket.on('error', (error) => {
    console.error(`🚨 [SOCKET] Client ${socket.id} error:`, error);
  });
  
  // Log any other events
  socket.onAny((event, ...args) => {
    if (event !== 'join-lesson') {
      console.log(`📨 [SOCKET] Client ${socket.id} emitted event '${event}':`, args);
    }
  });
});

// Log server startup
httpServer.listen(PORT, () => {
  console.log(`🎉 [REALTIME] Server running on port ${PORT}`);
  console.log(`🌐 [REALTIME] Health check available at http://localhost:${PORT}/health`);
  console.log(`🧪 [REALTIME] Test endpoint available at http://localhost:${PORT}/test`);
  console.log(`🔗 [REALTIME] Socket.io endpoint: http://localhost:${PORT}/socket.io/`);
  console.log(`🔗 [REALTIME] Socket.io WebSocket: ws://localhost:${PORT}/socket.io/`);
  console.log(`📊 [REALTIME] Server ready to accept connections`);
});

// Add error handling
httpServer.on('error', (error) => {
  console.error('🚨 [REALTIME] HTTP Server error:', error);
});

process.on('uncaughtException', (error) => {
  console.error('🚨 [REALTIME] Uncaught Exception:', error);
});

process.on('unhandledRejection', (reason, promise) => {
  console.error('🚨 [REALTIME] Unhandled Rejection at:', promise, 'reason:', reason);
});