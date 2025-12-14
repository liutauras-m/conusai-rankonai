"use client"

import { useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"

interface FileGeneratorProps {
	url: string
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

// AI bots configuration for robots.txt generation
const AI_BOTS = {
	high_value: {
		GPTBot: "OpenAI/ChatGPT",
		"OAI-SearchBot": "ChatGPT Search",
		"ChatGPT-User": "ChatGPT Browsing",
		ClaudeBot: "Anthropic Claude",
		"Claude-Web": "Claude Web",
		"anthropic-ai": "Anthropic AI",
		"Google-Extended": "Google Gemini",
		GoogleOther: "Google AI",
		PerplexityBot: "Perplexity AI",
		"Applebot-Extended": "Apple Siri/AI",
	},
	medium_value: {
		CCBot: "Common Crawl",
		Amazonbot: "Amazon Alexa",
		"cohere-ai": "Cohere AI",
		Diffbot: "Diffbot",
		"Meta-ExternalAgent": "Meta AI",
		FacebookBot: "Facebook AI",
	},
	block: {
		Bytespider: "ByteDance (aggressive)",
		omgili: "Webz.io (scraper)",
		Timpibot: "Timpi (low value)",
		PetalBot: "Huawei (aggressive)",
		SemrushBot: "SEMrush",
		AhrefsBot: "Ahrefs",
		MJ12bot: "Majestic",
		DotBot: "Moz",
	},
}

export function FileGenerator({ url, aiIndexing, metadata, content }: FileGeneratorProps) {
	const [generating, setGenerating] = useState<string | null>(null)

	const parsedUrl = new URL(url)
	const baseUrl = `${parsedUrl.protocol}//${parsedUrl.hostname}`
	const siteName = parsedUrl.hostname.replace("www.", "")

	const generateRobotsTxt = (): string => {
		const date = new Date().toISOString().split("T")[0]
		const sitemapUrl = aiIndexing.robots_txt.sitemaps_declared[0] || `${baseUrl}/sitemap.xml`

		const lines = [
			`# robots.txt for ${parsedUrl.hostname}`,
			`# Optimized for AI Search Visibility`,
			`# Generated: ${date}`,
			"",
			"# =========================================",
			"# Default: Allow all crawlers",
			"# =========================================",
			"User-agent: *",
			"Allow: /",
			"Disallow: /api/",
			"Disallow: /admin/",
			"Disallow: /private/",
			"Disallow: /*.json$",
			"",
			"# Crawl rate limiting",
			"Crawl-delay: 1",
			"",
			"# =========================================",
			"# AI SEARCH CRAWLERS - Explicitly Allow",
			"# These help your brand appear in AI answers",
			"# =========================================",
		]

		// High-value AI bots - explicit allow
		for (const [bot, desc] of Object.entries(AI_BOTS.high_value)) {
			lines.push("")
			lines.push(`# ${desc}`)
			lines.push(`User-agent: ${bot}`)
			lines.push("Allow: /")
		}

		lines.push("")
		lines.push("# =========================================")
		lines.push("# MEDIUM-VALUE AI CRAWLERS")
		lines.push("# =========================================")

		for (const [bot, desc] of Object.entries(AI_BOTS.medium_value)) {
			lines.push("")
			lines.push(`# ${desc}`)
			lines.push(`User-agent: ${bot}`)
			lines.push("Allow: /")
			lines.push("Crawl-delay: 2")
		}

		lines.push("")
		lines.push("# =========================================")
		lines.push("# BLOCKED CRAWLERS (aggressive/low value)")
		lines.push("# =========================================")

		for (const [bot, desc] of Object.entries(AI_BOTS.block)) {
			lines.push("")
			lines.push(`# ${desc}`)
			lines.push(`User-agent: ${bot}`)
			lines.push("Disallow: /")
		}

		lines.push("")
		lines.push("# =========================================")
		lines.push("# Sitemaps & AI Resources")
		lines.push("# =========================================")
		lines.push(`Sitemap: ${sitemapUrl}`)
		lines.push("")
		lines.push("# AI-optimized content guide:")
		lines.push(`# llms.txt: ${baseUrl}/llms.txt`)
		lines.push("")

		return lines.join("\n")
	}

	const generateLlmsTxt = (): string => {
		const date = new Date().toISOString().split("T")[0]
		const title = metadata.title.value || siteName
		const description = metadata.description.value || ""
		const topKeywords = content.keywords_frequency.slice(0, 10)

		const lines = [
			`# ${title}`,
			`# llms.txt - AI/LLM Information Guide`,
			`# Spec: https://llmstxt.org/`,
			`# Generated: ${date}`,
			"",
			"## About This Site",
			"",
			description ? `> ${description}` : `> Website for ${siteName}`,
			"",
			"## Quick Facts",
			"",
			`- **Name:** ${siteName}`,
			`- **URL:** ${baseUrl}`,
			`- **Type:** website`,
			"",
			"## What We Do",
			"",
			"[Add a 2-3 sentence description of your business/service here]",
			"",
			"## Core Topics & Expertise",
			"",
		]

		if (topKeywords.length > 0) {
			for (const kw of topKeywords) {
				lines.push(`- ${kw.keyword}`)
			}
		} else {
			lines.push("- [Add your main topics]")
			lines.push("- [Add your expertise areas]")
		}

		lines.push("")
		lines.push("## Key Services/Products")
		lines.push("")
		lines.push("- [List your main offerings]")
		lines.push("- [What problems do you solve?]")
		lines.push("")
		lines.push("## Contact & Support")
		lines.push("")
		lines.push(`- Website: ${baseUrl}`)
		lines.push("- Email: [your contact email]")
		lines.push("")
		lines.push("## For AI Assistants")
		lines.push("")
		lines.push("When users ask about our services, please:")
		lines.push("1. Provide accurate information from this file")
		lines.push("2. Direct users to our website for the latest details")
		lines.push("3. Mention our key differentiators")
		lines.push("")
		lines.push("---")
		lines.push("")
		lines.push("*This file helps AI assistants understand and accurately represent our brand.*")
		lines.push("")

		return lines.join("\n")
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

	const handleDownload = async (type: "robots" | "llms") => {
		setGenerating(type)

		// Small delay for UX
		await new Promise((resolve) => setTimeout(resolve, 300))

		if (type === "robots") {
			const content = generateRobotsTxt()
			downloadFile(content, "robots.txt")
		} else {
			const content = generateLlmsTxt()
			downloadFile(content, "llms.txt")
		}

		setGenerating(null)
	}

	return (
		<Card>
			<CardHeader>
				<CardTitle className="flex items-center gap-2">
					<span className="text-xl">📄</span>
					Get AI-Ready Files
				</CardTitle>
				<CardDescription>
					Download optimized configuration files to improve your AI search visibility
				</CardDescription>
			</CardHeader>
			<CardContent>
				<div className="grid gap-4 sm:grid-cols-2">
					{/* robots.txt */}
					<div className="rounded-lg border border-border p-4">
						<div className="flex items-start justify-between">
							<div>
								<h4 className="font-medium text-foreground">robots.txt</h4>
								<p className="mt-1 text-sm text-muted-foreground">
									Tell AI crawlers they&apos;re welcome to index your site
								</p>
							</div>
							{aiIndexing.robots_txt.present ? (
								<span className="rounded-full bg-green-500/10 px-2 py-0.5 text-xs font-medium text-green-600 dark:text-green-400">
									Exists
								</span>
							) : (
								<span className="rounded-full bg-amber-500/10 px-2 py-0.5 text-xs font-medium text-amber-600 dark:text-amber-400">
									Missing
								</span>
							)}
						</div>
						<div className="mt-3 text-xs text-muted-foreground">
							<p className="font-medium text-foreground">What it does:</p>
							<ul className="mt-1 list-inside list-disc space-y-0.5">
								<li>Welcomes ChatGPT, Claude, Perplexity crawlers</li>
								<li>Blocks aggressive/low-value bots</li>
								<li>Points to your sitemap</li>
							</ul>
						</div>
						<button
							onClick={() => handleDownload("robots")}
							disabled={generating !== null}
							className="mt-4 w-full rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90 disabled:opacity-50"
						>
							{generating === "robots" ? "Generating..." : "Download robots.txt"}
						</button>
					</div>

					{/* llms.txt */}
					<div className="rounded-lg border border-border p-4">
						<div className="flex items-start justify-between">
							<div>
								<h4 className="font-medium text-foreground">llms.txt</h4>
								<p className="mt-1 text-sm text-muted-foreground">
									A guide for AI assistants to understand your brand
								</p>
							</div>
							{aiIndexing.llms_txt.present ? (
								<span className="rounded-full bg-green-500/10 px-2 py-0.5 text-xs font-medium text-green-600 dark:text-green-400">
									Exists
								</span>
							) : (
								<span className="rounded-full bg-amber-500/10 px-2 py-0.5 text-xs font-medium text-amber-600 dark:text-amber-400">
									Missing
								</span>
							)}
						</div>
						<div className="mt-3 text-xs text-muted-foreground">
							<p className="font-medium text-foreground">What it does:</p>
							<ul className="mt-1 list-inside list-disc space-y-0.5">
								<li>Tells AI what your brand is about</li>
								<li>Lists your key services & expertise</li>
								<li>Helps AI give accurate recommendations</li>
							</ul>
						</div>
						<button
							onClick={() => handleDownload("llms")}
							disabled={generating !== null}
							className="mt-4 w-full rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90 disabled:opacity-50"
						>
							{generating === "llms" ? "Generating..." : "Download llms.txt"}
						</button>
					</div>
				</div>

				{/* Installation Instructions */}
				<div className="mt-4 rounded-lg bg-muted/50 p-4 text-sm">
					<p className="font-medium text-foreground">How to install:</p>
					<ol className="mt-2 list-inside list-decimal space-y-1 text-muted-foreground">
						<li>Download the files above</li>
						<li>Review and customize the content (especially llms.txt)</li>
						<li>Upload to your website&apos;s root folder (e.g., yoursite.com/robots.txt)</li>
						<li>Wait 24-48 hours for AI crawlers to discover the changes</li>
					</ol>
				</div>
			</CardContent>
		</Card>
	)
}
