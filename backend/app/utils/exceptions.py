class AppError(Exception):
    """アプリケーション基底例外"""

    code: str = "APP_ERROR"
    message: str = "アプリケーションエラーが発生しました。"
    status_code: int = 500

    def __init__(
        self,
        message: str | None = None,
        code: str | None = None,
        status_code: int | None = None,
    ):
        self.message = message or self.message
        self.code = code or self.code
        self.status_code = status_code or self.status_code
        super().__init__(self.message)


class UnsupportedFileTypeError(AppError):
    """非対応ファイル形式"""

    code = "UNSUPPORTED_FILE_TYPE"
    message = "対応していないファイル形式です。jpg / png を使用してください。"
    status_code = 400


class EmptyFileError(AppError):
    """空ファイル"""

    code = "EMPTY_FILE"
    message = "空ファイルです。"
    status_code = 400


class FileTooLargeError(AppError):
    """ファイルサイズ超過"""

    code = "FILE_TOO_LARGE"
    message = "ファイルサイズが大きすぎます。10MB未満のファイルを選択してください。"
    status_code = 413


class TextExtractionFailedError(AppError):
    """テキスト抽出失敗"""

    code = "TEXT_EXTRACTION_FAILED"
    message = "テキスト抽出に失敗しました。"
    status_code = 422


class SummaryGenerationFailedError(AppError):
    """要約生成失敗"""

    code = "SUMMARY_GENERATION_FAILED"
    message = "要約生成に失敗しました。"
    status_code = 422


class OpenAIAPIError(AppError):
    """OpenAI API呼び出し失敗"""

    code = "OPENAI_API_ERROR"
    message = "外部APIの呼び出しに失敗しました。"
    status_code = 502


# Phase 2: Ollama related errors
class LocalLLMUnavailableError(AppError):
    """Ollama利用不可"""

    code = "LOCAL_LLM_UNAVAILABLE"
    message = "ローカルLLMサービスが利用できません。"
    status_code = 503


class LocalLLMModelMissingError(AppError):
    """Ollamaモデル未設定"""

    code = "LOCAL_LLM_MODEL_MISSING"
    message = "ローカルLLMのモデルが設定されていません。"
    status_code = 503


class LocalLLMTimeoutError(AppError):
    """Ollama応答タイムアウト"""

    code = "LOCAL_LLM_TIMEOUT"
    message = "ローカルLLMの応答がタイムアウトしました。"
    status_code = 503


# Phase 2: NDLOCR related errors
class NDLOCRUnavailableError(AppError):
    """NDLOCR-Lite利用不可"""

    code = "NDLOCR_UNAVAILABLE"
    message = "NDLOCR-Liteが利用できません。"
    status_code = 503


class NDLOCRExecutionFailedError(AppError):
    """NDLOCR-Lite実行失敗"""

    code = "NDLOCR_EXECUTION_FAILED"
    message = "NDLOCR-Liteの実行に失敗しました。"
    status_code = 503


class NDLOCRTimeoutError(AppError):
    """NDLOCR-Lite実行タイムアウト"""

    code = "NDLOCR_TIMEOUT"
    message = "NDLOCR-Liteの実行がタイムアウトしました。"
    status_code = 503
