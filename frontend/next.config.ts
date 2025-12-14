import type { NextConfig } from "next"

const nextConfig: NextConfig = {
	// Enable standalone output for Docker
	output: "standalone",
	// Environment variables
	env: {
		OPENAI_API_KEY: process.env.OPENAI_API_KEY,
		GOOGLE_API_KEY: process.env.GOOGLE_API_KEY,
		XAI_API_KEY: process.env.XAI_API_KEY,
		BACKEND_URL: process.env.BACKEND_URL || "http://localhost:8000",
		NEXT_PUBLIC_TURNSTILE_SITE_KEY: process.env.NEXT_PUBLIC_TURNSTILE_SITE_KEY,
	},
	experimental: {
		typedRoutes: true,
	},
}

export default nextConfig
