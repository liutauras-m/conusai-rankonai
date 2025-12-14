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
