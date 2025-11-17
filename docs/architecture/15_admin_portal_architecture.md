# 🖥️ Anvil Platform - Admin Portal Architecture

## Next.js Admin Console Design

**Version:** 1.0  
**Date:** November 2025  
**Platform:** Web (Next.js 14)

---

## 🎯 Overview

The Anvil Admin Portal is a Next.js 14 web application that provides administrators and auditors with tools to manage users, monitor transactions, configure system settings, and view audit logs.

### Key Features

```yaml
User Management:
  - View all users
  - Search and filter
  - KYC approval workflow
  - User detail views
  - Account suspension

Transaction Monitoring:
  - Real-time transaction feed
  - Transaction search
  - Fraud detection alerts
  - Volume analytics

System Configuration:
  - AI model settings
  - Feature flags
  - Rate limits
  - Notification templates

Analytics & Reporting:
  - User metrics
  - Transaction volumes
  - Revenue tracking
  - Custom reports

Audit Logs:
  - Complete audit trail
  - Admin action logs
  - Security events
  - Export capabilities
```

---

## 📂 Project Structure

```
anvil-admin/
├── app/                      # Next.js 14 app directory
│   ├── (auth)/              # Auth routes
│   │   ├── login/
│   │   └── layout.tsx
│   ├── (dashboard)/         # Protected routes
│   │   ├── dashboard/
│   │   ├── users/
│   │   ├── transactions/
│   │   ├── settings/
│   │   ├── ai/
│   │   ├── audit/
│   │   └── layout.tsx
│   ├── api/                 # API routes (if needed)
│   ├── layout.tsx
│   └── page.tsx
│
├── components/              # React components
│   ├── ui/                 # shadcn/ui components
│   │   ├── button.tsx
│   │   ├── input.tsx
│   │   ├── table.tsx
│   │   ├── dialog.tsx
│   │   └── ...
│   ├── layouts/
│   │   ├── sidebar.tsx
│   │   ├── header.tsx
│   │   └── page-header.tsx
│   ├── users/
│   │   ├── user-table.tsx
│   │   ├── user-detail.tsx
│   │   ├── kyc-review.tsx
│   │   └── user-actions.tsx
│   ├── transactions/
│   │   ├── transaction-table.tsx
│   │   ├── transaction-detail.tsx
│   │   └── transaction-filters.tsx
│   ├── analytics/
│   │   ├── metric-card.tsx
│   │   ├── chart.tsx
│   │   └── dashboard-grid.tsx
│   └── audit/
│       ├── audit-log-table.tsx
│       └── event-detail.tsx
│
├── lib/                    # Utilities
│   ├── api.ts             # API client
│   ├── auth.ts            # Auth utilities
│   ├── utils.ts           # Helpers
│   └── constants.ts
│
├── hooks/                  # Custom hooks
│   ├── use-users.ts
│   ├── use-transactions.ts
│   ├── use-analytics.ts
│   └── use-audit-logs.ts
│
├── types/                  # TypeScript types
│   ├── user.ts
│   ├── transaction.ts
│   ├── analytics.ts
│   └── api.ts
│
├── styles/
│   └── globals.css
│
├── public/
│   ├── images/
│   └── icons/
│
├── .env.local
├── next.config.js
├── tailwind.config.ts
├── tsconfig.json
└── package.json
```

---

## 🎨 UI Components (shadcn/ui)

### Installation

```bash
npx shadcn-ui@latest init

# Install components
npx shadcn-ui@latest add button
npx shadcn-ui@latest add input
npx shadcn-ui@latest add table
npx shadcn-ui@latest add dialog
npx shadcn-ui@latest add dropdown-menu
npx shadcn-ui@latest add select
npx shadcn-ui@latest add badge
npx shadcn-ui@latest add card
npx shadcn-ui@latest add tabs
npx shadcn-ui@latest add alert
npx shadcn-ui@latest add toast
```

---

## 🔐 Authentication

### Auth Flow

