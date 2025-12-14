import { type NextRequest, NextResponse } from "next/server"

const DEFAULT_MODELS = ["gpt-4o", "grok"]
const getBackendUrl = () => process.env.BACKEND_URL

export async function POST(request: NextRequest) {
  try {
    const payload = await request.json()
    const prompt = (payload?.prompt ?? "").trim()
    if (!prompt) {
      return NextResponse.json({ success: false, error: "Prompt is required" }, { status: 400 })
    }

    const models = Array.isArray(payload?.models) && payload.models.length > 0
      ? payload.models
      : DEFAULT_MODELS

    // Call the backend API (works in both Docker and development if backend is running)
    const backendUrl = getBackendUrl() || "http://localhost:8000"
    
    const response = await fetch(`${backendUrl}/insights`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ prompt, models }),
    })

    if (!response.ok) {
      const error = await response.json().catch(() => ({}))
      return NextResponse.json(
        { success: false, error: error.detail || "Insights generation failed" },
        { status: response.status }
      )
    }

    return NextResponse.json(await response.json())
  } catch (error) {
    return NextResponse.json(
      { success: false, error: error instanceof Error ? error.message : "Unknown error" },
      { status: 500 }
    )
  }
}
