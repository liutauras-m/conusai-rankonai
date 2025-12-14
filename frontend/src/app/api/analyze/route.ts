import { NextRequest, NextResponse } from "next/server"
import { spawn } from "child_process"
import path from "path"

export const maxDuration = 60 // Allow up to 60 seconds for analysis

export async function POST(request: NextRequest) {
	try {
		const { url } = await request.json()

		if (!url) {
			return NextResponse.json({ error: "URL is required" }, { status: 400 })
		}

		// Validate URL format
		try {
			new URL(url.startsWith("http") ? url : `https://${url}`)
		} catch {
			return NextResponse.json({ error: "Invalid URL format" }, { status: 400 })
		}

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
