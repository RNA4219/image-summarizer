import { SummarizeResponse, MultiSummarizeResponse } from "@/types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export type OcrMode = "api" | "local_llm" | "high_accuracy";
export type SummaryMode = "api" | "local_llm";

export interface ProcessingOptions {
  ocrMode: OcrMode;
  summaryMode: SummaryMode;
}

export async function summarizeImage(
  file: File,
  options: ProcessingOptions = { ocrMode: "api", summaryMode: "api" }
): Promise<SummarizeResponse> {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("ocr_mode", options.ocrMode);
  formData.append("summary_mode", options.summaryMode);

  const response = await fetch(`${API_BASE_URL}/api/summarize`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.error?.message || "Error occurred");
  }

  return response.json();
}

export async function summarizeMultipleImages(
  files: File[],
  options: ProcessingOptions = { ocrMode: "api", summaryMode: "api" }
): Promise<MultiSummarizeResponse> {
  const formData = new FormData();
  files.forEach((file) => {
    formData.append("files", file);
  });
  formData.append("ocr_mode", options.ocrMode);
  formData.append("summary_mode", options.summaryMode);

  const response = await fetch(`${API_BASE_URL}/api/summarize-multiple`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.error?.message || "Error occurred");
  }

  return response.json();
}