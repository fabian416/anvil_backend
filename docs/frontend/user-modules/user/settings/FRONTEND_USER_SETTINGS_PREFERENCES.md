# FRONTEND_USER_SETTINGS_PREFERENCES

## User Settings - Preferences Module

**User Type:** Authenticated User  
**Module:** Settings - User Preferences & Customization  
**Route:** `/settings/preferences`  
**Platform:** Mobile (React Native) & Web  
**Version:** 1.0

---

## 📋 Module Overview

### Title
**User Preferences** - Complete Customization and Personalization Settings

### Description
Comprehensive preference management system allowing users to customize their DeFi experience. Includes risk tolerance, chain preferences, favorite protocols, search settings, notification preferences, and display customization.

### Key Capabilities
- ✅ Risk tolerance settings (conservative/moderate/aggressive)
- ✅ Preferred blockchain chains selection
- ✅ Favorite protocols management
- ✅ Excluded protocols blacklist
- ✅ Saved search presets
- ✅ Search behavior settings
- ✅ Notification preferences (risk alerts, push, email)
- ✅ Severity threshold configuration
- ✅ Display settings (theme, currency, compact mode)
- ✅ Analytics opt-in/out
- ✅ Real-time sync across devices

---

## 👤 User Stories

### US-USER-PREFS-001: Set Risk Tolerance
**As a** user  
**I want to** set my risk tolerance level  
**So that** the system recommends appropriate protocols and warns me about risky operations

**Acceptance Criteria:**
- Three levels: Conservative, Moderate, Aggressive
- Visual explanation of each level
- Applies to all protocol recommendations
- Affects risk score display thresholds
- Clear impact description

---

### US-USER-PREFS-002: Select Preferred Chains
**As a** user  
**I want to** select my preferred blockchain networks  
**So that** I see relevant protocols and operations for my chains

**Acceptance Criteria:**
- Multi-select chain picker
- Common chains prominently displayed
- Search functionality
- Shows protocol count per chain
- Persists across sessions

---

### US-USER-PREFS-003: Manage Favorite Protocols
**As a** user  
**I want to** mark protocols as favorites  
**So that** I can quickly access them and receive priority updates

**Acceptance Criteria:**
- One-tap add to favorites
- Favorites shown first in lists
- Remove from favorites easily
- Favorites synced across devices
- Max 20 favorites limit

---

### US-USER-PREFS-004: Configure Notifications
**As a** user  
**I want to** control which notifications I receive  
**So that** I only get alerts that matter to me

**Acceptance Criteria:**
- Enable/disable by type (risk, price, protocol updates)
- Enable/disable by channel (push, email, WebSocket)
- Set minimum severity threshold
- Quiet hours configuration
- Preview notification examples

---

### US-USER-PREFS-005: Save Search Presets
**As a** user  
**I want to** save my frequent search configurations  
**So that** I can quickly re-run them without re-entering criteria

**Acceptance Criteria:**
- Name and save search configurations
- Include query + filters
- Max 10 saved searches
- One-tap re-run
- Delete saved searches

---

### US-USER-PREFS-006: Customize Display Settings
**As a** user  
**I want to** customize how the app looks and feels  
**So that** I have a comfortable and personalized experience

**Acceptance Criteria:**
- Dark/light theme selection
- Default currency (USD, EUR, etc.)
- Compact mode for dense information
- Font size preference
- Language selection (future)

---

### US-USER-PREFS-007: Manage Search Behavior
**As a** user  
**I want to** configure how search works for me  
**So that** I get results matching my expectations

**Acceptance Criteria:**
- Set similarity threshold (0-1)
- Default risk filter level
- Enable/disable search history
- Max history entries
- Clear search history option

---

### US-USER-PREFS-008: Control Analytics
**As a** user  
**I want to** opt in or out of analytics tracking  
**So that** I control my data privacy

**Acceptance Criteria:**
- Clear explanation of what's tracked
- One-toggle opt-in/out
- Immediate effect
- No impact on core functionality
- Export my data option

---

## 🖼️ Wireframes

### View 1: Preferences Main Screen (Mobile)

