# 📱 Anvil Platform - Mobile App Architecture

## React Native Mobile Application Design

**Version:** 1.0  
**Date:** November 2025  
**Platform:** iOS & Android

---

## 🎯 Architecture Overview

### High-Level Architecture

```
┌─────────────────────────────────────────────────────┐
│              PRESENTATION LAYER                     │
│  ┌───────────┬───────────┬───────────┬──────────┐  │
│  │  Screens  │Components │Navigation │  Theme   │  │
│  └───────────┴───────────┴───────────┴──────────┘  │
└─────────────────────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────┐
│              STATE MANAGEMENT LAYER                 │
│  ┌───────────┬───────────┬───────────┬──────────┐  │
│  │  Zustand  │  Queries  │ Mutations │  Cache   │  │
│  └───────────┴───────────┴───────────┴──────────┘  │
└─────────────────────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────┐
│              BUSINESS LOGIC LAYER                   │
│  ┌───────────┬───────────┬───────────┬──────────┐  │
│  │   APIs    │  Services │  Helpers  │  Utils   │  │
│  └───────────┴───────────┴───────────┴──────────┘  │
└─────────────────────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────┐
│              INTEGRATION LAYER                      │
│  ┌───────────┬───────────┬───────────┬──────────┐  │
│  │  Privy    │  Stripe   │ Analytics │ Storage  │  │
│  └───────────┴───────────┴───────────┴──────────┘  │
└─────────────────────────────────────────────────────┘
```

---

## 📂 Project Structure

```
anvil-mobile/
├── src/
│   ├── screens/          # Screen components
│   │   ├── auth/
│   │   │   ├── LoginScreen.tsx
│   │   │   ├── SignupScreen.tsx
│   │   │   └── OnboardingScreen.tsx
│   │   ├── home/
│   │   │   ├── HomeScreen.tsx
│   │   │   └── DashboardScreen.tsx
│   │   ├── wallet/
│   │   │   ├── WalletScreen.tsx
│   │   │   └── TransactionHistoryScreen.tsx
│   │   ├── swap/
│   │   │   ├── SwapScreen.tsx
│   │   │   ├── SwapConfirmScreen.tsx
│   │   │   └── SwapSuccessScreen.tsx
│   │   ├── earn/
│   │   │   ├── EarnScreen.tsx
│   │   │   ├── EarnDetailScreen.tsx
│   │   │   └── PositionDetailScreen.tsx
│   │   ├── save/
│   │   │   ├── SaveScreen.tsx
│   │   │   ├── CreateScheduleScreen.tsx
│   │   │   └── ScheduleDetailScreen.tsx
│   │   ├── perpetuals/
│   │   │   ├── PerpetualsScreen.tsx
│   │   │   ├── TradeScreen.tsx
│   │   │   └── PositionsScreen.tsx
│   │   ├── ai/
│   │   │   ├── ChatScreen.tsx
│   │   │   └── ConversationHistoryScreen.tsx
│   │   ├── profile/
│   │   │   ├── ProfileScreen.tsx
│   │   │   ├── SettingsScreen.tsx
│   │   │   └── SubscriptionScreen.tsx
│   │   └── funding/
│   │       ├── FundingScreen.tsx
│   │       └── PaymentMethodScreen.tsx
│   │
│   ├── components/       # Reusable components
│   │   ├── common/
│   │   │   ├── Button.tsx
│   │   │   ├── Input.tsx
│   │   │   ├── Card.tsx
│   │   │   ├── Modal.tsx
│   │   │   ├── Loading.tsx
│   │   │   └── ErrorBoundary.tsx
│   │   ├── wallet/
│   │   │   ├── BalanceCard.tsx
│   │   │   ├── TokenList.tsx
│   │   │   └── TransactionItem.tsx
│   │   ├── swap/
│   │   │   ├── TokenSelector.tsx
│   │   │   ├── SwapForm.tsx
│   │   │   └── QuoteDisplay.tsx
│   │   ├── earn/
│   │   │   ├── OpportunityCard.tsx
│   │   │   ├── ProtocolIcon.tsx
│   │   │   └── APYDisplay.tsx
│   │   └── charts/
│   │       ├── LineChart.tsx
│   │       ├── PieChart.tsx
│   │       └── BarChart.tsx
│   │
│   ├── navigation/       # Navigation setup
│   │   ├── RootNavigator.tsx
│   │   ├── AuthNavigator.tsx
│   │   ├── MainNavigator.tsx
│   │   └── types.ts
│   │
│   ├── store/           # State management (Zustand)
│   │   ├── userStore.ts
│   │   ├── walletStore.ts
│   │   ├── swapStore.ts
│   │   ├── earnStore.ts
│   │   └── index.ts
│   │
│   ├── services/        # Business logic
│   │   ├── api/
│   │   │   ├── client.ts
│   │   │   ├── auth.ts
│   │   │   ├── wallet.ts
│   │   │   ├── trading.ts
│   │   │   ├── earn.ts
│   │   │   ├── perpetuals.ts
│   │   │   └── ai.ts
│   │   ├── privy/
│   │   │   └── privyService.ts
│   │   ├── stripe/
│   │   │   └── stripeService.ts
│   │   ├── analytics/
│   │   │   └── analyticsService.ts
│   │   └── notifications/
│   │       └── notificationService.ts
│   │
│   ├── hooks/           # Custom React hooks
│   │   ├── useAuth.ts
│   │   ├── useWallet.ts
│   │   ├── useBalance.ts
│   │   ├── useSwap.ts
│   │   ├── useEarn.ts
│   │   └── usePerpetualsPositions.ts
│   │
│   ├── utils/           # Utility functions
│   │   ├── format.ts
│   │   ├── validation.ts
│   │   ├── crypto.ts
│   │   └── constants.ts
│   │
│   ├── types/           # TypeScript types
│   │   ├── user.ts
│   │   ├── wallet.ts
│   │   ├── transaction.ts
│   │   ├── earn.ts
│   │   └── api.ts
│   │
│   ├── theme/           # Design system
│   │   ├── colors.ts
│   │   ├── spacing.ts
│   │   ├── typography.ts
│   │   └── index.ts
│   │
│   ├── assets/          # Static assets
│   │   ├── images/
│   │   ├── icons/
│   │   └── fonts/
│   │
│   └── config/          # App configuration
│       ├── env.ts
│       └── constants.ts
│
├── __tests__/           # Tests
│   ├── components/
│   ├── screens/
│   ├── utils/
│   └── e2e/
│
├── ios/                 # iOS specific
├── android/             # Android specific
├── package.json
├── tsconfig.json
├── babel.config.js
├── metro.config.js
└── .env.example
```

