"""
Chat Widget - Conversa com IA sobre Sentimento
=============================================

Tela de chat para conversar com a IA sobre análise de sentimento.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QFrame, QTextEdit, QLineEdit, QScrollArea
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont
import random

class ChatWidget(QWidget):
    """Widget de chat com IA."""
    
    # Sinais
    back_to_analysis_requested = pyqtSignal()
    
    def __init__(self, data=None, data_type="sentiment", parent=None):
        super().__init__(parent)
        self.data = data or {}
        self.data_type = data_type  # "sentiment", "opportunity", "objection"
        self._setup_ui()
        
    def _setup_ui(self):
        """Configurar interface do chat."""
        # Layout principal
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)
        
        # ===== HEADER =====
        header_layout = QVBoxLayout()
        
        # Linha superior do header
        top_header = QHBoxLayout()
        
        # Botão voltar
        back_button = QPushButton("← Voltar")
        back_button.setObjectName("backButton")
        back_button.setFixedSize(100, 40)
        back_button.clicked.connect(self.back_to_analysis_requested.emit)
        
        top_header.addWidget(back_button)
        top_header.addStretch()
        
        # Título dinâmico baseado no tipo
        if self.data_type == "sentiment":
            title_text = "💬 Chat com IA - Análise de Sentimento"
        elif self.data_type == "opportunity":
            title_text = "🔔 OPORTUNIDADES"
        elif self.data_type == "objection":
            title_text = "🛡️ OBJEÇÕES"
        else:
            title_text = "💬 Chat com IA"
            
        title_label = QLabel(title_text)
        title_label.setStyleSheet("color: white; font-size: 18px; font-weight: bold;")
        
        top_header.addWidget(title_label)
        top_header.addStretch()
        
        header_layout.addLayout(top_header)
        
        # Descrição específica para oportunidades/objeções
        if self.data_type in ["opportunity", "objection"] and self.data.get('text'):
            description_label = QLabel(self.data.get('text', ''))
            description_label.setStyleSheet("color: white; font-size: 14px; margin-top: 5px;")
            header_layout.addWidget(description_label)
        
        main_layout.addLayout(header_layout)
        
        # ===== CONTEÚDO PRINCIPAL =====
        content_layout = QVBoxLayout()
        content_layout.setSpacing(20)
        
        # ===== CHAT =====
        chat_frame = QFrame()
        chat_frame.setObjectName("chatFrame")
        
        chat_layout = QVBoxLayout(chat_frame)
        chat_layout.setContentsMargins(20, 20, 20, 20)
        chat_layout.setSpacing(15)
        
        # Área de mensagens
        self.messages_area = QTextEdit()
        self.messages_area.setObjectName("messagesArea")
        self.messages_area.setReadOnly(True)
        self.messages_area.setPlaceholderText("Mensagens aparecerão aqui...")
        
        chat_layout.addWidget(self.messages_area)
        
        # Campo de entrada
        input_layout = QHBoxLayout()
        
        # Label para o campo
        input_label = QLabel("label")
        input_label.setStyleSheet("color: white; font-size: 14px;")
        
        input_layout.addWidget(input_label)
        input_layout.addStretch()
        
        chat_layout.addLayout(input_layout)
        
        # Campo de entrada
        self.input_field = QLineEdit()
        self.input_field.setObjectName("inputField")
        self.input_field.setPlaceholderText("value")
        self.input_field.returnPressed.connect(self._send_message)
        
        chat_layout.addWidget(self.input_field)
        
        content_layout.addWidget(chat_frame)
        
        main_layout.addLayout(content_layout)
        
        self._apply_styles()
        self._add_welcome_message()
    
    def _add_welcome_message(self):
        """Adicionar mensagem de boas-vindas da IA."""
        if self.data_type == "sentiment":
            welcome_message = """
<div style="background: rgba(0, 0, 0, 0.3); border-radius: 8px; padding: 10px; margin: 5px 0; text-align: left;">
🤖 <b>IA Assistant:</b><br>
Olá! Analisei o sentimento da conversa e detectei que está <b>positivo</b> (score: 85%).<br><br>

Posso te ajudar com:<br>
• 📈 Interpretação dos dados de sentimento<br>
• 💡 Sugestões para melhorar a conversa<br>
• 🎯 Estratégias para manter o engajamento<br>
• ⚠️ Alertas sobre mudanças de humor<br><br>

Como posso te ajudar hoje?
</div>
            """
        elif self.data_type == "opportunity":
            opportunity_text = self.data.get('text', 'Oportunidade identificada')
            welcome_message = f"""
<div style="background: rgba(0, 0, 0, 0.3); border-radius: 8px; padding: 10px; margin: 5px 0; text-align: left;">
🤖 <b>IA Assistant:</b><br>
Identifiquei uma <b>oportunidade</b>: {opportunity_text}<br><br>

Posso te ajudar com:<br>
• 💡 Como aproveitar essa oportunidade<br>
• 🎯 Estratégias para abordar o cliente<br>
• 📊 Análise do momento ideal<br>
• 🚀 Próximos passos recomendados<br><br>