```
┌─────────────────────────────────────┐
│  [←]    Preferences                 │
├─────────────────────────────────────┤
│                                     │
│  Risk & Safety                      │
│  ┌─────────────────────────────────┐│
│  │  🎯 Risk Tolerance              ││
│  │     Moderate                    ││
│  │     Conservative to aggressive  ││
│  │                              → ││
│  └─────────────────────────────────┘│
│                                     │
│  ┌─────────────────────────────────┐│
│  │  ⛔ Excluded Protocols          ││
│  │     3 protocols blocked         ││
│  │     Manage blacklist            ││
│  │                              → ││
│  └─────────────────────────────────┘│
│                                     │
│  DeFi Preferences                   │
│  ┌─────────────────────────────────┐│
│  │  ⛓️  Preferred Chains            ││
│  │     Ethereum, Arbitrum, Base    ││
│  │     +2 more                     ││
│  │                              → ││
│  └─────────────────────────────────┘│
│                                     │
│  ┌─────────────────────────────────┐│
│  │  ⭐ Favorite Protocols          ││
│  │     8 favorites                 ││
│  │     Quick access list           ││
│  │                              → ││
│  └─────────────────────────────────┘│
│                                     │
│  Search & Discovery                 │
│  ┌─────────────────────────────────┐│
│  │  💾 Saved Searches              ││
│  │     5 search presets            ││
│  │     Manage saved searches       ││
│  │                              → ││
│  └─────────────────────────────────┘│
│                                     │
│  ┌─────────────────────────────────┐│
│  │  🔍 Search Settings             ││
│  │     Similarity threshold: 0.7   ││
│  │     Risk filter: Medium         ││
│  │                              → ││
│  └─────────────────────────────────┘│
│                                     │
│  Notifications                      │
│  ┌─────────────────────────────────┐│
│  │  🔔 Notification Preferences    ││
│  │     Risk alerts, Push, Email    ││
│  │     Severity: Medium & above    ││
│  │                              → ││
│  └─────────────────────────────────┘│
│                                     │
│  Display                            │
│  ┌─────────────────────────────────┐│
│  │  🎨 Theme & Display             ││
│  │     Dark mode • USD • Compact   ││
│  │                              → ││
│  └─────────────────────────────────┘│
│                                     │
│  Privacy                            │
│  ┌─────────────────────────────────┐│
│  │  📊 Analytics                   ││
│  │     [✓] Enable analytics        ││
│  │     Help improve the app        ││
│  │                              → ││
│  └─────────────────────────────────┘│
│                                     │
└─────────────────────────────────────┘
```

---

### View 2: Risk Tolerance Selection

```
┌─────────────────────────────────────┐
│  [←]    Risk Tolerance              │
├─────────────────────────────────────┤
│                                     │
│  Choose your risk comfort level     │
│                                     │
│  ┌─────────────────────────────────┐│
│  │  🛡️  CONSERVATIVE                ││
│  │                                 ││
│  │  • Low-risk protocols only      ││
│  │  • Maximum safety warnings      ││
│  │  • Conservative APY estimates   ││
│  │  • Strict risk thresholds       ││
│  │                                 ││
│  │  Recommended for beginners      ││
│  │                                 ││
│  │     [Select Conservative]       ││
│  └─────────────────────────────────┘│
│                                     │
│  ┌─────────────────────────────────┐│
│  │  ⚖️  MODERATE          ✓ Active ││
│  │                                 ││
│  │  • Balanced risk/reward         ││
│  │  • Standard warnings            ││
│  │  • Realistic APY estimates      ││
│  │  • Moderate risk thresholds     ││
│  │                                 ││
│  │  Recommended for most users     ││
│  │                                 ││
│  │     [Currently Selected]        ││
│  └─────────────────────────────────┘│
│                                     │
│  ┌─────────────────────────────────┐│
│  │  ⚡ AGGRESSIVE                   ││
│  │                                 ││
│  │  • Higher risk protocols OK     ││
│  │  • Fewer warnings               ││
│  │  • Optimistic APY estimates     ││
│  │  • Relaxed risk thresholds      ││
│  │                                 ││
│  │  For experienced users only     ││
│  │                                 ││
│  │     [Select Aggressive]         ││
│  └─────────────────────────────────┘│
│                                     │
│  ⚠️  This affects all protocol      │
│     recommendations and risk        │
│     warnings throughout the app.    │
│                                     │
└─────────────────────────────────────┘
```

---

### View 3: Preferred Chains Selection