---

## 🧩 Key Components

### 1. Navigation System

**RootNavigator.tsx:**
```typescript
import React from 'react'
import { NavigationContainer } from '@react-navigation/native'
import { useAuthStore } from '@/store/userStore'
import { AuthNavigator } from './AuthNavigator'
import { MainNavigator } from './MainNavigator'

export const RootNavigator: React.FC = () => {
  const { isAuthenticated } = useAuthStore()

  return (
    <NavigationContainer>
      {isAuthenticated ? <MainNavigator /> : <AuthNavigator />}
    </NavigationContainer>
  )
}
```

**MainNavigator.tsx (Bottom Tabs):**
```typescript
import React from 'react'
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs'
import { HomeScreen } from '@/screens/home/HomeScreen'
import { SwapScreen } from '@/screens/swap/SwapScreen'
import { EarnScreen } from '@/screens/earn/EarnScreen'
import { ChatScreen } from '@/screens/ai/ChatScreen'
import { ProfileScreen } from '@/screens/profile/ProfileScreen'

const Tab = createBottomTabNavigator()

export const MainNavigator: React.FC = () => {
  return (
    <Tab.Navigator
      screenOptions={{
        tabBarActiveTintColor: colors.primary,
        tabBarInactiveTintColor: colors.text.secondary,
      }}
    >
      <Tab.Screen 
        name="Home" 
        component={HomeScreen}
        options={{
          tabBarIcon: ({ color }) => <HomeIcon color={color} />,
        }}
      />
      <Tab.Screen 
        name="Swap" 
        component={SwapScreen}
        options={{
          tabBarIcon: ({ color }) => <SwapIcon color={color} />,
        }}
      />
      <Tab.Screen 
        name="Earn" 
        component={EarnScreen}
        options={{
          tabBarIcon: ({ color }) => <EarnIcon color={color} />,
        }}
      />
      <Tab.Screen 
        name="AI" 
        component={ChatScreen}
        options={{
          tabBarIcon: ({ color }) => <ChatIcon color={color} />,
        }}
      />
      <Tab.Screen 
        name="Profile" 
        component={ProfileScreen}
        options={{
          tabBarIcon: ({ color }) => <ProfileIcon color={color} />,
        }}
      />
    </Tab.Navigator>
  )
}
```

---

### 2. State Management (Zustand)

