# Component Library Guide

**Version**: 1.0  
**Last Updated**: December 1, 2025  
**Target Audience**: Frontend Developers

---

## 📋 Overview

Reusable component patterns and best practices for building consistent, accessible Anvil Frontend interfaces across web and mobile platforms.

---

## 🎨 Core Components

### Risk Badge

Display ML risk scores with color coding and confidence.

```typescript
interface RiskBadgeProps {
  score: number;  // 0-10
  level: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  confidence?: number;  // 0-1
  size?: 'sm' | 'md' | 'lg';
  showLabel?: boolean;
}

function RiskBadge({ score, level, confidence, size = 'md', showLabel = true }: RiskBadgeProps) {
  const colors = {
    LOW: 'bg-green-500',
    MEDIUM: 'bg-yellow-500',
    HIGH: 'bg-orange-500',
    CRITICAL: 'bg-red-500',
  };
  
  return (
    <div className={`flex items-center gap-2 ${colors[level]} px-2 py-1 rounded`}>
      <span className="text-white font-bold">{score.toFixed(1)}</span>
      {showLabel && <span className="text-white text-sm">{level}</span>}
      {confidence && (
        <span className="text-white/70 text-xs">
          {Math.round(confidence * 100)}%
        </span>
      )}
    </div>
  );
}
```

---

### Protocol Card

Standard card for displaying protocol information.

```typescript
interface ProtocolCardProps {
  protocol: {
    protocol_id: string;
    protocol_name: string;
    logo_url?: string;
    chain: string;
    category: string;
    tvl_usd: number;
    risk_score: number;
    risk_level: string;
  };
  onPress?: () => void;
  showRisk?: boolean;
}

function ProtocolCard({ protocol, onPress, showRisk = true }: ProtocolCardProps) {
  return (
    <div 
      className="border rounded-lg p-4 hover:shadow-lg cursor-pointer"
      onClick={onPress}
    >
      <div className="flex items-center gap-3">
        {protocol.logo_url && (
          <img 
            src={protocol.logo_url} 
            alt={protocol.protocol_name}
            className="w-12 h-12 rounded-full"
          />
        )}
        <div className="flex-1">
          <h3 className="font-bold">{protocol.protocol_name}</h3>
          <p className="text-sm text-gray-500">
            {protocol.category} • {protocol.chain}
          </p>
        </div>
        {showRisk && (
          <RiskBadge 
            score={protocol.risk_score} 
            level={protocol.risk_level}
          />
        )}
      </div>
      <div className="mt-3 flex justify-between">
        <span className="text-sm">TVL: ${formatLargeNumber(protocol.tvl_usd)}</span>
      </div>
    </div>
  );
}
```

---

### Search Bar with Autocomplete

```typescript
interface SearchBarProps {
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  suggestions?: string[];
  onSuggestionClick?: (suggestion: string) => void;
}

function SearchBar({ 
  value, 
  onChange, 
  placeholder = 'Search...', 
  suggestions = [],
  onSuggestionClick 
}: SearchBarProps) {
  const [showSuggestions, setShowSuggestions] = useState(false);
  
  return (
    <div className="relative">
      <input
        type="text"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className="w-full px-4 py-2 border rounded-lg"
        onFocus={() => setShowSuggestions(true)}
        onBlur={() => setTimeout(() => setShowSuggestions(false), 200)}
      />
      {showSuggestions && suggestions.length > 0 && (
        <div className="absolute w-full mt-1 bg-white border rounded-lg shadow-lg z-10">
          {suggestions.map((suggestion, idx) => (
            <button
              key={idx}
              className="w-full px-4 py-2 text-left hover:bg-gray-100"
              onClick={() => onSuggestionClick?.(suggestion)}
            >
              {suggestion}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
```

---

## 🎭 Motion Patterns

### Risk Warning Animation

```typescript
import { motion } from 'framer-motion';

function RiskWarning({ message }: { message: string }) {
  return (
    <motion.div
      initial={{ x: 0 }}
      animate={{ x: [-10, 10, -10, 10, 0] }}
      transition={{ duration: 0.4 }}
      className="bg-red-50 border-l-4 border-red-500 p-4"
    >
      <p className="text-red-800 font-semibold">{message}</p>
    </motion.div>
  );
}
```

