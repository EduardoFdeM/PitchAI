"""
Summary Widget - Resumo da Reunião
====================================

Exibe o resumo gerado pela IA após o término da análise.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QScrollArea, 
    QFrame, QHBoxLayout, QTextEdit
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from typing import Dict, Any

class SummaryWidget(QWidget):
    """Widget para exibir o resumo da reunião."""
    
    back_to_start_requested = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_summary = None
        self._setup_ui()

    def _setup_ui(self):
        """Configurar a interface do widget."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # Header
        header_layout = QHBoxLayout()
        title_label = QLabel("📋 Resumo da Reunião")
        title_font = QFont()
        title_font.setPointSize(24)
        title_font.setWeight(QFont.Weight.Bold)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #ECEFF4;")
        
        back_button = QPushButton("← Voltar")
        back_button.setObjectName("secondaryButton")
        back_button.clicked.connect(self.back_to_start_requested)

        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(back_button)
        
        main_layout.addLayout(header_layout)

        # Área de Resumo
        self.summary_text = QTextEdit()
        self.summary_text.setReadOnly(True)
        self.summary_text.setStyleSheet("""
            QTextEdit {
                background: rgba(46, 52, 64, 0.8);
                border: 1px solid rgba(129, 161, 193, 0.3);
                border-radius: 8px;
                color: #ECEFF4;
                font-family: 'Segoe UI', sans-serif;
                font-size: 14px;
                line-height: 1.6;
                padding: 15px;
            }
        """)
        main_layout.addWidget(self.summary_text)
        
        # Botões de Ação
        action_layout = QHBoxLayout()
        action_layout.addStretch()

        self.export_md_button = QPushButton("📄 Exportar MD")
        self.export_md_button.setObjectName("actionButton")
        self.export_md_button.clicked.connect(self._export_markdown)

        self.export_pdf_button = QPushButton("📕 Exportar PDF")
        self.export_pdf_button.setObjectName("actionButton")
        self.export_pdf_button.clicked.connect(self._export_pdf)

        self.save_history_button = QPushButton("💾 Salvar Histórico")
        self.save_history_button.setObjectName("actionButton")
        self.save_history_button.clicked.connect(self._save_to_history)

        action_layout.addWidget(self.export_md_button)
        action_layout.addWidget(self.export_pdf_button)
        action_layout.addWidget(self.save_history_button)
        
        main_layout.addLayout(action_layout)
        
        # Mostrar dados de exemplo inicialmente
        self._show_example_summary()

    def update_summary(self, summary_data: Dict[str, Any]):
        """Atualizar o resumo exibido."""
        try:
            self.current_summary = summary_data
            self._format_and_display_summary(summary_data)
            print("✅ Resumo atualizado no SummaryWidget")
        except Exception as e:
            print(f"❌ Erro ao atualizar resumo: {e}")
            self._show_error_summary(str(e))

    def _format_and_display_summary(self, summary):
        """Formatar e exibir o resumo."""
        try:
            html_content = f"""
            <div style='font-family: "Segoe UI", sans-serif; line-height: 1.6;'>

            <h2 style='color: #88C0D0; border-bottom: 2px solid #88C0D0; padding-bottom: 10px;'>
                🎯 Pontos Principais
            </h2>
            """

            # Pontos principais
            key_points = summary.get('key_points', [])
            if key_points:
                for point in key_points:
                    html_content += f"<p style='margin: 10px 0;'>• {point}</p>"
            else:
                html_content += "<p style='color: #888888;'>Nenhum ponto principal identificado</p>"

            html_content += "<br>"

            # Objeções
            html_content += f"""
            <h2 style='color: #A3BE8C; border-bottom: 2px solid #A3BE8C; padding-bottom: 10px;'>
                🚨 Objeções Tratadas
            </h2>
            """

            objections = summary.get('objections', [])
            if objections:
                for obj in objections:
                    handled_icon = "✅" if obj.get('handled', False) else "❌"
                    type_text = obj.get('type', 'N/A').upper()
                    note_text = obj.get('note', '')
                    html_content += f"<p style='margin: 10px 0;'>{handled_icon} <strong>{type_text}</strong>: {note_text}</p>"
            else:
                html_content += "<p style='color: #888888;'>Nenhuma objeção detectada</p>"

            html_content += "<br>"

            # Próximos passos
            html_content += f"""
            <h2 style='color: #EBCB8B; border-bottom: 2px solid #EBCB8B; padding-bottom: 10px;'>
                📝 Próximos Passos
            </h2>
            """

            next_steps = summary.get('next_steps', [])
            if next_steps:
                for step in next_steps:
                    desc = step.get('desc', '')
                    due = f" (até {step.get('due', 'N/A')})" if step.get('due') else ""
                    owner = f" - {step.get('owner', '')}" if step.get('owner') else ""
                    html_content += f"<p style='margin: 10px 0;'>• {desc}{due}{owner}</p>"
            else:
                html_content += "<p style='color: #888888;'>Nenhum próximo passo definido</p>"

            html_content += "<br>"

            # Métricas
            html_content += f"""
            <h2 style='color: #D08770; border-bottom: 2px solid #D08770; padding-bottom: 10px;'>
                📊 Métricas da Chamada
            </h2>
            """

            metrics = summary.get('metrics', {})
            if metrics:
                html_content += f"""
                <p style='margin: 8px 0;'>⏱️ <strong>Tempo de fala vendedor:</strong> {metrics.get('talk_time_vendor_pct', 0):.1f}%</p>
                <p style='margin: 8px 0;'>🎤 <strong>Tempo de fala cliente:</strong> {metrics.get('talk_time_client_pct', 0):.1f}%</p>
                <p style='margin: 8px 0;'>😊 <strong>Sentimento médio:</strong> {metrics.get('sentiment_avg', 0):.2f}</p>
                <p style='margin: 8px 0;'>🚨 <strong>Objeções totais:</strong> {metrics.get('objections_total', 0)}</p>
                <p style='margin: 8px 0;'>✅ <strong>Objeções resolvidas:</strong> {metrics.get('objections_resolved', 0)}</p>
                <p style='margin: 8px 0;'>💰 <strong>Sinais de compra:</strong> {metrics.get('buying_signals', 0)}</p>
                """
            else:
                html_content += "<p style='color: #888888;'>Métricas não disponíveis</p>"

            # Insights
            insights = summary.get('insights', {})
            if insights:
                html_content += "<br>"
                html_content += f"""
                <h2 style='color: #B48EAD; border-bottom: 2px solid #B48EAD; padding-bottom: 10px;'>
                    💡 Insights Estratégicos
                </h2>
                <p style='margin: 8px 0;'>🎯 <strong>Interesse do cliente:</strong> {insights.get('cliente_interesse', 'N/A')}</p>
                <p style='margin: 8px 0;'>⏰ <strong>Urgência:</strong> {insights.get('urgencia', 'N/A')}</p>
                <p style='margin: 8px 0;'>👤 <strong>Autoridade de decisão:</strong> {insights.get('autoridade_decisao', 'N/A')}</p>
                <p style='margin: 8px 0;'>🎪 <strong>Próxima ação recomendada:</strong> {insights.get('proxima_acao_recomendada', 'N/A')}</p>
                """

            html_content += "</div>"

            self.summary_text.setHtml(html_content)

        except Exception as e:
            print(f"❌ Erro ao formatar resumo: {e}")
            self._show_error_summary(str(e))

    def _show_example_summary(self):
        """Mostrar resumo de exemplo."""
        example_summary = {
            "key_points": [
                "Cliente demonstrou interesse na solução",
                "Discutiu integração com sistema legado",
                "Mencionou necessidade de suporte técnico"
            ],
            "objections": [
                {"type": "preco", "handled": True, "note": "Explicado ROI de 340% em 18 meses"},
                {"type": "timeline", "handled": False, "note": "Cliente precisa aprovar com equipe técnica"}
            ],
            "next_steps": [
                {"desc": "Enviar proposta técnica detalhada", "due": "2025-01-17", "owner": "vendedor"},
                {"desc": "Agendar demonstração para equipe técnica", "due": "2025-01-24", "owner": "vendedor"},
                {"desc": "Preparar case study similar", "due": "2025-01-18", "owner": "vendedor"}
            ],
            "metrics": {
                "talk_time_vendor_pct": 55.0,
                "talk_time_client_pct": 45.0,
                "sentiment_avg": 0.75,
                "objections_total": 2,
                "objections_resolved": 1,
                "buying_signals": 3
            },
            "insights": {
                "cliente_interesse": "alto",
                "urgencia": "media",
                "autoridade_decisao": "influenciador",
                "proxima_acao_recomendada": "demo"
            }
        }
        self._format_and_display_summary(example_summary)

    def _show_error_summary(self, error_msg: str):
        """Mostrar mensagem de erro."""
        error_html = f"""
        <div style='color: #BF616A; font-size: 16px; text-align: center; margin-top: 50px;'>
            <h2>❌ Erro ao carregar resumo</h2>
            <p>{error_msg}</p>
            <p style='color: #888888; font-size: 14px;'>Tente gerar o resumo novamente.</p>
        </div>
        """
        self.summary_text.setHtml(error_html)

    def _export_markdown(self):
        """Exportar resumo em formato Markdown."""
        if not self.current_summary:
            print("⚠️ Nenhum resumo disponível para exportar")
            return

        try:
            # Gerar conteúdo Markdown
            md_content = self._generate_markdown_content(self.current_summary)

            # Salvar arquivo
            from PyQt6.QtWidgets import QFileDialog
            file_name, _ = QFileDialog.getSaveFileName(
                self, "Salvar Resumo", "", "Markdown Files (*.md);;All Files (*)"
            )

            if file_name:
                with open(file_name, 'w', encoding='utf-8') as f:
                    f.write(md_content)
                print(f"✅ Resumo salvo em: {file_name}")

        except Exception as e:
            print(f"❌ Erro ao exportar Markdown: {e}")

    def _export_pdf(self):
        """Exportar resumo em formato PDF."""
        print("📄 Exportar PDF - Função em desenvolvimento")

    def _save_to_history(self):
        """Salvar resumo no histórico."""
        print("💾 Salvar no histórico - Função em desenvolvimento")

    def _generate_markdown_content(self, summary) -> str:
        """Gerar conteúdo Markdown do resumo."""
        md = "# 📋 Resumo da Reunião\n\n"

        # Pontos principais
        md += "## 🎯 Pontos Principais\n"
        for point in summary.get('key_points', []):
            md += f"- {point}\n"
        md += "\n"

        # Objeções
        md += "## 🚨 Objeções Tratadas\n"
        for obj in summary.get('objections', []):
            status = "✅" if obj.get('handled') else "❌"
            md += f"- {status} **{obj.get('type', '').upper()}**: {obj.get('note', '')}\n"
        md += "\n"

        # Próximos passos
        md += "## 📝 Próximos Passos\n"
        for step in summary.get('next_steps', []):
            due = f" (até {step.get('due')})" if step.get('due') else ""
            owner = f" - {step.get('owner')}" if step.get('owner') else ""
            md += f"- [ ] {step.get('desc', '')}{due}{owner}\n"
        md += "\n"

        # Métricas
        md += "## 📊 Métricas da Chamada\n"
        metrics = summary.get('metrics', {})
        md += f"- ⏱️ Tempo de fala vendedor: {metrics.get('talk_time_vendor_pct', 0):.1f}%\n"
        md += f"- 🎤 Tempo de fala cliente: {metrics.get('talk_time_client_pct', 0):.1f}%\n"
        md += f"- 😊 Sentimento médio: {metrics.get('sentiment_avg', 0):.2f}\n"
        md += f"- 🚨 Objeções totais: {metrics.get('objections_total', 0)}\n"
        md += f"- ✅ Objeções resolvidas: {metrics.get('objections_resolved', 0)}\n"
        md += f"- 💰 Sinais de compra: {metrics.get('buying_signals', 0)}\n\n"

        # Insights
        insights = summary.get('insights', {})
        if insights:
            md += "## 💡 Insights Estratégicos\n"
            md += f"- 🎯 Interesse do cliente: {insights.get('cliente_interesse', 'N/A')}\n"
            md += f"- ⏰ Urgência: {insights.get('urgencia', 'N/A')}\n"
            md += f"- 👤 Autoridade de decisão: {insights.get('autoridade_decisao', 'N/A')}\n"
            md += f"- 🎪 Próxima ação recomendada: {insights.get('proxima_acao_recomendada', 'N/A')}\n"

        return md
