import type { NextConfig } from "next"
import path from "path"

const nextConfig: NextConfig = {
	reactCompiler: true,
	// Load .env from parent directory (monorepo root)
	env: {
		OPENAI_API_KEY: process.env.OPENAI_API_KEY,
		GOOGLE_API_KEY: process.env.GOOGLE_API_KEY,
		XAI_API_KEY: process.env.XAI_API_KEY,
	},
	// Allow importing from parent data directory
	experimental: {
		typedRoutes: true,
	},
}

export default nextConfig