```
┌─────────────────────────────────────┐
│  [←]    Preferred Chains        [✓] │
├─────────────────────────────────────┤
│                                     │
│  [Search chains...]                 │
│                                     │
│  Popular Chains                     │
│  ┌─────────────────────────────────┐│
│  │  [✓] Ethereum                   ││
│  │      2,847 protocols            ││
│  └─────────────────────────────────┘│
│  ┌─────────────────────────────────┐│
│  │  [✓] Arbitrum                   ││
│  │      1,205 protocols            ││
│  └─────────────────────────────────┘│
│  ┌─────────────────────────────────┐│
│  │  [✓] Base                       ││
│  │      847 protocols              ││
│  └─────────────────────────────────┘│
│  ┌─────────────────────────────────┐│
│  │  [ ] Optimism                   ││
│  │      632 protocols              ││
│  └─────────────────────────────────┘│
│  ┌─────────────────────────────────┐│
│  │  [✓] Polygon                    ││
│  │      1,456 protocols            ││
│  └─────────────────────────────────┘│
│                                     │
│  Other Chains                       │
│  ┌─────────────────────────────────┐│
│  │  [ ] Avalanche                  ││
│  │      523 protocols              ││
│  └─────────────────────────────────┘│
│  ┌─────────────────────────────────┐│
│  │  [✓] BNB Chain                  ││
│  │      894 protocols              ││
│  └─────────────────────────────────┘│
│  ┌─────────────────────────────────┐│
│  │  [ ] Solana                     ││
│  │      378 protocols              ││
│  └─────────────────────────────────┘│
│                                     │
│  Selected: 5 chains                 │
│                                     │
└─────────────────────────────────────┘
```

---

### View 4: Favorite Protocols Management

```
┌─────────────────────────────────────┐
│  [←]    Favorite Protocols          │
├─────────────────────────────────────┤
│                                     │
│  [Search protocols...]              │
│                                     │
│  Your Favorites (8/20)              │
│  ┌─────────────────────────────────┐│
│  │  ⭐ Aave V3                      ││
│  │     Ethereum, Arbitrum, Base    ││
│  │     Risk: 2.1 • TVL: $6.2B      ││
│  │                           [✕]   ││
│  └─────────────────────────────────┘│
│  ┌─────────────────────────────────┐│
│  │  ⭐ Uniswap V3                   ││
│  │     Ethereum, Polygon           ││
│  │     Risk: 1.8 • TVL: $4.5B      ││
│  │                           [✕]   ││
│  └─────────────────────────────────┘│
│  ┌─────────────────────────────────┐│
│  │  ⭐ Curve Finance                ││
│  │     Ethereum, Arbitrum          ││
│  │     Risk: 2.3 • TVL: $3.8B      ││
│  │                           [✕]   ││
│  └─────────────────────────────────┘│
│  ┌─────────────────────────────────┐│
│  │  ⭐ Lido                         ││
│  │     Ethereum                    ││
│  │     Risk: 2.0 • TVL: $28.4B     ││
│  │                           [✕]   ││
│  └─────────────────────────────────┘│
│  ┌─────────────────────────────────┐│
│  │  ⭐ GMX                          ││
│  │     Arbitrum, Avalanche         ││
│  │     Risk: 3.2 • TVL: $845M      ││
│  │                           [✕]   ││
│  └─────────────────────────────────┘│
│                                     │
│  [+ Add More Favorites]             │
│                                     │
│  💡 Favorites appear first in       │
│     searches and get priority       │
│     updates                         │
│                                     │
└─────────────────────────────────────┘
```

---

### View 5: Notification Preferences