```typescript
// lib/auth.ts
import { cookies } from 'next/headers'
import { redirect } from 'next/navigation'

export async function getSession() {
  const token = cookies().get('admin_token')
  
  if (!token) {
    return null
  }

  try {
    // Verify token with backend
    const response = await fetch(`${process.env.API_URL}/admin/auth/verify`, {
      headers: {
        'Authorization': `Bearer ${token.value}`
      }
    })

    if (!response.ok) {
      return null
    }

    return await response.json()
  } catch (error) {
    return null
  }
}

export async function requireAuth() {
  const session = await getSession()
  
  if (!session) {
    redirect('/login')
  }

  // Check if admin or auditor
  if (session.user.role > 1) {
    redirect('/unauthorized')
  }

  return session
}

export async function requireAdmin() {
  const session = await getSession()
  
  if (!session || session.user.role !== 0) {
    redirect('/unauthorized')
  }

  return session
}
```

### Login Page

```typescript
// app/(auth)/login/page.tsx
'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card } from '@/components/ui/card'

export default function LoginPage() {
  const router = useRouter()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [totpCode, setTotpCode] = useState('')
  const [step, setStep] = useState<'credentials' | 'totp'>('credentials')
  const [isLoading, setIsLoading] = useState(false)

  const handleCredentialsSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsLoading(true)

    try {
      const response = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password })
      })

      if (response.ok) {
        setStep('totp')
      } else {
        alert('Invalid credentials')
      }
    } catch (error) {
      alert('Login failed')
    } finally {
      setIsLoading(false)
    }
  }

  const handleTotpSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsLoading(true)

    try {
      const response = await fetch('/api/auth/verify-totp', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password, totp_code: totpCode })
      })

      if (response.ok) {
        router.push('/dashboard')
      } else {
        alert('Invalid code')
      }
    } catch (error) {
      alert('Verification failed')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center">
      <Card className="w-full max-w-md p-8">
        <h1 className="text-2xl font-bold mb-6">Anvil Admin Portal</h1>
        
        {step === 'credentials' ? (
          <form onSubmit={handleCredentialsSubmit}>
            <div className="space-y-4">
              <div>
                <Label htmlFor="email">Email</Label>
                <Input
                  id="email"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                />
              </div>
              <div>
                <Label htmlFor="password">Password</Label>
                <Input
                  id="password"
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                />
              </div>
              <Button type="submit" className="w-full" disabled={isLoading}>
                {isLoading ? 'Logging in...' : 'Continue'}
              </Button>
            </div>
          </form>
        ) : (
          <form onSubmit={handleTotpSubmit}>
            <div className="space-y-4">
              <div>
                <Label htmlFor="totp">2FA Code</Label>
                <Input
                  id="totp"
                  type="text"
                  value={totpCode}
                  onChange={(e) => setTotpCode(e.target.value)}
                  placeholder="000000"
                  maxLength={6}
                  required
                />
              </div>
              <Button type="submit" className="w-full" disabled={isLoading}>
                {isLoading ? 'Verifying...' : 'Login'}
              </Button>
            </div>
          </form>
        )}
      </Card>
    </div>
  )
}
```

---

## 📊 Dashboard Page

```typescript
// app/(dashboard)/dashboard/page.tsx
import { requireAuth } from '@/lib/auth'
import { MetricCard } from '@/components/analytics/metric-card'
import { Chart } from '@/components/analytics/chart'
import { RecentTransactions } from '@/components/transactions/recent-transactions'

export default async function DashboardPage() {
  const session = await requireAuth()

  // Fetch analytics data
  const analytics = await fetch(`${process.env.API_URL}/admin/analytics/summary`, {
    headers: {
      'Authorization': `Bearer ${session.token}`
    }
  }).then(res => res.json())

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold">Dashboard</h1>

      {/* Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          title="Total Users"
          value={analytics.total_users}
          change={analytics.users_growth}
          trend="up"
        />
        <MetricCard
          title="Active Users (30d)"
          value={analytics.active_users}
          change={analytics.active_users_growth}
          trend="up"
        />
        <MetricCard
          title="Transaction Volume"
          value={`$${analytics.transaction_volume.toLocaleString()}`}
          change={analytics.volume_growth}
          trend="up"
        />
        <MetricCard
          title="Revenue (MRR)"
          value={`$${analytics.mrr.toLocaleString()}`}
          change={analytics.revenue_growth}
          trend="up"
        />
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Chart
          title="User Growth"
          data={analytics.user_growth_chart}
          type="line"
        />
        <Chart
          title="Transaction Volume"
          data={analytics.volume_chart}
          type="bar"
        />
      </div>

      {/* Recent Transactions */}
      <RecentTransactions limit={10} />
    </div>
  )
}
```

