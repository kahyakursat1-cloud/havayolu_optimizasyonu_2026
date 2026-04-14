import os
from llama_cpp import Llama
import logging
from datetime import datetime

# v34.0: Cognitive Narrative Intelligence (Shikra Intercept)
# Powering the "Chief Aviation Officer" persona locally

logger = logging.getLogger("AviationSingularity.Gemma")

class CognitiveNarrator:
    def __init__(self, model_path="assets/models/gemma-2-2b-it-Q4_K_M.gguf"):
        self.model_path = model_path
        self.llm = None
        self.is_ready = False
        
        if os.path.exists(self.model_path):
            try:
                # v35.2: Expanded context for longer operational reports
                self.llm = Llama(
                    model_path=self.model_path,
                    n_ctx=2048, 
                    n_threads=2, 
                    verbose=False
                )
                self.is_ready = True
                logger.info("✅ Gemma-2-2B Cognitive Brain Loaded Successfully.")
            except Exception as e:
                logger.error(f"❌ Failed to load Gemma model: {str(e)}")
        else:
            logger.warning(f"⚠️ Gemma model not found at {self.model_path}. Briefing disabled.")

    def generate_briefing(self, flight_summary, stats, seed=None):
        """
        v35.1: Enhanced Creativity - Generates a tactical report with randomization.
        """
        if not self.is_ready or not self.llm:
            return "Cognitive Narrative Offline: Model not loaded."

        # Randomize seed if not provided to bypass repetitive patterns
        current_seed = seed if seed is not None else -1
        
        prompt = f"<start_of_turn>user\n" \
                 f"Sistem Zamanı: {datetime.now().strftime('%H:%M:%S')}\n" \
                 f"Sistem Durumu: {stats}\n" \
                 f"Kritik Uçuşlar: {flight_summary}\n\n" \
                 f"Görevin: Bir Baş Pilot (Chief Pilot) olarak bu verileri profesyonel, " \
                 f"kısa ve etkileyici bir operasyonel brifinge dönüştür. Her raporda farklı bir " \
                 f"stratejik perspektife odaklan. Sadece Türkçe konuş.\n<end_of_turn>\n" \
                 f"<start_of_turn>model\n"

        try:
            output = self.llm(
                prompt,
                max_tokens=512, # v35.2: Higher ceiling for complete narratives
                temperature=0.7, # v35.1: Increased for variety
                stop=["<end_of_turn>", "user", "model"],
                echo=False,
                seed=current_seed # v35.1: Random seed integration
            )
            return output['choices'][0]['text'].strip()
        except Exception as e:
            return f"Strategic Briefing Error: {str(e)}"

    def analyze_hypothetical(self, query, scenario_results, stats):
        """
        v21.0 Agentic DSS: Analyzes the delta between current and hypothetical regimes.
        """
        if not self.is_ready or not self.llm:
            return "Cognitive Brain Offline."

        prompt = f"<start_of_turn>user\n" \
                 f"Soru/Senaryo: {query}\n" \
                 f"Mevcut Filo Analizi: {stats}\n" \
                 f"Optimizasyon Çıktısı: {scenario_results[:500]}...\n\n" \
                 f"Görevin: Bu 'Farazi' (What-if) senaryoyu analiz et. Havayolu üzerindeki " \
                 f"stratejik etkilerini, risklerini ve çözüm önerilerini Baş Pilot diliyle anlat. " \
                 f"Jürinin beklediği profesyonel derinlikte bir yanıt ver. Sadece Türkçe.\n<end_of_turn>\n" \
                 f"<start_of_turn>model\n"

        try:
            output = self.llm(prompt, max_tokens=1024, temperature=0.5)
            return output['choices'][0]['text'].strip()
        except Exception as e:
            return f"What-If Analysis Error: {str(e)}"

# Singleton Instance for Global Access
narrator = CognitiveNarrator()
