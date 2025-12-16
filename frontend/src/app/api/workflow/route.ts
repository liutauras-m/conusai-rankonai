import { type NextRequest, NextResponse } from "next/server"

export const maxDuration = 60

// Runtime env vars - must be accessed at request time for standalone mode
const getTurnstileSecretKey = () => process.env.TURNSTILE_SECRET_KEY
const getBackendUrl = () => process.env.BACKEND_URL || "http://localhost:8000"

/**
 * Normalize URL for consistent cache key matching.
 * Must match backend's normalize_url function.
 */
function normalizeUrl(url: string): string {
	if (!url) return url

	let normalized = url.trim()

	// Add scheme if missing
	if (!normalized.startsWith("http://") && !normalized.startsWith("https://")) {
		normalized = `https://${normalized}`
	}

	try {
		const parsed = new URL(normalized)

		// Lowercase hostname and remove www.
		let hostname = parsed.hostname.toLowerCase()
		if (hostname.startsWith("www.")) {
			hostname = hostname.slice(4)
		}

		// Remove default ports
		let port = parsed.port
		if ((parsed.protocol === "http:" && port === "80") || 
		    (parsed.protocol === "https:" && port === "443")) {
			port = ""
		}

		// Remove trailing slash from path (except root)
		let path = parsed.pathname
		if (path !== "/" && path.endsWith("/")) {
			path = path.slice(0, -1)
		} else if (path === "/") {
			path = ""
		}

		// Reconstruct URL (without fragment)
		let result = `${parsed.protocol}//${hostname}`
		if (port) result += `:${port}`
		result += path
		if (parsed.search) result += parsed.search

		return result
	} catch {
		return normalized
	}
}

// Verify Cloudflare Turnstile CAPTCHA token
async function verifyCaptcha(token: string, ip: string): Promise<boolean> {
	const secretKey = getTurnstileSecretKey()
	if (!secretKey) {
		// Skip verification if not configured (development)
		return true
	}

	try {
		const response = await fetch("https://challenges.cloudflare.com/turnstile/v0/siteverify", {
			method: "POST",
			headers: { "Content-Type": "application/x-www-form-urlencoded" },
			body: new URLSearchParams({
				secret: secretKey,
				response: token,
				remoteip: ip,
			}),
		})

		const data = await response.json()
		return data.success === true
	} catch (error) {
		console.error("CAPTCHA verification error:", error)
		return false
	}
}

/**
 * POST /api/workflow - Start a new workflow
 */
export async function POST(request: NextRequest) {
	try {
		const body = await request.json()
		const { url, brand, captchaToken } = body

		if (!url && !brand) {
			return NextResponse.json({ error: "URL or brand is required" }, { status: 400 })
		}

		// Verify CAPTCHA if secret key is configured
		const turnstileSecretKey = getTurnstileSecretKey()
		if (turnstileSecretKey) {
			if (!captchaToken) {
				return NextResponse.json({ error: "CAPTCHA verification required" }, { status: 400 })
			}

			const ip =
				request.headers.get("x-forwarded-for")?.split(",")[0] ||
				request.headers.get("x-real-ip") ||
				"unknown"

			const isValid = await verifyCaptcha(captchaToken, ip)
			if (!isValid) {
				return NextResponse.json(
					{ error: "CAPTCHA verification failed. Please try again." },
					{ status: 403 }
				)
			}
		}

		// Validate URL only when URL mode is used
		let bodyToSend: Record<string, unknown>
		if (url) {
			try {
				new URL(url.startsWith("http") ? url : `https://${url}`)
			} catch {
				return NextResponse.json({ error: "Invalid URL format" }, { status: 400 })
			}

			bodyToSend = { url }
		} else {
			// brand provided - we'll forward brand and a readable placeholder URL
			bodyToSend = { url: `brand:${brand}`, brand }
		}

		const backendUrl = getBackendUrl()
		const response = await fetch(`${backendUrl}/workflow/start`, {
			method: "POST",
			headers: { "Content-Type": "application/json" },
			body: JSON.stringify(bodyToSend),
		})

		if (!response.ok) {
			const error = await response.json().catch(() => ({}))
			return NextResponse.json(
				{ error: error.detail || "Failed to start workflow" },
				{ status: response.status }
			)
		}

		const data = await response.json()
		return NextResponse.json(data)
	} catch (error) {
		console.error("Workflow start error:", error)
		return NextResponse.json(
			{ error: error instanceof Error ? error.message : "Internal server error" },
			{ status: 500 }
		)
	}
}

