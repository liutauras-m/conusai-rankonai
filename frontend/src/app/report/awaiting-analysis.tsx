"use client"

import { useEffect } from "react"
import { useRouter, useSearchParams } from "next/navigation"
import { LoadingOverlay } from "@/components/ui/spinner"

export function AwaitingAnalysis() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const queryUrl = searchParams.get("url")
  
  useEffect(() => {
    // Only redirect to homepage if there's no URL to analyze
    if (!queryUrl) {
      router.push("/")
    }
  }, [router, queryUrl])

  // If there's a URL, show loading state while analysis is in progress
  if (queryUrl) {
    return <LoadingOverlay message="Analyzing your website..." />
  }

  return null
}
