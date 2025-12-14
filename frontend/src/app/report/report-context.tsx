"use client"

import { createContext, type Dispatch, type SetStateAction, useCallback, useContext, useEffect, useMemo, useState } from "react"
import type { Route } from "next"
import { usePathname, useRouter, useSearchParams } from "next/navigation"

type AnalysisReport = {
  url?: string
  timestamp?: string
  crawl_time_ms?: number
  scores?: {
    overall?: number
    technical?: number
    on_page?: number
    content?: number
    structured_data?: number
    ai_readiness?: number
  }
  metadata?: {
    title?: { value?: string | null }
    description?: { value?: string | null }
    canonical?: string
    robots_meta?: string
    viewport?: string
    language?: string
    keywords_meta?: string
  }
  content?: {
    word_count?: number
    readability?: Record<string, number>
    keywords_frequency?: Array<{ keyword: string; count: number }>
    top_bigrams?: Array<{ phrase: string; count: number }>
  }
  issues?: Array<{ severity: string; category: string; code: string; message: string }>
  recommendations?: Array<{ priority: number; category: string; action: string }>
  ai_indexing?: {
    robots_txt?: { present?: boolean; ai_bots_status?: Record<string, string>; sitemaps_declared?: string[] }
    llms_txt?: { present?: boolean; content_preview?: string | null }
    sitemap_xml?: { present?: boolean }
  }
  llm_context?: {
    summary?: string
    overall_score?: number
    critical_issues_count?: number
    total_issues_count?: number
    key_metrics?: Record<string, boolean | number | string>
    top_keywords?: string[]
    prompt_for_improvement?: string
  }
  technical?: {
    https?: boolean
    response_time_ms?: number
    content_type?: string
    server?: string
  }
}

type InsightResponse = {
  success: boolean
  prompt?: string
  models?: string[]
  result?: {
    prompt?: string
    responses?: Record<
      string,
      {
        model_key?: string
        model_name?: string
        provider?: string
        success?: boolean
        response?: string
        error?: string
        latency_ms?: number
        tokens_used?: number
      }
    >
    total_time_ms?: number
    models_queried?: number
    models_successful?: number
  }
  meta?: Record<string, unknown>
  error?: string
  detail?: string
}

type InsightState =
  | { status: "idle" }
  | { status: "loading" }
  | { status: "success"; data: InsightResponse }
  | { status: "error"; error: string }

type PreferenceOption = {
  id: string
  label: string
  detail: string
}

type TargetKeyword = {
  keyword: string
  searchIntent: "informational" | "transactional" | "navigational" | "commercial"
  difficulty: "low" | "medium" | "high"
  tip: string
}

type SocialPost = {
  platform: "facebook" | "linkedin" | "twitter"
  content: string
  hashtags: string[]
  callToAction: string
  bestTimeToPost: string
}

type MarketingData = {
  targetKeywords: TargetKeyword[]
  socialPosts: SocialPost[]
  contentIdeas: string[]
}

type ReportContextValue = {
  analysis: AnalysisReport | null
  status: "idle" | "loading" | "success" | "error"
  error: string | null
  urlInput: string
  setUrlInput: (value: string) => void
  handleRun: () => void
  insights: InsightState
  insightsResponses: Array<{
    key: string
    name: string
    provider: string
    success?: boolean
    text?: string
    error?: string
    latency?: number
  }>
  preferences: string[]
  setPreferences: Dispatch<SetStateAction<string[]>>
  preferenceOptions: PreferenceOption[]
  preferenceOptionsLoading: boolean
  aiIndexing: {
    robots_txt: { present: boolean; ai_bots_status: Record<string, string>; sitemaps_declared: string[] }
    llms_txt: { present: boolean; content_preview: string | null }
    sitemap_xml: { present: boolean }
  }
  bestFeatures: Array<[string, number | undefined]>
  topFeatures: Array<[string, number | undefined]>
  questions: string[]
  questionsLoading: boolean
  marketingData: MarketingData | null
  marketingLoading: boolean
  keyMetrics: Array<[string, boolean | number | string]>
  formattedTimestamp: string
  metadataForFiles: {
    title: { value: string | null }
    description: { value: string | null }
  }
  contentForFiles: {
    keywords_frequency: Array<{ keyword: string; count: number }>
  }
  queryString: string
}

const ReportContext = createContext<ReportContextValue | null>(null)

