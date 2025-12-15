"use client"

import Image from "next/image"
import { useState, useEffect, useCallback, useRef } from "react"
import { useRouter } from "next/navigation"
import { ThemeToggle } from "@/components/theme-toggle"
import { Turnstile } from "@/components/turnstile"
import {
  Target,
  FileText,
  Lightbulb,
  Rocket,
  CheckCircle2,
  Sparkles,
  Zap,
  Loader2,
  Brain,
  TrendingUp,
  Search,
  MessageSquare,
  Check,
  Clock,
  AlertCircle,
  ArrowRight,
  Info,
} from "lucide-react"
import { cn } from "@/lib/utils"

const TURNSTILE_SITE_KEY = process.env.NEXT_PUBLIC_TURNSTILE_SITE_KEY || ""
const POLLING_INTERVAL = 2000 // 2 seconds

// AI Platforms with their logos
const AI_PLATFORMS = [
  { name: "ChatGPT", logo: "/logos/platforms/chatgpt.png" },
  { name: "Claude", logo: "/logos/platforms/claude.png" },
  { name: "Gemini", logo: "/logos/platforms/gemini.png" },
  { name: "Perplexity", logo: "/logos/platforms/perplexity.ico" },
  { name: "Copilot", logo: "/logos/platforms/microsoft-copilot.svg" },
  { name: "Mistral", logo: "/logos/platforms/mistral.png" },
]

// Workflow step definitions with clear explanations
const WORKFLOW_STEPS = [
  {
    id: "overview",
    name: "SEO Analysis",
    icon: Search,
    description: "Technical SEO health check",
    definition: "Comprehensive analysis of your website's technical SEO elements including meta tags, headings, structured data, and crawlability.",
    metrics: [
      { name: "Technical Score", desc: "Server response, HTTPS, mobile-friendliness" },
      { name: "On-Page Score", desc: "Meta tags, headings, internal linking" },
      { name: "Content Score", desc: "Word count, readability, keyword usage" },
    ],
  },
  {
    id: "insights",
    name: "AI Insights",
    icon: Brain,
    description: "Multi-LLM analysis",
    definition: "We query multiple AI models (GPT-4, Grok) to understand how AI assistants interpret and recommend your brand.",
    metrics: [
      { name: "Brand Recognition", desc: "How well AI identifies your brand" },
      { name: "Context Accuracy", desc: "Quality of AI-generated descriptions" },
      { name: "Recommendation Fit", desc: "Relevance in AI suggestions" },
    ],
  },
  {
    id: "signals",
    name: "AI Signals",
    icon: TrendingUp,
    description: "Visibility indicators",
    definition: "Detection of signals that help AI crawlers discover and index your content, including robots.txt, llms.txt, and sitemap configurations.",
    metrics: [
      { name: "Crawl Access", desc: "AI bot permissions in robots.txt" },
      { name: "LLMs.txt", desc: "Dedicated AI instruction file" },
      { name: "Sitemap", desc: "XML sitemap for content discovery" },
    ],
  },
  {
    id: "keywords",
    name: "Keywords",
    icon: Target,
    description: "Strategic keywords",
    definition: "Extraction and analysis of keywords that AI models associate with your brand and industry.",
    metrics: [
      { name: "Primary Keywords", desc: "Main terms AI associates with you" },
      { name: "Long-tail Phrases", desc: "Specific queries triggering mentions" },
      { name: "Competitor Terms", desc: "Keywords where competitors rank" },
    ],
  },
  {
    id: "marketing",
    name: "Marketing",
    icon: MessageSquare,
    description: "Content strategy",
    definition: "AI-generated marketing recommendations to improve your visibility across AI platforms and search engines.",
    metrics: [
      { name: "Content Ideas", desc: "Topics to increase AI mentions" },
      { name: "Social Strategy", desc: "Platform-specific recommendations" },
      { name: "Optimization Tips", desc: "Quick wins for better rankings" },
    ],
  },
]

type WorkflowStatus = "idle" | "starting" | "pending" | "running" | "completed" | "failed"

interface WorkflowState {
  jobId: string | null
  status: WorkflowStatus
  progress: number
  currentStep: string | null
  completedSteps: string[]
  error: string | null
}

