"""
Prosody Analyzer - RF-3.2: Motor de prosódia (áudio)
==================================================

Análise de prosódia para extrair sentimento e engajamento da voz.
"""

import logging
import numpy as np
from typing import List, Dict, Any, Optional
from scipy import signal
from scipy.stats import linregress

try:
    import onnxruntime as ort
    ONNX_AVAILABLE = True
except ImportError:
    ONNX_AVAILABLE = False
    print("⚠️ ONNX Runtime não disponível. Usando simulação.")

from .models import ProsodyFeatures, SentimentConfig


class ProsodyAnalyzer:
    """RF-3.2: Motor de prosódia (áudio)"""
    
    def __init__(self, config: SentimentConfig = None, model_manager=None):
        self.config = config or SentimentConfig()
        self.model_manager = model_manager
        self.logger = logging.getLogger(__name__)
        
        # Modelo ONNX para classificação de prosódia
        self.prosody_session = None
        
        # Configurações de análise
        self.sample_rate = 16000
        self.frame_length = int(0.025 * self.sample_rate)  # 25ms
        self.hop_length = int(0.010 * self.sample_rate)    # 10ms
        
        # Inicializar
        self._initialize_model()
    
    def _initialize_model(self):
        """Inicializar modelo de prosódia."""
        try:
            if not ONNX_AVAILABLE:
                self.logger.warning("ONNX não disponível, usando simulação")
                return
            
            # Tentar carregar via ModelManager
            if self.model_manager:
                self.prosody_session = self.model_manager.get_session("prosody_classifier")
                if self.prosody_session:
                    self.logger.info("✅ Modelo de prosódia carregado via ModelManager")
                    return
            
            # Fallback para carregamento manual
            model_path = "models/prosody_classifier.onnx"
            providers = ["QNNExecutionProvider", "CPUExecutionProvider"]
            
            try:
                self.prosody_session = ort.InferenceSession(model_path, providers=providers)
                self.logger.info(f"✅ Modelo de prosódia carregado: {model_path}")
            except Exception as e:
                self.logger.warning(f"⚠️ Erro ao carregar modelo: {e}")
                
        except Exception as e:
            self.logger.error(f"❌ Erro na inicialização do modelo: {e}")
    
    def extract_features(self, audio: np.ndarray) -> ProsodyFeatures:
        """Extrair F0, energia, ritmo."""
        try:
            # Normalizar áudio
            if audio.dtype == np.int16:
                audio = audio.astype(np.float32) / 32768.0
            
            # Extrair features
            f0_mean, f0_std = self._extract_f0(audio)
            energy_mean, energy_std = self._extract_energy(audio)
            speaking_rate = self._extract_speaking_rate(audio)
            pause_ratio = self._extract_pause_ratio(audio)
            jitter = self._extract_jitter(audio)
            shimmer = self._extract_shimmer(audio)
            
            features = ProsodyFeatures(
                f0_mean=f0_mean,
                f0_std=f0_std,
                energy_mean=energy_mean,
                energy_std=energy_std,
                speaking_rate=speaking_rate,
                pause_ratio=pause_ratio,
                jitter=jitter,
                shimmer=shimmer
            )
            
            return features
            
        except Exception as e:
            self.logger.error(f"Erro na extração de features: {e}")
            return ProsodyFeatures()
    
    def _extract_f0(self, audio: np.ndarray) -> tuple[float, float]:
        """Extrair frequência fundamental (F0)."""
        try:
            # Usar autocorrelação para estimar F0
            # Janela de análise para F0
            window_size = int(0.040 * self.sample_rate)  # 40ms
            hop_size = int(0.010 * self.sample_rate)     # 10ms
            
            f0_values = []
            
            for i in range(0, len(audio) - window_size, hop_size):
                window = audio[i:i + window_size]
                
                # Aplicar janela de Hamming
                window = window * np.hamming(len(window))
                
                # Autocorrelação
                autocorr = np.correlate(window, window, mode='full')
                autocorr = autocorr[len(autocorr)//2:]
                
                # Encontrar pico principal (excluindo lag 0)
                peaks = signal.find_peaks(autocorr[20:], height=0.1*np.max(autocorr))[0]
                
                if len(peaks) > 0:
                    # Converter lag para frequência
                    lag = peaks[0] + 20
                    f0 = self.sample_rate / lag
                    
                    # Filtrar valores razoáveis (80-400 Hz)
                    if 80 <= f0 <= 400:
                        f0_values.append(f0)
            
            if f0_values:
                return np.mean(f0_values), np.std(f0_values)
            else:
                return 150.0, 50.0  # valores padrão
                
        except Exception as e:
            self.logger.warning(f"Erro na extração F0: {e}")
            return 150.0, 50.0
    
    def _extract_energy(self, audio: np.ndarray) -> tuple[float, float]:
        """Extrair energia do sinal."""
        try:
            # Energia RMS por frame
            frame_length = int(0.025 * self.sample_rate)  # 25ms
            hop_length = int(0.010 * self.sample_rate)    # 10ms
            
            energies = []
            
            for i in range(0, len(audio) - frame_length, hop_length):
                frame = audio[i:i + frame_length]
                energy = np.sqrt(np.mean(frame**2))
                energies.append(energy)
            
            if energies:
                return np.mean(energies), np.std(energies)
            else:
                return 0.1, 0.05
                
        except Exception as e:
            self.logger.warning(f"Erro na extração de energia: {e}")
            return 0.1, 0.05
    
    def _extract_speaking_rate(self, audio: np.ndarray) -> float:
        """Estimar taxa de fala (sílabas/segundo)."""
        try:
            # Detectar atividade de voz usando energia
            frame_length = int(0.025 * self.sample_rate)
            hop_length = int(0.010 * self.sample_rate)
            
            voice_activity = []
            
            for i in range(0, len(audio) - frame_length, hop_length):
                frame = audio[i:i + frame_length]
                energy = np.sqrt(np.mean(frame**2))
                
                # Threshold para atividade de voz
                threshold = 0.01
                voice_activity.append(energy > threshold)
            
            if voice_activity:
                # Calcular proporção de frames com voz
                voice_ratio = np.mean(voice_activity)
                
                # Estimar sílabas por segundo (aproximação)
                # Assumindo ~5 sílabas por segundo em fala normal
                speaking_rate = voice_ratio * 5.0
                
                return np.clip(speaking_rate, 0.5, 10.0)
            else:
                return 3.0
                
        except Exception as e:
            self.logger.warning(f"Erro na extração de taxa de fala: {e}")
            return 3.0
    
    def _extract_pause_ratio(self, audio: np.ndarray) -> float:
        """Calcular proporção de pausas."""
        try:
            # Detectar pausas usando energia baixa
            frame_length = int(0.025 * self.sample_rate)
            hop_length = int(0.010 * self.sample_rate)
            
            pause_frames = 0
            total_frames = 0
            
            for i in range(0, len(audio) - frame_length, hop_length):
                frame = audio[i:i + frame_length]
                energy = np.sqrt(np.mean(frame**2))
                
                # Threshold para pausa
                pause_threshold = 0.005
                if energy < pause_threshold:
                    pause_frames += 1
                
                total_frames += 1
            
            if total_frames > 0:
                return pause_frames / total_frames
            else:
                return 0.3
                
        except Exception as e:
            self.logger.warning(f"Erro na extração de pausas: {e}")
            return 0.3
    
    def _extract_jitter(self, audio: np.ndarray) -> float:
        """Calcular jitter (variação de F0)."""
        try:
            # Extrair F0 em múltiplos pontos
            window_size = int(0.040 * self.sample_rate)
            hop_size = int(0.010 * self.sample_rate)
            
            f0_values = []
            
            for i in range(0, len(audio) - window_size, hop_size):
                window = audio[i:i + window_size]
                window = window * np.hamming(len(window))
                
                autocorr = np.correlate(window, window, mode='full')
                autocorr = autocorr[len(autocorr)//2:]
                
                peaks = signal.find_peaks(autocorr[20:], height=0.1*np.max(autocorr))[0]
                
                if len(peaks) > 0:
                    lag = peaks[0] + 20
                    f0 = self.sample_rate / lag
                    
                    if 80 <= f0 <= 400:
                        f0_values.append(f0)
            
            if len(f0_values) > 1:
                # Calcular jitter como variação relativa
                f0_mean = np.mean(f0_values)
                jitter = np.std(f0_values) / f0_mean
                return np.clip(jitter, 0.0, 0.5)
            else:
                return 0.1
                
        except Exception as e:
            self.logger.warning(f"Erro na extração de jitter: {e}")
            return 0.1
    
    def _extract_shimmer(self, audio: np.ndarray) -> float:
        """Calcular shimmer (variação de amplitude)."""
        try:
            # Extrair amplitudes em múltiplos pontos
            frame_length = int(0.025 * self.sample_rate)
            hop_length = int(0.010 * self.sample_rate)
            
            amplitudes = []
            
            for i in range(0, len(audio) - frame_length, hop_length):
                frame = audio[i:i + frame_length]
                amplitude = np.max(np.abs(frame))
                amplitudes.append(amplitude)
            
            if len(amplitudes) > 1:
                # Calcular shimmer como variação relativa
                amp_mean = np.mean(amplitudes)
                shimmer = np.std(amplitudes) / amp_mean
                return np.clip(shimmer, 0.0, 0.5)
            else:
                return 0.1
                
        except Exception as e:
            self.logger.warning(f"Erro na extração de shimmer: {e}")
            return 0.1
    
    def classify_valence(self, features: ProsodyFeatures) -> float:
        """Classificar valência (-1 a +1)."""
        try:
            if self.prosody_session:
                # Usar modelo ONNX
                return self._classify_with_model(features)
            else:
                # Simulação baseada em features
                return self._simulate_valence(features)
                
        except Exception as e:
            self.logger.error(f"Erro na classificação de valência: {e}")
            return 0.0
    
    def _classify_with_model(self, features: ProsodyFeatures) -> float:
        """Classificação usando AnythingLLM."""
        try:
            if not hasattr(self, 'anythingllm_client') or not self.anythingllm_client:
                return self._simulate_valence(features)
            
            # Preparar descrição das features
            features_desc = f"""
            Features de prosódia:
            - F0 médio: {features.f0_mean:.2f} Hz
            - F0 std: {features.f0_std:.2f} Hz
            - Energia média: {features.energy_mean:.2f}
            - Energia std: {features.energy_std:.2f}
            - Taxa de fala: {features.speaking_rate:.2f} sílabas/s
            - Proporção de pausas: {features.pause_ratio:.2f}
            - Jitter: {features.jitter:.2f}
            - Shimmer: {features.shimmer:.2f}
            """
            
            # Prompt para análise de prosódia
            system_prompt = (
                "Você é um especialista em análise de prosódia. "
                "Analise as features vocais e retorne APENAS um número entre -1 e +1, "
                "onde -1 = sentimento negativo na voz, 0 = neutro, +1 = positivo. "
                "Considere: F0 alto = excitação, energia alta = engajamento, etc. "
                "Exemplo: 0.6"
            )
            
            user_prompt = f"{features_desc}\n\nSentimento da voz (-1 a +1):"
            
            # Configurar payload
            payload = {
                "model": self.anythingllm_client.default_model,
                "temperature": 0.1,
                "stream": False,
                "max_tokens": 10,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ]
            }
            
            # Fazer requisição
            response = self.anythingllm_client._make_request(payload, stream=False)
            
            if response.status_code != 200:
                return self._simulate_valence(features)
            
            # Processar resposta
            data = response.json()
            content = data['choices'][0]['message']['content'].strip()
            
            # Parsear número
            try:
                score = float(content)
                return np.clip(score, -1.0, 1.0)
            except ValueError:
                return self._simulate_valence(features)
                
        except Exception as e:
            self.logger.error(f"Erro na análise de prosódia com AnythingLLM: {e}")
            return self._simulate_valence(features)
    
    def _simulate_valence(self, features: ProsodyFeatures) -> float:
        """Simular classificação de valência baseada em features."""
        valence_score = 0.0
        
        # F0 alto = mais positivo
        f0_factor = (features.f0_mean - 150) / 100  # normalizar
        valence_score += np.clip(f0_factor * 0.3, -0.3, 0.3)
        
        # Energia alta = mais positivo
        energy_factor = (features.energy_mean - 0.1) / 0.1  # normalizar
        valence_score += np.clip(energy_factor * 0.2, -0.2, 0.2)
        
        # Taxa de fala moderada = mais positivo
        rate_factor = (features.speaking_rate - 3.0) / 2.0  # normalizar
        valence_score += np.clip(rate_factor * 0.1, -0.1, 0.1)
        
        # Menos pausas = mais positivo
        pause_factor = (0.3 - features.pause_ratio) / 0.3  # normalizar
        valence_score += np.clip(pause_factor * 0.2, -0.2, 0.2)
        
        # Menos jitter = mais positivo
        jitter_factor = (0.1 - features.jitter) / 0.1  # normalizar
        valence_score += np.clip(jitter_factor * 0.2, -0.2, 0.2)
        
        return np.clip(valence_score, -1.0, 1.0)
    
    def detect_micro_expressions(self, features: ProsodyFeatures) -> List[str]:
        """Detectar micro-expressões vocais."""
        expressions = []
        
        # Hesitação (muitas pausas + jitter alto)
        if features.pause_ratio > 0.4 and features.jitter > 0.2:
            expressions.append("hesitation")
        
        # Ênfase (energia alta + F0 variável)
        if features.energy_mean > 0.15 and features.f0_std > 60:
            expressions.append("emphasis")
        
        # Nervosismo (jitter alto + shimmer alto)
        if features.jitter > 0.25 and features.shimmer > 0.25:
            expressions.append("nervousness")
        
        # Confiança (F0 estável + energia consistente)
        if features.jitter < 0.1 and features.energy_std < 0.05:
            expressions.append("confidence")
        
        # Interesse (taxa de fala moderada + poucas pausas)
        if 2.5 <= features.speaking_rate <= 4.5 and features.pause_ratio < 0.25:
            expressions.append("interest")
        
        return expressions
    
    def analyze_audio_chunk(self, audio: np.ndarray, ts_start_ms: int, ts_end_ms: int) -> Dict[str, Any]:
        """Análise completa de um chunk de áudio."""
        features = self.extract_features(audio)
        valence = self.classify_valence(features)
        micro_expressions = self.detect_micro_expressions(features)
        
        return {
            "valence": valence,
            "features": features,
            "micro_expressions": micro_expressions,
            "ts_start_ms": ts_start_ms,
            "ts_end_ms": ts_end_ms,
            "audio_length": len(audio)
        } 