```
┌─────────────────────────────────────┐
│  [←]    Notification Preferences    │
├─────────────────────────────────────┤
│                                     │
│  Alert Types                        │
│  ┌─────────────────────────────────┐│
│  │  [✓] Risk Alerts                ││
│  │      Protocol risk changes      ││
│  └─────────────────────────────────┘│
│  ┌─────────────────────────────────┐│
│  │  [✓] Protocol Updates           ││
│  │      New features, changes      ││
│  └─────────────────────────────────┘│
│  ┌─────────────────────────────────┐│
│  │  [ ] Price Alerts               ││
│  │      Token price movements      ││
│  └─────────────────────────────────┘│
│  ┌─────────────────────────────────┐│
│  │  [✓] Transaction Alerts         ││
│  │      Tx confirmations, fails    ││
│  └─────────────────────────────────┘│
│                                     │
│  Delivery Channels                  │
│  ┌─────────────────────────────────┐│
│  │  [✓] Push Notifications         ││
│  │      Mobile & browser push      ││
│  └─────────────────────────────────┘│
│  ┌─────────────────────────────────┐│
│  │  [ ] Email Notifications        ││
│  │      Send to alice@example.com  ││
│  └─────────────────────────────────┘│
│  ┌─────────────────────────────────┐│
│  │  [✓] In-App Alerts              ││
│  │      Real-time WebSocket        ││
│  └─────────────────────────────────┘│
│                                     │
│  Severity Threshold                 │
│  ┌─────────────────────────────────┐│
│  │  Only notify for:               ││
│  │                                 ││
│  │  ( ) Low & above                ││
│  │  (•) Medium & above   ✓ Active  ││
│  │  ( ) High & above               ││
│  │  ( ) Critical only              ││
│  └─────────────────────────────────┘│
│                                     │
│  Quiet Hours                        │
│  ┌─────────────────────────────────┐│
│  │  [ ] Enable quiet hours         ││
│  │      23:00 - 08:00              ││
│  │      (Only critical alerts)     ││
│  └─────────────────────────────────┘│
│                                     │
│  [Preview Notification]             │
│                                     │
└─────────────────────────────────────┘
```

---

### View 6: Saved Searches Management

```
┌─────────────────────────────────────┐
│  [←]    Saved Searches              │
├─────────────────────────────────────┤
│                                     │
│  Your Saved Searches (5/10)         │
│                                     │
│  ┌─────────────────────────────────┐│
│  │  💾 Low Risk Staking            ││
│  │     "staking" • Risk: Low       ││
│  │     Ethereum, Polygon           ││
│  │                                 ││
│  │     [Run Search]          [✕]  ││
│  └─────────────────────────────────┘│
│                                     │
│  ┌─────────────────────────────────┐│
│  │  💾 High Yield Arbitrum         ││
│  │     "yield" • Risk: Any         ││
│  │     Arbitrum                    ││
│  │                                 ││
│  │     [Run Search]          [✕]  ││
│  └─────────────────────────────────┘│
│                                     │
│  ┌─────────────────────────────────┐│
│  │  💾 Aave V3 Protocols           ││
│  │     "aave v3" • Risk: Low-Med   ││
│  │     All Chains                  ││
│  │                                 ││
│  │     [Run Search]          [✕]  ││
│  └─────────────────────────────────┘│
│                                     │
│  ┌─────────────────────────────────┐│
│  │  💾 Liquid Staking Tokens       ││
│  │     "liquid staking"            ││
│  │     Ethereum                    ││
│  │                                 ││
│  │     [Run Search]          [✕]  ││
│  └─────────────────────────────────┘│
│                                     │
│  ┌─────────────────────────────────┐│
│  │  💾 DEX Aggregators             ││
│  │     "dex aggregator" • Any      ││
│  │     Ethereum, Arbitrum          ││
│  │                                 ││
│  │     [Run Search]          [✕]  ││
│  └─────────────────────────────────┘│
│                                     │
│  [+ Create New Saved Search]        │
│                                     │
│  💡 Quickly re-run frequent         │
│     searches with one tap           │
│                                     │
└─────────────────────────────────────┘
```

---

## 🔌 API Integration

### Get User Preferences

```typescript
// GET /api/v1/users/me/preferences
interface UserPreferencesResponse {
  user_id: string;
  risk_tolerance: 'conservative' | 'moderate' | 'aggressive';
  preferred_chains: string[];
  preferred_categories: string[];
  excluded_protocols: string[];
  favorite_protocols: string[];
  search_settings: {
    default_similarity_threshold: number;
    default_risk_filter: string | null;
    search_history_enabled: boolean;
  };
  notification_settings: {
    risk_alerts_enabled: boolean;
    push_enabled: boolean;
    min_severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  };
  default_currency: string;
  theme: 'dark' | 'light';
}

const getPreferences = async (): Promise<UserPreferencesResponse> => {
  const response = await api.get('/api/v1/users/me/preferences');
  return response.data;
};
```

### Update Risk Tolerance

```typescript
// PUT /api/v1/users/me/preferences/risk-tolerance
interface UpdateRiskToleranceRequest {
  risk_tolerance: 'conservative' | 'moderate' | 'aggressive';
}

const updateRiskTolerance = async (
  riskTolerance: string
): Promise<UserPreferencesResponse> => {
  const response = await api.put(
    '/api/v1/users/me/preferences/risk-tolerance',
    { risk_tolerance: riskTolerance }
  );
  return response.data;
};
```

