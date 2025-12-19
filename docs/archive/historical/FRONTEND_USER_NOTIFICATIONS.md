# FRONTEND_USER_NOTIFICATIONS

## User Notifications Module

**User Type:** Authenticated User  
**Module:** Notifications - In-App & Push Notifications  
**Route:** `/notifications`  
**Platform:** Mobile (React Native) & Web  
**Version:** 1.0

---

## 📋 Module Overview

### Title
**Notifications** - Manage User Notifications and Alerts

### Description
Comprehensive notification system for displaying system notifications, user activity updates, subscription changes, and important platform events.

### Key Capabilities
- ✅ View notification history (paginated)
- ✅ Mark notifications as read
- ✅ Filter by category (info, warning, success, error)
- ✅ Real-time push via WebSocket
- ✅ Browser push notifications
- ✅ Notification badges/counters
- ✅ Action buttons (deep links)

---

## 🔌 API Integration

### 1. Get User Notifications

```typescript
// GET /api/v1/notifications/?page=1&per_page=10
// Description: Get paginated list of user's notifications
// Authentication: Required (Bearer token)
//
// Path Parameters: None
//
// Query Parameters:
//   - page: number - Page number (default: 1, min: 1)
//   - per_page: number - Items per page (default: 10, max: 100)

// Response:
interface NotificationListResponse {
  items: Notification[];
  page: number;
  per_page: number;
  total: number;
  unread_count: number;
}

interface Notification {
  id: string;
  user_id: number;
  title: string;
  body: string;
  category: 'info' | 'warning' | 'success' | 'error';
  action_url?: string; // Optional deep link
  action_text?: string; // Optional action button text
  read: boolean;
  created_at: string;
  read_at?: string;
}

const getNotifications = async (
  page: number = 1,
  perPage: number = 10
): Promise<NotificationListResponse> => {
  const response = await api.get('/api/v1/notifications/', {
    params: { page, per_page: perPage },
    headers: {
      Authorization: `Bearer ${localStorage.getItem('access_token')}`
    }
  });
  return response.data;
};

// Example Request:
// GET /api/v1/notifications/?page=1&per_page=20

// Example Response (200 OK):
{
  "items": [
    {
      "id": "notif_123",
      "user_id": 12345,
      "title": "Subscription Renewed",
      "body": "Your PRO subscription has been renewed successfully for another month",
      "category": "success",
      "action_url": "/settings/subscription",
      "action_text": "View Details",
      "read": false,
      "created_at": "2025-12-01T08:00:00Z",
      "read_at": null
    },
    {
      "id": "notif_122",
      "user_id": 12345,
      "title": "Risk Alert: High Volatility",
      "body": "AAVE protocol detected high volatility. Review your positions.",
      "category": "warning",
      "action_url": "/alerts/notif_122",
      "action_text": "View Alert",
      "read": true,
      "created_at": "2025-11-30T14:30:00Z",
      "read_at": "2025-11-30T15:00:00Z"
    },
    {
      "id": "notif_121",
      "user_id": 12345,
      "title": "New Feature Available",
      "body": "GraphRAG search is now available! Try semantic search across protocols.",
      "category": "info",
      "action_url": "/search",
      "action_text": "Try It Now",
      "read": true,
      "created_at": "2025-11-29T10:00:00Z",
      "read_at": "2025-11-29T12:00:00Z"
    }
  ],
  "page": 1,
  "per_page": 20,
  "total": 45,
  "unread_count": 8
}

// Example Error Response (401 Unauthorized):
{
  "error": {
    "code": "AUTHENTICATION_REQUIRED",
    "message": "Valid authentication token required",
    "details": {}
  }
}
```

---

### 2. Mark Notification as Read

```typescript
// PUT /api/v1/notifications/{notification_id}/read
// Description: Mark a specific notification as read
// Authentication: Required (Bearer token)
//
// Path Parameters:
//   - notification_id: string - ID of the notification to mark as read
//
// Query Parameters: None
// Request Body: None

// Response:
interface MarkReadResponse {
  success: boolean;
  notification_id: string;
  read_at: string;
}

const markNotificationAsRead = async (
  notificationId: string
): Promise<MarkReadResponse> => {
  const response = await api.put(
    `/api/v1/notifications/${notificationId}/read`,
    {},
    {
      headers: {
        Authorization: `Bearer ${localStorage.getItem('access_token')}`
      }
    }
  );
  return response.data;
};

// Example Request:
// PUT /api/v1/notifications/notif_123/read

// Example Response (200 OK):
{
  "success": true,
  "notification_id": "notif_123",
  "read_at": "2025-12-01T12:00:00Z"
}

// Example Error Response (404 Not Found):
{
  "error": {
    "code": "NOTIFICATION_NOT_FOUND",
    "message": "Notification with ID 'notif_999' not found",
    "details": {
      "notification_id": "notif_999"
    }
  }
}
```

