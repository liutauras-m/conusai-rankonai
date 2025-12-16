"use client"

import { CheckCircle2, Download, FileCode, Zap } from "lucide-react"
import { useState } from "react"

interface FileGeneratorProps {
	url: string
	report?: Record<string, unknown> | null
	aiIndexing: {
		robots_txt: {
			present: boolean
			ai_bots_status: Record<string, string>
			sitemaps_declared: string[]
		}
		llms_txt: {
			present: boolean
			content_preview: string | null
		}
		sitemap_xml: {
			present: boolean
		}
	}
	metadata: {
		title: { value: string | null }
		description: { value: string | null }
	}
	content: {
		keywords_frequency: Array<{ keyword: string; count: number }>
	}
}

export function FileGenerator({
	url,
	report,
	aiIndexing,
	metadata,
	content: _content,
}: FileGeneratorProps) {
	const [generating, setGenerating] = useState<string | null>(null)
	const [apiGenerating, setApiGenerating] = useState<"robots" | "llms" | null>(null)
	const [error, setError] = useState<string | null>(null)

	const parsedUrl = new URL(url)
	const baseUrl = `${parsedUrl.protocol}//${parsedUrl.hostname}`
	const siteName = parsedUrl.hostname.replace("www.", "")

	// Simple fallback generator (used only for quick/offline mode)
	const generateSimpleRobotsTxt = (): string => {
		const sitemapUrl = aiIndexing.robots_txt.sitemaps_declared[0] || `${baseUrl}/sitemap.xml`
		return `# robots.txt for ${parsedUrl.hostname}
# Basic template - Use AI-powered generation for optimized content

User-agent: *
Allow: /

Sitemap: ${sitemapUrl}
`
	}

	const generateSimpleLlmsTxt = (): string => {
		const title = metadata.title.value || siteName
		const description = metadata.description.value || ""
		return `# ${title}

> ${description || `Website for ${siteName}`}

## Overview
- **URL:** ${baseUrl}

## AI/LLM Permissions
This site allows AI crawlers to index public content.

---
*Use AI-powered generation for comprehensive, customized content.*
`
	}

	const downloadFile = (content: string, filename: string) => {
		const blob = new Blob([content], { type: "text/plain" })
		const url = URL.createObjectURL(blob)
		const a = document.createElement("a")
		a.href = url
		a.download = filename
		document.body.appendChild(a)
		a.click()
		document.body.removeChild(a)
		URL.revokeObjectURL(url)
	}

	const handleDownload = async (type: "robots" | "llms", mode: "local" | "api" = "api") => {
		// Quick/fallback mode - uses simple templates
		if (mode === "local") {
			setGenerating(type)
			await new Promise((resolve) => setTimeout(resolve, 200))
			const content = type === "robots" ? generateSimpleRobotsTxt() : generateSimpleLlmsTxt()
			downloadFile(content, `${type}.txt`)
			setGenerating(null)
			return
		}

		// AI-powered mode - calls ChatGPT via Python backend
		if (!report) {
			setError("Run an analysis first to enable AI-powered generation")
			return
		}

		setError(null)
		setApiGenerating(type)

		try {
			const response = await fetch("/api/generate-files", {
				method: "POST",
				headers: { "Content-Type": "application/json" },
				body: JSON.stringify({ report }),
			})

			if (!response.ok) {
				const body = await response.json().catch(() => ({}))
				throw new Error(body?.error || "AI generation request failed")
			}

			const payload = await response.json()
			// Handle both frontend API (robotsContent/llmsContent) and backend API (robots_txt/llms_txt)
			const content =
				type === "robots"
					? payload.robotsContent || payload.robots_txt
					: payload.llmsContent || payload.llms_txt
			if (!content) {
				throw new Error("No content returned from AI generator")
			}
			downloadFile(content, `${type}.txt`)
		} catch (generatorError) {
			const message =
				generatorError instanceof Error ? generatorError.message : "AI generation error"
			setError(message)
		} finally {
			setApiGenerating(null)
		}
	}

	return (
		<section className="space-y-4">
			<div className="flex items-center gap-2">
				<FileCode className="h-4 w-4 text-primary" />
				<h2 className="font-medium text-muted-foreground text-sm uppercase tracking-wider">
					Generate Files
				</h2>
			</div>

			<div className="rounded-xl border border-border/50 bg-card p-4 sm:p-6">
				{/* Info Banner */}
				<div className="mb-5 flex items-center gap-3 rounded-lg border border-primary/10 bg-primary/5 p-3">
					<Download className="h-4 w-4 shrink-0 text-primary" />
					<span className="text-foreground text-sm">
						AI-powered file generation based on your analysis
					</span>
				</div>

				{error && (
					<p className="mb-4 rounded-lg border border-destructive/10 bg-destructive/5 p-3 text-destructive text-sm">
						{error}
					</p>
				)}

				<div className="grid gap-4 sm:grid-cols-2">
					{/* robots.txt */}
					<div className="rounded-xl border border-border/50 bg-background p-4 transition-all duration-200 hover:border-primary/20">
						<div className="mb-3 flex items-start justify-between">
							<div>
								<h4 className="font-medium text-foreground">robots.txt</h4>
								<p className="mt-1 text-muted-foreground text-xs">
									Crawler directives for your site
								</p>
							</div>
							{aiIndexing.robots_txt.present ? (
								<span className="flex items-center gap-1 text-primary text-xs">
									<CheckCircle2 className="h-3 w-3" /> Exists
								</span>
							) : (
								<span className="text-muted-foreground text-xs">Missing</span>
							)}
						</div>

						<ul className="mb-4 space-y-1 text-muted-foreground text-xs">
							<li>• AI crawler permissions</li>
							<li>• Path restrictions</li>
							<li>• Sitemap declaration</li>
						</ul>

						<div className="grid gap-2">
							<button
								type="button"
								onClick={() => handleDownload("robots", "api")}
								disabled={apiGenerating !== null || generating !== null}
								className="flex w-full items-center justify-center gap-2 rounded-lg bg-primary px-4 py-2 font-medium text-primary-foreground text-sm transition-all duration-200 hover:bg-primary/90 disabled:opacity-50"
							>
								<Download className="h-3.5 w-3.5" />
								{apiGenerating === "robots" ? "Generating..." : "Generate with AI"}
							</button>
							<button
								type="button"
								onClick={() => handleDownload("robots", "local")}
								disabled={generating !== null || apiGenerating !== null}
								className="flex w-full items-center justify-center gap-2 rounded-lg border border-border/50 px-4 py-2 font-medium text-muted-foreground text-sm transition-colors hover:bg-muted/50 disabled:opacity-50"
							>
								<Zap className="h-3.5 w-3.5" />
								{generating === "robots" ? "..." : "Quick template"}
							</button>
						</div>
					</div>

					{/* llms.txt */}
					<div className="rounded-xl border border-border/50 bg-background p-4 transition-all duration-200 hover:border-primary/20">
						<div className="mb-3 flex items-start justify-between">
							<div>
								<h4 className="font-medium text-foreground">llms.txt</h4>
								<p className="mt-1 text-muted-foreground text-xs">
									AI assistant guide for your brand
								</p>
							</div>
							{aiIndexing.llms_txt.present ? (
								<span className="flex items-center gap-1 text-primary text-xs">
									<CheckCircle2 className="h-3 w-3" /> Exists
								</span>
							) : (
								<span className="text-muted-foreground text-xs">Missing</span>
							)}
						</div>

						<ul className="mb-4 space-y-1 text-muted-foreground text-xs">
							<li>• Site overview</li>
							<li>• Key topics & keywords</li>
							<li>• LLM permissions</li>
						</ul>

						<div className="grid gap-2">
							<button
								type="button"
								onClick={() => handleDownload("llms", "api")}
								disabled={apiGenerating !== null || generating !== null}
								className="flex w-full items-center justify-center gap-2 rounded-lg bg-primary px-4 py-2 font-medium text-primary-foreground text-sm transition-all duration-200 hover:bg-primary/90 disabled:opacity-50"
							>
								<Download className="h-3.5 w-3.5" />
								{apiGenerating === "llms" ? "Generating..." : "Generate with AI"}
							</button>
							<button
								type="button"
								onClick={() => handleDownload("llms", "local")}
								disabled={generating !== null || apiGenerating !== null}
								className="flex w-full items-center justify-center gap-2 rounded-lg border border-border/50 px-4 py-2 font-medium text-muted-foreground text-sm transition-colors hover:bg-muted/50 disabled:opacity-50"
							>
								<Zap className="h-3.5 w-3.5" />
								{generating === "llms" ? "..." : "Quick template"}
							</button>
						</div>
					</div>
				</div>

				{/* Installation Instructions */}
				<div className="mt-5 border-border/50 border-t pt-4">
					<p className="mb-2 font-medium text-muted-foreground text-xs uppercase tracking-wider">
						Installation
					</p>
					<ol className="space-y-1 text-muted-foreground text-xs">
						<li>1. Generate and review the file content</li>
						<li>2. Upload to your site root (e.g., yoursite.com/robots.txt)</li>
						<li>3. Allow 24-48 hours for crawlers to discover changes</li>
					</ol>
				</div>
			</div>
		</section>
	)
}