O que posso fazer para ajustar a comunicação com o meu cliente?
</div>
            """
        elif self.data_type == "objection":
            objection_text = self.data.get('text', 'Objeção identificada')
            welcome_message = f"""
<div style="background: rgba(0, 0, 0, 0.3); border-radius: 8px; padding: 10px; margin: 5px 0; text-align: left;">
🤖 <b>IA Assistant:</b><br>
Detectei uma <b>objeção</b>: {objection_text}<br><br>

Posso te ajudar com:<br>
• 🛡️ Como lidar com essa objeção<br>
• 💡 Estratégias de resposta<br>
• 📊 Análise da preocupação do cliente<br>
• 🎯 Técnicas de superação<br><br>

O que posso fazer para ajustar a comunicação com o meu cliente?
</div>
            """
        else:
            welcome_message = """
<div style="background: rgba(0, 0, 0, 0.3); border-radius: 8px; padding: 10px; margin: 5px 0; text-align: left;">
🤖 <b>IA Assistant:</b><br>
Como posso te ajudar hoje?
</div>
            """
        
        self.messages_area.setHtml(welcome_message)
    
    def _send_message(self):
        """Enviar mensagem para a IA."""
        message = self.input_field.text().strip()
        if not message:
            return
        
        # Adicionar mensagem do usuário
        user_html = f"""
<div style="background: rgba(255, 255, 255, 0.1); border-radius: 8px; padding: 10px; margin: 5px 0; text-align: right;">
👤 <b>Você:</b><br>
{message}
</div>
        """
        self.messages_area.append(user_html)
        
        # Limpar input
        self.input_field.clear()
        
        # Simular resposta da IA
        QTimer.singleShot(1000, lambda: self._add_ai_response(message))
    
    def _add_ai_response(self, user_message):
        """Adicionar resposta da IA."""
        message_lower = user_message.lower()
        
        if self.data_type == "sentiment":
            # Respostas para sentimento
            if "sentimento" in message_lower:
                response = "O sentimento está <b>positivo</b> com tendência de melhoria. Recomendo manter o tom atual da conversa."
            elif "melhorar" in message_lower or "melhor" in message_lower:
                response = "Para melhorar o engajamento, sugiro:<br>• Fazer mais perguntas abertas<br>• Usar exemplos específicos<br>• Mostrar empatia com as preocupações"
            elif "estratégia" in message_lower:
                response = "Baseado no sentimento atual, recomendo:<br>• Continuar com o tom positivo<br>• Focar nos benefícios<br>• Evitar pressão excessiva"
            else:
                response = "Entendo sua pergunta. Baseado na análise atual, o sentimento está positivo e a conversa está fluindo bem. Posso te ajudar com algo específico sobre a análise?"
        
        elif self.data_type == "opportunity":
            # Respostas para oportunidades
            if "ajustar" in message_lower or "comunicação" in message_lower or "cliente" in message_lower:
                response = "Indique ao cliente de que tal coisa e tal coisa, lorem impsum adpam ofsuam luso pialsnd askdj akshi jsb jsdh kasj lalsdks laisrhsf skdfnvc jsdkfsbdkf skdfshkdjf ksj kjd f kjnkdj kjsdbk Iskd skjdbf."
            elif "aproveitar" in message_lower or "oportunidade" in message_lower:
                response = "Para aproveitar essa oportunidade:<br>• Identifique o momento ideal<br>• Apresente os benefícios de forma clara<br>• Use exemplos específicos<br>• Mantenha o tom positivo"
            else:
                response = "Baseado na oportunidade identificada, recomendo focar nos benefícios e usar exemplos específicos para engajar o cliente."
        
        elif self.data_type == "objection":
            # Respostas para objeções
            if "ajustar" in message_lower or "comunicação" in message_lower or "cliente" in message_lower:
                response = "Indique ao cliente de que tal coisa e tal coisa, lorem impsum adpam ofsuam luso pialsnd askdj akshi jsb jsdh kasj lalsdks laisrhsf skdfnvc jsdkfsbdkf skdfshkdjf ksj kjd f kjnkdj kjsdbk Iskd skjdbf."
            elif "lidar" in message_lower or "objeção" in message_lower:
                response = "Para lidar com essa objeção:<br>• Reconheça a preocupação do cliente<br>• Apresente soluções específicas<br>• Use dados e exemplos<br>• Mantenha a calma e seja empático"
            else:
                response = "Baseado na objeção identificada, recomendo abordar a preocupação do cliente de forma direta e empática."
        
        else:
            response = "Como posso te ajudar com essa questão?"
        
        ai_html = f"""
<div style="background: rgba(0, 0, 0, 0.3); border-radius: 8px; padding: 10px; margin: 5px 0; text-align: left;">
🤖 <b>IA Assistant:</b><br>
{response}
</div>
        """
        self.messages_area.append(ai_html)
        
        # Scroll para baixo
        scrollbar = self.messages_area.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def _apply_styles(self):
        """Aplicar estilos do chat."""
        # Estilos movidos para glassmorphism.qss
        pass