**userStore.ts:**
```typescript
import { create } from 'zustand'
import { persist, createJSONStorage } from 'zustand/middleware'
import AsyncStorage from '@react-native-async-storage/async-storage'

interface User {
  id: number
  uid: string
  email: string
  firstName?: string
  lastName?: string
}

interface UserStore {
  user: User | null
  accessToken: string | null
  refreshToken: string | null
  isAuthenticated: boolean
  
  setUser: (user: User) => void
  setTokens: (accessToken: string, refreshToken: string) => void
  logout: () => void
}

export const useUserStore = create<UserStore>()(
  persist(
    (set) => ({
      user: null,
      accessToken: null,
      refreshToken: null,
      isAuthenticated: false,
      
      setUser: (user) => set({ user, isAuthenticated: true }),
      
      setTokens: (accessToken, refreshToken) => 
        set({ accessToken, refreshToken }),
      
      logout: () => set({ 
        user: null, 
        accessToken: null, 
        refreshToken: null,
        isAuthenticated: false 
      }),
    }),
    {
      name: 'user-storage',
      storage: createJSONStorage(() => AsyncStorage),
    }
  )
)
```

**walletStore.ts:**
```typescript
import { create } from 'zustand'

interface Balance {
  asset: string
  amount: string
  valueUsd: string
}

interface WalletStore {
  address: string | null
  balances: Balance[]
  isLoading: boolean
  
  setAddress: (address: string) => void
  setBalances: (balances: Balance[]) => void
  setLoading: (isLoading: boolean) => void
  refreshBalances: () => Promise<void>
}

export const useWalletStore = create<WalletStore>((set, get) => ({
  address: null,
  balances: [],
  isLoading: false,
  
  setAddress: (address) => set({ address }),
  
  setBalances: (balances) => set({ balances }),
  
  setLoading: (isLoading) => set({ isLoading }),
  
  refreshBalances: async () => {
    const { address } = get()
    if (!address) return
    
    set({ isLoading: true })
    try {
      const balances = await walletApi.getBalances(address)
      set({ balances })
    } catch (error) {
      console.error('Failed to refresh balances:', error)
    } finally {
      set({ isLoading: false })
    }
  },
}))
```

---

### 3. API Client

**services/api/client.ts:**
```typescript
import axios, { AxiosInstance, AxiosRequestConfig } from 'axios'
import { useUserStore } from '@/store/userStore'
import Config from '@/config/env'

class ApiClient {
  private client: AxiosInstance

  constructor() {
    this.client = axios.create({
      baseURL: Config.API_URL,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    })

    this.setupInterceptors()
  }

  private setupInterceptors() {
    // Request interceptor - add auth token
    this.client.interceptors.request.use(
      (config) => {
        const { accessToken } = useUserStore.getState()
        if (accessToken) {
          config.headers.Authorization = `Bearer ${accessToken}`
        }
        return config
      },
      (error) => Promise.reject(error)
    )

    // Response interceptor - handle errors
    this.client.interceptors.response.use(
      (response) => response,
      async (error) => {
        const originalRequest = error.config

        // Handle 401 - token expired
        if (error.response?.status === 401 && !originalRequest._retry) {
          originalRequest._retry = true

          try {
            const { refreshToken } = useUserStore.getState()
            const response = await this.client.post('/user/auth/refresh', {
              refresh_token: refreshToken,
            })

            const { access_token } = response.data.data
            useUserStore.getState().setTokens(access_token, refreshToken!)

            originalRequest.headers.Authorization = `Bearer ${access_token}`
            return this.client(originalRequest)
          } catch (refreshError) {
            // Refresh failed, logout user
            useUserStore.getState().logout()
            return Promise.reject(refreshError)
          }
        }

        return Promise.reject(error)
      }
    )
  }

  async get<T>(url: string, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.client.get<ApiResponse<T>>(url, config)
    return response.data.data
  }

  async post<T>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.client.post<ApiResponse<T>>(url, data, config)
    return response.data.data
  }

  async put<T>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.client.put<ApiResponse<T>>(url, data, config)
    return response.data.data
  }

  async delete<T>(url: string, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.client.delete<ApiResponse<T>>(url, config)
    return response.data.data
  }
}

export const api = new ApiClient()
```

