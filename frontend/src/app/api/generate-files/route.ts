import { spawn } from "node:child_process"
import fsSync from "node:fs"
import fs from "node:fs/promises"
import os from "node:os"
import path from "node:path"
import { type NextRequest, NextResponse } from "next/server"

const DEFAULT_TIMEOUT_MS = 60000
const getBackendUrl = () => process.env.BACKEND_URL

function resolvePythonBinary(): string {
	const candidates = [
		path.resolve(process.cwd(), "../venv/bin/python3"),
		path.resolve(process.cwd(), "../venv/bin/python"),
		process.env.PYTHON,
		"python3",
		"python",
	]

	for (const candidate of candidates) {
		if (!candidate) continue
		if (candidate.startsWith("/") && !fsSync.existsSync(candidate)) continue
		return candidate
	}

	return "python3"
}

async function removeDirSafe(dir: string) {
	try {
		await fs.rm(dir, { recursive: true, force: true })
	} catch (error) {
		console.error("Failed to clean temp dir", error)
	}
}

export async function POST(request: NextRequest) {
	try {
		const payload = await request.json()
		const report = payload?.report

		if (!report || typeof report !== "object") {
			return NextResponse.json(
				{ success: false, error: "report payload is required" },
				{ status: 400 }
			)
		}

		// In production (Docker), call the backend API
		const backendUrl = getBackendUrl()
		if (backendUrl) {
			const response = await fetch(`${backendUrl}/generate-files`, {
				method: "POST",
				headers: { "Content-Type": "application/json" },
				body: JSON.stringify({ report }),
			})

			if (!response.ok) {
				const error = await response.json().catch(() => ({}))
				return NextResponse.json(
					{ success: false, error: error.detail || "Generation failed" },
					{ status: response.status }
				)
			}

			const data = await response.json()
			return NextResponse.json({
				success: true,
				robotsContent: data.robots_txt,
				llmsContent: data.llms_txt,
				meta: { ai_powered: data.ai_powered },
			})
		}

		// In development, run Python directly
		const scriptPath = path.resolve(process.cwd(), "../backend/seo_ai_generator.py")
		const python = resolvePythonBinary()

		const tempDir = await fs.mkdtemp(path.join(os.tmpdir(), "seoai-"))
		const reportPath = path.join(tempDir, "report.json")
		await fs.writeFile(reportPath, JSON.stringify(report))

		const args = [scriptPath, reportPath, "--output-dir", tempDir]

		const proc = spawn(python, args, {
			cwd: path.resolve(process.cwd(), "../backend"),
			env: { ...process.env },
		})

		const stdoutChunks: string[] = []
		const stderrChunks: string[] = []

		const timeout = setTimeout(() => proc.kill(), DEFAULT_TIMEOUT_MS)

		proc.stdout.on("data", (chunk) =>
			stdoutChunks.push(typeof chunk === "string" ? chunk : chunk.toString())
		)
		proc.stderr.on("data", (chunk) =>
			stderrChunks.push(typeof chunk === "string" ? chunk : chunk.toString())
		)

		const exitCode: number = await new Promise((resolve, reject) => {
			proc.on("error", (error) => {
				clearTimeout(timeout)
				reject(error)
			})
			proc.on("close", (code) => {
				clearTimeout(timeout)
				resolve(code ?? 0)
			})
		})

		const stdout = stdoutChunks.join("\n")
		const stderr = stderrChunks.join("\n")

		if (exitCode !== 0) {
			await removeDirSafe(tempDir)
			return NextResponse.json(
				{ success: false, error: "Generator failed", detail: stderr || stdout || "Unknown error" },
				{ status: 500 }
			)
		}

		const robotsPath = path.join(tempDir, "robots.txt")
		const llmsPath = path.join(tempDir, "llms.txt")

		let robotsContent = ""
		let llmsContent = ""

		try {
			robotsContent = await fs.readFile(robotsPath, "utf8")
			llmsContent = await fs.readFile(llmsPath, "utf8")
		} catch (error) {
			await removeDirSafe(tempDir)
			return NextResponse.json(
				{
					success: false,
					error: "Generated files missing",
					detail: error instanceof Error ? error.message : String(error),
				},
				{ status: 500 }
			)
		}

		await removeDirSafe(tempDir)

		let meta: unknown = null
		try {
			meta = JSON.parse(stdout)
		} catch (error) {
			meta = { parseError: error instanceof Error ? error.message : "parse error", raw: stdout }
		}

		return NextResponse.json({
			success: true,
			robotsContent,
			llmsContent,
			meta,
			stderr: stderr || undefined,
		})
	} catch (error) {
		return NextResponse.json(
			{ success: false, error: error instanceof Error ? error.message : "Unknown error" },
			{ status: 500 }
		)
	}
}