---

### 3. Mark All Notifications as Read

```typescript
// PUT /api/v1/notifications/read-all
// Description: Mark all user's notifications as read
// Authentication: Required (Bearer token)
//
// Path Parameters: None
// Query Parameters: None
// Request Body: None

// Response:
interface MarkAllReadResponse {
  success: boolean;
  count: number; // Number of notifications marked as read
}

const markAllNotificationsAsRead = async (): Promise<MarkAllReadResponse> => {
  const response = await api.put(
    '/api/v1/notifications/read-all',
    {},
    {
      headers: {
        Authorization: `Bearer ${localStorage.getItem('access_token')}`
      }
    }
  );
  return response.data;
};

// Example Response (200 OK):
{
  "success": true,
  "count": 8
}
```

---

### 4. Delete Notification

```typescript
// DELETE /api/v1/notifications/{notification_id}
// Description: Delete a specific notification
// Authentication: Required (Bearer token)
//
// Path Parameters:
//   - notification_id: string - ID of the notification to delete
//
// Query Parameters: None
// Request Body: None

// Response:
interface DeleteNotificationResponse {
  success: boolean;
  notification_id: string;
}

const deleteNotification = async (
  notificationId: string
): Promise<DeleteNotificationResponse> => {
  const response = await api.delete(
    `/api/v1/notifications/${notificationId}`,
    {
      headers: {
        Authorization: `Bearer ${localStorage.getItem('access_token')}`
      }
    }
  );
  return response.data;
};

// Example Response (200 OK):
{
  "success": true,
  "notification_id": "notif_123"
}
```

---

### 5. Get Unread Count

```typescript
// GET /api/v1/notifications/unread-count
// Description: Get count of unread notifications (for badge display)
// Authentication: Required (Bearer token)
//
// Path Parameters: None
// Query Parameters: None
// Request Body: None

// Response:
interface UnreadCountResponse {
  unread_count: number;
}

const getUnreadCount = async (): Promise<UnreadCountResponse> => {
  const response = await api.get('/api/v1/notifications/unread-count', {
    headers: {
      Authorization: `Bearer ${localStorage.getItem('access_token')}`
    }
  });
  return response.data;
};

// Example Response (200 OK):
{
  "unread_count": 8
}
```

---

## 🔗 React Hooks

### useNotifications Hook

```typescript
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

export function useNotifications(page: number = 1, perPage: number = 10) {
  const queryClient = useQueryClient();
  
  const { data, isLoading, error } = useQuery({
    queryKey: ['notifications', page, perPage],
    queryFn: async () => {
      const response = await api.get('/api/v1/notifications/', {
        params: { page, per_page: perPage }
      });
      return response.data;
    },
  });
  
  const markAsRead = useMutation({
    mutationFn: async (notificationId: string) => {
      const response = await api.put(
        `/api/v1/notifications/${notificationId}/read`
      );
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notifications'] });
      queryClient.invalidateQueries({ queryKey: ['unread-count'] });
    },
  });
  
  const markAllAsRead = useMutation({
    mutationFn: async () => {
      const response = await api.put('/api/v1/notifications/read-all');
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notifications'] });
      queryClient.invalidateQueries({ queryKey: ['unread-count'] });
      toast.success('All notifications marked as read');
    },
  });
  
  const deleteNotification = useMutation({
    mutationFn: async (notificationId: string) => {
      await api.delete(`/api/v1/notifications/${notificationId}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notifications'] });
      toast.success('Notification deleted');
    },
  });
  
  return {
    notifications: data?.items || [],
    page: data?.page || 1,
    perPage: data?.per_page || 10,
    total: data?.total || 0,
    unreadCount: data?.unread_count || 0,
    isLoading,
    error,
    markAsRead: markAsRead.mutate,
    markAllAsRead: markAllAsRead.mutate,
    deleteNotification: deleteNotification.mutate,
  };
}
```

### useUnreadCount Hook

```typescript
export function useUnreadCount() {
  const { data, isLoading } = useQuery({
    queryKey: ['unread-count'],
    queryFn: async () => {
      const response = await api.get('/api/v1/notifications/unread-count');
      return response.data;
    },
    refetchInterval: 60000, // Refresh every minute
  });
  
  return {
    unreadCount: data?.unread_count || 0,
    isLoading,
  };
}
```

---

## 🎨 React Components

### NotificationBadge Component

```typescript
export function NotificationBadge() {
  const { unreadCount } = useUnreadCount();
  
  if (unreadCount === 0) return null;
  
  return (
    <span className="notification-badge">
      {unreadCount > 99 ? '99+' : unreadCount}
    </span>
  );
}
```

### NotificationItem Component

```typescript
interface NotificationItemProps {
  notification: Notification;
  onRead: (id: string) => void;
  onDelete: (id: string) => void;
}