### Update Chain Preferences

```typescript
// PUT /api/v1/users/me/preferences/chains
interface UpdateChainPreferencesRequest {
  preferred_chains: string[];
}

const updateChainPreferences = async (
  chains: string[]
): Promise<UserPreferencesResponse> => {
  const response = await api.put('/api/v1/users/me/preferences/chains', {
    preferred_chains: chains,
  });
  return response.data;
};
```

### Save Search Preset

```typescript
// POST /api/v1/users/me/preferences/search/saved
interface SaveSearchRequest {
  name: string;
  query: string;
  filters: Record<string, any>;
}

interface SavedSearchResponse {
  id: string;
  name: string;
  query: string;
  filters: Record<string, any>;
  created_at: string;
}

const saveSearch = async (
  search: SaveSearchRequest
): Promise<SavedSearchResponse> => {
  const response = await api.post(
    '/api/v1/users/me/preferences/search/saved',
    search
  );
  return response.data;
};
```

### Delete Saved Search

```typescript
// DELETE /api/v1/users/me/preferences/search/saved/:search_id
const deleteSavedSearch = async (searchId: string): Promise<void> => {
  await api.delete(`/api/v1/users/me/preferences/search/saved/${searchId}`);
};
```

### Manage Favorite Protocols

```typescript
// POST /api/v1/users/me/preferences/favorites/protocols/:protocol_id
const addFavoriteProtocol = async (protocolId: string): Promise<void> => {
  await api.post(
    `/api/v1/users/me/preferences/favorites/protocols/${protocolId}`
  );
};

// DELETE /api/v1/users/me/preferences/favorites/protocols/:protocol_id
const removeFavoriteProtocol = async (protocolId: string): Promise<void> => {
  await api.delete(
    `/api/v1/users/me/preferences/favorites/protocols/${protocolId}`
  );
};
```

---

## 🎨 Motion Design

### Preference Update Animation (Framer Motion)

```typescript
import { motion } from 'framer-motion';

function PreferenceCard({ title, value, onChange }: PreferenceCardProps) {
  const [isUpdating, setIsUpdating] = useState(false);
  
  const handleChange = async (newValue: any) => {
    setIsUpdating(true);
    await onChange(newValue);
    setIsUpdating(false);
  };
  
  return (
    <motion.div
      animate={{
        scale: isUpdating ? 0.98 : 1,
        opacity: isUpdating ? 0.6 : 1,
      }}
      transition={{ duration: 0.2 }}
      className="bg-white rounded-lg p-4 border border-gray-200"
    >
      <div className="flex items-center justify-between">
        <span className="font-semibold">{title}</span>
        {isUpdating && (
          <motion.div
            animate={{ rotate: 360 }}
            transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
          >
            ⟳
          </motion.div>
        )}
      </div>
      <div className="mt-2">{value}</div>
    </motion.div>
  );
}
```

### Risk Tolerance Selector Animation

```typescript
function RiskToleranceSelector({ value, onChange }: RiskToleranceSelectorProps) {
  const options = [
    {
      value: 'conservative',
      label: 'Conservative',
      icon: '🛡️',
      color: '#10B981',
    },
    { value: 'moderate', label: 'Moderate', icon: '⚖️', color: '#3B82F6' },
    { value: 'aggressive', label: 'Aggressive', icon: '⚡', color: '#EF4444' },
  ];
  
  return (
    <div className="space-y-3">
      {options.map((option) => (
        <motion.button
          key={option.value}
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          animate={{
            borderColor: value === option.value ? option.color : '#E5E7EB',
            backgroundColor:
              value === option.value ? `${option.color}10` : 'white',
          }}
          onClick={() => onChange(option.value)}
          className="w-full p-4 border-2 rounded-xl text-left"
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <span className="text-3xl">{option.icon}</span>
              <div>
                <div className="font-bold">{option.label}</div>
                <div className="text-sm text-gray-600">
                  {option.value === 'conservative' && 'Maximum safety'}
                  {option.value === 'moderate' && 'Balanced approach'}
                  {option.value === 'aggressive' && 'Higher risk tolerance'}
                </div>
              </div>
            </div>
            {value === option.value && (
              <motion.div
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                style={{ color: option.color }}
              >
                ✓
              </motion.div>
            )}
          </div>
        </motion.button>
      ))}
    </div>
  );
}
```

### Saved Search Success Animation

