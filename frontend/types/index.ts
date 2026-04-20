export interface DetailItem {
  label: string;
  value: string;
  confidence: "high" | "medium" | "low";
}

export type OcrMode = "api" | "local_llm" | "high_accuracy";
export type SummaryMode = "api" | "local_llm";

export interface StructuredSummary {
  documentType: string;
  targetPeriod: string | null;
  recordCount: number | null;
  summary: string;
  details: DetailItem[];
  uncertainItems: string[];
}

export interface SingleFileResult {
  filename: string;
  ocrMode: OcrMode;
  summaryMode: SummaryMode;
  summary: string;
  structuredData: StructuredSummary;
  extractedText: string;
  warnings: string[];
  error?: string;
}

export interface SummarizeResponse {
  filename: string;
  ocrMode: OcrMode;
  summaryMode: SummaryMode;
  summary: string;
  structuredData: StructuredSummary;
  extractedText: string;
  warnings: string[];
}

export interface MultiSummarizeResponse {
  totalFiles: number;
  successCount: number;
  errorCount: number;
  results: SingleFileResult[];
}

export interface ErrorResponse {
  error: {
    code: string;
    message: string;
  };
}

export type UploadStatus = "idle" | "loading" | "success" | "error";

export type UploadMode = "single" | "multi" | undefined;

export interface BaseUploadState {
  status: UploadStatus;
  errorMessage: string | null;
}

export interface SingleUploadState extends BaseUploadState {
  mode: "single";
  filename: string;
  ocrMode: OcrMode;
  summaryMode: SummaryMode;
  summary: string;
  structuredData: StructuredSummary;
  extractedText: string;
  warnings: string[];
}

export interface MultiUploadState extends BaseUploadState {
  mode: "multi";
  results: SingleFileResult[];
  totalFiles: number;
  successCount: number;
  errorCount: number;
}

export interface LoadingState extends BaseUploadState {
  status: "loading";
  mode: undefined;
}

export interface IdleState extends BaseUploadState {
  status: "idle";
  mode: undefined;
}

export interface ErrorState extends BaseUploadState {
  status: "error";
  mode: undefined;
}

export type UploadState =
  | SingleUploadState
  | MultiUploadState
  | IdleState
  | LoadingState
  | ErrorState;