export function NotificationItem({ 
  notification, 
  onRead, 
  onDelete 
}: NotificationItemProps) {
  const getCategoryIcon = (category: string) => {
    switch (category) {
      case 'success': return '✅';
      case 'warning': return '⚠️';
      case 'error': return '❌';
      default: return 'ℹ️';
    }
  };
  
  return (
    <div className={`notification-item ${notification.read ? 'read' : 'unread'}`}>
      <div className="notification-icon">
        {getCategoryIcon(notification.category)}
      </div>
      
      <div className="notification-content">
        <h4>{notification.title}</h4>
        <p>{notification.body}</p>
        <span className="notification-time">
          {formatDistanceToNow(new Date(notification.created_at))} ago
        </span>
      </div>
      
      <div className="notification-actions">
        {!notification.read && (
          <button onClick={() => onRead(notification.id)}>
            Mark as read
          </button>
        )}
        
        {notification.action_url && (
          <Link to={notification.action_url}>
            {notification.action_text || 'View'}
          </Link>
        )}
        
        <button onClick={() => onDelete(notification.id)}>
          Delete
        </button>
      </div>
    </div>
  );
}
```

---

## 🎭 User Flows

### Flow 1: View Notifications

```
1. User taps notification bell icon
   ↓
2. Notification badge shows unread count (8)
   ↓
3. GET /api/v1/notifications/?page=1&per_page=10
   ↓
4. Displays paginated list of notifications
   ↓
5. Unread notifications highlighted
   ↓
6. User scrolls to load more (page 2, 3...)
   ↓
7. User taps "Mark all as read"
   ↓
8. PUT /api/v1/notifications/read-all
   ↓
9. Badge count resets to 0
```

### Flow 2: Receive Real-Time Notification

```
1. User has app open
   ↓
2. WebSocket connection active
   WS /api/v1/ws/notifications
   ↓
3. Backend publishes new notification
   ↓
4. Client receives:
   { type: 'notification', notification: { ... } }
   ↓
5. In-app notification banner appears
   ↓
6. Notification badge count increments
   ↓
7. Browser push notification (if permission granted)
   ↓
8. User taps notification to view details
   ↓
9. PUT /api/v1/notifications/{id}/read
   ↓
10. Notification marked as read
```

---

## 📱 Push Notifications Integration

### Request Browser Permission

```typescript
const requestNotificationPermission = async () => {
  if (!('Notification' in window)) {
    console.log('Browser does not support notifications');
    return false;
  }
  
  if (Notification.permission === 'granted') {
    return true;
  }
  
  if (Notification.permission !== 'denied') {
    const permission = await Notification.requestPermission();
    return permission === 'granted';
  }
  
  return false;
};

// Usage in app initialization
useEffect(() => {
  requestNotificationPermission();
}, []);
```

### Show Browser Notification

```typescript
const showBrowserNotification = (notification: Notification) => {
  if (Notification.permission === 'granted') {
    const notif = new Notification(notification.title, {
      body: notification.body,
      icon: '/notification-icon.png',
      badge: '/badge-icon.png',
      tag: notification.id,
      requireInteraction: notification.category === 'error',
    });
    
    notif.onclick = () => {
      window.focus();
      if (notification.action_url) {
        window.location.href = notification.action_url;
      }
      notif.close();
    };
  }
};
```

---

*Document Version: 1.0*  
*Last Updated: December 1, 2025*  
*Module: Notifications*  
*Backend Status: ✅ 100% Implemented (5 endpoints)*  
*Frontend Status: ✅ Ready for Implementation*