```typescript
function SaveSearchButton({ onSave }: SaveSearchButtonProps) {
  const [saved, setSaved] = useState(false);
  
  const handleSave = async () => {
    await onSave();
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };
  
  return (
    <motion.button
      whileTap={{ scale: 0.95 }}
      onClick={handleSave}
      className="px-4 py-2 rounded-lg"
      animate={{
        backgroundColor: saved ? '#10B981' : '#3B82F6',
      }}
    >
      <motion.div
        animate={{
          x: saved ? [0, 10, 0] : 0,
        }}
        transition={{ duration: 0.5 }}
        className="flex items-center gap-2 text-white"
      >
        {saved ? '✓ Saved!' : '💾 Save Search'}
      </motion.div>
    </motion.button>
  );
}
```

---

## 🎨 React Native Motion (Reanimated)

### Preference Toggle Animation

```typescript
import Animated, {
  useAnimatedStyle,
  useSharedValue,
  withSpring,
  withTiming,
} from 'react-native-reanimated';

function PreferenceToggle({ value, onToggle, label }: ToggleProps) {
  const offset = useSharedValue(value ? 1 : 0);
  const backgroundColor = useSharedValue(value ? '#10B981' : '#D1D5DB');
  
  const animatedStyle = useAnimatedStyle(() => ({
    transform: [{ translateX: withSpring(offset.value * 24) }],
  }));
  
  const containerStyle = useAnimatedStyle(() => ({
    backgroundColor: withTiming(backgroundColor.value),
  }));
  
  const handleToggle = () => {
    const newValue = !value;
    offset.value = newValue ? 1 : 0;
    backgroundColor.value = newValue ? '#10B981' : '#D1D5DB';
    onToggle(newValue);
  };
  
  return (
    <View style={styles.toggleContainer}>
      <Text style={styles.label}>{label}</Text>
      <Pressable onPress={handleToggle}>
        <Animated.View style={[styles.track, containerStyle]}>
          <Animated.View style={[styles.thumb, animatedStyle]} />
        </Animated.View>
      </Pressable>
    </View>
  );
}
```

---

## 📱 Component Specifications

### PreferencesScreen Component

```typescript
interface PreferencesScreenProps {
  userId: string;
}

function PreferencesScreen({ userId }: PreferencesScreenProps) {
  const { preferences, isLoading, updatePreference } = usePreferences();
  
  const sections = [
    {
      title: 'Risk & Safety',
      items: [
        {
          id: 'risk-tolerance',
          icon: '🎯',
          label: 'Risk Tolerance',
          value: preferences?.risk_tolerance || 'moderate',
          route: '/settings/preferences/risk-tolerance',
        },
        {
          id: 'excluded-protocols',
          icon: '⛔',
          label: 'Excluded Protocols',
          value: `${preferences?.excluded_protocols.length || 0} blocked`,
          route: '/settings/preferences/excluded-protocols',
        },
      ],
    },
    {
      title: 'DeFi Preferences',
      items: [
        {
          id: 'chains',
          icon: '⛓️',
          label: 'Preferred Chains',
          value: preferences?.preferred_chains.slice(0, 2).join(', ') || '',
          route: '/settings/preferences/chains',
        },
        {
          id: 'favorites',
          icon: '⭐',
          label: 'Favorite Protocols',
          value: `${preferences?.favorite_protocols.length || 0} favorites`,
          route: '/settings/preferences/favorites',
        },
      ],
    },
    // ... more sections
  ];
  
  if (isLoading) {
    return <LoadingSpinner />;
  }
  
  return (
    <ScrollView style={styles.container}>
      {sections.map((section) => (
        <PreferenceSection key={section.title} section={section} />
      ))}
    </ScrollView>
  );
}
```

### RiskToleranceSelector Component

```typescript
interface RiskToleranceSelectorProps {
  value: 'conservative' | 'moderate' | 'aggressive';
  onChange: (value: string) => Promise<void>;
}

function RiskToleranceSelector({ value, onChange }: RiskToleranceSelectorProps) {
  const [isUpdating, setIsUpdating] = useState(false);
  
  const handleSelect = async (newValue: string) => {
    setIsUpdating(true);
    try {
      await onChange(newValue);
      toast.success('Risk tolerance updated');
    } catch (error) {
      toast.error('Failed to update risk tolerance');
    } finally {
      setIsUpdating(false);
    }
  };
  
  return (
    <div className="space-y-4">
      <p className="text-gray-600">
        Choose your risk comfort level. This affects protocol recommendations
        and risk warnings.
      </p>
      <RiskOptions
        value={value}
        onChange={handleSelect}
        disabled={isUpdating}
      />
    </div>
  );
}
```

