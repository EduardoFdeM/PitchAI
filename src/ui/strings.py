"""
UI Strings - Textos centralizados da interface
=============================================

Definições de textos, mensagens e labels para a interface.
"""

from typing import Dict, Any


class Labels:
    """Labels da interface."""
    
    # Títulos principais
    APP_TITLE = "PitchAI - Assistente de Vendas"
    DASHBOARD_TITLE = "Dashboard"
    TRANSCRIPTION_TITLE = "Transcrição"
    SENTIMENT_TITLE = "Análise de Sentimento"
    SUGGESTIONS_TITLE = "Sugestões"
    SUMMARY_TITLE = "Resumo"
    SETTINGS_TITLE = "Configurações"
    
    # Controles
    START_BUTTON = "Iniciar Gravação"
    STOP_BUTTON = "Parar Gravação"
    PAUSE_BUTTON = "Pausar"
    RESUME_BUTTON = "Retomar"
    CLEAR_BUTTON = "Limpar"
    EXPORT_BUTTON = "Exportar"
    SETTINGS_BUTTON = "Configurações"
    
    # Status
    STATUS_READY = "Pronto"
    STATUS_RECORDING = "Gravando..."
    STATUS_PROCESSING = "Processando..."
    STATUS_ERROR = "Erro"
    STATUS_CONNECTING = "Conectando..."
    
    # Transcrição
    TRANSCRIPT_MIC = "Vendedor (Microfone)"
    TRANSCRIPT_LOOPBACK = "Cliente (Loopback)"
    TRANSCRIPT_EMPTY = "Nenhuma transcrição disponível"
    TRANSCRIPT_LOADING = "Carregando transcrição..."
    
    # Sentimento
    SENTIMENT_VALENCE = "Valência"
    SENTIMENT_ENGAGEMENT = "Engajamento"
    SENTIMENT_POSITIVE = "Positivo"
    SENTIMENT_NEUTRAL = "Neutro"
    SENTIMENT_NEGATIVE = "Negativo"
    SENTIMENT_HIGH = "Alto"
    SENTIMENT_MEDIUM = "Médio"
    SENTIMENT_LOW = "Baixo"
    
    # Objeções
    OBJECTION_PRICE = "Objeção: Preço"
    OBJECTION_TIMING = "Objeção: Timing"
    OBJECTION_AUTHORITY = "Objeção: Autoridade"
    OBJECTION_NEED = "Objeção: Necessidade"
    OBJECTION_DETECTED = "Objeção Detectada"
    OBJECTION_CONFIDENCE = "Confiança"
    
    # Sugestões RAG
    SUGGESTIONS_TITLE_TEMPLATE = "SUGESTÕES: {category}"
    SUGGESTIONS_LOADING = "Carregando sugestões..."
    SUGGESTIONS_EMPTY = "Nenhuma sugestão disponível"
    SUGGESTIONS_SCORE = "Score"
    SUGGESTIONS_SOURCES = "Fontes"
    SUGGESTIONS_COPY = "Copiar"
    SUGGESTIONS_OPEN_SOURCE = "Abrir Fonte"
    SUGGESTIONS_MARK_USED = "Marcar como Usada"
    
    # Resumo
    SUMMARY_MAIN_POINTS = "Pontos Principais"
    SUMMARY_OBJECTIONS_HANDLED = "Objeções Tratadas"
    SUMMARY_NEXT_STEPS = "Próximos Passos"
    SUMMARY_KPIS = "KPIs"
    SUMMARY_EXPORT_PDF = "Exportar PDF"
    SUMMARY_EXPORT_MD = "Exportar Markdown"
    SUMMARY_EMPTY = "Nenhum resumo disponível"
    
    # Sistema
    SYSTEM_NPU = "NPU"
    SYSTEM_ASR = "ASR"
    SYSTEM_SENTIMENT = "Sentimento"
    SYSTEM_RAG = "RAG"
    SYSTEM_STATUS_OK = "OK"
    SYSTEM_STATUS_FAIL = "FALHA"
    SYSTEM_STATUS_LOADING = "CARREGANDO"
    
    # Configurações
    SETTINGS_AUDIO = "Áudio"
    SETTINGS_MODELS = "Modelos"
    SETTINGS_RAG = "RAG"
    SETTINGS_UI = "Interface"
    SETTINGS_SAVE = "Salvar"
    SETTINGS_CANCEL = "Cancelar"
    SETTINGS_RESET = "Restaurar Padrões"