**services/api/trading.ts:**
```typescript
import { api } from './client'

export interface SwapQuoteParams {
  from_asset: string
  from_amount: string
  to_asset: string
  chain: string
  slippage?: number
}

export interface SwapQuote {
  quote_id: string
  from_asset: string
  from_amount: string
  to_asset: string
  to_amount: string
  rate: string
  gas_estimate_usd: string
  expires_at: string
}

export interface SwapParams {
  quote_id: string
  from_asset: string
  from_amount: string
  to_asset: string
  chain: string
}

export const tradingApi = {
  getQuote: (params: SwapQuoteParams): Promise<SwapQuote> => {
    return api.post('/user/trade/quote', params)
  },

  executeSwap: (params: SwapParams): Promise<Transaction> => {
    return api.post('/user/trade/swap', params)
  },

  getSwapHistory: (page: number = 1, limit: number = 20): Promise<PaginatedResponse<Transaction>> => {
    return api.get('/user/transactions', {
      params: { page, limit, type: 'swap' }
    })
  },
}
```

---

### 4. Custom Hooks

**hooks/useAuth.ts:**
```typescript
import { useState } from 'react'
import { usePrivy } from '@privy-io/expo'
import { useUserStore } from '@/store/userStore'
import { authApi } from '@/services/api/auth'

export const useAuth = () => {
  const [isLoading, setIsLoading] = useState(false)
  const { login: privyLogin } = usePrivy()
  const { setUser, setTokens } = useUserStore()

  const login = async () => {
    setIsLoading(true)
    try {
      // Login with Privy
      await privyLogin()
      
      // Get Privy token
      const privyToken = await getPrivyToken()
      
      // Exchange for backend token
      const response = await authApi.loginWithPrivy(privyToken)
      
      // Save user and tokens
      setUser(response.user)
      setTokens(response.access_token, response.refresh_token)
      
      return true
    } catch (error) {
      console.error('Login failed:', error)
      throw error
    } finally {
      setIsLoading(false)
    }
  }

  const logout = async () => {
    try {
      await authApi.logout()
    } catch (error) {
      console.error('Logout error:', error)
    } finally {
      useUserStore.getState().logout()
    }
  }

  return {
    login,
    logout,
    isLoading,
  }
}
```

**hooks/useSwap.ts:**
```typescript
import { useState } from 'react'
import { tradingApi } from '@/services/api/trading'

export const useSwap = () => {
  const [quote, setQuote] = useState<SwapQuote | null>(null)
  const [isLoadingQuote, setIsLoadingQuote] = useState(false)
  const [isExecuting, setIsExecuting] = useState(false)

  const getQuote = async (params: SwapQuoteParams) => {
    setIsLoadingQuote(true)
    try {
      const quoteData = await tradingApi.getQuote(params)
      setQuote(quoteData)
      return quoteData
    } catch (error) {
      console.error('Failed to get quote:', error)
      throw error
    } finally {
      setIsLoadingQuote(false)
    }
  }

  const executeSwap = async (params: SwapParams) => {
    setIsExecuting(true)
    try {
      const transaction = await tradingApi.executeSwap(params)
      return transaction
    } catch (error) {
      console.error('Failed to execute swap:', error)
      throw error
    } finally {
      setIsExecuting(false)
    }
  }

  const clearQuote = () => setQuote(null)

  return {
    quote,
    isLoadingQuote,
    isExecuting,
    getQuote,
    executeSwap,
    clearQuote,
  }
}
```

---

### 5. Screen Example

