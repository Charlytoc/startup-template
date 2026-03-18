import { io, Socket } from 'socket.io-client';
import { REALTIME_URL } from '../config/env';

class RealtimeService {
  private socket: Socket | null = null;
  private listeners: Map<string, Set<Function>> = new Map();
  private connectionPromise: Promise<void> | null = null;
  private pendingActions: Array<() => void> = [];

  connect(): Promise<void> {
    console.log('🔌 [REALTIME] Connecting to realtime service...', REALTIME_URL);
    
    if (this.socket?.connected) {
      console.log('🔌 [REALTIME] Already connected to realtime service');
      return Promise.resolve();
    }

    // Return existing promise if connection is in progress
    if (this.connectionPromise) {
      console.log('🔌 [REALTIME] Connection already in progress, returning existing promise');
      return this.connectionPromise;
    }

    this.connectionPromise = new Promise((resolve, reject) => {
      this.socket = io(REALTIME_URL, {
        transports: ['polling', 'websocket'], // Try polling first
        timeout: 10000,
        forceNew: true,
        reconnection: true,
        reconnectionAttempts: 5,
        reconnectionDelay: 1000
      });

      this.socket.on('connect', () => {
        console.log('✅ [REALTIME] Connected to realtime service');
        console.log('🆔 [REALTIME] Socket ID:', this.socket?.id);
        
        // Execute pending actions
        console.log(`📋 [REALTIME] Executing ${this.pendingActions.length} pending actions`);
        this.pendingActions.forEach(action => action());
        this.pendingActions = [];
        
        resolve();
      });

      this.socket.on('disconnect', (reason) => {
        console.log('❌ [REALTIME] Disconnected from realtime service:', reason);
        this.connectionPromise = null;
      });

      this.socket.on('connect_error', (error) => {
        console.error('🚨 [REALTIME] Connection error:', error);
        console.error('🚨 [REALTIME] Error details:', {
          message: error.message,
          description: (error as any).description || 'No description',
          context: (error as any).context || 'No context',
          type: (error as any).type || 'No type'
        });
        reject(error);
      });

      this.socket.on('error', (error) => {
        console.error('🚨 [REALTIME] Socket error:', error);
      });

      this.socket.on('message', (data) => {
        console.log('📨 [REALTIME] Received message:', data);
        this.notifyListeners('message', data);
      });
      this.socket.on('agentic-chat-message', (data) => {
        console.log('📨 [REALTIME] Received agentic chat message:', data);
        this.notifyListeners('agentic-chat-message', data);
      });

      // Add timeout to detect if connection takes too long
      setTimeout(() => {
        if (!this.socket?.connected) {
          console.warn('⏰ [REALTIME] Connection timeout - still not connected after 10 seconds');
          reject(new Error('Connection timeout'));
        }
      }, 10000);
    });

    return this.connectionPromise;
  }

  disconnect() {
    if (this.socket) {
      console.log('🔌 [REALTIME] Disconnecting from realtime service');
      this.socket.disconnect();
      this.socket = null;
    }
  }

  async joinUser(userId: number) {
    const roomName = `user-${userId}`;
    console.log(`🚪 [REALTIME] Requesting to join user room: ${roomName}`);
    
    // If socket is connected, join immediately
    if (this.socket?.connected) {
      console.log(`✅ [REALTIME] Socket already connected, joining room immediately`);
      this.socket.emit('join-user', { userId });
      
      // Listen for room join confirmation
      this.socket.on('room-joined', (data) => {
        console.log('✅ [REALTIME] Successfully joined room:', data);
      });
      return;
    }

    // If not connected, add to pending actions
    console.log(`⏳ [REALTIME] Socket not connected yet, adding join to pending actions`);
    this.pendingActions.push(() => {
      console.log(`🚪 [REALTIME] Executing pending join for room: ${roomName}`);
      if (this.socket) {
        this.socket.emit('join-user', { userId });
        
        // Listen for room join confirmation
        this.socket.on('room-joined', (data) => {
          console.log('✅ [REALTIME] Successfully joined room:', data);
        });
      }
    });
  }

  on(event: string, callback: Function) {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, new Set());
    }
    this.listeners.get(event)?.add(callback);
    console.log(`👂 [REALTIME] Added listener for event: ${event}`);
  }

  off(event: string, callback: Function) {
    this.listeners.get(event)?.delete(callback);
    console.log(`🔇 [REALTIME] Removed listener for event: ${event}`);
  }

  private notifyListeners(event: string, data: any) {
    this.listeners.get(event)?.forEach((callback) => {
      callback(data);
    });
  }
}

export const realtimeService = new RealtimeService();

