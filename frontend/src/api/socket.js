import { io } from 'socket.io-client';

let connectionCount = 0;

/**
 * This is the main, shared socket connection to the backend server.
 */
const socket = io({
  autoConnect: false,
  transports: ['websocket'],
});

/**
 * Increments the connection counter and connects the shared socket if it's the first user.
 */
export const connectSharedSocket = () => {
  connectionCount++;
  if (connectionCount === 1) {
    console.log('First user of shared socket connected, opening connection.');
    socket.connect();
  }
};

/**
 * Decrements the connection counter and disconnects the shared socket if it's the last user.
 */
export const disconnectSharedSocket = () => {
  // Prevent counter from going below zero
  if (connectionCount > 0) {
    connectionCount--;
  }
  
  if (connectionCount === 0) {
    console.log('Last user of shared socket disconnected, closing connection.');
    socket.disconnect();
  }
};


/**
 * Creates a new, separate socket.io connection for monitoring individual runs.
 * @param {number} port The port number to connect to.
 * @returns {Socket} A new socket instance.
 */
export const createSocketConnection = (port) => {
  const URL = `http://${window.location.hostname}:${port}`;
  return io(URL, {
    autoConnect: false,
    transports: ['websocket'],
  });
};

// Export the shared instance as the default export
export default socket;