---

## 👥 User Management

```typescript
// app/(dashboard)/users/page.tsx
import { requireAuth } from '@/lib/auth'
import { UserTable } from '@/components/users/user-table'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'

export default async function UsersPage({
  searchParams
}: {
  searchParams: { page?: string; search?: string; status?: string }
}) {
  const session = await requireAuth()
  
  const page = parseInt(searchParams.page || '1')
  const search = searchParams.search || ''
  const status = searchParams.status || 'all'

  const response = await fetch(
    `${process.env.API_URL}/admin/users?` + new URLSearchParams({
      page: page.toString(),
      limit: '20',
      search,
      status
    }),
    {
      headers: { 'Authorization': `Bearer ${session.token}` }
    }
  )

  const { data: users, pagination } = await response.json()

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold">Users</h1>
      </div>

      {/* Filters */}
      <div className="flex gap-4">
        <Input
          placeholder="Search users..."
          defaultValue={search}
          className="max-w-sm"
        />
        <select defaultValue={status} className="border rounded px-3">
          <option value="all">All Status</option>
          <option value="active">Active</option>
          <option value="suspended">Suspended</option>
          <option value="kyc_pending">KYC Pending</option>
        </select>
      </div>

      {/* User Table */}
      <UserTable users={users} pagination={pagination} />
    </div>
  )
}
```

### User Detail Page

```typescript
// app/(dashboard)/users/[id]/page.tsx
import { requireAuth } from '@/lib/auth'
import { UserDetail } from '@/components/users/user-detail'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'

export default async function UserDetailPage({
  params
}: {
  params: { id: string }
}) {
  const session = await requireAuth()

  const user = await fetch(
    `${process.env.API_URL}/admin/users/${params.id}`,
    {
      headers: { 'Authorization': `Bearer ${session.token}` }
    }
  ).then(res => res.json())

  return (
    <div className="space-y-6">
      <UserDetail user={user} />

      <Tabs defaultValue="transactions">
        <TabsList>
          <TabsTrigger value="transactions">Transactions</TabsTrigger>
          <TabsTrigger value="positions">Positions</TabsTrigger>
          <TabsTrigger value="activity">Activity Log</TabsTrigger>
          <TabsTrigger value="kyc">KYC Documents</TabsTrigger>
        </TabsList>

        <TabsContent value="transactions">
          {/* Transaction history for this user */}
        </TabsContent>

        <TabsContent value="positions">
          {/* Active positions */}
        </TabsContent>

        <TabsContent value="activity">
          {/* Activity log */}
        </TabsContent>

        <TabsContent value="kyc">
          {/* KYC documents */}
        </TabsContent>
      </Tabs>
    </div>
  )
}
```

---

## 💳 Transaction Monitoring

```typescript
// components/transactions/transaction-table.tsx
'use client'

import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Badge } from '@/components/ui/badge'
import Link from 'next/link'

interface Transaction {
  id: number
  user_id: number
  user_email: string
  type: string
  from_asset: string
  to_asset: string
  amount: string
  amount_in_usd: string
  status: string
  created_at: string
}

export function TransactionTable({ transactions }: { transactions: Transaction[] }) {
  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>ID</TableHead>
          <TableHead>User</TableHead>
          <TableHead>Type</TableHead>
          <TableHead>From → To</TableHead>
          <TableHead>Amount (USD)</TableHead>
          <TableHead>Status</TableHead>
          <TableHead>Date</TableHead>
          <TableHead></TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {transactions.map((tx) => (
          <TableRow key={tx.id}>
            <TableCell className="font-mono text-sm">{tx.id}</TableCell>
            <TableCell>
              <Link href={`/users/${tx.user_id}`} className="hover:underline">
                {tx.user_email}
              </Link>
            </TableCell>
            <TableCell>
              <Badge variant="outline">{tx.type}</Badge>
            </TableCell>
            <TableCell>
              {tx.from_asset} → {tx.to_asset}
            </TableCell>
            <TableCell>${parseFloat(tx.amount_in_usd).toLocaleString()}</TableCell>
            <TableCell>
              <Badge variant={
                tx.status === 'success' ? 'default' :
                tx.status === 'pending' ? 'secondary' : 'destructive'
              }>
                {tx.status}
              </Badge>
            </TableCell>
            <TableCell>{new Date(tx.created_at).toLocaleString()}</TableCell>
            <TableCell>
              <Link href={`/transactions/${tx.id}`}>
                <Button variant="ghost" size="sm">View</Button>
              </Link>
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  )
}
```