/**
 * GET /api/workflow?jobId=xxx - Get workflow status
 * GET /api/workflow?jobId=xxx&result=true - Get workflow result
 * GET /api/workflow?url=xxx - Get cached result by URL (no jobId needed)
 */
export async function GET(request: NextRequest) {
	try {
		const { searchParams } = new URL(request.url)
		const jobId = searchParams.get("jobId")
		const url = searchParams.get("url")
		const getResult = searchParams.get("result") === "true"

		const backendUrl = getBackendUrl()

		// If URL is provided (no jobId), fetch by URL
		if (url && !jobId) {
			// Normalize URL to match backend's cache key format
			const normalizedUrl = normalizeUrl(url)
			const endpoint = `${backendUrl}/workflow/by-url?url=${encodeURIComponent(normalizedUrl)}`
			const response = await fetch(endpoint)

			if (!response.ok) {
				if (response.status === 404) {
					return NextResponse.json(
						{ error: "No cached result for this URL", notFound: true },
						{ status: 404 }
					)
				}
				const error = await response.json().catch(() => ({}))
				return NextResponse.json(
					{ error: error.detail || "Failed to get workflow result" },
					{ status: response.status }
				)
			}

			const data = await response.json()
			return NextResponse.json(data)
		}

		// Legacy: jobId-based lookup
		if (!jobId) {
			return NextResponse.json({ error: "jobId or url is required" }, { status: 400 })
		}

		const endpoint = getResult
			? `${backendUrl}/workflow/${jobId}/result`
			: `${backendUrl}/workflow/${jobId}/status`

		const response = await fetch(endpoint)

		if (!response.ok) {
			// Handle 202 (still processing) differently
			if (response.status === 202) {
				const data = await response.json().catch(() => ({}))
				return NextResponse.json(
					{ status: "running", message: data.detail || "Still processing" },
					{ status: 202 }
				)
			}

			const error = await response.json().catch(() => ({}))
			return NextResponse.json(
				{ error: error.detail || "Failed to get workflow status" },
				{ status: response.status }
			)
		}

		const data = await response.json()
		return NextResponse.json(data)
	} catch (error) {
		console.error("Workflow status error:", error)
		return NextResponse.json(
			{ error: error instanceof Error ? error.message : "Internal server error" },
			{ status: 500 }
		)
	}
}

/**
 * DELETE /api/workflow?jobId=xxx - Cancel a workflow
 */
export async function DELETE(request: NextRequest) {
	try {
		const { searchParams } = new URL(request.url)
		const jobId = searchParams.get("jobId")

		if (!jobId) {
			return NextResponse.json({ error: "jobId is required" }, { status: 400 })
		}

		const backendUrl = getBackendUrl()
		const response = await fetch(`${backendUrl}/workflow/${jobId}`, {
			method: "DELETE",
		})

		if (!response.ok) {
			const error = await response.json().catch(() => ({}))
			return NextResponse.json(
				{ error: error.detail || "Failed to cancel workflow" },
				{ status: response.status }
			)
		}

		const data = await response.json()
		return NextResponse.json(data)
	} catch (error) {
		console.error("Workflow cancel error:", error)
		return NextResponse.json(
			{ error: error instanceof Error ? error.message : "Internal server error" },
			{ status: 500 }
		)
	}
}
