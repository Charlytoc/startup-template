import { createClient } from 'redis';
import { Server } from 'socket.io';

const REDIS_HOST = process.env.REDIS_HOST || 'localhost';
const REDIS_PORT = parseInt(process.env.REDIS_PORT || '6379');
const REDIS_PASSWORD = process.env.REDIS_PASSWORD || undefined;

export async function initRedis(io: Server) {
  const client = createClient({
    socket: {
      host: REDIS_HOST,
      port: REDIS_PORT
    },
    password: REDIS_PASSWORD
  });

  client.on('error', (err) => {
    console.error('Redis Client Error:', err);
  });

  await client.connect();
  await client.subscribe('bridge', (message) => {
    try {
      const m = JSON.parse(message);
      const { listener, event, data } = m;
      io.to(listener).emit(event, data);
    } catch (error) {
      console.error('Error processing Redis message:', error);
    }
  });
}

