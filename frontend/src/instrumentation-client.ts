import posthog from 'posthog-js'

if (process.env.NEXT_PUBLIC_POSTHOG_KEY) {
  posthog.init(process.env.NEXT_PUBLIC_POSTHOG_KEY, {
    api_host: '/ingest',
    ui_host: 'https://eu.posthog.com',
    defaults: '2025-11-30', // Use latest defaults for automatic pageview/pageleave tracking
    person_profiles: 'identified_only',
    capture_exceptions: true,
    debug: process.env.NODE_ENV === 'development',
  })
}