export function ReportProvider({ children }: { children: React.ReactNode }) {
  const searchParams = useSearchParams()
  const router = useRouter()
  const pathname = usePathname()

  const queryUrl = searchParams.get("url") ?? ""
  const captchaToken = searchParams.get("token") ?? ""

  const [analysis, setAnalysis] = useState<AnalysisReport | null>(null)
  const [status, setStatus] = useState<"idle" | "loading" | "success" | "error">("idle")
  const [error, setError] = useState<string | null>(null)
  const [urlInput, setUrlInput] = useState(queryUrl)
  const [insights, setInsights] = useState<InsightState>({ status: "idle" })
  const [preferences, setPreferences] = useState<string[]>([])
  const [preferenceOptions, setPreferenceOptions] = useState<PreferenceOption[]>([])
  const [preferenceOptionsLoading, setPreferenceOptionsLoading] = useState(false)
  const [questions, setQuestions] = useState<string[]>([])
  const [questionsLoading, setQuestionsLoading] = useState(false)
  const [marketingData, setMarketingData] = useState<MarketingData | null>(null)
  const [marketingLoading, setMarketingLoading] = useState(false)
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setUrlInput(queryUrl)
  }, [queryUrl])

  useEffect(() => {
    setMounted(true)
  }, [])

  // Load stored preferences from localStorage
  useEffect(() => {
    if (!mounted) return
    const stored = window.localStorage.getItem("rank-on-ai-preferences")
    if (stored) {
      try {
        const parsed = JSON.parse(stored)
        if (Array.isArray(parsed)) {
          setPreferences(parsed)
        }
      } catch (storageError) {
        console.error(storageError)
      }
    }
  }, [mounted])

  // Save preferences to localStorage
  useEffect(() => {
    if (!mounted || preferences.length === 0) return
    window.localStorage.setItem("rank-on-ai-preferences", JSON.stringify(preferences))
  }, [preferences, mounted])

  // Fetch AI-generated preference options when analysis is ready
  useEffect(() => {
    if (!analysis) {
      setPreferenceOptions([])
      return
    }

    const controller = new AbortController()
    setPreferenceOptionsLoading(true)

    fetch("/api/generate-suggestions", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ analysis, type: "preferences" }),
      signal: controller.signal,
    })
      .then(async (res) => {
        if (!res.ok) throw new Error("Failed to generate preferences")
        return res.json()
      })
      .then((payload) => {
        if (payload.success && Array.isArray(payload.data)) {
          setPreferenceOptions(payload.data)
          // Auto-select first two preferences if none selected
          if (preferences.length === 0 && payload.data.length >= 2) {
            setPreferences([payload.data[0].id, payload.data[1].id])
          }
        }
      })
      .catch((err) => {
        if (!controller.signal.aborted) {
          console.error("Preference generation error:", err)
        }
      })
      .finally(() => {
        if (!controller.signal.aborted) {
          setPreferenceOptionsLoading(false)
        }
      })

    return () => controller.abort()
  }, [analysis, preferences.length])

  // Fetch AI-generated questions when analysis is ready
  useEffect(() => {
    if (!analysis) {
      setQuestions([])
      return
    }

    const controller = new AbortController()
    setQuestionsLoading(true)

    fetch("/api/generate-suggestions", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ analysis, type: "questions" }),
      signal: controller.signal,
    })
      .then(async (res) => {
        if (!res.ok) throw new Error("Failed to generate questions")
        return res.json()
      })
      .then((payload) => {
        if (payload.success && Array.isArray(payload.data)) {
          setQuestions(payload.data)
        }
      })
      .catch((err) => {
        if (!controller.signal.aborted) {
          console.error("Question generation error:", err)
        }
      })
      .finally(() => {
        if (!controller.signal.aborted) {
          setQuestionsLoading(false)
        }
      })

    return () => controller.abort()
  }, [analysis])

  // Fetch AI-generated marketing content when analysis is ready
  useEffect(() => {
    if (!analysis) {
      setMarketingData(null)
      return
    }

    const controller = new AbortController()
    setMarketingLoading(true)

    fetch("/api/generate-marketing", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ analysis }),
      signal: controller.signal,
    })
      .then(async (res) => {
        if (!res.ok) throw new Error("Failed to generate marketing content")
        return res.json()
      })
      .then((payload) => {
        if (payload.success && payload.data) {
          setMarketingData(payload.data)
        }
      })
      .catch((err) => {
        if (!controller.signal.aborted) {
          console.error("Marketing generation error:", err)
        }
      })
      .finally(() => {
        if (!controller.signal.aborted) {
          setMarketingLoading(false)
        }
      })

    return () => controller.abort()
  }, [analysis])

  useEffect(() => {
    if (!queryUrl) {
      setAnalysis(null)
      setStatus("idle")
      setError(null)
      return
    }

    const controller = new AbortController()
    setStatus("loading")
    setError(null)

    fetch("/api/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url: queryUrl, captchaToken }),
      signal: controller.signal,
    })
      .then(async (res) => {
        if (!res.ok) {
          const body = await res.json().catch(() => ({}))
          throw new Error(body?.error ?? "AI analysis failed")
        }
        return res.json()
      })
      .then((payload) => {
        // Handle both nested (from backend via nginx) and flat (from frontend API) responses
        const analysisData = payload.data ?? payload
        setAnalysis(analysisData)
        setStatus("success")
      })
      .catch((fetchError) => {
        if (controller.signal.aborted) return
        setStatus("error")
        setError(fetchError instanceof Error ? fetchError.message : "Analysis failed")
      })

    return () => controller.abort()
  }, [queryUrl, captchaToken])

  useEffect(() => {
    const prompt = analysis?.llm_context?.prompt_for_improvement
    if (!prompt) {
      setInsights({ status: "idle" })
      return
    }

    const controller = new AbortController()
    setInsights({ status: "loading" })

    fetch("/api/insights", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ prompt }),
      signal: controller.signal,
    })
      .then(async (res) => {
        if (!res.ok) {
          const body = await res.json().catch(() => ({}))
          throw new Error(body?.error ?? "AI insight generation failed")
        }
        return res.json()
      })
      .then((payload: InsightResponse) => {
        setInsights({ status: "success", data: payload })
      })
      .catch((insightError) => {
        if (controller.signal.aborted) return
        setInsights({ status: "error", error: insightError instanceof Error ? insightError.message : "Insight failed" })
      })

    return () => controller.abort()
  }, [analysis?.llm_context?.prompt_for_improvement])

  const handleRun = useCallback(() => {
    if (!urlInput) return
    const normalized = urlInput.startsWith("http") ? urlInput : `https://${urlInput}`
    const params = new URLSearchParams(searchParams.toString())
    params.set("url", normalized)
    if (captchaToken) params.set("token", captchaToken)
    const target = `${pathname}?${params.toString()}` as Route
    router.push(target)
  }, [urlInput, searchParams, pathname, router, captchaToken])

  const aiIndexing = useMemo(() => {
    const source = analysis?.ai_indexing
    return {
      robots_txt: {
        present: source?.robots_txt?.present ?? false,
        ai_bots_status: source?.robots_txt?.ai_bots_status ?? {},
        sitemaps_declared: source?.robots_txt?.sitemaps_declared ?? [],
      },
      llms_txt: {
        present: source?.llms_txt?.present ?? false,
        content_preview: source?.llms_txt?.content_preview ?? null,
      },
      sitemap_xml: {
        present: source?.sitemap_xml?.present ?? false,
      },
    }
  }, [analysis?.ai_indexing])

  const bestFeatures = useMemo(() => {
    const scoreEntries = analysis?.scores
      ? Object.entries(analysis.scores).filter(([key]) => key !== "overall")
      : []
    scoreEntries.sort(([, a], [, b]) => (b ?? 0) - (a ?? 0))
    const topCount = Math.max(1, Math.ceil(scoreEntries.length * 0.1))
    return scoreEntries.slice(0, topCount)
  }, [analysis?.scores])

  const topFeatures = useMemo(() => {
    if (!analysis?.scores) return []
    return Object.entries(analysis.scores)
      .filter(([key]) => key !== "overall")
      .sort(([, a], [, b]) => (b ?? 0) - (a ?? 0))
      .slice(0, 3)
  }, [analysis?.scores])

  const keyMetrics = useMemo(() => {
    if (!analysis?.llm_context?.key_metrics) return []
    return Object.entries(analysis.llm_context.key_metrics)
  }, [analysis?.llm_context?.key_metrics])

  const formattedTimestamp = useMemo(() => {
    if (!analysis?.timestamp) return "pending"
    return new Date(analysis.timestamp).toLocaleString()
  }, [analysis?.timestamp])

  const insightsResponses = useMemo(() => {
    if (insights.status !== "success" || !insights.data?.result?.responses) return []
    return Object.entries(insights.data.result.responses).map(([model, response]) => ({
      key: model,
      name: response.model_name ?? model,
      provider: response.provider ?? "AI",
      success: response.success,
      text: response.response,
      error: response.error,
      latency: response.latency_ms,
    }))
  }, [insights])

  const metadataForFiles = useMemo(() => {
    return {
      title: { value: analysis?.metadata?.title?.value ?? null },
      description: { value: analysis?.metadata?.description?.value ?? null },
    }
  }, [analysis?.metadata])

  const contentForFiles = useMemo(() => {
    return {
      keywords_frequency: analysis?.content?.keywords_frequency ?? [],
    }
  }, [analysis?.content?.keywords_frequency])

  const queryString = useMemo(() => {
    const params = new URLSearchParams()
    if (queryUrl) params.set("url", queryUrl)
    if (captchaToken) params.set("token", captchaToken)
    return params.toString()
  }, [queryUrl, captchaToken])

  const value: ReportContextValue = {
    analysis,
    status,
    error,
    urlInput,
    setUrlInput,
    handleRun,
    insights,
    insightsResponses,
    preferences,
    setPreferences,
    preferenceOptions,
    preferenceOptionsLoading,
    aiIndexing,
    bestFeatures,
    topFeatures,
    questions,
    questionsLoading,
    marketingData,
    marketingLoading,
    keyMetrics,
    formattedTimestamp,
    metadataForFiles,
    contentForFiles,
    queryString,
  }

  return <ReportContext.Provider value={value}>{children}</ReportContext.Provider>
}

export function useReportContext() {
  const context = useContext(ReportContext)
  if (!context) {
    throw new Error("useReportContext must be used within a ReportProvider")
  }
  return context
}
