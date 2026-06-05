# Active Status Detection

This file explains the online/offline status tracking feature.
It is written for people who know Python but may not know much JavaScript.

---

## What it does

The active status detection tracks whether a user is actively using the application.
It sends periodic signals (called "heartbeats") to the server to say "I am still here."
When the user closes the browser or tab, it notifies the server that they are offline.

The code lives in:

- `static/js/online_status_tracker.js`

---

## How it works

### 1. Create the tracker

When the page loads, a `OnlineStatusTracker` object is created.
Think of it like a Python class that manages the heartbeat logic.

```js
class OnlineStatusTracker {
  constructor(options = {}) {
    this.heartbeatInterval = options.heartbeatInterval || 30000;
    this.heartbeatUrl = options.heartbeatUrl || '/auth/heartbeat';
    this.offlineUrl = options.offlineUrl || '/auth/set-offline';
    this.isLoggedIn = options.isLoggedIn || false;
  }
}
```

### 2. Listen for user activity

The tracker listens for page visibility and focus events:

```js
document.addEventListener('visibilitychange', () => this.handleVisibilityChange());
window.addEventListener('focus', () => this.handleFocus());
window.addEventListener('blur', () => this.handleBlur());
window.addEventListener('beforeunload', () => this.handlePageUnload());
```

### 3. Send heartbeats periodically

Every 30 seconds (by default), the tracker sends a heartbeat to the server:

```js
sendHeartbeat() {
  fetch(this.heartbeatUrl, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ timestamp: new Date().toISOString() })
  })
}
```

This is like a Python function that sends a POST request to `/auth/heartbeat`.

### 4. Handle visibility changes

When the user switches tabs or windows, the tracker reacts:

- **Tab hidden**: Stop sending heartbeats (user not actively on this page)
- **Tab visible again**: Resume heartbeats
- **Page unload**: Send an offline signal

This prevents marking users as "offline" if they just switched to another tab temporarily.

### 5. Send offline signal on exit

When the user closes the browser or tab, the tracker sends an explicit offline signal:

```js
setOffline(useBeacon = true) {
  navigator.sendBeacon(this.offlineUrl, formData);
}
```

`sendBeacon` is a browser API that reliably sends data even as the page is closing.

---

## Why it matters

This feature helps the app know:

- Which users are currently online
- Which users are idle or away
- When to clean up old user sessions

---

## Python equivalent

If you were to implement this in Python, it might look like:

```python
class OnlineStatusTracker:
    def __init__(self, heartbeat_interval=30000):
        self.heartbeat_interval = heartbeat_interval
        self.is_logged_in = False
        self.heartbeat_timer = None
    
    def send_heartbeat(self):
        # POST to /auth/heartbeat with timestamp
        response = requests.post(
            '/auth/heartbeat',
            json={'timestamp': datetime.now().isoformat()}
        )
        return response.json()
    
    def set_offline(self):
        # POST to /auth/set-offline
        response = requests.post(
            '/auth/set-offline',
            json={'timestamp': datetime.now().isoformat()}
        )
        return response.json()
    
    def start_heartbeat(self):
        # Schedule heartbeat every 30 seconds (like setInterval)
        self.heartbeat_timer = threading.Timer(
            self.heartbeat_interval / 1000,
            self.send_heartbeat
        )
```

---

## Configuration

You can customize the tracker by passing options:

```js
new OnlineStatusTracker({
  heartbeatInterval: 60000,  // Send every 60 seconds
  heartbeatUrl: '/auth/heartbeat',
  offlineUrl: '/auth/set-offline',
  isLoggedIn: true
});
```