**screens/swap/SwapScreen.tsx:**
```typescript
import React, { useState } from 'react'
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native'
import { useNavigation } from '@react-navigation/native'
import { Button, Input, TokenSelector, Loading } from '@/components'
import { useSwap } from '@/hooks/useSwap'
import { useWalletStore } from '@/store/walletStore'
import { colors, spacing } from '@/theme'

export const SwapScreen: React.FC = () => {
  const navigation = useNavigation()
  const { balances } = useWalletStore()
  const { quote, isLoadingQuote, getQuote, executeSwap } = useSwap()

  const [fromAsset, setFromAsset] = useState('USDC')
  const [toAsset, setToAsset] = useState('ETH')
  const [amount, setAmount] = useState('')

  const handleGetQuote = async () => {
    try {
      await getQuote({
        from_asset: fromAsset,
        from_amount: amount,
        to_asset: toAsset,
        chain: 'arbitrum',
      })
    } catch (error) {
      // Handle error
      Alert.alert('Error', 'Failed to get quote')
    }
  }

  const handleSwap = async () => {
    if (!quote) return

    try {
      const transaction = await executeSwap({
        quote_id: quote.quote_id,
        from_asset: fromAsset,
        from_amount: amount,
        to_asset: toAsset,
        chain: 'arbitrum',
      })

      navigation.navigate('SwapSuccess', { transaction })
    } catch (error) {
      Alert.alert('Error', 'Failed to execute swap')
    }
  }

  const isValid = amount && parseFloat(amount) > 0

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Swap Tokens</Text>

      <View style={styles.form}>
        <TokenSelector
          label="From"
          value={fromAsset}
          onChange={setFromAsset}
          balances={balances}
        />

        <Input
          label="Amount"
          value={amount}
          onChangeText={setAmount}
          keyboardType="decimal-pad"
          placeholder="0.00"
        />

        <TouchableOpacity 
          style={styles.switchButton}
          onPress={() => {
            const temp = fromAsset
            setFromAsset(toAsset)
            setToAsset(temp)
          }}
        >
          <Text>⇅</Text>
        </TouchableOpacity>

        <TokenSelector
          label="To"
          value={toAsset}
          onChange={setToAsset}
        />

        {quote && (
          <View style={styles.quoteCard}>
            <Text>You'll receive: {quote.to_amount} {toAsset}</Text>
            <Text>Rate: 1 {fromAsset} = {quote.rate} {toAsset}</Text>
            <Text>Gas: ~${quote.gas_estimate_usd}</Text>
          </View>
        )}
      </View>

      <Button
        title={quote ? 'Execute Swap' : 'Get Quote'}
        onPress={quote ? handleSwap : handleGetQuote}
        disabled={!isValid}
        loading={isLoadingQuote}
      />
    </View>
  )
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    padding: spacing.md,
    backgroundColor: colors.background,
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    marginBottom: spacing.lg,
  },
  form: {
    flex: 1,
  },
  switchButton: {
    alignSelf: 'center',
    padding: spacing.sm,
  },
  quoteCard: {
    padding: spacing.md,
    backgroundColor: colors.surface,
    borderRadius: 8,
    marginTop: spacing.md,
  },
})
```

---

## 🔐 Security Features

### Secure Storage

```typescript
import * as SecureStore from 'expo-secure-store'

export const secureStorage = {
  async save(key: string, value: string): Promise<void> {
    await SecureStore.setItemAsync(key, value)
  },

  async get(key: string): Promise<string | null> {
    return await SecureStore.getItemAsync(key)
  },

  async delete(key: string): Promise<void> {
    await SecureStore.deleteItemAsync(key)
  },
}
```

### Biometric Authentication

```typescript
import * as LocalAuthentication from 'expo-local-authentication'

export const biometricAuth = {
  async isAvailable(): Promise<boolean> {
    const hasHardware = await LocalAuthentication.hasHardwareAsync()
    const isEnrolled = await LocalAuthentication.isEnrolledAsync()
    return hasHardware && isEnrolled
  },

  async authenticate(reason: string): Promise<boolean> {
    const result = await LocalAuthentication.authenticateAsync({
      promptMessage: reason,
      fallbackLabel: 'Use passcode',
    })
    return result.success
  },
}
```

---

## 📊 Performance Optimization

### Image Optimization

```typescript
import FastImage from 'react-native-fast-image'

<FastImage
  source={{
    uri: imageUrl,
    priority: FastImage.priority.normal,
  }}
  resizeMode={FastImage.resizeMode.contain}
  style={styles.image}
/>
```

### List Optimization

```typescript
import { FlashList } from '@shopify/flash-list'

<FlashList
  data={transactions}
  renderItem={({ item }) => <TransactionItem item={item} />}
  estimatedItemSize={80}
  keyExtractor={(item) => item.id.toString()}
/>
```

### Memoization

```typescript
import React, { useMemo, useCallback } from 'react'

const ExpensiveComponent: React.FC<Props> = ({ data }) => {
  const processedData = useMemo(() => {
    return expensiveOperation(data)
  }, [data])

  const handlePress = useCallback(() => {
    // Handler logic
  }, [])

  return <View>{/* Component */}</View>
}

export default React.memo(ExpensiveComponent)
```

---

## 🧪 Testing

### Component Tests

```typescript
import { render, fireEvent } from '@testing-library/react-native'
import { SwapScreen } from '../SwapScreen'

describe('SwapScreen', () => {
  it('should render swap form', () => {
    const { getByText, getByPlaceholderText } = render(<SwapScreen />)

    expect(getByText('Swap Tokens')).toBeTruthy()
    expect(getByPlaceholderText('0.00')).toBeTruthy()
  })

  it('should update amount on input', () => {
    const { getByPlaceholderText } = render(<SwapScreen />)
    const input = getByPlaceholderText('0.00')

    fireEvent.changeText(input, '50')

    expect(input.props.value).toBe('50')
  })
})
```

---

**Document Version:** 1.0  
**Last Updated:** November 2025  
**Maintained By:** Mobile Team  
**Questions:** mobile-lead@anvil.com
