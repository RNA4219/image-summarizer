"use client";

import { useState, useRef } from "react";
import {
  Box,
  Button,
  Typography,
  CircularProgress,
  Alert,
  Paper,
  Chip,
  FormControl,
  FormControlLabel,
  Radio,
  RadioGroup,
  FormLabel,
} from "@mui/material";
import CloudUploadIcon from "@mui/icons-material/CloudUpload";
import ImageIcon from "@mui/icons-material/Image";

import { OcrMode, SummaryMode, ProcessingOptions } from "@/lib/api";

interface UploadFormProps {
  onSubmit: (files: File[], options: ProcessingOptions) => Promise<void>;
  isLoading: boolean;
  errorMessage: string | null;
}

const ACCEPTED_TYPES = ["image/jpeg", "image/png"];

function isAcceptedType(type: string): boolean {
  return ACCEPTED_TYPES.includes(type);
}

export default function UploadForm({
  onSubmit,
  isLoading,
  errorMessage,
}: UploadFormProps) {
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [ocrMode, setOcrMode] = useState<OcrMode>("api");
  const [summaryMode, setSummaryMode] = useState<SummaryMode>("api");
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files;
    if (files) {
      setSelectedFiles(Array.from(files));
    }
  };

  const handleUploadClick = () => {
    fileInputRef.current?.click();
  };

  const handleSubmit = async () => {
    if (selectedFiles.length > 0) {
      await onSubmit(selectedFiles, { ocrMode, summaryMode });
    }
  };

  const handleClear = () => {
    setSelectedFiles([]);
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  const validFiles = selectedFiles.filter((f) => isAcceptedType(f.type));
  const hasInvalidFiles = selectedFiles.some((f) => !isAcceptedType(f.type));

  const isLocalModeSelected = ocrMode === "local_llm" || ocrMode === "high_accuracy" || summaryMode === "local_llm";

  return (
    <Paper elevation={3} sx={{ p: 3, mb: 3 }}>
      <Typography variant="h5" sx={{ mb: 2 }}>
        画像要約アプリ
      </Typography>

      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
        JPG / PNG ファイルをアップロードしてください（複数選択可）。
        <br />
        給与明細や帳票などの画像からテキストを抽出し、要約します。
      </Typography>

      {/* Mode Selection */}
      <Box sx={{ mb: 3 }}>
        <FormControl component="fieldset" sx={{ mb: 2 }}>
          <FormLabel component="legend">OCR方式</FormLabel>
          <RadioGroup
            value={ocrMode}
            onChange={(e) => setOcrMode(e.target.value as OcrMode)}
            row
          >
            <FormControlLabel
              value="api"
              control={<Radio />}
              label="標準 (API OCR)"
            />
            <FormControlLabel
              value="local_llm"
              control={<Radio />}
              label="ローカル (Ollama OCR)"
            />
            <FormControlLabel
              value="high_accuracy"
              control={<Radio />}
              label="高精度 (NDLOCR-Lite)"
            />
          </RadioGroup>
        </FormControl>

        <FormControl component="fieldset">
          <FormLabel component="legend">要約方式</FormLabel>
          <RadioGroup
            value={summaryMode}
            onChange={(e) => setSummaryMode(e.target.value as SummaryMode)}
            row
          >
            <FormControlLabel
              value="api"
              control={<Radio />}
              label="クラウド要約 (API)"
            />
            <FormControlLabel
              value="local_llm"
              control={<Radio />}
              label="ローカル要約 (Ollama)"
            />
          </RadioGroup>
        </FormControl>
      </Box>

      {/* Local mode warning */}
      {isLocalModeSelected && (
        <Alert severity="info" sx={{ mb: 2 }}>
          ローカルモードを選択しています。OllamaまたはNDLOCR-Liteの環境が必要です。
          <br />
          推奨モデル: Qwen3.6-35B-A3B
        </Alert>
      )}

      <Box sx={{ mb: 2 }}>
        <input
          type="file"
          ref={fileInputRef}
          onChange={handleFileChange}
          accept="image/jpeg,image/png"
          multiple
          style={{ display: "none" }}
        />
        <Button
          variant="outlined"
          onClick={handleUploadClick}
          startIcon={<CloudUploadIcon />}
          disabled={isLoading}
          sx={{ mr: 1 }}
        >
          ファイル選択
        </Button>

        {selectedFiles.length > 0 && (
          <Button variant="text" onClick={handleClear} disabled={isLoading}>
            クリア
          </Button>
        )}
      </Box>

      {selectedFiles.length > 0 && (
        <Box sx={{ mb: 2 }}>
          <Typography variant="body2" sx={{ mb: 1 }}>
            選択ファイル: {selectedFiles.length}件
          </Typography>
          <Box sx={{ display: "flex", flexWrap: "wrap", gap: 0.5 }}>
            {selectedFiles.map((file, index) => (
              <Chip
                key={index}
                icon={<ImageIcon fontSize="small" />}
                label={file.name}
                size="small"
                color={isAcceptedType(file.type) ? "primary" : "error"}
                onDelete={() => {
                  setSelectedFiles((prev) => prev.filter((_, i) => i !== index));
                }}
              />
            ))}
          </Box>
        </Box>
      )}

      {hasInvalidFiles && (
        <Alert severity="error" sx={{ mb: 2 }}>
          非対応のファイル形式が含まれています。JPG / PNG のみ選択してください。
        </Alert>
      )}

      {errorMessage && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {errorMessage}
        </Alert>
      )}

      <Button
        variant="contained"
        onClick={handleSubmit}
        disabled={validFiles.length === 0 || isLoading}
        sx={{ minWidth: 120 }}
      >
        {isLoading ? <CircularProgress size={24} /> : "要約実行"}
      </Button>
    </Paper>
  );
}