export default function Home() {
  const [url, setUrl] = useState("")
  const [brand, setBrand] = useState("")
  const [inputType, setInputType] = useState<"url" | "brand">("url")
  const [captchaToken, setCaptchaToken] = useState<string | null>(null)
  const [mounted, setMounted] = useState(false)
  const [showMetricInfo, setShowMetricInfo] = useState<string | null>(null)
  
  const [workflow, setWorkflow] = useState<WorkflowState>({
    jobId: null,
    status: "idle",
    progress: 0,
    currentStep: null,
    completedSteps: [],
    error: null,
  })
  
  const router = useRouter()
  const pollingRef = useRef<NodeJS.Timeout | null>(null)
  const abortControllerRef = useRef<AbortController | null>(null)

  useEffect(() => {
    setMounted(true)
    return () => {
      // Cleanup polling on unmount
      if (pollingRef.current) {
        clearInterval(pollingRef.current)
      }
      if (abortControllerRef.current) {
        abortControllerRef.current.abort()
      }
    }
  }, [])

  const isAnalyzing = workflow.status === "starting" || workflow.status === "pending" || workflow.status === "running"

  // Poll for workflow status
  const pollStatus = useCallback(async (jobId: string) => {
    try {
      abortControllerRef.current = new AbortController()
      
      const response = await fetch(`/api/workflow?jobId=${jobId}`, {
        signal: abortControllerRef.current.signal,
      })
      
      if (!response.ok) {
        throw new Error("Failed to get status")
      }
      
      const data = await response.json()
      
      setWorkflow(prev => ({
        ...prev,
        status: data.status as WorkflowStatus,
        progress: data.progress || prev.progress,
        currentStep: data.current_step || prev.currentStep,
        completedSteps: data.completed_steps || prev.completedSteps,
        error: data.error || null,
      }))
      
      // If completed, navigate to report
      if (data.status === "completed") {
        if (pollingRef.current) {
          clearInterval(pollingRef.current)
          pollingRef.current = null
        }
        
        // Small delay for UX before navigation
        setTimeout(() => {
          const params = new URLSearchParams({ jobId })
          if (inputType === "url") params.set("url", url.trim())
          else params.set("brand", brand.trim())
          router.push(`/report/overview?${params.toString()}`)
        }, 800)
      }
      
      // If failed, stop polling
      if (data.status === "failed") {
        if (pollingRef.current) {
          clearInterval(pollingRef.current)
          pollingRef.current = null
        }
      }
    } catch (error) {
      if (error instanceof Error && error.name === "AbortError") {
        return
      }
      console.error("Polling error:", error)
    }
  }, [router, url, brand, inputType])

  const startWorkflow = async () => {
    const trimmedUrl = url.trim()
    const trimmedBrand = brand.trim()

    // Validate input presence depending on type
    if (inputType === "url" && !trimmedUrl) return
    if (inputType === "brand" && !trimmedBrand) return

    if (TURNSTILE_SITE_KEY && !captchaToken) {
      setWorkflow(prev => ({ ...prev, error: "Please complete the verification" }))
      return
    }

    // Normalize URL when using URL mode
    let normalizedUrl = trimmedUrl
    if (inputType === "url") {
      if (!normalizedUrl.startsWith("http://") && !normalizedUrl.startsWith("https://")) {
        normalizedUrl = `https://${normalizedUrl}`
      }
    }

    setWorkflow({
      jobId: null,
      status: "starting",
      progress: 0,
      currentStep: null,
      completedSteps: [],
      error: null,
    })

    try {
      const body: Record<string, unknown> = { captchaToken }
      if (inputType === "url") body.url = normalizedUrl
      else body.brand = trimmedBrand

      const response = await fetch("/api/workflow", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      })

      if (!response.ok) {
        const error = await response.json().catch(() => ({}))
        throw new Error(error.error || "Failed to start analysis")
      }

      const data = await response.json()
      
      setWorkflow(prev => ({
        ...prev,
        jobId: data.job_id,
        status: data.status as WorkflowStatus,
        progress: data.cached ? 100 : 5,
      }))

      // If cached, navigate immediately
      if (data.cached && data.status === "completed") {
        const params = new URLSearchParams({ jobId: data.job_id })
        if (inputType === "url") params.set("url", normalizedUrl)
        else params.set("brand", trimmedBrand)
        router.push(`/report/overview?${params.toString()}`)
        return
      }

      // Start polling for status
      pollingRef.current = setInterval(() => {
        pollStatus(data.job_id)
      }, POLLING_INTERVAL)
      
      // Also poll immediately
      pollStatus(data.job_id)
    } catch (error) {
      setWorkflow(prev => ({
        ...prev,
        status: "failed",
        error: error instanceof Error ? error.message : "Analysis failed",
      }))
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && url && (captchaToken || !TURNSTILE_SITE_KEY) && !isAnalyzing) {
      startWorkflow()
    }
  }

  const cancelAnalysis = () => {
    if (pollingRef.current) {
      clearInterval(pollingRef.current)
      pollingRef.current = null
    }
    if (abortControllerRef.current) {
      abortControllerRef.current.abort()
    }
    if (workflow.jobId) {
      fetch(`/api/workflow?jobId=${workflow.jobId}`, { method: "DELETE" }).catch(() => {})
    }
    setWorkflow({
      jobId: null,
      status: "idle",
      progress: 0,
      currentStep: null,
      completedSteps: [],
      error: null,
    })
  }

  const getStepStatus = (stepId: string) => {
    if (workflow.completedSteps.includes(stepId)) return "completed"
    if (workflow.currentStep === stepId) return "running"
    return "pending"
  }

  return (
    <div className="relative min-h-screen overflow-hidden bg-gradient-to-b from-background via-background to-muted/20">
      {/* Animated background elements */}
      <div className="pointer-events-none absolute inset-0 overflow-hidden">
        <div className="-top-40 -left-40 absolute h-80 w-80 animate-blob rounded-full bg-primary/5 blur-3xl" />
        <div className="animation-delay-2000 -bottom-40 -right-40 absolute h-80 w-80 animate-blob rounded-full bg-primary/5 blur-3xl" />
        <div className="animation-delay-4000 -translate-x-1/2 -translate-y-1/2 absolute top-1/2 left-1/2 h-60 w-60 animate-blob rounded-full bg-primary/3 blur-3xl" />
      </div>

      {/* Header */}
      <header className="relative z-10 flex items-center justify-between px-6 py-4">
        <div className="flex items-center gap-2">
          <Image
            src="/favicon.png"
            alt="Rank on AI Search"
            width={32}
            height={32}
            className="transition-transform hover:scale-110"
          />
          <span className="hidden font-medium text-foreground sm:inline">
            Rank on AI Search
          </span>
        </div>
        <ThemeToggle />
      </header>

      {/* Main Content */}
      <main className="relative z-10 flex flex-col items-center px-4 pt-8 pb-20 sm:pt-16">
        {/* Hero Section - Hide during analysis */}
        {!isAnalyzing && workflow.status !== "completed" && (
          <div
            className={`flex max-w-3xl flex-col items-center text-center transition-all duration-700 ${
              mounted ? "translate-y-0 opacity-100" : "translate-y-8 opacity-0"
            }`}
          >
            {/* Badge */}
            <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-primary/20 bg-primary/5 px-4 py-1.5 text-primary text-sm">
              <span className="relative flex h-2 w-2">
                <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-primary opacity-75" />
                <span className="relative inline-flex h-2 w-2 rounded-full bg-primary" />
              </span>
              AI Search is the new SEO
            </div>

            {/* Headline */}
            <h1 className="font-bold font-display text-4xl text-foreground tracking-tight sm:text-5xl md:text-6xl">
              Does AI recommend{" "}
              <span className="bg-gradient-to-r from-primary to-primary/60 bg-clip-text text-transparent">
                your brand?
              </span>
            </h1>

            {/* Subheadline */}
            <p className="mt-6 max-w-xl text-lg text-muted-foreground sm:text-xl">
              Check if ChatGPT, Claude, Perplexity and other AI assistants can
              find and recommend your business.
            </p>
          </div>
        )}

        {/* Platform Logos - Hide during analysis */}
        {!isAnalyzing && workflow.status !== "completed" && (
          <div
            className={`mt-10 transition-all delay-200 duration-700 ${
              mounted ? "translate-y-0 opacity-100" : "translate-y-8 opacity-0"
            }`}
          >
            <p className="mb-4 text-center font-medium text-muted-foreground text-xs uppercase tracking-wider">
              Check your visibility across
            </p>
            <div className="flex flex-wrap items-center justify-center gap-3 sm:gap-4">
              {AI_PLATFORMS.map((platform, index) => (
                <div
                  key={platform.name}
                  className="group flex items-center gap-2 rounded-full border border-border/50 bg-card/50 px-3 py-2 backdrop-blur-sm transition-all hover:border-primary/30 hover:bg-card hover:shadow-md"
                  style={{ animationDelay: `${index * 100}ms` }}
                >
                  <Image
                    src={platform.logo}
                    alt={platform.name}
                    width={20}
                    height={20}
                    className="h-5 w-5 transition-transform group-hover:scale-110"
                  />
                  <span className="font-medium text-foreground text-sm">
                    {platform.name}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Analysis Progress View */}
        {isAnalyzing && (
          <div className="w-full max-w-2xl animate-in fade-in slide-in-from-bottom-4 duration-500">
            <div className="rounded-2xl border border-border/50 bg-card/90 p-8 shadow-2xl backdrop-blur-sm">
              {/* Header */}
              <div className="mb-8 text-center">
                <div className="mb-4 inline-flex items-center gap-2 rounded-full bg-primary/10 px-4 py-2">
                  <Loader2 className="h-4 w-4 animate-spin text-primary" />
                  <span className="font-medium text-primary text-sm">
                    Analyzing {inputType === "url" ? (url || "website") : (brand || "brand")}
                  </span>
                </div>
                <h2 className="font-bold text-2xl text-foreground">
                  AI Visibility Analysis
                </h2>
                <p className="mt-2 text-muted-foreground">
                  We're checking how AI assistants perceive your brand
                </p>
              </div>

              {/* Progress Bar */}
              <div className="mb-8">
                <div className="mb-2 flex items-center justify-between text-sm">
                  <span className="text-muted-foreground">Progress</span>
                  <span className="font-medium text-foreground">{workflow.progress}%</span>
                </div>
                <div className="h-2 overflow-hidden rounded-full bg-muted">
                  <div
                    className="h-full rounded-full bg-gradient-to-r from-primary to-primary/60 transition-all duration-500"
                    style={{ width: `${workflow.progress}%` }}
                  />
                </div>
              </div>

              {/* Steps */}
              <div className="space-y-3">
                {WORKFLOW_STEPS.map((step) => {
                  const stepStatus = getStepStatus(step.id)
                  const Icon = step.icon
                  
                  return (
                    <div
                      key={step.id}
                      className={cn(
                        "group relative rounded-xl border p-4 transition-all duration-300",
                        stepStatus === "completed" && "border-green-500/30 bg-green-500/5",
                        stepStatus === "running" && "border-primary/50 bg-primary/5 shadow-lg shadow-primary/10",
                        stepStatus === "pending" && "border-border/50 bg-muted/30 opacity-60"
                      )}
                    >
                      <div className="flex items-center gap-4">
                        {/* Status Icon */}
                        <div
                          className={cn(
                            "flex h-10 w-10 shrink-0 items-center justify-center rounded-full transition-all",
                            stepStatus === "completed" && "bg-green-500/20 text-green-500",
                            stepStatus === "running" && "bg-primary/20 text-primary",
                            stepStatus === "pending" && "bg-muted text-muted-foreground"
                          )}
                        >
                          {stepStatus === "completed" ? (
                            <Check className="h-5 w-5" />
                          ) : stepStatus === "running" ? (
                            <Loader2 className="h-5 w-5 animate-spin" />
                          ) : (
                            <Clock className="h-5 w-5" />
                          )}
                        </div>

                        {/* Step Info */}
                        <div className="min-w-0 flex-1">
                          <div className="flex items-center gap-2">
                            <Icon className="h-4 w-4 text-muted-foreground" />
                            <h3 className="font-semibold text-foreground">{step.name}</h3>
                          </div>
                          <p className="text-muted-foreground text-sm">{step.description}</p>
                        </div>

                        {/* Info Button */}
                        <button
                          type="button"
                          onClick={() => setShowMetricInfo(showMetricInfo === step.id ? null : step.id)}
                          className="shrink-0 rounded-full p-2 text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
                        >
                          <Info className="h-4 w-4" />
                        </button>
                      </div>

                      {/* Expanded Info */}
                      {showMetricInfo === step.id && (
                        <div className="mt-4 animate-in fade-in slide-in-from-top-2 rounded-lg bg-muted/50 p-4">
                          <p className="mb-3 text-foreground text-sm">{step.definition}</p>
                          <div className="space-y-2">
                            {step.metrics.map((metric) => (
                              <div key={metric.name} className="flex items-start gap-2 text-sm">
                                <div className="mt-1 h-1.5 w-1.5 shrink-0 rounded-full bg-primary" />
                                <div>
                                  <span className="font-medium text-foreground">{metric.name}:</span>{" "}
                                  <span className="text-muted-foreground">{metric.desc}</span>
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  )
                })}
              </div>

              {/* Cancel Button */}
              <button
                type="button"
                onClick={cancelAnalysis}
                className="mt-6 w-full rounded-xl border border-border bg-background py-3 font-medium text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
              >
                Cancel Analysis
              </button>
            </div>
          </div>
        )}

        {/* Error State */}
        {workflow.status === "failed" && workflow.error && (
          <div className="w-full max-w-xl animate-in fade-in slide-in-from-bottom-4">
            <div className="rounded-2xl border border-destructive/30 bg-destructive/5 p-6 text-center">
              <AlertCircle className="mx-auto mb-4 h-12 w-12 text-destructive" />
              <h3 className="mb-2 font-semibold text-foreground text-lg">Analysis Failed</h3>
              <p className="mb-4 text-muted-foreground">{workflow.error}</p>
              <button
                type="button"
                onClick={() => setWorkflow(prev => ({ ...prev, status: "idle", error: null }))}
                className="rounded-lg bg-primary px-6 py-2 font-medium text-primary-foreground transition-colors hover:bg-primary/90"
              >
                Try Again
              </button>
            </div>
          </div>
        )}

        {/* Search Box - Show when idle or failed */}
        {(workflow.status === "idle" || workflow.status === "failed") && (
          <div
            className={`mt-12 w-full max-w-xl transition-all delay-300 duration-700 ${
              mounted ? "translate-y-0 opacity-100" : "translate-y-8 opacity-0"
            }`}
          >
            <div className="rounded-2xl border border-border/50 bg-card/80 p-6 shadow-xl backdrop-blur-sm">
              {/* Input mode toggle */}
              <div className="mb-3 flex items-center gap-2 text-sm">
                <button
                  type="button"
                  onClick={() => setInputType("url")}
                  className={cn(
                    "rounded-full px-3 py-1.5 font-medium transition-colors",
                    inputType === "url" ? "bg-primary text-primary-foreground" : "bg-muted/20 text-muted-foreground"
                  )}
                >
                  URL
                </button>
                <button
                  type="button"
                  onClick={() => setInputType("brand")}
                  className={cn(
                    "rounded-full px-3 py-1.5 font-medium transition-colors",
                    inputType === "brand" ? "bg-primary text-primary-foreground" : "bg-muted/20 text-muted-foreground"
                  )}
                >
                  Brand
                </button>
                <span className="ml-3 text-xs text-muted-foreground">Analyze by website or brand name</span>
              </div>

              <div className="relative">
                <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-4">
                  {inputType === "url" ? (
                    <svg aria-hidden="true" className="h-5 w-5 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9" />
                    </svg>
                  ) : (
                    <Sparkles className="h-5 w-5 text-muted-foreground" />
                  )}
                </div>

                {inputType === "url" ? (
                  <input
                    type="text"
                    value={url}
                    onChange={(e) => setUrl(e.target.value)}
                    onKeyDown={handleKeyDown}
                    placeholder="yourwebsite.com"
                    className="h-14 w-full rounded-xl border-0 bg-muted/50 pr-4 pl-12 text-foreground text-lg placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/50"
                    disabled={isAnalyzing}
                  />
                ) : (
                  <input
                    type="text"
                    value={brand}
                    onChange={(e) => setBrand(e.target.value)}
                    onKeyDown={handleKeyDown}
                    placeholder="Your brand name (e.g. Acme Inc)"
                    className="h-14 w-full rounded-xl border-0 bg-muted/50 pr-4 pl-12 text-foreground text-lg placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/50"
                    disabled={isAnalyzing}
                  />
                )}
              </div>

              {/* CAPTCHA */}
              {TURNSTILE_SITE_KEY && (
                <div className="mt-4 flex justify-center">
                  <Turnstile
                    siteKey={TURNSTILE_SITE_KEY}
                    onVerify={(token) => setCaptchaToken(token)}
                    onExpire={() => setCaptchaToken(null)}
                    onError={() =>
                      setWorkflow(prev => ({ ...prev, error: "Verification failed. Please try again." }))
                    }
                    theme="auto"
                    size="normal"
                  />
                </div>
              )}

              {workflow.error && workflow.status === "idle" && (
                <p className="mt-3 text-center text-destructive text-sm">
                  {workflow.error}
                </p>
              )}

              {/* CTA Button */}
              <button
                type="button"
                onClick={startWorkflow}
                disabled={
                  (inputType === "url" ? !url.trim() : !brand.trim()) ||
                  isAnalyzing ||
                  (!!TURNSTILE_SITE_KEY && !captchaToken)
                }
                className="group relative mt-4 h-14 w-full overflow-hidden rounded-xl bg-gradient-to-r from-primary to-primary/80 font-semibold text-primary-foreground transition-transform hover:scale-[1.01] disabled:pointer-events-none disabled:opacity-50"
              >
                <span className="relative z-10 flex items-center justify-center gap-2">
                  {inputType === "url" ? "Check Website" : "Analyze Brand"}
                  <ArrowRight className="h-5 w-5 transition-transform group-hover:translate-x-1" />
                </span>
                <div className="-translate-x-full absolute inset-0 bg-white/5 transition-transform group-hover:translate-x-full" />
              </button>
            </div>
          </div>
        )}

        {/* Features - Hide during analysis */}
        {!isAnalyzing && workflow.status !== "completed" && (
          <div
            className={`mt-16 grid w-full max-w-4xl gap-6 px-4 transition-all delay-500 duration-700 sm:grid-cols-3 ${
              mounted ? "translate-y-0 opacity-100" : "translate-y-8 opacity-0"
            }`}
          >
            {/* AI Visibility Score */}
            <div className="group relative overflow-hidden rounded-2xl border border-border/50 bg-gradient-to-br from-card/80 to-card/40 p-6 backdrop-blur-sm transition-all duration-300 hover:border-primary/30 hover:shadow-primary/5 hover:shadow-xl">
              <div className="-right-4 -top-4 absolute h-24 w-24 rounded-full bg-primary/5 blur-2xl transition-all group-hover:bg-primary/10" />
              <div className="relative">
                <div className="mb-4 inline-flex rounded-xl bg-primary/10 p-3 text-primary transition-transform duration-300 group-hover:scale-110">
                  <Target className="h-6 w-6" strokeWidth={1.5} />
                </div>
                <h3 className="font-semibold text-foreground text-lg">AI Visibility Score</h3>
                <p className="mt-2 text-muted-foreground text-sm leading-relaxed">
                  See how discoverable you are to AI assistants
                </p>
              </div>
            </div>

            {/* Get AI-Ready Files */}
            <div className="group relative overflow-hidden rounded-2xl border border-border/50 bg-gradient-to-br from-card/80 to-card/40 p-6 backdrop-blur-sm transition-all duration-300 hover:border-primary/30 hover:shadow-primary/5 hover:shadow-xl">
              <div className="-right-4 -top-4 absolute h-24 w-24 rounded-full bg-blue-500/5 blur-2xl transition-all group-hover:bg-blue-500/10" />
              <div className="relative">
                <div className="mb-4 inline-flex rounded-xl bg-blue-500/10 p-3 text-blue-500 transition-transform duration-300 group-hover:scale-110">
                  <FileText className="h-6 w-6" strokeWidth={1.5} />
                </div>
                <h3 className="font-semibold text-foreground text-lg">Get AI-Ready Files</h3>
                <p className="mt-2 text-muted-foreground text-sm leading-relaxed">
                  Download optimized robots.txt & llms.txt
                </p>
              </div>
            </div>

            {/* Smart Recommendations */}
            <div className="group relative overflow-hidden rounded-2xl border border-border/50 bg-gradient-to-br from-card/80 to-card/40 p-6 backdrop-blur-sm transition-all duration-300 hover:border-primary/30 hover:shadow-primary/5 hover:shadow-xl">
              <div className="-right-4 -top-4 absolute h-24 w-24 rounded-full bg-amber-500/5 blur-2xl transition-all group-hover:bg-amber-500/10" />
              <div className="relative">
                <div className="mb-4 inline-flex rounded-xl bg-amber-500/10 p-3 text-amber-500 transition-transform duration-300 group-hover:scale-110">
                  <Lightbulb className="h-6 w-6" strokeWidth={1.5} />
                </div>
                <h3 className="font-semibold text-foreground text-lg">Smart Recommendations</h3>
                <p className="mt-2 text-muted-foreground text-sm leading-relaxed">
                  Actionable tips to improve your AI presence
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Social Proof - Hide during analysis */}
        {!isAnalyzing && workflow.status !== "completed" && (
          <div
            className={`mt-16 max-w-2xl text-center transition-all delay-700 duration-700 ${
              mounted ? "translate-y-0 opacity-100" : "translate-y-8 opacity-0"
            }`}
          >
            <div className="relative overflow-hidden rounded-2xl border border-primary/10 bg-gradient-to-br from-primary/5 via-transparent to-primary/5 p-8">
              {/* Decorative elements */}
              <div className="-left-10 -top-10 absolute h-32 w-32 rounded-full bg-primary/10 blur-3xl" />
              <div className="-bottom-10 -right-10 absolute h-32 w-32 rounded-full bg-primary/10 blur-3xl" />
              
              <div className="relative">
                <div className="mb-5 inline-flex rounded-2xl bg-gradient-to-br from-primary/20 to-primary/10 p-4">
                  <Rocket className="h-8 w-8 text-primary" strokeWidth={1.5} />
                </div>
                <h2 className="font-bold text-2xl text-foreground">
                  AI is the new search engine
                </h2>
                <p className="mx-auto mt-4 max-w-lg text-muted-foreground leading-relaxed">
                  More people are asking ChatGPT, Claude, and Perplexity for
                  recommendations instead of searching on Google. When someone asks
                  &quot;What&apos;s the best [your category]?&quot; — will your brand show up?
                </p>
                <div className="mt-8 flex flex-wrap items-center justify-center gap-6 text-sm">
                  <div className="flex items-center gap-2 rounded-full bg-green-500/10 px-4 py-2 text-green-600 dark:text-green-400">
                    <CheckCircle2 className="h-4 w-4" strokeWidth={2} />
                    <span className="font-medium">Free analysis</span>
                  </div>
                  <div className="flex items-center gap-2 rounded-full bg-blue-500/10 px-4 py-2 text-blue-600 dark:text-blue-400">
                    <Sparkles className="h-4 w-4" strokeWidth={2} />
                    <span className="font-medium">No signup required</span>
                  </div>
                  <div className="flex items-center gap-2 rounded-full bg-amber-500/10 px-4 py-2 text-amber-600 dark:text-amber-400">
                    <Zap className="h-4 w-4" strokeWidth={2} />
                    <span className="font-medium">Instant results</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="relative z-10 py-8 text-center">
        <p className="flex items-center justify-center gap-1.5 text-muted-foreground text-xs">
          Powered by{" "}
          <a
            href="https://www.conusai.com"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-block transition-opacity hover:opacity-80"
          >
            <Image
              src="/logos/conusai_logo_darkmode.png"
              alt="ConusAI"
              width={80}
              height={20}
              className="hidden dark:block"
            />
            <Image
              src="/logos/conusai_logo_lightmode.png"
              alt="ConusAI"
              width={80}
              height={20}
              className="block dark:hidden"
            />
          </a>
        </p>
        <a
          href="/docs/terms-and-conditions.md"
          target="_blank"
          rel="noopener noreferrer"
          className="mt-2 inline-block text-muted-foreground/70 text-xs transition-colors hover:text-muted-foreground"
        >
          Terms & Conditions
        </a>
      </footer>

      {/* Custom animations */}
      <style jsx>{`
        @keyframes blob {
          0% {
            transform: translate(0px, 0px) scale(1);
          }
          33% {
            transform: translate(30px, -50px) scale(1.1);
          }
          66% {
            transform: translate(-20px, 20px) scale(0.9);
          }
          100% {
            transform: translate(0px, 0px) scale(1);
          }
        }
        .animate-blob {
          animation: blob 7s infinite;
        }
        .animation-delay-2000 {
          animation-delay: 2s;
        }
        .animation-delay-4000 {
          animation-delay: 4s;
        }
      `}</style>
    </div>
  )
}
