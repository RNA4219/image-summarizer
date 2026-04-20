from pydantic import BaseModel, Field
from typing import Optional, List


class DetailItem(BaseModel):
    """詳細項目"""
    label: str = Field(..., description="項目名")
    value: str = Field(..., description="値")
    confidence: str = Field("high", description="確信度: high/medium/low")


class StructuredSummary(BaseModel):
    """構造化された要約データ"""
    documentType: str = Field("不明", description="文書種別")
    targetPeriod: Optional[str] = Field(None, description="対象期間")
    recordCount: Optional[int] = Field(None, description="対象件数")
    summary: str = Field("", description="短い自然文要約")
    details: List[DetailItem] = Field(default_factory=list, description="詳細項目リスト")
    uncertainItems: List[str] = Field(default_factory=list, description="不確実な項目リスト")


class SingleFileResult(BaseModel):
    """単一ファイルの結果"""
    filename: str = Field(..., description="ファイル名")
    ocrMode: str = Field("api", description="使用したOCRモード")
    summaryMode: str = Field("api", description="使用した要約モード")
    summary: str = Field(..., description="短い自然文要約")
    structuredData: StructuredSummary = Field(..., description="構造化された要約データ")
    extractedText: str = Field(..., description="抽出・整形後のテキスト")
    warnings: List[str] = Field(default_factory=list, description="警告メッセージ")
    error: Optional[str] = Field(None, description="エラーメッセージ（失敗時のみ）")


class SummarizeResponse(BaseModel):
    """単一ファイル用レスポンス（後方互換性維持）"""
    filename: str = Field(..., description="アップロードされたファイル名")
    ocrMode: str = Field("api", description="使用したOCRモード")
    summaryMode: str = Field("api", description="使用した要約モード")
    summary: str = Field(..., description="短い自然文要約")
    structuredData: StructuredSummary = Field(..., description="構造化された要約データ")
    extractedText: str = Field(..., description="抽出・整形後のテキスト")
    warnings: List[str] = Field(default_factory=list, description="警告メッセージ")


class MultiSummarizeResponse(BaseModel):
    """複数ファイル用レスポンス"""
    totalFiles: int = Field(..., description="アップロードされたファイル数")
    successCount: int = Field(..., description="成功したファイル数")
    errorCount: int = Field(..., description="失敗したファイル数")
    results: List[SingleFileResult] = Field(..., description="各ファイルの結果")