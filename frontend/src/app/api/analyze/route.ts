import { type NextRequest, NextResponse } from "next/server"
import { spawn } from "node:child_process"
import path from "node:path"

export const maxDuration = 60 // Allow up to 60 seconds for analysis

// Runtime env vars - must be accessed at request time for standalone mode
const getTurnstileSecretKey = () => process.env.TURNSTILE_SECRET_KEY
const getBackendUrl = () => process.env.BACKEND_URL

// Verify Cloudflare Turnstile CAPTCHA token
async function verifyCaptcha(token: string, ip: string): Promise<boolean> {
	const secretKey = getTurnstileSecretKey()
	if (!secretKey) {
		// Skip verification if not configured (development)
		return true
	}

	try {
		const response = await fetch(
			"https://challenges.cloudflare.com/turnstile/v0/siteverify",
			{
				method: "POST",
				headers: { "Content-Type": "application/x-www-form-urlencoded" },
				body: new URLSearchParams({
					secret: secretKey,
					response: token,
					remoteip: ip,
				}),
			}
		)

		const data = await response.json()
		return data.success === true
	} catch (error) {
		console.error("CAPTCHA verification error:", error)
		return false
	}
}

export async function POST(request: NextRequest) {
	try {
		const { url, captchaToken } = await request.json()

		if (!url) {
			return NextResponse.json({ error: "URL is required" }, { status: 400 })
		}

		// Verify CAPTCHA if secret key is configured
		const turnstileSecretKey = getTurnstileSecretKey()
		if (turnstileSecretKey) {
			if (!captchaToken) {
				return NextResponse.json(
					{ error: "CAPTCHA verification required" },
					{ status: 400 }
				)
			}

			const ip = request.headers.get("x-forwarded-for")?.split(",")[0] || 
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

		// Validate URL format
		try {
			new URL(url.startsWith("http") ? url : `https://${url}`)
		} catch {
			return NextResponse.json({ error: "Invalid URL format" }, { status: 400 })
		}

		// In production (Docker), call the backend API
		const backendUrl = getBackendUrl()
		if (backendUrl) {
			const response = await fetch(`${backendUrl}/analyze`, {
				method: "POST",
				headers: { "Content-Type": "application/json" },
				body: JSON.stringify({ url }),
			})

			if (!response.ok) {
				const error = await response.json()
				return NextResponse.json(
					{ error: error.detail || "Analysis failed" },
					{ status: response.status }
				)
			}

			const data = await response.json()
			return NextResponse.json(data.data)
		}

		// In development, run Python directly
		const result = await runSEOAnalyzer(url)
		return NextResponse.json(result)
	} catch (error) {
		console.error("Analysis error:", error)
		return NextResponse.json(
			{ error: error instanceof Error ? error.message : "Analysis failed" },
			{ status: 500 }
		)
	}
}

function runSEOAnalyzer(url: string): Promise<Record<string, unknown>> {
	return new Promise((resolve, reject) => {
		const scriptPath = path.resolve(process.cwd(), "../backend/seo_analyzer.py")

		// Use venv python from project root
		const python = path.resolve(process.cwd(), "../venv/bin/python3")

		const args = [scriptPath, url, "--pretty"]

		const proc = spawn(python, args, {
			cwd: path.resolve(process.cwd(), "../backend"),
			env: { ...process.env },
		})

		let stdout = ""
		let stderr = ""

		proc.stdout.on("data", (data) => {
			stdout += data.toString()
		})

		proc.stderr.on("data", (data) => {
			stderr += data.toString()
		})

		proc.on("close", (code) => {
			if (code !== 0) {
				console.error("Python stderr:", stderr)
				reject(new Error(`Analysis failed: ${stderr || "Unknown error"}`))
				return
			}

			try {
				const result = JSON.parse(stdout)
				resolve(result)
			} catch {
				reject(new Error("Failed to parse analysis results"))
			}
		})

		proc.on("error", (err) => {
			reject(new Error(`Failed to start analyzer: ${err.message}`))
		})

		// Timeout after 55 seconds
		setTimeout(() => {
			proc.kill()
			reject(new Error("Analysis timed out"))
		}, 55000)
	})
}
