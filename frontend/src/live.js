export function subscribe(id, key, onMessage, onStatus) {
  let socket;
  let timer;
  let stopped = false;
  let terminal = false;

  function connect() {
    if (stopped || terminal) return;
    onStatus('connecting');
    const protocol = location.protocol === 'https:' ? 'wss:' : 'ws:';
    socket = new WebSocket(`${protocol}//${location.host}/api/shares/${id}/live`);
    socket.onopen = () => socket.send(JSON.stringify({type: 'subscribe', key}));
    socket.onmessage = ({data}) => {
      const message = JSON.parse(data);
      if (['room_full', 'invalid_link', 'revoked'].includes(message.type)) terminal = true;
      if (message.type === 'ready') onStatus('connected');
      onMessage(message);
    };
    socket.onclose = () => {
      if (stopped || terminal) return;
      onStatus('reconnecting');
      timer = setTimeout(connect, 1000);
    };
  }

  connect();
  return {
    close() {
      stopped = true;
      clearTimeout(timer);
      socket?.close();
    },
    retry() {
      terminal = false;
      clearTimeout(timer);
      connect();
    },
  };
}