---

## ⚙️ System Settings

```typescript
// app/(dashboard)/settings/page.tsx
import { requireAdmin } from '@/lib/auth'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { AISettings } from '@/components/settings/ai-settings'
import { FeatureFlags } from '@/components/settings/feature-flags'
import { RateLimits } from '@/components/settings/rate-limits'
import { NotificationTemplates } from '@/components/settings/notification-templates'

export default async function SettingsPage() {
  const session = await requireAdmin() // Only admins can access

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold">System Settings</h1>

      <Tabs defaultValue="ai">
        <TabsList>
          <TabsTrigger value="ai">AI Models</TabsTrigger>
          <TabsTrigger value="features">Feature Flags</TabsTrigger>
          <TabsTrigger value="limits">Rate Limits</TabsTrigger>
          <TabsTrigger value="notifications">Notifications</TabsTrigger>
        </TabsList>

        <TabsContent value="ai">
          <AISettings />
        </TabsContent>

        <TabsContent value="features">
          <FeatureFlags />
        </TabsContent>

        <TabsContent value="limits">
          <RateLimits />
        </TabsContent>

        <TabsContent value="notifications">
          <NotificationTemplates />
        </TabsContent>
      </Tabs>
    </div>
  )
}
```

---

## 📋 Audit Logs

```typescript
// app/(dashboard)/audit/page.tsx
import { requireAuth } from '@/lib/auth'
import { AuditLogTable } from '@/components/audit/audit-log-table'

export default async function AuditPage({
  searchParams
}: {
  searchParams: { page?: string; actor?: string; action?: string }
}) {
  const session = await requireAuth()

  const response = await fetch(
    `${process.env.API_URL}/admin/audit-logs?` + new URLSearchParams(searchParams),
    {
      headers: { 'Authorization': `Bearer ${session.token}` }
    }
  )

  const { data: logs, pagination } = await response.json()

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold">Audit Logs</h1>
      <AuditLogTable logs={logs} pagination={pagination} />
    </div>
  )
}
```

---

## 🎨 Design System

### Colors (Tailwind Config)

```typescript
// tailwind.config.ts
export default {
  theme: {
    extend: {
      colors: {
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        primary: {
          DEFAULT: "hsl(var(--primary))",
          foreground: "hsl(var(--primary-foreground))",
        },
        secondary: {
          DEFAULT: "hsl(var(--secondary))",
          foreground: "hsl(var(--secondary-foreground))",
        },
        destructive: {
          DEFAULT: "hsl(var(--destructive))",
          foreground: "hsl(var(--destructive-foreground))",
        },
        muted: {
          DEFAULT: "hsl(var(--muted))",
          foreground: "hsl(var(--muted-foreground))",
        },
        accent: {
          DEFAULT: "hsl(var(--accent))",
          foreground: "hsl(var(--accent-foreground))",
        },
      },
    },
  },
}
```

---

## 🚀 Deployment

### Vercel Deployment

```yaml
# vercel.json
{
  "buildCommand": "npm run build",
  "outputDirectory": ".next",
  "framework": "nextjs",
  "env": {
    "NEXT_PUBLIC_API_URL": "https://api.anvil.com/api/v1"
  }
}
```

### Docker Deployment

```dockerfile
FROM node:18-alpine AS builder

WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM node:18-alpine AS runner
WORKDIR /app

COPY --from=builder /app/public ./public
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static

EXPOSE 3000
CMD ["node", "server.js"]
```

---

**Document Version:** 1.0  
**Last Updated:** November 2025  
**Maintained By:** Frontend Team  
**Questions:** frontend-lead@anvil.com
