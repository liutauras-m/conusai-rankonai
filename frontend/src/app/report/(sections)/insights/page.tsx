"use client"

import { useState } from "react"
import { CheckCircle2, XCircle, Brain, MessageCircleQuestion, Clock, FileText, ChevronDown, ChevronUp } from "lucide-react"
import { Spinner } from "@/components/ui/spinner"
import { Markdown } from "@/components/ui/markdown"
import { AwaitingAnalysis } from "../../awaiting-analysis"
import { useReportContext } from "../../report-context"

export default function InsightsPage() {
  const { analysis, insights, insightsResponses, questions, questionsLoading, aiIndexing } = useReportContext()
  const [expandedModels, setExpandedModels] = useState<Set<string>>(new Set())

  if (!analysis) return <AwaitingAnalysis />

  const toggleExpand = (key: string) => {
    setExpandedModels(prev => {
      const next = new Set(prev)
      if (next.has(key)) {
        next.delete(key)
      } else {
        next.add(key)
      }
      return next
    })
  }

  return (
    <div className="space-y-6">
      {/* AI Braintrust Section */}
      <section className="space-y-4">
        <div className="flex items-center gap-2">
          <Brain className="h-4 w-4 text-primary" />
          <h2 className="font-medium text-muted-foreground text-sm uppercase tracking-wider">AI Braintrust</h2>
        </div>
        
        <div className="rounded-xl border border-border/50 bg-card p-4 sm:p-6">
          <p className="mb-4 text-muted-foreground text-sm">
            Multiple AI models analyze your site and provide improvement suggestions.
          </p>
          
          {insights.status === "loading" && (
            <div className="flex items-center justify-center gap-3 py-8">
              <Spinner size="sm" />
              <span className="text-muted-foreground text-sm">Gathering insights...</span>
            </div>
          )}

          {insights.status === "error" && (
            <div className="rounded-lg border border-destructive/20 bg-destructive/10 p-4">
              <p className="text-destructive text-sm">
                {insights.error}
              </p>
              <p className="mt-1 text-muted-foreground text-xs">
                Check that API keys for GPT/Grok are configured correctly.
              </p>
            </div>
          )}

          {insights.status === "success" && insightsResponses.length > 0 && (
            <div className="space-y-4">
              {insightsResponses.map((response) => {
                const isExpanded = expandedModels.has(response.key)
                const hasLongContent = (response.text?.length ?? 0) > 300
                
                return (
                  <div 
                    key={response.key} 
                    className="group rounded-lg border border-border/50 bg-background p-4 transition-all duration-200 hover:border-primary/20"
                  >
                    <div className="mb-3 flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        {response.success ? (
                          <CheckCircle2 className="h-4 w-4 text-primary" aria-hidden="true" />
                        ) : (
                          <XCircle className="h-4 w-4 text-destructive" aria-hidden="true" />
                        )}
                        <span className="font-medium text-foreground text-sm">{response.name}</span>
                      </div>
                      <div className="flex items-center gap-1.5 text-muted-foreground text-xs">
                        <Clock className="h-3 w-3" aria-hidden="true" />
                        <span className="tabular-nums">{response.latency ? `${Math.round(response.latency)}ms` : "—"}</span>
                      </div>
                    </div>
                    
                    {response.text ? (
                      <div className="relative">
                        <div className={!isExpanded && hasLongContent ? "max-h-48 overflow-hidden" : ""}>
                          <Markdown content={isExpanded ? response.text : response.text.slice(0, 800)} />
                        </div>
                        
                        {!isExpanded && hasLongContent && (
                          <div className="absolute inset-x-0 bottom-0 h-16 bg-gradient-to-t from-background to-transparent" />
                        )}
                        
                        {hasLongContent && (
                          <button
                            type="button"
                            onClick={() => toggleExpand(response.key)}
                            className="mt-2 flex w-full items-center justify-center gap-1.5 rounded-lg border border-border/50 py-2 text-muted-foreground text-xs transition-colors hover:border-primary/30 hover:text-foreground"
                          >
                            {isExpanded ? (
                              <>
                                <ChevronUp className="h-3.5 w-3.5" />
                                Show less
                              </>
                            ) : (
                              <>
                                <ChevronDown className="h-3.5 w-3.5" />
                                Show full response
                              </>
                            )}
                          </button>
                        )}
                      </div>
                    ) : (
                      <p className="text-destructive/80 text-sm">
                        {response.error ?? "No response received"}
                      </p>
                    )}
                  </div>
                )
              })}
              
              <div className="flex items-center justify-between border-border/50 border-t pt-2">
                <p className="text-muted-foreground text-xs">
                  {insights.data?.models_successful}/{insights.data?.models_queried} models responded
                </p>
                <p className="text-muted-foreground text-xs tabular-nums">
                  Total: {insights.data?.total_time_ms ?? "-"}ms
                </p>
              </div>
            </div>
          )}

          {insights.status === "success" && insightsResponses.length === 0 && (
            <p className="py-4 text-center text-muted-foreground text-sm">
              No model responses available. Verify API configuration.
            </p>
          )}
        </div>
      </section>

      {/* Brand Questions Section */}
      <section className="space-y-4">
        <div className="flex items-center gap-2">
          <MessageCircleQuestion className="h-4 w-4 text-primary" />
          <h2 className="font-medium text-muted-foreground text-sm uppercase tracking-wider">Brand Questions</h2>
        </div>
        
        <div className="rounded-xl border border-border/50 bg-card p-4 sm:p-6">
          <p className="mb-4 text-muted-foreground text-sm">
            AI-generated questions to help craft FAQs and improve content discoverability.
          </p>

          {questionsLoading && (
            <div className="flex items-center justify-center gap-3 py-8">
              <Spinner size="sm" />
              <span className="text-muted-foreground text-sm">Generating questions...</span>
            </div>
          )}

          {!questionsLoading && questions.length === 0 && (
            <p className="py-4 text-center text-muted-foreground text-sm">
              No questions generated yet.
            </p>
          )}

          {!questionsLoading && questions.length > 0 && (
            <div className="space-y-2">
              {questions.map((text, index) => (
                <div 
                  key={text} 
                  className="flex gap-3 rounded-lg border border-border/50 bg-background p-3 transition-all duration-200 hover:border-primary/20"
                >
                  <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-primary/10 font-medium text-primary text-xs">
                    {index + 1}
                  </span>
                  <p className="text-foreground text-sm leading-relaxed">{text}</p>
                </div>
              ))}
            </div>
          )}
        </div>
      </section>

      {/* LLMs.txt Preview */}
      {aiIndexing.llms_txt.content_preview && (
        <section className="space-y-4">
          <div className="flex items-center gap-2">
            <FileText className="h-4 w-4 text-primary" />
            <h2 className="font-medium text-muted-foreground text-sm uppercase tracking-wider">LLMs.txt Preview</h2>
          </div>
          
          <div className="rounded-xl border border-border/50 bg-muted/30 p-4 sm:p-6">
            <pre className="whitespace-pre-wrap font-mono text-muted-foreground text-xs leading-relaxed">
              {aiIndexing.llms_txt.content_preview.slice(0, 300)}...
            </pre>
          </div>
        </section>
      )}
    </div>
  )
}