class Messages:
    """Mensagens do sistema."""
    
    # Sucesso
    SUCCESS_RECORDING_STARTED = "Gravação iniciada com sucesso"
    SUCCESS_RECORDING_STOPPED = "Gravação parada com sucesso"
    SUCCESS_SETTINGS_SAVED = "Configurações salvas com sucesso"
    SUCCESS_EXPORT_COMPLETED = "Exportação concluída com sucesso"
    SUCCESS_SUGGESTION_COPIED = "Sugestão copiada para a área de transferência"
    
    # Avisos
    WARNING_NO_AUDIO_DEVICE = "Nenhum dispositivo de áudio encontrado"
    WARNING_LOW_CONFIDENCE = "Confiança baixa na transcrição"
    WARNING_MODEL_LOADING = "Modelo ainda carregando..."
    WARNING_RAG_TIMEOUT = "Timeout na busca de sugestões"
    WARNING_NO_SUGGESTIONS = "Nenhuma sugestão encontrada para esta objeção"
    
    # Erros
    ERROR_RECORDING_FAILED = "Falha ao iniciar gravação"
    ERROR_AUDIO_DEVICE = "Erro no dispositivo de áudio"
    ERROR_MODEL_LOADING = "Erro ao carregar modelo"
    ERROR_TRANSCRIPTION = "Erro na transcrição"
    ERROR_SENTIMENT_ANALYSIS = "Erro na análise de sentimento"
    ERROR_RAG_REQUEST = "Erro na requisição RAG"
    ERROR_EXPORT_FAILED = "Falha na exportação"
    ERROR_SETTINGS_LOAD = "Erro ao carregar configurações"
    ERROR_SETTINGS_SAVE = "Erro ao salvar configurações"
    
    # Informações
    INFO_RECORDING_ACTIVE = "Gravação ativa - fale normalmente"
    INFO_PROCESSING_AUDIO = "Processando áudio..."
    INFO_GENERATING_SUGGESTIONS = "Gerando sugestões..."
    INFO_GENERATING_SUMMARY = "Gerando resumo..."
    INFO_MODEL_READY = "Modelo pronto para uso"
    INFO_RAG_READY = "Sistema RAG pronto"


class Tooltips:
    """Tooltips da interface."""
    
    # Controles
    TOOLTIP_START = "Iniciar gravação de áudio"
    TOOLTIP_STOP = "Parar gravação atual"
    TOOLTIP_PAUSE = "Pausar gravação temporariamente"
    TOOLTIP_CLEAR = "Limpar dados da sessão atual"
    TOOLTIP_EXPORT = "Exportar dados da sessão"
    TOOLTIP_SETTINGS = "Abrir configurações"
    
    # Status
    TOOLTIP_NPU_STATUS = "Status do processador neural"
    TOOLTIP_ASR_STATUS = "Status do reconhecimento de fala"
    TOOLTIP_SENTIMENT_STATUS = "Status da análise de sentimento"
    TOOLTIP_RAG_STATUS = "Status do sistema de sugestões"
    
    # Sentimento
    TOOLTIP_VALENCE = "Sentimento geral (-1 = negativo, +1 = positivo)"
    TOOLTIP_ENGAGEMENT = "Nível de engajamento (0 = baixo, 1 = alto)"
    TOOLTIP_SENTIMENT_GRAPH = "Histórico de sentimento ao longo do tempo"
    
    # Sugestões
    TOOLTIP_SUGGESTION_SCORE = "Relevância da sugestão (0-1)"
    TOOLTIP_SUGGESTION_SOURCES = "Fontes de conhecimento utilizadas"
    TOOLTIP_COPY_SUGGESTION = "Copiar sugestão para área de transferência"
    TOOLTIP_OPEN_SOURCE = "Abrir documento fonte"
    TOOLTIP_MARK_USED = "Marcar sugestão como utilizada"
    
    # Resumo
    TOOLTIP_EXPORT_PDF = "Exportar resumo em formato PDF"
    TOOLTIP_EXPORT_MD = "Exportar resumo em formato Markdown"


