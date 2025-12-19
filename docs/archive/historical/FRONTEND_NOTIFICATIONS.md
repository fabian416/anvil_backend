# FRONTEND_NOTIFICATIONS

## Notifications Module

**User Type:** Authenticated User  
**Module:** Notifications - User Notification System  
**Route:** `/notifications`  
**Platform:** Mobile (React Native) & Web  
**Version:** 1.0

---

## 📋 Module Overview

### Title
**Notifications** - User Notification Management

### Description
Paginated notification system for delivering system messages, alerts, updates, and important information to users.

### Key Capabilities
- ✅ Paginated notification listing
- ✅ Real-time delivery
- ✅ Read/unread status
- ✅ Notification history
- ✅ Priority-based display

---

## 🔌 API Integration

### Get User Notifications

```typescript
// GET /api/v1/notifications/
// Description: Get paginated list of user's notifications
// Authentication: Required (Bearer token)

interface NotificationItem {
  id: number;
  user_id: number;
  type: string;
  title: string;
  message: string;
  data?: Record<string, any>;
  is_read: boolean;
  priority: 'low' | 'medium' | 'high' | 'urgent';
  created_at: string;
  read_at?: string;
}

interface GetNotificationsParams {
  page?: number; // Default: 1, min: 1
  per_page?: number; // Default: 10, min: 1, max: 100
}

const getUserNotifications = async (
  params: GetNotificationsParams = { page: 1, per_page: 10 }
): Promise<NotificationItem[]> => {
  const response = await api.get('/api/v1/notifications/', {
    params,
    headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` }
  });
  return response.data;
};

// Example Request:
GET /api/v1/notifications/?page=1&per_page=20

// Example Response (200 OK):
[
  {
    "id": 1,
    "user_id": 123,
    "type": "risk_alert",
    "title": "High Risk Detected",
    "message": "Protocol XYZ risk score increased to 8.5/10",
    "data": {
      "protocol_id": "xyz-uuid",
      "protocol_name": "XYZ Protocol",
      "risk_score": 8.5,
      "previous_score": 5.2
    },
    "is_read": false,
    "priority": "high",
    "created_at": "2025-12-01T12:00:00Z",
    "read_at": null
  },
  {
    "id": 2,
    "user_id": 123,
    "type": "portfolio_update",
    "title": "Portfolio Value Updated",
    "message": "Your portfolio value increased by 5.2% today",
    "data": {
      "value_change": 520.50,
      "percentage_change": 5.2,
      "total_value": 10520.50
    },
    "is_read": true,
    "priority": "medium",
    "created_at": "2025-12-01T11:00:00Z",
    "read_at": "2025-12-01T11:30:00Z"
  }
]
```

---

## 🔗 React Hooks

```typescript
export function useNotifications(page: number = 1, perPage: number = 10) {
  return useQuery({
    queryKey: ['notifications', page, perPage],
    queryFn: () => getUserNotifications({ page, per_page: perPage }),
    refetchInterval: 30000, // Refetch every 30 seconds
  });
}

export function useInfiniteNotifications(perPage: number = 20) {
  return useInfiniteQuery({
    queryKey: ['notifications', 'infinite'],
    queryFn: ({ pageParam = 1 }) => 
      getUserNotifications({ page: pageParam, per_page: perPage }),
    getNextPageParam: (lastPage, pages) => {
      // Return next page number if there are more notifications
      return lastPage.length === perPage ? pages.length + 1 : undefined;
    },
  });
}
```

---

## 🎨 React Components

### NotificationList Component

```typescript
import { useNotifications } from '@/hooks/useNotifications';

interface NotificationListProps {
  onNotificationClick?: (notification: NotificationItem) => void;
}

export function NotificationList({ onNotificationClick }: NotificationListProps) {
  const [page, setPage] = useState(1);
  const { data: notifications, isLoading, error } = useNotifications(page, 20);

  if (isLoading) return <LoadingSpinner />;
  if (error) return <ErrorMessage error={error} />;

  return (
    <div className="notification-list">
      {notifications?.map((notification) => (
        <NotificationItem
          key={notification.id}
          notification={notification}
          onClick={() => onNotificationClick?.(notification)}
        />
      ))}
      
      <Pagination
        currentPage={page}
        onPageChange={setPage}
        hasMore={notifications?.length === 20}
      />
    </div>
  );
}
```

### NotificationItem Component

```typescript
interface NotificationItemProps {
  notification: NotificationItem;
  onClick?: () => void;
}