### SavedSearchesList Component

```typescript
interface SavedSearchesListProps {
  searches: SavedSearch[];
  onRun: (search: SavedSearch) => void;
  onDelete: (searchId: string) => Promise<void>;
}

function SavedSearchesList({ searches, onRun, onDelete }: SavedSearchesListProps) {
  return (
    <div className="space-y-3">
      {searches.map((search) => (
        <SavedSearchCard
          key={search.id}
          search={search}
          onRun={() => onRun(search)}
          onDelete={() => onDelete(search.id)}
        />
      ))}
      
      {searches.length === 0 && (
        <EmptyState
          icon="💾"
          title="No saved searches"
          description="Save your frequent search configurations for quick access"
        />
      )}
      
      {searches.length < 10 && (
        <Link to="/settings/preferences/saved-searches/new">
          <button className="w-full py-3 border-2 border-dashed border-gray-300 rounded-lg text-gray-600 hover:border-blue-500 hover:text-blue-600">
            + Create New Saved Search
          </button>
        </Link>
      )}
    </div>
  );
}
```

---

## 🔗 React Hooks

### usePreferences Hook

```typescript
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

export function usePreferences() {
  const queryClient = useQueryClient();
  
  const { data: preferences, isLoading } = useQuery({
    queryKey: ['user-preferences'],
    queryFn: async () => {
      const response = await api.get('/api/v1/users/me/preferences');
      return response.data;
    },
  });
  
  const updateRiskTolerance = useMutation({
    mutationFn: async (riskTolerance: string) => {
      await api.put('/api/v1/users/me/preferences/risk-tolerance', {
        risk_tolerance: riskTolerance,
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['user-preferences'] });
    },
  });
  
  const updateChainPreferences = useMutation({
    mutationFn: async (chains: string[]) => {
      await api.put('/api/v1/users/me/preferences/chains', {
        preferred_chains: chains,
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['user-preferences'] });
    },
  });
  
  const addFavoriteProtocol = useMutation({
    mutationFn: async (protocolId: string) => {
      await api.post(
        `/api/v1/users/me/preferences/favorites/protocols/${protocolId}`
      );
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['user-preferences'] });
    },
  });
  
  const removeFavoriteProtocol = useMutation({
    mutationFn: async (protocolId: string) => {
      await api.delete(
        `/api/v1/users/me/preferences/favorites/protocols/${protocolId}`
      );
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['user-preferences'] });
    },
  });
  
  return {
    preferences,
    isLoading,
    updateRiskTolerance: updateRiskTolerance.mutate,
    updateChainPreferences: updateChainPreferences.mutate,
    addFavoriteProtocol: addFavoriteProtocol.mutate,
    removeFavoriteProtocol: removeFavoriteProtocol.mutate,
  };
}
```

### useSavedSearches Hook

```typescript
export function useSavedSearches() {
  const queryClient = useQueryClient();
  
  const saveSearch = useMutation({
    mutationFn: async (search: SaveSearchRequest) => {
      const response = await api.post(
        '/api/v1/users/me/preferences/search/saved',
        search
      );
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['saved-searches'] });
      toast.success('Search saved successfully');
    },
  });
  
  const deleteSavedSearch = useMutation({
    mutationFn: async (searchId: string) => {
      await api.delete(
        `/api/v1/users/me/preferences/search/saved/${searchId}`
      );
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['saved-searches'] });
      toast.success('Search deleted');
    },
  });
  
  return {
    saveSearch: saveSearch.mutate,
    deleteSavedSearch: deleteSavedSearch.mutate,
    isSaving: saveSearch.isPending,
  };
}
```

---

## 🎭 User Flows

### Flow 1: Update Risk Tolerance

```
1. User navigates to Settings > Preferences
   ↓
2. Taps "Risk Tolerance" card
   ↓
3. Sees three options with descriptions
   ↓
4. Taps desired risk level (e.g., Conservative)
   ↓
5. Confirmation animation plays
   ↓
6. Success toast: "Risk tolerance updated"
   ↓
7. Returns to preferences screen
   ↓
8. All protocol recommendations now reflect new tolerance
```

### Flow 2: Manage Favorite Protocols

