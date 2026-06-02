/**
 * online_status_tracker.js
 * Tracks user online/offline status by sending periodic heartbeats to the server
 * When browser window is active (visible/focused), sends heartbeats
 * When browser window is inactive (hidden/unfocused), sends OFFLINE signal immediately
 */

class OnlineStatusTracker {
  constructor(options = {}) {
    this.heartbeatInterval = options.heartbeatInterval || 30000; // Send heartbeat every 30 seconds
    this.heartbeatUrl = options.heartbeatUrl || '/auth/heartbeat';
    this.offlineUrl = options.offlineUrl || '/auth/set-offline'; // Endpoint to explicitly set offline
    this.isLoggedIn = options.isLoggedIn || false;
    
    this.heartbeatTimer = null;
    this.isTabVisible = !document.hidden;
    this.isWindowFocused = document.hasFocus();
    
    // Initialize only if user is logged in
    if (this.isLoggedIn) {
      this.init();
    }
  }
  
  init() {
    // Listen for page visibility changes (tab becomes active/inactive)
    document.addEventListener('visibilitychange', () => this.handleVisibilityChange());
    
    // Listen for window focus/blur events
    window.addEventListener('focus', () => this.handleFocus());
    window.addEventListener('blur', () => this.handleBlur());
    
    // Listen for page unload (user closing tab/window)
    window.addEventListener('beforeunload', () => this.handlePageUnload());
    
    // Start sending heartbeats
    this.startHeartbeat();
    
    // Send initial heartbeat immediately
    this.sendHeartbeat();
    
    console.log('[OnlineStatus] Tracker initialized');
  }
  
  handleVisibilityChange() {
    this.isTabVisible = !document.hidden;
    
    if (document.hidden) {
      // Page is hidden (user switched to another tab in SAME window)
      console.log('[OnlineStatus] Tab hidden - stopping heartbeats');
      this.stopHeartbeat();
      // DO NOT send offline signal here - only on actual page unload
      // This prevents false offline when switching between windows
    } else {
      // Page is visible (user switched back to this tab)
      console.log('[OnlineStatus] Tab visible - resuming heartbeats');
      if (!this.heartbeatTimer) {
        this.startHeartbeat();
      }
      this.sendHeartbeat(); // Send immediate heartbeat
    }
  }
  
  handleFocus() {
    this.isWindowFocused = true;
    console.log('[OnlineStatus] Window focused - resuming heartbeats');
    // Always resume heartbeats when window gets focus if tab is still visible
    if (!this.heartbeatTimer && this.isTabVisible) {
      this.startHeartbeat();
    }
    // Send heartbeat to show activity (but don't set is_active = False if it fails)
    if (this.isTabVisible) {
      this.sendHeartbeat();
    }
  }
  
  handleBlur() {
    this.isWindowFocused = false;
    console.log('[OnlineStatus] Window blurred - will continue heartbeats if tab is visible');
    // Important: Do NOT stop heartbeats on blur! Just stop on actual tab visibility change
    // This prevents switching windows from incorrectly marking user as offline
  }
  
  handlePageUnload() {
    // User is closing the tab/window
    console.log('[OnlineStatus] Page unloading - setting offline');
    this.setOffline(true); // Use sendBeacon for reliability on unload
  }
  
  startHeartbeat() {
    if (this.heartbeatTimer) {
      return; // Already running
    }
    
    this.heartbeatTimer = setInterval(() => {
      this.sendHeartbeat();
    }, this.heartbeatInterval);
    
    console.log('[OnlineStatus] Heartbeat started (interval: ' + this.heartbeatInterval + 'ms)');
  }
  
  stopHeartbeat() {
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer);
      this.heartbeatTimer = null;
      console.log('[OnlineStatus] Heartbeat stopped');
    }
  }
  
  sendHeartbeat() {
    // Only send if tab is visible AND we have a session
    if (!this.isTabVisible) {
      console.log('[OnlineStatus] Tab not visible - skipping heartbeat');
      return;
    }
    
    console.log('[OnlineStatus] Sending heartbeat...');
    
    fetch(this.heartbeatUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      credentials: 'same-origin',
      body: JSON.stringify({
        timestamp: new Date().toISOString()
      })
    })
    .then(response => {
      if (!response.ok) {
        console.warn('[OnlineStatus] Heartbeat HTTP error:', response.status);
        return null;
      }
      return response.json();
    })
    .then(data => {
      if (data && data.success) {
        console.log('[OnlineStatus] Heartbeat sent successfully at', new Date().toLocaleTimeString());
      } else if (data) {
        console.warn('[OnlineStatus] Heartbeat API error:', data.message);
      }
    })
    .catch(error => {
      console.error('[OnlineStatus] Heartbeat network error:', error);
    });
  }
  
  setOffline(useBeacon = false) {
    // Send explicit offline signal to mark user as offline
    // Only called on page unload to avoid false offline signals
    
    if (useBeacon) {
      // Use sendBeacon for best-effort delivery on page unload
      // sendBeacon requires FormData, not JSON strings for reliability
      console.log('[OnlineStatus] Using sendBeacon for offline signal on page unload');
      const formData = new FormData();
      formData.append('timestamp', new Date().toISOString());
      
      // sendBeacon returns true/false to indicate if the request was queued
      const sent = navigator.sendBeacon(this.offlineUrl, formData);
      console.log('[OnlineStatus] sendBeacon result:', sent);
    } else {
      // Use regular fetch for immediate offline signal (not on unload)
      console.log('[OnlineStatus] Sending offline signal via fetch');
      fetch(this.offlineUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        credentials: 'same-origin',
        body: JSON.stringify({
          timestamp: new Date().toISOString()
        }),
        keepalive: true // Important for ensuring request completes even if page unloads
      })
      .then(response => response.json())
      .then(data => {
        if (data.success) {
          console.log('[OnlineStatus] Offline signal sent successfully');
        } else {
          console.warn('[OnlineStatus] Offline signal failed:', data.message);
        }
      })
      .catch(error => {
        console.error('[OnlineStatus] Offline signal error:', error);
      });
    }
  }
  
  destroy() {
    this.stopHeartbeat();
    document.removeEventListener('visibilitychange', () => this.handleVisibilityChange());
    window.removeEventListener('focus', () => this.handleFocus());
    window.removeEventListener('blur', () => this.handleBlur());
  }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
  // Check if user is logged in from session
  const isLoggedIn = document.body.dataset.loggedIn === 'true';
  
  if (isLoggedIn) {
    window.onlineStatusTracker = new OnlineStatusTracker({
      heartbeatInterval: 30000, // 30 seconds
      isLoggedIn: true
    });
  }
});