export function NotificationItem({ notification, onClick }: NotificationItemProps) {
  const priorityColors = {
    low: 'bg-gray-100',
    medium: 'bg-blue-100',
    high: 'bg-orange-100',
    urgent: 'bg-red-100',
  };

  return (
    <div
      className={`notification-item ${priorityColors[notification.priority]} ${
        !notification.is_read ? 'font-bold' : ''
      }`}
      onClick={onClick}
    >
      <div className="notification-header">
        <h4>{notification.title}</h4>
        <span className="time">{formatTimeAgo(notification.created_at)}</span>
      </div>
      <p className="notification-message">{notification.message}</p>
      {!notification.is_read && <span className="unread-badge">New</span>}
    </div>
  );
}
```

### InfiniteNotificationList Component

```typescript
export function InfiniteNotificationList() {
  const {
    data,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
  } = useInfiniteNotifications(20);

  return (
    <div className="infinite-scroll-notifications">
      {data?.pages.map((page, pageIndex) => (
        <Fragment key={pageIndex}>
          {page.map((notification) => (
            <NotificationItem key={notification.id} notification={notification} />
          ))}
        </Fragment>
      ))}
      
      {hasNextPage && (
        <button onClick={() => fetchNextPage()} disabled={isFetchingNextPage}>
          {isFetchingNextPage ? 'Loading...' : 'Load More'}
        </button>
      )}
    </div>
  );
}
```

---

## 🎯 User Flows

### 1. View Notifications
```
User opens notifications
    ↓
Load first page (20 items)
    ↓
Display with unread badges
    ↓
User scrolls/pages through
    ↓
Load more as needed
```

### 2. Real-time Updates
```
New notification arrives
    ↓
Refetch notifications (30s interval)
    ↓
Update list with new items
    ↓
Show unread badge
    ↓
Display toast/banner (optional)
```

---

## ❌ Error Handling

```typescript
const { data, error } = useNotifications();

if (error) {
  // Handle different error types
  if (error.response?.status === 401) {
    // Redirect to login
    return <Navigate to="/login" />;
  }
  
  if (error.response?.status === 503) {
    return (
      <ErrorMessage 
        title="Service Unavailable"
        message="Notification service is temporarily unavailable. Please try again later."
      />
    );
  }
  
  return <GenericError error={error} />;
}
```

---

## 📱 Mobile Implementation

```typescript
// React Native
import { FlatList, RefreshControl } from 'react-native';

export function NotificationScreen() {
  const { data, isLoading, refetch } = useNotifications();
  const [refreshing, setRefreshing] = useState(false);

  const onRefresh = async () => {
    setRefreshing(true);
    await refetch();
    setRefreshing(false);
  };

  return (
    <FlatList
      data={data}
      renderItem={({ item }) => <NotificationItem notification={item} />}
      keyExtractor={(item) => item.id.toString()}
      refreshControl={
        <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
      }
    />
  );
}
```

---

## 🎯 Use Cases

### 1. Risk Alert Notification
```typescript
{
  "type": "risk_alert",
  "title": "Risk Level Increased",
  "message": "Aave protocol risk increased from 3.2 to 7.8",
  "priority": "high",
  "data": {
    "protocol_id": "aave-uuid",
    "old_score": 3.2,
    "new_score": 7.8
  }
}
```

### 2. Portfolio Update
```typescript
{
  "type": "portfolio_update",
  "title": "Daily Portfolio Summary",
  "message": "Your portfolio gained $1,250 today (+2.5%)",
  "priority": "medium",
  "data": {
    "change_usd": 1250,
    "change_percent": 2.5
  }
}
```

### 3. System Announcement
```typescript
{
  "type": "system_announcement",
  "title": "New Feature Available",
  "message": "ML-powered risk prediction is now available!",
  "priority": "low",
  "data": {
    "feature": "ml_prediction",
    "link": "/features/ml-prediction"
  }
}
```

---

*Document Version: 1.0*  
*Last Updated: December 1, 2025*  
*Module: Notifications*  
*Backend Status: ✅ 100% Implemented (1 endpoint)*  
*Frontend Status: ✅ Ready for Implementation*
