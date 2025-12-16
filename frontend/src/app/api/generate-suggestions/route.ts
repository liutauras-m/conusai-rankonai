import { type NextRequest, NextResponse } from "next/server"

const OPENAI_API_KEY = process.env.OPENAI_API_KEY
const getBackendUrl = () => process.env.BACKEND_URL

interface AnalysisReport {
	url?: string
	metadata?: {
		title?: { value?: string | null }
		description?: { value?: string | null }
	}
	content?: {
		keywords_frequency?: Array<{ keyword: string; count: number }>
	}
	llm_context?: {
		top_keywords?: string[]
		summary?: string
	}
	scores?: Record<string, number>
}

export async function POST(request: NextRequest) {
	try {
		const body = await request.json()
		const analysis: AnalysisReport = body.analysis
		const type: "preferences" | "questions" = body.type

		if (!analysis) {
			return NextResponse.json({ error: "analysis payload is required" }, { status: 400 })
		}

		// In production (Docker), call the backend API
		const backendUrl = getBackendUrl()
		if (backendUrl) {
			const response = await fetch(`${backendUrl}/generate-suggestions`, {
				method: "POST",
				headers: { "Content-Type": "application/json" },
				body: JSON.stringify({ analysis, type }),
			})

			if (!response.ok) {
				const error = await response.json().catch(() => ({}))
				return NextResponse.json(
					{ error: error.detail || "Suggestions generation failed" },
					{ status: response.status }
				)
			}

			return NextResponse.json(await response.json())
		}

		// In development, call OpenAI directly
		if (!OPENAI_API_KEY) {
			return NextResponse.json({ error: "OPENAI_API_KEY not configured" }, { status: 500 })
		}

		// Extract context from analysis
		const brand =
			analysis.metadata?.title?.value ||
			(analysis.url ? new URL(analysis.url).hostname : "the brand")
		const description = analysis.metadata?.description?.value || ""
		const keywords =
			analysis.llm_context?.top_keywords?.slice(0, 10) ||
			analysis.content?.keywords_frequency?.slice(0, 10).map((k) => k.keyword) ||
			[]
		const scores = analysis.scores || {}

		let prompt: string
		let systemPrompt: string

		if (type === "preferences") {
			systemPrompt =
				"You are an AI SEO expert. Generate user preference options based on SEO analysis. Return valid JSON only."
			prompt = `Based on this website analysis, generate 4 personalized preference options that users can select to focus their AI optimization efforts.

WEBSITE CONTEXT:
- Brand: ${brand}
- Description: ${description}
- Top Keywords: ${keywords.join(", ")}
- Current Scores: ${JSON.stringify(scores)}

Generate 4 preference options as a JSON array. Each option should be relevant to this specific website's content and goals.

Format:
[
  {
    "id": "unique_snake_case_id",
    "label": "Short Label (2-3 words)",
    "detail": "One sentence explaining how this preference helps AI recommend this brand."
  }
]

Return ONLY the JSON array, no markdown or explanation.`
		} else {
			systemPrompt =
				"You are an AI brand strategist. Generate questions users should answer to improve AI discoverability. Return valid JSON only."
			prompt = `Based on this website analysis, generate 5 strategic questions that will help improve how AI assistants recommend this brand.

WEBSITE CONTEXT:
- Brand: ${brand}
- Description: ${description}
- Top Keywords: ${keywords.join(", ")}

Generate questions as a JSON array of strings. Questions should:
1. Be specific to this brand/website
2. Help craft FAQs and AI-friendly content
3. Focus on what makes this brand recommendable

Format:
["Question 1?", "Question 2?", "Question 3?", "Question 4?", "Question 5?"]

Return ONLY the JSON array, no markdown or explanation.`
		}

		const response = await fetch("https://api.openai.com/v1/chat/completions", {
			method: "POST",
			headers: {
				Authorization: `Bearer ${OPENAI_API_KEY}`,
				"Content-Type": "application/json",
			},
			body: JSON.stringify({
				model: "gpt-4o",
				messages: [
					{ role: "system", content: systemPrompt },
					{ role: "user", content: prompt },
				],
				temperature: 0.7,
				max_tokens: 1024,
			}),
		})

		if (!response.ok) {
			const errorText = await response.text()
			return NextResponse.json(
				{ error: `OpenAI API error: ${response.status}`, detail: errorText.slice(0, 200) },
				{ status: 500 }
			)
		}

		const data = await response.json()
		const content = data.choices?.[0]?.message?.content?.trim() || ""

		// Clean up potential markdown code blocks
		let cleanContent = content
		if (cleanContent.startsWith("```json")) {
			cleanContent = cleanContent.slice(7)
		} else if (cleanContent.startsWith("```")) {
			cleanContent = cleanContent.slice(3)
		}
		if (cleanContent.endsWith("```")) {
			cleanContent = cleanContent.slice(0, -3)
		}

		try {
			const result = JSON.parse(cleanContent.trim())
			return NextResponse.json({ success: true, data: result, type })
		} catch (_parseError) {
			return NextResponse.json(
				{ error: "Failed to parse AI response", raw: content.slice(0, 500) },
				{ status: 500 }
			)
		}
	} catch (error) {
		return NextResponse.json(
			{ error: error instanceof Error ? error.message : "Unknown error" },
			{ status: 500 }
		)
	}
}
