import { NextRequest, NextResponse } from "next/server"

const BACKEND_URL = process.env.BACKEND_URL || "http://backend:8000"

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    
    if (!body.analysis) {
      return NextResponse.json(
        { error: "Analysis data is required" },
        { status: 400 }
      )
    }

    const response = await fetch(`${BACKEND_URL}/ai-summary`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ analysis: body.analysis }),
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      return NextResponse.json(
        { error: errorData.detail || "Failed to generate AI summary" },
        { status: response.status }
      )
    }

    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    console.error("AI summary error:", error)
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 }
    )
  }
}