### Loading Skeleton

```typescript
function ProtocolCardSkeleton() {
  return (
    <div className="border rounded-lg p-4 animate-pulse">
      <div className="flex items-center gap-3">
        <div className="w-12 h-12 bg-gray-200 rounded-full" />
        <div className="flex-1 space-y-2">
          <div className="h-4 bg-gray-200 rounded w-3/4" />
          <div className="h-3 bg-gray-200 rounded w-1/2" />
        </div>
      </div>
    </div>
  );
}
```

---

## ♿ Accessibility

### ARIA Labels

```typescript
<RiskBadge 
  score={7.8}
  level="HIGH"
  aria-label="High risk: 7.8 out of 10"
  role="status"
/>
```

### Keyboard Navigation

```typescript
function ProtocolList({ protocols }: { protocols: Protocol[] }) {
  return (
    <div role="list">
      {protocols.map((protocol, idx) => (
        <div
          key={protocol.protocol_id}
          role="listitem"
          tabIndex={0}
          onKeyPress={(e) => {
            if (e.key === 'Enter' || e.key === ' ') {
              selectProtocol(protocol);
            }
          }}
        >
          <ProtocolCard protocol={protocol} />
        </div>
      ))}
    </div>
  );
}
```

---

## 🎨 Theme Configuration

```typescript
// tailwind.config.js
module.exports = {
  theme: {
    extend: {
      colors: {
        risk: {
          low: '#10b981',
          medium: '#f59e0b',
          high: '#f97316',
          critical: '#ef4444',
        },
      },
    },
  },
};
```

---

## 📱 React Native Components

```typescript
// Mobile Risk Badge
import { View, Text } from 'react-native';
import Animated, { useAnimatedStyle, withRepeat, withTiming } from 'react-native-reanimated';

function RiskBadgeNative({ score, level }: RiskBadgeProps) {
  const pulse = useSharedValue(1);
  
  React.useEffect(() => {
    if (level === 'CRITICAL') {
      pulse.value = withRepeat(
        withTiming(1.1, { duration: 500 }),
        -1,
        true
      );
    }
  }, [level]);
  
  const animatedStyle = useAnimatedStyle(() => ({
    transform: [{ scale: pulse.value }],
  }));
  
  return (
    <Animated.View style={[styles.badge, animatedStyle]}>
      <Text style={styles.badgeText}>{score.toFixed(1)}</Text>
    </Animated.View>
  );
}
```

---

## 🔧 Utility Functions

```typescript
// Format large numbers
export function formatLargeNumber(num: number): string {
  if (num >= 1e9) return `${(num / 1e9).toFixed(1)}B`;
  if (num >= 1e6) return `${(num / 1e6).toFixed(1)}M`;
  if (num >= 1e3) return `${(num / 1e3).toFixed(1)}K`;
  return num.toFixed(0);
}

// Format percentage
export function formatPercent(value: number): string {
  const sign = value >= 0 ? '+' : '';
  return `${sign}${value.toFixed(2)}%`;
}

// Get risk color
export function getRiskColor(level: string): string {
  const colors = {
    LOW: '#10b981',
    MEDIUM: '#f59e0b',
    HIGH: '#f97316',
    CRITICAL: '#ef4444',
  };
  return colors[level as keyof typeof colors] || colors.MEDIUM;
}
```

---

## 🧪 Testing Components

```typescript
import { render, screen, fireEvent } from '@testing-library/react';

describe('RiskBadge', () => {
  it('displays correct risk level', () => {
    render(<RiskBadge score={7.8} level="HIGH" />);
    expect(screen.getByText('7.8')).toBeInTheDocument();
    expect(screen.getByText('HIGH')).toBeInTheDocument();
  });
  
  it('shows confidence when provided', () => {
    render(<RiskBadge score={2.1} level="LOW" confidence={0.94} />);
    expect(screen.getByText('94%')).toBeInTheDocument();
  });
});
```

---

*Guide Version: 1.0*  
*For complete design system, see: Figma Design Files*
