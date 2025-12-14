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
    word_count?: number
    keywords_frequency?: Array<{ keyword: string; count: number }>
    top_bigrams?: Array<{ phrase: string; count: number }>
    top_trigrams?: Array<{ phrase: string; count: number }>
  }
  llm_context?: {
    top_keywords?: string[]
    summary?: string
  }
  scores?: Record<string, number>
  issues?: Array<{ severity: string; category: string; code: string; message: string }>
}

interface TargetKeyword {
  keyword: string
  searchIntent: "informational" | "transactional" | "navigational" | "commercial"
  difficulty: "low" | "medium" | "high"
  tip: string
}

interface SocialPost {
  platform: "facebook" | "linkedin" | "twitter"
  content: string
  hashtags: string[]
  callToAction: string
  bestTimeToPost: string
}

interface MarketingData {
  targetKeywords: TargetKeyword[]
  socialPosts: SocialPost[]
  contentIdeas: string[]
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    const analysis: AnalysisReport = body.analysis

    if (!analysis) {
      return NextResponse.json(
        { error: "analysis payload is required" },
        { status: 400 }
      )
    }

    // In production (Docker), call the backend API
    const backendUrl = getBackendUrl()
    if (backendUrl) {
      const response = await fetch(`${backendUrl}/generate-marketing`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ analysis }),
      })

      if (!response.ok) {
        const error = await response.json().catch(() => ({}))
        return NextResponse.json(
          { error: error.detail || "Marketing generation failed" },
          { status: response.status }
        )
      }

      return NextResponse.json(await response.json())
    }

    // In development, call OpenAI directly
    if (!OPENAI_API_KEY) {
      return NextResponse.json(
        { error: "OPENAI_API_KEY not configured" },
        { status: 500 }
      )
    }

    // Extract rich context from SEO analysis
    const brand = analysis.metadata?.title?.value || 
      (analysis.url ? new URL(analysis.url).hostname : "the brand")
    const description = analysis.metadata?.description?.value || ""
    const url = analysis.url || ""
    
    // Get keywords from multiple sources
    const frequencyKeywords = analysis.content?.keywords_frequency?.slice(0, 15).map(k => k.keyword) || []
    const topKeywords = analysis.llm_context?.top_keywords?.slice(0, 10) || []
    const bigrams = analysis.content?.top_bigrams?.slice(0, 5).map(b => b.phrase) || []
    const trigrams = analysis.content?.top_trigrams?.slice(0, 3).map(t => t.phrase) || []
    
    const _allKeywords = [...new Set([...frequencyKeywords, ...topKeywords, ...bigrams, ...trigrams])]
    const scores = analysis.scores || {}

    const systemPrompt = `You are an expert content marketing strategist specializing in SEO and social media marketing. 
Generate actionable marketing recommendations based on SEO analysis data.
Return valid JSON only, no markdown formatting or code blocks.`

    const userPrompt = `Based on this comprehensive SEO analysis, generate content marketing recommendations:

WEBSITE ANALYSIS:
- URL: ${url}
- Brand/Title: ${brand}
- Description: ${description}
- Word Count: ${analysis.content?.word_count || "N/A"}
- Current SEO Scores: ${JSON.stringify(scores)}

EXTRACTED KEYWORDS (from page analysis):
- Frequency keywords: ${frequencyKeywords.join(", ")}
- Top semantic keywords: ${topKeywords.join(", ")}
- Key phrases (bigrams): ${bigrams.join(", ")}
- Key phrases (trigrams): ${trigrams.join(", ")}

TASK: Generate a JSON object with these three sections:

1. "targetKeywords": Array of 8 strategic keywords/phrases to target. For each:
   - "keyword": The keyword or phrase to target
   - "searchIntent": One of "informational", "transactional", "navigational", "commercial"
   - "difficulty": Estimated ranking difficulty "low", "medium", or "high"
   - "tip": A brief actionable tip on how to use this keyword

2. "socialPosts": Array of 3 ready-to-use social media posts (one for each platform):
   - "platform": "facebook", "linkedin", or "twitter"
   - "content": The full post text (appropriate length for each platform: Twitter ~280 chars, LinkedIn ~300-600 chars, Facebook ~100-250 chars)
   - "hashtags": Array of 3-5 relevant hashtags
   - "callToAction": A clear CTA for the post
   - "bestTimeToPost": Suggested best time to post (e.g., "Tuesday 10-11 AM")

3. "contentIdeas": Array of 5 blog post or content ideas that would help this brand rank better for their target keywords

IMPORTANT GUIDELINES:
- Make keywords specific to the brand's industry and offerings
- Social posts should be engaging, professional, and platform-appropriate
- Include a mix of promotional and value-adding content
- Focus on keywords that align with the brand's apparent goals
- Use the extracted keywords as inspiration but suggest variations and long-tail versions

Return ONLY the JSON object with these three keys: targetKeywords, socialPosts, contentIdeas.`

    const openaiResponse = await fetch("https://api.openai.com/v1/chat/completions", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${OPENAI_API_KEY}`,
      },
      body: JSON.stringify({
        model: "gpt-4o",
        messages: [
          { role: "system", content: systemPrompt },
          { role: "user", content: userPrompt },
        ],
        temperature: 0.7,
        max_tokens: 2500,
      }),
    })

    if (!openaiResponse.ok) {
      const errorData = await openaiResponse.json().catch(() => ({}))
      console.error("OpenAI error:", errorData)
      return NextResponse.json(
        { error: "AI generation failed", details: errorData },
        { status: 500 }
      )
    }

    const openaiData = await openaiResponse.json()
    const rawContent = openaiData.choices?.[0]?.message?.content || ""

    // Clean and parse JSON
    let cleanedContent = rawContent.trim()
    if (cleanedContent.startsWith("```json")) {
      cleanedContent = cleanedContent.slice(7)
    } else if (cleanedContent.startsWith("```")) {
      cleanedContent = cleanedContent.slice(3)
    }
    if (cleanedContent.endsWith("```")) {
      cleanedContent = cleanedContent.slice(0, -3)
    }
    cleanedContent = cleanedContent.trim()

    let marketingData: MarketingData
    try {
      marketingData = JSON.parse(cleanedContent)
    } catch (parseError) {
      console.error("JSON parse error:", parseError, "Content:", cleanedContent)
      return NextResponse.json(
        { error: "Failed to parse AI response as JSON" },
        { status: 500 }
      )
    }

    // Validate structure
    if (!marketingData.targetKeywords || !marketingData.socialPosts || !marketingData.contentIdeas) {
      return NextResponse.json(
        { error: "Invalid marketing data structure from AI" },
        { status: 500 }
      )
    }

    return NextResponse.json({
      success: true,
      data: marketingData,
    })
  } catch (error) {
    console.error("Marketing generation error:", error)
    return NextResponse.json(
      { error: error instanceof Error ? error.message : "Unknown error" },
      { status: 500 }
    )
  }
}
