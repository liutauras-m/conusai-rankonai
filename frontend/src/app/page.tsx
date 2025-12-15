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
  AlertCircle,
  ArrowRight,
  Share2,
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

// Simplified workflow steps
const WORKFLOW_STEPS = [
  { id: "overview", name: "SEO Analysis", icon: Search },
  { id: "insights", name: "AI Insights", icon: Brain },
  { id: "signals", name: "AI Signals", icon: TrendingUp },
  { id: "keywords", name: "Keywords", icon: Target },
  { id: "marketing", name: "Marketing", icon: MessageSquare },
  { id: "social", name: "Social", icon: Share2 },
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
  const [captchaToken, setCaptchaToken] = useState<string | null>(null)
  const [mounted, setMounted] = useState(false)
  
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
          const params = new URLSearchParams({ jobId, url: url.trim() })
          router.push(`/report/overview?${params.toString()}`)
        }, 500)
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
  }, [router, url])

  const startWorkflow = async () => {
    const trimmedUrl = url.trim()
    if (!trimmedUrl) return

    if (TURNSTILE_SITE_KEY && !captchaToken) {
      setWorkflow(prev => ({ ...prev, error: "Please complete the verification" }))
      return
    }

    // Normalize URL
    let normalizedUrl = trimmedUrl
    if (!normalizedUrl.startsWith("http://") && !normalizedUrl.startsWith("https://")) {
      normalizedUrl = `https://${normalizedUrl}`
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
      const response = await fetch("/api/workflow", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url: normalizedUrl, captchaToken }),
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
        const params = new URLSearchParams({ jobId: data.job_id, url: normalizedUrl })
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
            alt="Rank on AI"
            width={32}
            height={32}
            className="transition-transform hover:scale-110"
          />
          <span className="hidden font-medium text-foreground sm:inline">
            Rank on AI
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

        {/* Minimalistic Analysis Progress */}
        {isAnalyzing && (
          <div className="w-full max-w-md animate-in fade-in slide-in-from-bottom-4 duration-500">
            <div className="rounded-2xl border border-border/50 bg-card/90 p-8 shadow-xl backdrop-blur-sm">
              <div className="mb-6 text-center">
                <Loader2 className="mx-auto mb-3 h-8 w-8 animate-spin text-primary" />
                <h2 className="font-semibold text-foreground text-lg">Analyzing {url || "website"}</h2>
                <p className="mt-1 text-muted-foreground text-sm">This may take a moment...</p>
              </div>

              {/* Progress Bar */}
              <div className="mb-6">
                <div className="mb-2 flex items-center justify-between text-xs">
                  <span className="text-muted-foreground">Progress</span>
                  <span className="font-medium text-foreground">{workflow.progress}%</span>
                </div>
                <div className="h-1.5 overflow-hidden rounded-full bg-muted">
                  <div
                    className="h-full rounded-full bg-primary transition-all duration-500"
                    style={{ width: `${workflow.progress}%` }}
                  />
                </div>
              </div>

              {/* Minimalistic Steps */}
              <div className="space-y-2">
                {WORKFLOW_STEPS.map((step) => {
                  const stepStatus = getStepStatus(step.id)
                  const Icon = step.icon
                  return (
                    <div key={step.id} className={cn(
                      "flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition-all",
                      stepStatus === "completed" && "text-green-600 dark:text-green-400",
                      stepStatus === "running" && "text-primary bg-primary/5",
                      stepStatus === "pending" && "text-muted-foreground opacity-50"
                    )}>
                      <div className="flex h-5 w-5 items-center justify-center">
                        {stepStatus === "completed" ? (
                          <Check className="h-4 w-4" />
                        ) : stepStatus === "running" ? (
                          <Loader2 className="h-4 w-4 animate-spin" />
                        ) : (
                          <Icon className="h-4 w-4" />
                        )}
                      </div>
                      <span className="font-medium">{step.name}</span>
                    </div>
                  )
                })}
              </div>

              <button
                type="button"
                onClick={cancelAnalysis}
                className="mt-6 w-full rounded-lg border border-border py-2 text-muted-foreground text-sm transition-colors hover:bg-muted hover:text-foreground"
              >
                Cancel
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
              <div className="relative">
                <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-4">
                  <svg aria-hidden="true" className="h-5 w-5 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9" />
                  </svg>
                </div>
                <input
                  type="text"
                  value={url}
                  onChange={(e) => setUrl(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder="yourwebsite.com"
                  className="h-14 w-full rounded-xl border-0 bg-muted/50 pr-4 pl-12 text-foreground text-lg placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/50"
                  disabled={isAnalyzing}
                />
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
                disabled={!url.trim() || isAnalyzing || (!!TURNSTILE_SITE_KEY && !captchaToken)}
                className="group relative mt-4 h-14 w-full overflow-hidden rounded-xl bg-gradient-to-r from-primary to-primary/80 font-semibold text-primary-foreground transition-transform hover:scale-[1.01] disabled:pointer-events-none disabled:opacity-50"
              >
                <span className="relative z-10 flex items-center justify-center gap-2">
                  Check AI Visibility
                  <ArrowRight className="h-5 w-5 transition-transform group-hover:translate-x-1" />
                </span>
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
            <div className="group relative overflow-hidden rounded-3xl border border-emerald-500/20 bg-gradient-to-br from-slate-900/80 via-slate-900/60 to-emerald-950/40 p-8 backdrop-blur-xl transition-all duration-500 hover:border-emerald-400/40 hover:shadow-emerald-500/10 hover:shadow-2xl dark:from-slate-900/90 dark:to-emerald-950/30">
              <div className="-right-8 -top-8 absolute h-32 w-32 rounded-full bg-emerald-500/10 blur-3xl transition-all duration-500 group-hover:bg-emerald-400/20" />
              <div className="absolute inset-0 bg-gradient-to-br from-emerald-500/5 via-transparent to-transparent opacity-0 transition-opacity duration-500 group-hover:opacity-100" />
              <div className="relative">
                <div className="mb-5 inline-flex rounded-2xl border border-emerald-500/20 bg-gradient-to-br from-emerald-500/20 to-emerald-600/10 p-4 text-emerald-400 shadow-lg shadow-emerald-500/10 transition-all duration-500 group-hover:scale-110 group-hover:shadow-emerald-500/20">
                  <Target className="h-7 w-7" strokeWidth={1.5} />
                </div>
                <h3 className="font-semibold text-foreground text-xl tracking-tight">AI Visibility Score</h3>
                <p className="mt-3 text-muted-foreground leading-relaxed">
                  See how discoverable you are to AI assistants
                </p>
              </div>
            </div>

            {/* Get AI-Ready Files */}
            <div className="group relative overflow-hidden rounded-3xl border border-emerald-500/20 bg-gradient-to-br from-slate-900/80 via-slate-900/60 to-emerald-950/40 p-8 backdrop-blur-xl transition-all duration-500 hover:border-emerald-400/40 hover:shadow-emerald-500/10 hover:shadow-2xl dark:from-slate-900/90 dark:to-emerald-950/30">
              <div className="-right-8 -top-8 absolute h-32 w-32 rounded-full bg-emerald-500/10 blur-3xl transition-all duration-500 group-hover:bg-emerald-400/20" />
              <div className="absolute inset-0 bg-gradient-to-br from-emerald-500/5 via-transparent to-transparent opacity-0 transition-opacity duration-500 group-hover:opacity-100" />
              <div className="relative">
                <div className="mb-5 inline-flex rounded-2xl border border-emerald-500/20 bg-gradient-to-br from-emerald-500/20 to-emerald-600/10 p-4 text-emerald-400 shadow-lg shadow-emerald-500/10 transition-all duration-500 group-hover:scale-110 group-hover:shadow-emerald-500/20">
                  <FileText className="h-7 w-7" strokeWidth={1.5} />
                </div>
                <h3 className="font-semibold text-foreground text-xl tracking-tight">Get AI-Ready Files</h3>
                <p className="mt-3 text-muted-foreground leading-relaxed">
                  Download optimized robots.txt & llms.txt
                </p>
              </div>
            </div>

            {/* Smart Recommendations */}
            <div className="group relative overflow-hidden rounded-3xl border border-emerald-500/20 bg-gradient-to-br from-slate-900/80 via-slate-900/60 to-emerald-950/40 p-8 backdrop-blur-xl transition-all duration-500 hover:border-emerald-400/40 hover:shadow-emerald-500/10 hover:shadow-2xl dark:from-slate-900/90 dark:to-emerald-950/30">
              <div className="-right-8 -top-8 absolute h-32 w-32 rounded-full bg-emerald-500/10 blur-3xl transition-all duration-500 group-hover:bg-emerald-400/20" />
              <div className="absolute inset-0 bg-gradient-to-br from-emerald-500/5 via-transparent to-transparent opacity-0 transition-opacity duration-500 group-hover:opacity-100" />
              <div className="relative">
                <div className="mb-5 inline-flex rounded-2xl border border-emerald-500/20 bg-gradient-to-br from-emerald-500/20 to-emerald-600/10 p-4 text-emerald-400 shadow-lg shadow-emerald-500/10 transition-all duration-500 group-hover:scale-110 group-hover:shadow-emerald-500/20">
                  <Lightbulb className="h-7 w-7" strokeWidth={1.5} />
                </div>
                <h3 className="font-semibold text-foreground text-xl tracking-tight">Smart Recommendations</h3>
                <p className="mt-3 text-muted-foreground leading-relaxed">
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
            <div className="relative overflow-hidden rounded-3xl border border-emerald-500/20 bg-gradient-to-br from-slate-900/80 via-slate-900/60 to-emerald-950/40 p-10 backdrop-blur-xl dark:from-slate-900/90 dark:to-emerald-950/30">
              {/* Decorative elements */}
              <div className="-left-16 -top-16 absolute h-48 w-48 rounded-full bg-emerald-500/10 blur-3xl" />
              <div className="-bottom-16 -right-16 absolute h-48 w-48 rounded-full bg-emerald-500/10 blur-3xl" />
              <div className="absolute inset-0 bg-gradient-to-r from-emerald-500/5 via-transparent to-emerald-500/5" />
              
              <div className="relative">
                <div className="mb-6 inline-flex rounded-2xl border border-emerald-500/20 bg-gradient-to-br from-emerald-500/20 to-emerald-600/10 p-5 shadow-lg shadow-emerald-500/10">
                  <Rocket className="h-10 w-10 text-emerald-400" strokeWidth={1.5} />
                </div>
                <h2 className="font-bold text-3xl text-foreground tracking-tight">
                  AI is the new search engine
                </h2>
                <p className="mx-auto mt-5 max-w-lg text-muted-foreground text-lg leading-relaxed">
                  More people are asking ChatGPT, Claude, and Perplexity for
                  recommendations instead of searching on Google. When someone asks
                  &quot;What&apos;s the best [your category]?&quot; - will your brand show up?
                </p>
                <div className="mt-10 flex flex-wrap items-center justify-center gap-4 text-sm">
                  <div className="flex items-center gap-2.5 rounded-full border border-emerald-500/20 bg-emerald-500/10 px-5 py-2.5 text-emerald-400 shadow-sm">
                    <CheckCircle2 className="h-4 w-4" strokeWidth={2} />
                    <span className="font-medium">Free analysis</span>
                  </div>
                  <div className="flex items-center gap-2.5 rounded-full border border-emerald-500/20 bg-emerald-500/10 px-5 py-2.5 text-emerald-400 shadow-sm">
                    <Sparkles className="h-4 w-4" strokeWidth={2} />
                    <span className="font-medium">No signup required</span>
                  </div>
                  <div className="flex items-center gap-2.5 rounded-full border border-emerald-500/20 bg-emerald-500/10 px-5 py-2.5 text-emerald-400 shadow-sm">
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
