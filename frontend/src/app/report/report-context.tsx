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
  social?: SocialData
}

type InsightResponse = {
  success?: boolean
  prompt?: string
  models?: string[]
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

type SocialTagIssue = {
  code?: string
  severity?: "low" | "medium" | "high"
  message: string
}

type SocialMetadataSection = {
  present: boolean
  tags: Record<string, string>
  missing_required: string[]
  missing_recommended: string[]
  issues: SocialTagIssue[]
  card_type?: string
}

type SocialMetadata = {
  open_graph: SocialMetadataSection
  twitter_card: SocialMetadataSection
}

type SocialImage = {
  url: string
  source: string
  width?: number
  height?: number
  alt?: string
  type?: string
}

type SocialPlatformStatus = {
  score: number
  status: "optimal" | "good" | "needs_improvement" | "poor"
  issues: string[]
}

type SocialImprovement = {
  priority: "high" | "medium" | "low"
  category: "open_graph" | "twitter_card" | "image" | "general"
  issue: string
  action: string
  impact: string
}

type SocialRecommendations = {
  summary?: string
  improvements: SocialImprovement[]
  best_practices: string[]
  sample_tags: {
    open_graph?: string[]
    twitter_card?: string[]
  }
}

type SocialPreview = {
  title: string
  description: string
  image?: string
  image_alt?: string
  site_name?: string
  url?: string
}

type SocialData = {
  metadata: SocialMetadata
  images: SocialImage[]
  platforms: Record<string, SocialPlatformStatus>
  score: number
  issues: SocialTagIssue[]
  recommendations: SocialRecommendations
  preview: SocialPreview
}

type SignalsData = {
  robots_txt?: {
    present?: boolean
    ai_bots_status?: Record<string, string>
    sitemaps_declared?: string[]
  }
  llms_txt?: {
    present?: boolean
    content_preview?: string | null
  }
  sitemap_xml?: {
    present?: boolean
  }
}

type KeywordsData = {
  primary?: string[]
  secondary?: string[]
  long_tail?: string[]
  frequency?: Array<{ keyword: string; count: number }>
}

type WorkflowResultData = {
  job_id?: string
  url?: string
  status?: string
  cached?: boolean
  timestamp?: string
  scores?: {
    overall?: number
    technical?: number
    on_page?: number
    content?: number
    structured_data?: number
    ai_readiness?: number
  }
  overview?: AnalysisReport
  insights?: InsightResponse
  signals?: SignalsData
  keywords?: KeywordsData
  marketing?: MarketingData
  social?: SocialData
  ai_summary?: {
    markdown?: string
    structured?: Record<string, unknown>
  }
  error?: string
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
  workflowData: WorkflowResultData | null
  keywordsData: KeywordsData | null
  signalsData: SignalsData | null
  socialData: SocialData | null
}

const ReportContext = createContext<ReportContextValue | null>(null)

export function ReportProvider({ children }: { children: React.ReactNode }) {
  const searchParams = useSearchParams()
  const router = useRouter()
  const pathname = usePathname()

  const queryUrl = searchParams.get("url") ?? ""
  const jobId = searchParams.get("jobId") ?? ""

  const [workflowData, setWorkflowData] = useState<WorkflowResultData | null>(null)
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
  const [keywordsData, setKeywordsData] = useState<KeywordsData | null>(null)
  const [signalsData, setSignalsData] = useState<SignalsData | null>(null)
  const [socialData, setSocialData] = useState<SocialData | null>(null)
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

  // Fetch workflow result when jobId is available
  useEffect(() => {
    if (!jobId) {
      // Reset state if no jobId
      setWorkflowData(null)
      setAnalysis(null)
      setStatus("idle")
      setError(null)
      setInsights({ status: "idle" })
      setMarketingData(null)
      setKeywordsData(null)
      setSignalsData(null)
      setSocialData(null)
      return
    }

    const controller = new AbortController()
    setStatus("loading")
    setError(null)

    fetch(`/api/workflow?jobId=${jobId}&result=true`, {
      signal: controller.signal,
    })
      .then(async (res) => {
        if (!res.ok) {
          const body = await res.json().catch(() => ({}))
          throw new Error(body?.error ?? "Failed to load analysis results")
        }
        return res.json()
      })
      .then((data: WorkflowResultData) => {
        setWorkflowData(data)
        
        // Set overview/analysis data
        const overviewData = data.overview || {}
        setAnalysis({
          ...overviewData,
          url: data.url || overviewData.url,
          timestamp: data.timestamp || overviewData.timestamp,
          scores: data.scores || overviewData.scores,
        })
        
        // Set insights from workflow
        if (data.insights) {
          setInsights({ 
            status: "success", 
            data: data.insights 
          })
        }
        
        // Set signals from workflow
        if (data.signals) {
          setSignalsData(data.signals)
        }
        
        // Set keywords from workflow
        if (data.keywords) {
          setKeywordsData(data.keywords)
        }
        
        // Set marketing from workflow
        if (data.marketing) {
          setMarketingData(data.marketing)
        }

        if (data.social) {
          setSocialData(data.social)
        } else {
          setSocialData(null)
        }
        
        setStatus("success")
      })
      .catch((fetchError) => {
        if (controller.signal.aborted) return
        setStatus("error")
        setError(fetchError instanceof Error ? fetchError.message : "Analysis failed")
      })

    return () => controller.abort()
  }, [jobId])

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

  const handleRun = useCallback(() => {
    if (!urlInput) return
    const normalized = urlInput.startsWith("http") ? urlInput : `https://${urlInput}`
    // Navigate back to home page to start new analysis
    router.push(`/?url=${encodeURIComponent(normalized)}`)
  }, [urlInput, router])

  const aiIndexing = useMemo(() => {
    // First try to get from signals data (from workflow)
    if (signalsData) {
      return {
        robots_txt: {
          present: signalsData.robots_txt?.present ?? false,
          ai_bots_status: signalsData.robots_txt?.ai_bots_status ?? {},
          sitemaps_declared: signalsData.robots_txt?.sitemaps_declared ?? [],
        },
        llms_txt: {
          present: signalsData.llms_txt?.present ?? false,
          content_preview: signalsData.llms_txt?.content_preview ?? null,
        },
        sitemap_xml: {
          present: signalsData.sitemap_xml?.present ?? false,
        },
      }
    }
    
    // Fall back to analysis data
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
  }, [analysis?.ai_indexing, signalsData])

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
    const ts = workflowData?.timestamp || analysis?.timestamp
    if (!ts) return "pending"
    return new Date(ts).toLocaleString()
  }, [workflowData?.timestamp, analysis?.timestamp])

  const insightsResponses = useMemo(() => {
    if (insights.status !== "success" || !insights.data?.responses) return []
    return Object.entries(insights.data.responses).map(([model, response]) => ({
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
    if (jobId) params.set("jobId", jobId)
    return params.toString()
  }, [queryUrl, jobId])

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
    workflowData,
    keywordsData,
    signalsData,
    socialData,
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