```
1. User navigates to Settings > Preferences > Favorite Protocols
   ↓
2. Sees current list of 8 favorites
   ↓
3. Taps [+ Add More Favorites]
   ↓
4. Search/browse protocols
   ↓
5. Taps star icon on a protocol
   ↓
6. Protocol added to favorites list
   ↓
7. Success toast: "Added to favorites"
   ↓
8. Protocol now appears first in all search results
```

### Flow 3: Save Search Preset

```
1. User performs a search with specific filters
   ↓
2. Gets good results
   ↓
3. Taps "Save This Search" button
   ↓
4. Modal opens: "Name Your Search"
   ↓
5. Enters name: "Low Risk Staking"
   ↓
6. Confirms save
   ↓
7. Search added to Saved Searches (5/10)
   ↓
8. Can now re-run with one tap from preferences
```

---

## ⚠️ Error Handling

```typescript
const preferenceErrors = {
  PREF_001: 'Failed to load preferences',
  PREF_002: 'Invalid risk tolerance value',
  PREF_003: 'Too many preferred chains (max 10)',
  PREF_004: 'Too many favorite protocols (max 20)',
  PREF_005: 'Too many saved searches (max 10)',
  PREF_006: 'Failed to save preference',
  PREF_007: 'Search name already exists',
};

// Handle preference update error
try {
  await updateRiskTolerance('conservative');
} catch (error) {
  if (error.code === 'PREF_002') {
    toast.error('Invalid risk tolerance selected');
  } else {
    toast.error('Failed to update preference. Please try again.');
  }
}
```

---

## ♿ Accessibility

### ARIA Labels

```typescript
<button
  aria-label={`Set risk tolerance to ${option.label}. ${option.description}`}
  role="radio"
  aria-checked={value === option.value}
  onClick={() => onChange(option.value)}
>
  {option.label}
</button>
```

### Keyboard Navigation

```typescript
function PreferencesList({ sections }: PreferencesListProps) {
  const handleKeyPress = (e: KeyboardEvent, route: string) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      navigate(route);
    }
  };
  
  return (
    <div role="list">
      {sections.map((section) => (
        <div key={section.title} role="listitem">
          {section.items.map((item, idx) => (
            <div
              key={item.id}
              role="button"
              tabIndex={0}
              onKeyPress={(e) => handleKeyPress(e, item.route)}
            >
              {item.label}
            </div>
          ))}
        </div>
      ))}
    </div>
  );
}
```

---

## 🔒 Security

### Preference Validation

```typescript
// Validate before sending to backend
const validatePreferences = (prefs: Partial<UserPreferences>) => {
  if (prefs.risk_tolerance) {
    if (!['conservative', 'moderate', 'aggressive'].includes(prefs.risk_tolerance)) {
      throw new Error('Invalid risk tolerance');
    }
  }
  
  if (prefs.preferred_chains) {
    if (prefs.preferred_chains.length > 10) {
      throw new Error('Too many chains selected');
    }
  }
  
  if (prefs.favorite_protocols) {
    if (prefs.favorite_protocols.length > 20) {
      throw new Error('Too many favorite protocols');
    }
  }
  
  return true;
};
```

---

## 🧪 Testing

```typescript
describe('PreferencesScreen', () => {
  it('loads and displays user preferences', async () => {
    const { getByText } = render(<PreferencesScreen userId="123" />);
    
    await waitFor(() => {
      expect(getByText('Risk Tolerance')).toBeInTheDocument();
      expect(getByText('Moderate')).toBeInTheDocument();
    });
  });
  
  it('updates risk tolerance', async () => {
    const { getByText } = render(<RiskToleranceSelector value="moderate" onChange={mockOnChange} />);
    
    fireEvent.click(getByText('Conservative'));
    
    await waitFor(() => {
      expect(mockOnChange).toHaveBeenCalledWith('conservative');
    });
  });
  
  it('manages favorite protocols', async () => {
    const { getByTestId } = render(<FavoritesList favorites={mockFavorites} />);
    
    fireEvent.click(getByTestId('remove-favorite-aave'));
    
    await waitFor(() => {
      expect(mockRemoveFavorite).toHaveBeenCalledWith('aave-id');
    });
  });
});
```

---

*Document Version: 1.0*  
*Last Updated: December 1, 2025*  
*Module: User Preferences*  
*Backend Status: ✅ 100% Implemented (7 endpoints)*  
*Frontend Status: ✅ Ready for Implementation*
