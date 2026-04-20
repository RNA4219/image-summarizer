"use client";

import { useState } from "react";
import { Container, Box } from "@mui/material";
import UploadForm from "@/components/UploadForm";
import SummaryResult from "@/components/SummaryResult";
import { ProcessingOptions, summarizeImage, summarizeMultipleImages } from "@/lib/api";
import {
  UploadState,
  SingleUploadState,
  MultiUploadState,
  LoadingState,
  ErrorState,
  StructuredSummary,
} from "@/types";

const createLoadingState: LoadingState = {
  status: "loading",
  mode: undefined,
  errorMessage: null,
};

const createErrorState = (message: string): ErrorState => ({
  status: "error",
  mode: undefined,
  errorMessage: message,
});

export default function Home() {
  const [state, setState] = useState<UploadState>({
    status: "idle",
    mode: undefined,
    errorMessage: null,
  });

  const handleSubmit = async (files: File[], options: ProcessingOptions) => {
    setState(createLoadingState);

    try {
      if (files.length === 1) {
        const result = await summarizeImage(files[0], options);
        const newState: SingleUploadState = {
          status: "success",
          mode: "single",
          errorMessage: null,
          filename: result.filename,
          ocrMode: result.ocrMode,
          summaryMode: result.summaryMode,
          summary: result.summary,
          structuredData: result.structuredData as StructuredSummary,
          extractedText: result.extractedText,
          warnings: result.warnings,
        };
        setState(newState);
      } else {
        const result = await summarizeMultipleImages(files, options);
        const newState: MultiUploadState = {
          status: "success",
          mode: "multi",
          errorMessage: null,
          results: result.results,
          totalFiles: result.totalFiles,
          successCount: result.successCount,
          errorCount: result.errorCount,
        };
        setState(newState);
      }
    } catch (error) {
      setState(createErrorState(error instanceof Error ? error.message : "Error occurred"));
    }
  };

  const isLoading = state.status === "loading";
  const errorMessage = state.errorMessage;

  return (
    <Container maxWidth="md" sx={{ py: 4 }}>
      <UploadForm
        onSubmit={handleSubmit}
        isLoading={isLoading}
        errorMessage={errorMessage}
      />

      {state.status === "success" && state.mode === "single" && (
        <Box sx={{ mt: 2 }}>
          <SummaryResult
            filename={state.filename}
            ocrMode={state.ocrMode}
            summaryMode={state.summaryMode}
            summary={state.summary}
            structuredData={state.structuredData}
            extractedText={state.extractedText}
            warnings={state.warnings}
          />
        </Box>
      )}

      {state.status === "success" && state.mode === "multi" && (
        <Box sx={{ mt: 2 }}>
          <SummaryResult
            results={state.results}
            totalFiles={state.totalFiles}
            successCount={state.successCount}
            errorCount={state.errorCount}
          />
        </Box>
      )}
    </Container>
  );
}