class Placeholders:
    """Textos placeholder."""
    
    # Campos de texto
    PLACEHOLDER_SEARCH = "Buscar..."
    PLACEHOLDER_FILTER = "Filtrar..."
    PLACEHOLDER_COMMENT = "Adicionar comentário..."
    
    # Estados vazios
    PLACEHOLDER_NO_TRANSCRIPT = "Aguardando transcrição..."
    PLACEHOLDER_NO_SENTIMENT = "Aguardando análise de sentimento..."
    PLACEHOLDER_NO_OBJECTIONS = "Nenhuma objeção detectada"
    PLACEHOLDER_NO_SUGGESTIONS = "Nenhuma sugestão disponível"
    PLACEHOLDER_NO_SUMMARY = "Resumo será gerado ao final da chamada"


class Formats:
    """Formatos de texto."""
    
    # Timestamps
    TIME_FORMAT = "%H:%M:%S"
    TIME_FORMAT_MS = "%H:%M:%S.%f"
    DATE_FORMAT = "%d/%m/%Y"
    DATETIME_FORMAT = "%d/%m/%Y %H:%M:%S"
    
    # Números
    PERCENTAGE_FORMAT = "{:.1f}%"
    DECIMAL_FORMAT = "{:.2f}"
    INTEGER_FORMAT = "{:d}"
    
    # Textos
    CALL_ID_FORMAT = "Chamada #{id}"
    DURATION_FORMAT = "{minutes:02d}:{seconds:02d}"
    CONFIDENCE_FORMAT = "Confiança: {:.1f}%"
    SCORE_FORMAT = "Score: {:.2f}"


class Categories:
    """Categorias e classificações."""
    
    # Objeções
    OBJECTION_CATEGORIES = {
        "preco": "Preço",
        "timing": "Timing",
        "autoridade": "Autoridade",
        "necessidade": "Necessidade"
    }
    
    # Sentimento
    SENTIMENT_LEVELS = {
        "very_positive": "Muito Positivo",
        "positive": "Positivo",
        "neutral": "Neutro",
        "negative": "Negativo",
        "very_negative": "Muito Negativo"
    }
    
    # Engajamento
    ENGAGEMENT_LEVELS = {
        "high": "Alto",
        "medium": "Médio",
        "low": "Baixo"
    }
    
    # Status
    STATUS_LEVELS = {
        "ok": "OK",
        "warning": "Aviso",
        "error": "Erro",
        "loading": "Carregando"
    }


def get_objection_label(category: str) -> str:
    """Obter label para categoria de objeção."""
    return Categories.OBJECTION_CATEGORIES.get(category, "Desconhecida")


def get_sentiment_label(valence: float) -> str:
    """Obter label para nível de sentimento."""
    if valence > 0.6:
        return Categories.SENTIMENT_LEVELS["very_positive"]
    elif valence > 0.2:
        return Categories.SENTIMENT_LEVELS["positive"]
    elif valence > -0.2:
        return Categories.SENTIMENT_LEVELS["neutral"]
    elif valence > -0.6:
        return Categories.SENTIMENT_LEVELS["negative"]
    else:
        return Categories.SENTIMENT_LEVELS["very_negative"]


def get_engagement_label(engagement: float) -> str:
    """Obter label para nível de engajamento."""
    if engagement > 0.7:
        return Categories.ENGAGEMENT_LEVELS["high"]
    elif engagement > 0.3:
        return Categories.ENGAGEMENT_LEVELS["medium"]
    else:
        return Categories.ENGAGEMENT_LEVELS["low"]


def format_duration(seconds: float) -> str:
    """Formatar duração em segundos."""
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    return Formats.DURATION_FORMAT.format(minutes=minutes, seconds=secs)


def format_confidence(confidence: float) -> str:
    """Formatar confiança como porcentagem."""
    return Formats.CONFIDENCE_FORMAT.format(confidence * 100)


def format_score(score: float) -> str:
    """Formatar score."""
    return Formats.SCORE_FORMAT.format(score) 