"use client";

import { useState } from "react";
import {
  Box,
  Typography,
  Paper,
  IconButton,
  Collapse,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableRow,
  Chip,
} from "@mui/material";
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import ExpandLessIcon from "@mui/icons-material/ExpandLess";
import CheckCircleIcon from "@mui/icons-material/CheckCircle";
import ErrorIcon from "@mui/icons-material/Error";
import { StructuredSummary, DetailItem, SingleFileResult } from "@/types";

interface SummaryResultProps {
  filename: string;
  ocrMode: string;
  summaryMode: string;
  summary: string;
  structuredData: StructuredSummary;
  extractedText: string;
  warnings: string[];
  error?: string;
}

interface MultiSummaryResultProps {
  results: SingleFileResult[];
  totalFiles: number;
  successCount: number;
  errorCount: number;
}

function getConfidenceColor(
  confidence: string
): "success" | "warning" | "error" {
  switch (confidence) {
    case "high":
      return "success";
    case "medium":
      return "warning";
    case "low":
      return "error";
    default:
      return "success";
  }
}

function getConfidenceLabel(confidence: string): string {
  switch (confidence) {
    case "high":
      return "確実";
    case "medium":
      return "推定";
    case "low":
      return "不確実";
    default:
      return confidence;
  }
}

function SingleResult({
  filename,
  ocrMode,
  summaryMode,
  summary,
  structuredData,
  extractedText,
  warnings,
  error,
}: SummaryResultProps & { error?: string }) {
  const [showDetails, setShowDetails] = useState(false);
  const [showExtractedText, setShowExtractedText] = useState(false);

  if (error) {
    return (
      <Paper
        elevation={1}
        sx={{ p: 2, mb: 2, borderLeft: 4, borderColor: "error.main" }}
      >
        <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
          <ErrorIcon color="error" />
          <Typography variant="subtitle1">{filename}</Typography>
        </Box>
        <Typography variant="caption" color="text.secondary" sx={{ display: "block", mb: 0.5 }}>
          OCR: {ocrMode} / 要約: {summaryMode}
        </Typography>
        <Typography variant="body2" color="error">
          {error}
        </Typography>
      </Paper>
    );
  }

  return (
    <Paper
      elevation={1}
      sx={{ p: 2, mb: 2, borderLeft: 4, borderColor: "success.main" }}
    >
      {/* Document Type Header */}
      <Box sx={{ display: "flex", alignItems: "center", gap: 2, mb: 1 }}>
        <CheckCircleIcon color="success" />
        <Typography variant="subtitle1">{structuredData.documentType}</Typography>
        {structuredData.targetPeriod && (
          <Chip label={structuredData.targetPeriod} size="small" />
        )}
      </Box>

      <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
        ファイル: {filename}
      </Typography>
      <Typography variant="caption" color="text.secondary" sx={{ display: "block", mb: 1 }}>
        OCR: {ocrMode} / 要約: {summaryMode}
      </Typography>

      {/* Summary */}
      <Paper variant="outlined" sx={{ p: 1.5, bgcolor: "grey.50", mb: 1 }}>
        <Typography variant="body2">{summary}</Typography>
      </Paper>

      {/* Details Toggle */}
      {structuredData.details && structuredData.details.length > 0 && (
        <Box>
          <Box
            sx={{ display: "flex", alignItems: "center", cursor: "pointer" }}
            onClick={() => setShowDetails(!showDetails)}
          >
            <IconButton size="small">
              {showDetails ? <ExpandLessIcon /> : <ExpandMoreIcon />}
            </IconButton>
            <Typography variant="caption" color="text.secondary">
              詳細情報 ({structuredData.details.length}件)
            </Typography>
          </Box>

          <Collapse in={showDetails}>
            <TableContainer component={Paper} variant="outlined" sx={{ mt: 1 }}>
              <Table size="small">
                <TableBody>
                  {structuredData.details.map((item: DetailItem, index: number) => (
                    <TableRow key={index}>
                      <TableCell component="th" scope="row" sx={{ width: "40%" }}>
                        <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
                          {item.label}
                          <Chip
                            label={getConfidenceLabel(item.confidence)}
                            size="small"
                            color={getConfidenceColor(item.confidence)}
                          />
                        </Box>
                      </TableCell>
                      <TableCell>{item.value}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </Collapse>
        </Box>
      )}

      {/* Uncertain Items */}
      {structuredData.uncertainItems &&
        structuredData.uncertainItems.length > 0 && (
          <Paper
            variant="outlined"
            sx={{ p: 1.5, mt: 1, bgcolor: "warning.lighter" }}
          >
            <Typography variant="caption" color="warning.dark">
              不確実な項目: {structuredData.uncertainItems.join(", ")}
            </Typography>
          </Paper>
        )}

      {/* Extracted Text Toggle */}
      <Box sx={{ mt: 1 }}>
        <Box
          sx={{ display: "flex", alignItems: "center", cursor: "pointer" }}
          onClick={() => setShowExtractedText(!showExtractedText)}
        >
          <IconButton size="small">
            {showExtractedText ? <ExpandLessIcon /> : <ExpandMoreIcon />}
          </IconButton>
          <Typography variant="caption" color="text.secondary">
            抽出テキストを表示
          </Typography>
        </Box>

        <Collapse in={showExtractedText}>
          <Paper
            variant="outlined"
            sx={{
              p: 1.5,
              mt: 1,
              bgcolor: "grey.100",
              maxHeight: 200,
              overflow: "auto",
            }}
          >
            <Typography
              variant="body2"
              sx={{
                whiteSpace: "pre-wrap",
                fontFamily: "monospace",
                fontSize: "0.75rem",
              }}
            >
              {extractedText}
            </Typography>
          </Paper>
        </Collapse>
      </Box>
    </Paper>
  );
}

export default function SummaryResult(
  props: SummaryResultProps | MultiSummaryResultProps
) {
  // Single file mode
  if ("filename" in props) {
    return (
      <SingleResult
        filename={props.filename}
        ocrMode={props.ocrMode}
        summaryMode={props.summaryMode}
        summary={props.summary}
        structuredData={props.structuredData}
        extractedText={props.extractedText}
        warnings={props.warnings}
      />
    );
  }

  // Multiple file mode
  const { results, totalFiles, successCount, errorCount } = props;

  return (
    <Paper elevation={3} sx={{ p: 3 }}>
      {/* Summary Header */}
      <Box sx={{ display: "flex", alignItems: "center", gap: 2, mb: 2 }}>
        <Typography variant="h6">
          処理結果: {successCount}/{totalFiles}件 成功
        </Typography>
        {errorCount > 0 && (
          <Chip label={`${errorCount}件 失敗`} color="error" size="small" />
        )}
      </Box>

      {/* Results List */}
      {results.map((result, index) => (
        <SingleResult
          key={index}
          filename={result.filename}
          ocrMode={result.ocrMode}
          summaryMode={result.summaryMode}
          summary={result.summary}
          structuredData={result.structuredData}
          extractedText={result.extractedText}
          warnings={result.warnings}
          error={result.error}
        />
      ))}
    </Paper>
  );
}
