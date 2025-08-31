"""
Analysis Widget - Análise em Tempo Real
===================================o

Tela de análise com transcrição em tempo real e gráfico de sentimento.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QFrame, QTextEdit, QScrollArea
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QRect, QPointF
from PyQt6.QtGui import QFont, QPainter, QPen, QBrush, QColor, QLinearGradient, QPainterPath, QMouseEvent

from .opportunity_widget import OpportunityWidget
from .objection_widget import ObjectionWidget
import random
import math

class SentimentGraph(QWidget):
    """Widget de gráfico de sentimento com desenho real."""
    
    # Sinais
    clicked = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(200)
        self.setObjectName("sentimentGraph")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        # Dados do gráfico
        self.data_points = [random.randint(80, 120) for _ in range(30)]
        self.positive_data = [random.randint(90, 140) for _ in range(30)]
        self.negative_data = [random.randint(0, 40) for _ in range(30)]
        
        # Estado de visibilidade
        self.is_visible = False
        
        self._apply_styles()
    
    def mousePressEvent(self, event: QMouseEvent):
        """Detectar clique no gráfico."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
    
    def show_graph(self):
        """Mostrar o gráfico."""
        self.is_visible = True
        self.show()
        self.update()
    
    def hide_graph(self):
        """Ocultar o gráfico."""
        self.is_visible = False
        self.hide()
    
    def _apply_styles(self):
        """Aplicar estilos do gráfico."""
        style = """
        QWidget#sentimentGraph {
            background: rgba(255, 255, 255, 0.12);
            border: 1px solid rgba(255, 255, 255, 0.18);
            border-radius: 12px;
        }
        """
        self.setStyleSheet(style)
    
    def update_sentiment(self, value):
        """Atualizar valor de sentimento."""
        # Adicionar novos pontos
        self.data_points.append(value)
        self.positive_data.append(random.randint(90, 140))
        self.negative_data.append(random.randint(0, 40))
        
        # Manter apenas os últimos 30 pontos
        if len(self.data_points) > 30:
            self.data_points.pop(0)
            self.positive_data.pop(0)
            self.negative_data.pop(0)
        
        self.update()  # Redesenhar o widget
    
    def paintEvent(self, event):
        """Desenhar o gráfico."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Obter dimensões
        width = self.width()
        height = self.height()
        margin = 20
        
        # Área de desenho
        graph_rect = QRect(margin, margin, width - 2*margin, height - 2*margin)
        
        # Desenhar fundo do gráfico
        painter.fillRect(graph_rect, QColor(0, 0, 0, 50))
        
        # Desenhar grade
        self._draw_grid(painter, graph_rect)
        
        # Desenhar eixos
        self._draw_axes(painter, graph_rect)
        
        # Desenhar dados
        self._draw_data(painter, graph_rect)
    
    def _draw_grid(self, painter, rect):
        """Desenhar grade de fundo."""
        painter.setPen(QPen(QColor(255, 255, 255, 30), 1))
        
        # Linhas horizontais
        for i in range(1, 5):
            y = rect.top() + (rect.height() * i) // 5
            painter.drawLine(rect.left(), y, rect.right(), y)
        
        # Linhas verticais
        for i in range(1, 5):
            x = rect.left() + (rect.width() * i) // 5
            painter.drawLine(x, rect.top(), x, rect.bottom())
    
    def _draw_axes(self, painter, rect):
        """Desenhar eixos e labels."""
        painter.setPen(QPen(QColor(255, 255, 255, 100), 2))
        
        # Eixo Y (vertical)
        painter.drawLine(rect.left(), rect.top(), rect.left(), rect.bottom())
        
        # Eixo X (horizontal)
        painter.drawLine(rect.left(), rect.bottom(), rect.right(), rect.bottom())
        
        # Labels do eixo Y
        painter.setPen(QColor(255, 255, 255, 150))
        font = QFont()
        font.setPointSize(8)
        painter.setFont(font)
        
        for i in range(6):
            y = rect.bottom() - (rect.height() * i) // 5
            value = (i * 140) // 5
            painter.drawText(rect.left() - 35, y + 3, f"{value}")
    
    def _draw_data(self, painter, rect):
        """Desenhar dados do gráfico."""
        if not self.data_points:
            return
        
        # Converter dados para coordenadas
        points = []
        for i, value in enumerate(self.data_points):
            x = rect.left() + (rect.width() * i) / (len(self.data_points) - 1)
            y = rect.bottom() - (rect.height() * value) / 140
            points.append(QPointF(x, y))
        
        # Desenhar área positiva (roxo/azul)
        positive_points = []
        for i, value in enumerate(self.positive_data):
            x = rect.left() + (rect.width() * i) / (len(self.positive_data) - 1)
            y = rect.bottom() - (rect.height() * value) / 140
            positive_points.append(QPointF(x, y))
        
        if len(positive_points) > 1:
            # Criar gradiente para área positiva
            gradient = QLinearGradient(0, rect.top(), 0, rect.bottom())
            gradient.setColorAt(0, QColor(138, 43, 226, 100))  # Roxo
            gradient.setColorAt(1, QColor(0, 123, 255, 50))    # Azul
            
            painter.setBrush(QBrush(gradient))
            painter.setPen(QPen(QColor(138, 43, 226, 150), 2))
            
            # Desenhar área preenchida
            path = QPainterPath()
            path.moveTo(positive_points[0])
            for point in positive_points[1:]:
                path.lineTo(point)
            path.lineTo(positive_points[-1].x(), rect.bottom())
            path.lineTo(positive_points[0].x(), rect.bottom())
            path.closeSubpath()
            
            painter.drawPath(path)
        
        # Desenhar área negativa (vermelho)
        negative_points = []
        for i, value in enumerate(self.negative_data):
            x = rect.left() + (rect.width() * i) / (len(self.negative_data) - 1)
            y = rect.bottom() - (rect.height() * value) / 140
            negative_points.append(QPointF(x, y))
        
        if len(negative_points) > 1:
            # Criar gradiente para área negativa
            gradient = QLinearGradient(0, rect.top(), 0, rect.bottom())
            gradient.setColorAt(0, QColor(255, 59, 48, 80))    # Vermelho
            gradient.setColorAt(1, QColor(255, 59, 48, 30))
            
            painter.setBrush(QBrush(gradient))
            painter.setPen(QPen(QColor(255, 59, 48, 120), 1))
            
            # Desenhar área preenchida
            path = QPainterPath()
            path.moveTo(negative_points[0])
            for point in negative_points[1:]:
                path.lineTo(point)
            path.lineTo(negative_points[-1].x(), rect.bottom())
            path.lineTo(negative_points[0].x(), rect.bottom())
            path.closeSubpath()
            
            painter.drawPath(path)
        
        # Desenhar linha principal (branca)
        if len(points) > 1:
            painter.setPen(QPen(QColor(255, 255, 255, 200), 2))
            for i in range(len(points) - 1):
                painter.drawLine(points[i], points[i + 1])


class AnalysisWidget(QWidget):
    """Widget de análise em tempo real."""
    
        # Sinais
    stop_recording_requested = pyqtSignal()
    menu_requested = pyqtSignal()
    chat_requested = pyqtSignal(dict)  # Emite dados de sentimento
    opportunity_chat_requested = pyqtSignal(dict)  # Emite dados de oportunidade
    objection_chat_requested = pyqtSignal(dict)  # Emite dados de objeção
    transcription_full_requested = pyqtSignal(str)  # Emite texto da transcrição
    back_to_dashboard_requested = pyqtSignal()
    
    def __init__(self, config, app_instance, parent=None):
        super().__init__(parent)
        self.config = config
        self.app_instance = app_instance
        self.is_recording = False
        self._setup_ui()

    def _setup_ui(self):
        """Configurar interface de análise."""
        # Layout principal
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)
        
        # ===== HEADER =====
        header_layout = QHBoxLayout()
        
        # Botão de voltar
        back_button = QPushButton("← Voltar")
        back_button.setObjectName("backButton")
        back_button.setFixedSize(100, 40)
        back_button.clicked.connect(lambda: self.back_to_dashboard_requested.emit())
        
        header_layout.addWidget(back_button)
        header_layout.addStretch()
        
        # Botão "Ask to your assistant"
        assistant_button = QPushButton("Ask to your assistant")
        assistant_button.setObjectName("assistantButton")
        assistant_button.setFixedSize(180, 40)
        
        header_layout.addWidget(assistant_button)
        header_layout.addStretch()
        
        # Botão de gravação (vermelho)
        self.record_button = QPushButton("⏹")
        self.record_button.setObjectName("recordButton")
        self.record_button.setFixedSize(40, 40)
        self.record_button.clicked.connect(self._toggle_recording)
        
        header_layout.addWidget(self.record_button)
        
        main_layout.addLayout(header_layout)
        
        # ===== CONTEÚDO PRINCIPAL =====
        content_layout = QVBoxLayout()
        content_layout.setSpacing(20)
        
        # ===== ÁREA DE DETECÇÕES (OBJEÇÕES/OPORTUNIDADES) =====
        detections_frame = QFrame()
        detections_frame.setObjectName("detectionsFrame")
        
        detections_layout = QVBoxLayout(detections_frame)
        detections_layout.setContentsMargins(20, 20, 20, 20)
        detections_layout.setSpacing(15)
        
        # Área scrollável para detecções
        self.detections_scroll = QScrollArea()
        self.detections_scroll.setWidgetResizable(True)
        self.detections_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.detections_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        # Estilo movido para glassmorphism.qss
        self.detections_scroll.setMaximumHeight(200)
        
        # Container para detecções
        self.detections_container = QWidget()
        self.detections_layout = QVBoxLayout(self.detections_container)
        self.detections_layout.setContentsMargins(0, 0, 0, 0)
        self.detections_layout.setSpacing(10)
        self.detections_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        # Widgets de detecção
        self.opportunity_widget = OpportunityWidget()
        self.objection_widget = ObjectionWidget()
        
        # Conectar sinais
        self.opportunity_widget.opportunity_clicked.connect(self._open_opportunity_chat)
        self.objection_widget.objection_clicked.connect(self._open_objection_chat)
        
        self.detections_layout.addWidget(self.opportunity_widget)
        self.detections_layout.addWidget(self.objection_widget)
        self.detections_layout.addStretch()
        
        self.detections_scroll.setWidget(self.detections_container)
        detections_layout.addWidget(self.detections_scroll)
        
        content_layout.addWidget(detections_frame)
        
        # ===== TRANSCRIPTION FEED =====
        transcription_frame = QFrame()
        transcription_frame.setObjectName("transcriptionFrame")
        
        transcription_layout = QVBoxLayout(transcription_frame)
        transcription_layout.setContentsMargins(20, 20, 20, 20)
        transcription_layout.setSpacing(15)
        
        # Título da transcrição
        transcription_title = QLabel("👤 Transcription Feed")
        transcription_title.setStyleSheet("color: white; font-size: 16px; font-weight: bold;")
        
        transcription_layout.addWidget(transcription_title)
        
        # Área de transcrição
        self.transcription_area = QTextEdit()
        self.transcription_area.setObjectName("transcriptionArea")
        self.transcription_area.setReadOnly(True)
        self.transcription_area.setPlaceholderText("Transcrição aparecerá aqui...")
        self.transcription_area.setMaximumHeight(150)
        
        # Inicialmente não clicável (só quando gravar)
        self.transcription_area.setCursor(Qt.CursorShape.ArrowCursor)
        self.transcription_area.mousePressEvent = self._transcription_clicked
        
        transcription_layout.addWidget(self.transcription_area)
        
        content_layout.addWidget(transcription_frame)
        
        # ===== SENTIMENT ANALYSIS =====
        sentiment_frame = QFrame()
        sentiment_frame.setObjectName("sentimentFrame")
        
        sentiment_layout = QVBoxLayout(sentiment_frame)
        sentiment_layout.setContentsMargins(20, 20, 20, 20)
        sentiment_layout.setSpacing(15)
        
        # Header do sentimento
        sentiment_header = QHBoxLayout()
        
        sentiment_title = QLabel("📊 Sentiment Analysis")
        sentiment_title.setStyleSheet("color: white; font-size: 16px; font-weight: bold;")
        
        sentiment_header.addWidget(sentiment_title)
        sentiment_header.addStretch()
        
        # Tag de status
        self.sentiment_status = QLabel("BOM")
        self.sentiment_status.setObjectName("sentimentStatus")
        self.sentiment_status.setFixedSize(60, 25)
        
        sentiment_header.addWidget(self.sentiment_status)
        
        sentiment_layout.addLayout(sentiment_header)
        
        # Gráfico de sentimento
        self.sentiment_graph = SentimentGraph()
        self.sentiment_graph.clicked.connect(self._open_chat)
        self.sentiment_graph.hide()  # Iniciar oculto
        sentiment_layout.addWidget(self.sentiment_graph)
        
        # Status inicial vazio
        self.sentiment_status.setText("")
        self.sentiment_status.hide()
        self.sentiment_status.setStyleSheet("""
            QLabel#sentimentStatus {
                background: transparent;
                border-radius: 12px;
                color: white;
                font-size: 12px;
                font-weight: bold;
                padding: 5px 10px;
            }
        """)
        
        content_layout.addWidget(sentiment_frame)
        
        main_layout.addLayout(content_layout)
        
        self._apply_styles()
        self._start_simulation()
        
        # Dados de sentimento para o chat
        self.current_sentiment_data = {
            'score': 85,
            'status': 'BOM',
            'trend': 'positive'
        }
    
    def _open_chat(self):
        """Abrir tela de chat com IA."""
        self.chat_requested.emit(self.current_sentiment_data)
    
    def _open_opportunity_chat(self, opportunity_data):
        """Abrir chat para oportunidade."""
        self.opportunity_chat_requested.emit(opportunity_data)
    
    def _open_objection_chat(self, objection_data):
        """Abrir chat para objeção."""
        self.objection_chat_requested.emit(objection_data)
    
    def _transcription_clicked(self, event):
        """Abrir tela de transcrição completa."""
        # Só abrir se estiver gravando
        if self.is_recording:
            transcription_text = self.transcription_area.toPlainText()
            self.transcription_full_requested.emit(transcription_text)
            
            # A simulação continua rodando em background
            # Não parar a gravação quando abrir a transcrição
    
    def _toggle_recording(self):
        """Alternar estado de gravação."""
        self.is_recording = not self.is_recording
        
        if self.is_recording:
            self.record_button.setText("⏹")
            self.record_button.setStyleSheet("""
                QPushButton#recordButton {
                    background: #FF3B30;
                    border: none;
                    border-radius: 20px;
                    color: white;
                    font-size: 16px;
                    font-weight: bold;
                }
            """)
            # Tornar transcrição clicável quando gravar
            self.transcription_area.setCursor(Qt.CursorShape.PointingHandCursor)
        else:
            self.record_button.setText("▶")
            self.record_button.setStyleSheet("""
                QPushButton#recordButton {
                    background: #007AFF;
                    border: none;
                    border-radius: 20px;
                    color: white;
                    font-size: 16px;
                    font-weight: bold;
                }
            """)
            # Tornar transcrição não clicável quando parar
            self.transcription_area.setCursor(Qt.CursorShape.ArrowCursor)
            self.stop_recording_requested.emit()
    
    def _start_simulation(self):
        """Iniciar simulação de dados."""
        self.simulation_timer = QTimer()
        self.simulation_timer.timeout.connect(self._update_simulation)
        self.simulation_timer.start(3000)  # Atualizar a cada 3 segundos
        
        # Dados simulados de transcrição
        self.transcript_samples = [
            "Sed ut perspiciatis unde omnis iste natus error sit voluptatem accusantium doloremque laudantium.",
            "Totam rem aperiam, eaque ipsa quae ab illo inventore veritatis et quasi architecto beatae vitae.",
            "Dicta sunt explicabo. Nemo enim ipsam voluptatem quia voluptas sit aspernatur aut odit aut fugit.",
            "Sed quia consequuntur magni dolores eos qui ratione voluptatem sequi nesciunt.",
            "Neque porro quisquam est, qui dolorem ipsum quia dolor sit amet, consectetur, adipisci velit."
        ]
        self.current_sample = 0
    
    def _update_simulation(self):
        """Atualizar simulação de dados."""
        if not self.is_recording:
            return
        
        # Adicionar nova transcrição
        sample = self.transcript_samples[self.current_sample]
        self.transcription_area.append(f"🟢 {sample}")
        self.current_sample = (self.current_sample + 1) % len(self.transcript_samples)
        
        # Atualizar sentimento
        sentiment_value = random.randint(80, 120)
        self.sentiment_graph.update_sentiment(sentiment_value)
        
        # Mostrar gráfico sempre que há sentimento detectado (ajustado para aparecer mais)
        if sentiment_value > 85:
            self.sentiment_graph.show_graph()
        else:
            self.sentiment_graph.hide_graph()
        
        # Atualizar dados para o chat
        self.current_sentiment_data['score'] = sentiment_value
        
        # Simular detecção de oportunidades (30% chance)
        if random.random() < 0.3:
            opportunity_texts = [
                'Remember to mention the limited discount',
                'Client showed interest in premium features',
                'Perfect moment to discuss pricing plans',
                'Opportunity to upsell additional services'
            ]
            opportunity_data = {
                'text': random.choice(opportunity_texts),
                'confidence': random.randint(75, 95),
                'type': 'Interesse'
            }
            self.opportunity_widget.add_opportunity(opportunity_data)
        
        # Simular detecção de objeções (20% chance)
        if random.random() < 0.2:
            objection_texts = [
                'Remember to mention the limited discount',
                'Client expressed budget concerns',
                'Price objection detected',
                'Timing concern identified'
            ]
            objection_data = {
                'text': random.choice(objection_texts),
                'confidence': random.randint(80, 95),
                'type': 'Preço'
            }
            self.objection_widget.add_objection(objection_data)
        
        # Atualizar status apenas quando há sentimento detectado
        if sentiment_value > 90:
            # Mostrar gráfico na primeira detecção e manter visível
            if not self.sentiment_graph.isVisible():
                self.sentiment_graph.show_graph()
            
            if sentiment_value > 100:
                self.sentiment_status.setText("BOM")
                self.current_sentiment_data['status'] = "BOM"
                self.sentiment_status.setStyleSheet("""
                    QLabel#sentimentStatus {
                        background: #34C759;
                        border-radius: 12px;
                        color: white;
                        font-size: 12px;
                        font-weight: bold;
                        padding: 5px 10px;
                    }
                """)
                self.sentiment_status.show()
            else:
                self.sentiment_status.setText("RUIM")
                self.current_sentiment_data['status'] = "RUIM"
                self.sentiment_status.setStyleSheet("""
                    QLabel#sentimentStatus {
                        background: #FF3B30;
                        border-radius: 12px;
                        color: white;
                        font-size: 12px;
                        font-weight: bold;
                        padding: 5px 10px;
                    }
                """)
                self.sentiment_status.show()
        else:
            # Se o gráfico já foi mostrado, apenas limpar o status do sentimento
            if self.sentiment_graph.isVisible():
                self.sentiment_status.setText("")
                self.sentiment_status.hide()
            # Se o gráfico ainda não foi mostrado, manter status vazio
            elif not self.sentiment_graph.isVisible():
                self.sentiment_status.setText("")
                self.sentiment_status.hide()
    
    def _apply_styles(self):
        """Aplicar estilos da análise."""
        # Estilos movidos para glassmorphism.qss
        pass
    

