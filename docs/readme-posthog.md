# PostHog Analytics Setup

This guide covers implementing PostHog analytics in a Next.js App Router project with EU data residency and ad blocker bypass.

---

## Quick Start

### 1. Install Dependencies

```bash
pnpm add posthog-js posthog-node
```

### 2. Environment Variables

Add to `.env.local`:

```env
NEXT_PUBLIC_POSTHOG_KEY=phc_your_project_key_here
NEXT_PUBLIC_POSTHOG_HOST=https://eu.i.posthog.com
```

> **Note:** Use `https://us.i.posthog.com` for US data residency.

---

## Implementation

### 3. Create PostHog Provider

Create `src/components/posthog-provider.tsx`:

```tsx
'use client'

import posthog from 'posthog-js'
import { PostHogProvider as PHProvider, usePostHog } from 'posthog-js/react'
import { usePathname, useSearchParams } from 'next/navigation'
import { Suspense, useEffect } from 'react'

export function PostHogProvider({ children }: { children: React.ReactNode }) {
  useEffect(() => {
    const key = process.env.NEXT_PUBLIC_POSTHOG_KEY
    if (!key) return

    posthog.init(key, {
      api_host: '/ingest',
      ui_host: 'https://eu.posthog.com',
      person_profiles: 'identified_only', // Only create profiles for identified users
      capture_pageview: false, // Capture manually for SPA navigation
      capture_pageleave: true,
      capture_exceptions: true,
      debug: process.env.NODE_ENV === 'development',
    })
  }, [])

  return (
    <PHProvider client={posthog}>
      <Suspense fallback={null}>
        <PostHogPageView />
      </Suspense>
      {children}
    </PHProvider>
  )
}

// Capture page views on route change
function PostHogPageView() {
  const pathname = usePathname()
  const searchParams = useSearchParams()
  const posthogClient = usePostHog()

  useEffect(() => {
    if (pathname && posthogClient) {
      let url = window.origin + pathname
      if (searchParams.toString()) {
        url = `${url}?${searchParams.toString()}`
      }
      posthogClient.capture('$pageview', { $current_url: url })
    }
  }, [pathname, searchParams, posthogClient])

  return null
}
```

### 4. Create Server-Side Client (Optional)

Create `src/lib/posthog.ts` for server-side event tracking:

```typescript
import { PostHog } from 'posthog-node'

export default function PostHogClient() {
  const key = process.env.NEXT_PUBLIC_POSTHOG_KEY
  if (!key) {
    throw new Error('NEXT_PUBLIC_POSTHOG_KEY is not set')
  }

  const posthogClient = new PostHog(key, {
    host: process.env.NEXT_PUBLIC_POSTHOG_HOST,
    flushAt: 1,
    flushInterval: 0,
  })

  return posthogClient
}
```

### 5. Add Proxy Rewrites (Ad Blocker Bypass)

Update `next.config.ts`:

```typescript
import type { NextConfig } from 'next'

const nextConfig: NextConfig = {
  // ... other config

  async rewrites() {
    return [
      {
        source: '/ingest/static/:path*',
        destination: 'https://eu-assets.i.posthog.com/static/:path*',
      },
      {
        source: '/ingest/:path*',
        destination: 'https://eu.i.posthog.com/:path*',
      },
      {
        source: '/ingest/decide',
        destination: 'https://eu.i.posthog.com/decide',
      },
    ]
  },
}

export default nextConfig
```

> **For US region:** Replace `eu.i.posthog.com` with `us.i.posthog.com` and `eu-assets.i.posthog.com` with `us-assets.i.posthog.com`.

### 6. Wrap Layout with Provider

Update `src/app/layout.tsx`:

```tsx
import { PostHogProvider } from '@/components/posthog-provider'

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <PostHogProvider>
          {children}
        </PostHogProvider>
      </body>
    </html>
  )
}
```

---

## Usage

### Track Custom Events (Client-Side)

```tsx
'use client'

import { usePostHog } from 'posthog-js/react'

export function MyComponent() {
  const posthog = usePostHog()

  const handleClick = () => {
    posthog.capture('button_clicked', {
      button_name: 'signup',
      page: '/pricing',
    })
  }

  return <button onClick={handleClick}>Sign Up</button>
}
```

### Track Events (Server-Side)

```typescript
import PostHogClient from '@/lib/posthog'

export async function POST(request: Request) {
  const posthog = PostHogClient()

  posthog.capture({
    distinctId: 'user-123',
    event: 'form_submitted',
    properties: {
      form_name: 'contact',
    },
  })

  await posthog.shutdown() // Flush events before response

  return Response.json({ success: true })
}
```

### Identify Users

```tsx
import { usePostHog } from 'posthog-js/react'

function handleLogin(user: { id: string; email: string; name: string }) {
  const posthog = usePostHog()

  posthog.identify(user.id, {
    email: user.email,
    name: user.name,
  })
}
```

### Feature Flags

```tsx
'use client'

import { useFeatureFlagEnabled } from 'posthog-js/react'

export function NewFeature() {
  const isEnabled = useFeatureFlagEnabled('new-feature-flag')

  if (!isEnabled) return null

  return <div>New Feature!</div>
}
```

---

## Configuration Options

| Option | Description | Default |
|--------|-------------|---------|
| `api_host` | API endpoint (use `/ingest` with proxy) | Direct URL |
| `person_profiles` | When to create person profiles (`identified_only` or `always`) | `identified_only` |
| `capture_pageview` | Auto-capture page views | `true` |
| `capture_pageleave` | Track when users leave | `false` |
| `capture_exceptions` | Auto-capture JS errors | `false` |
| `autocapture` | Auto-capture clicks, inputs | `true` |
| `persistence` | Storage type | `localStorage+cookie` |
| `debug` | Enable debug logging | `false` |

---

## File Structure

```
src/
├── app/
│   └── layout.tsx          # Wrap with PostHogProvider
├── components/
│   └── posthog-provider.tsx # Client-side provider
└── lib/
    └── posthog.ts          # Server-side client
```

---

## Troubleshooting

### Events not appearing?

1. Check `.env.local` has correct `NEXT_PUBLIC_POSTHOG_KEY`
2. Verify rewrites are working: visit `/ingest/decide` (should not 404)
3. Enable debug mode: `debug: true` in init options
4. Check browser console for PostHog logs

### Ad blockers still blocking?

Ensure all rewrites are in place and use `/ingest` as `api_host`, not the direct PostHog URL.

### Duplicate page views?

Set `capture_pageview: false` and use the manual `PostHogPageView` component.

---

## Resources

- [PostHog Next.js Docs](https://posthog.com/docs/libraries/next-js)
- [PostHog React Hooks](https://posthog.com/docs/libraries/react)
- [Feature Flags](https://posthog.com/docs/feature-flags)
- [Session Replay](https://posthog.com/docs/session-replay)

---

*Last updated: December 2024*
