import json
import logging
from typing import Dict, Any, List, Optional
import pandas as pd

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from google.api_core.exceptions import ResourceExhausted

from app.infrastructure.services.model_rotation_service import ModelRotationService

EVALUATION_PROMPT_TEMPLATE = """
Anda adalah seorang evaluator metrik AI yang sangat teliti dan objektif. Tugas Anda adalah menilai kualitas rangkuman berdasarkan beberapa kriteria.

[PERTANYAAN PENGGUNA]:
---
{user_prompt}
---

[DATA SUMBER]:
---
{source_document}
---

[RANGKUMAN YANG DIUJI]:
---
{summary_to_evaluate}
---

INSTRUKSI EVALUASI:
1.  **Akurasi Faktual (Factual Accuracy)**:
    - **FOKUS UTAMA**: Verifikasi apakah **entitas utama** (seperti nama aset) yang disebutkan dalam rangkuman **benar-benar ada** di [DATA SUMBER].
    - **PENILAIAN**:
        - Jika sebuah aset yang disebutkan dalam rangkuman TIDAK ADA di [DATA SUMBER], maka itu adalah kesalahan faktual (`is_correct: false`).
        - Jika detail dari sebuah aset (seperti nilai, PIC, atau kondisi) dalam rangkuman **berbeda** dengan [DATA SUMBER], JANGAN tandai sebagai kesalahan faktual, tetapi catat perbedaan tersebut di `notes`.
    - Tentukan `is_correct` menjadi `true` selama semua entitas utama yang disebutkan ada di data sumber.

2.  **Kelengkapan (Completeness Score)**:
    - Seberapa baik rangkuman menjawab inti pertanyaan pengguna? Apakah informasi paling vital dari [DATA SUMBER] sudah disertakan?
    - Beri skor dari 1 (tidak lengkap) hingga 5 (sangat lengkap).

3.  **Relevansi (Relevance Score)**:
    - Apakah rangkuman fokus pada apa yang ditanyakan? Apakah ada informasi yang tidak relevan?
    - Beri skor dari 1 (tidak relevan) hingga 5 (sangat relevan).
    - **PENTING**: Abaikan "Opsi Selanjutnya" dan kalimat percakapan saat menilai relevansi.

4.  **Skor Akhir (Final Score)**:
    - Hitung skor akhir sebagai rata-rata. Asumsikan skor akurasi faktual adalah 1.0 jika `is_correct` true, dan 0.0 jika false.
    - Rumus: `(Skor Akurasi Faktual + (Skor Kelengkapan / 5) + (Skor Relevansi / 5)) / 3`. Bulatkan ke 2 desimal.

5.  **OUTPUT**: Jawab HANYA dalam format JSON yang valid.

FORMAT JSON OUTPUT:
{{
  "factual_accuracy": {{
    "is_correct": <true atau false, berdasarkan keberadaan entitas>,
    "notes": ["Catat di sini jika ada detail yang berbeda, contoh: 'Nilai Aset ROUTER CORE berbeda antara rangkuman dan sumber data.' Kosongkan jika semua detail cocok."]
  }},
  "completeness_score": <integer 1-5>,
  "relevance_score": <integer 1-5>,
  "final_score": <float 0.0-1.0>,
  "reasoning": "Penjelasan singkat mengenai alasan di balik semua skor yang Anda berikan."
}}
"""

class DocumentAnalyzer:
    """
    Service yang bertanggung jawab untuk interaksi dengan LLM,
    dengan rotasi otomatis model dan API key untuk mengatasi quota limits.
    """
    COL_NO_ASET = 'NO ASSET'

    def __init__(self):
        """Menginisialisasi model rotation service."""
        self.rotation_service = ModelRotationService()
        self.model = None
        self.eval_model = None # Tambahkan instance khusus evaluasi
        self._initialize_model()

    def _initialize_model(self):
        """Inisialisasi model dengan config saat ini."""
        # PERBAIKAN: Gunakan get_current_api_key() untuk mendapatkan string API key
        model_name, _ = self.rotation_service.get_current_config()
        api_key = self.rotation_service.get_current_api_key()
        
        if not api_key:
            raise ValueError("GEMINI_API_KEY tidak ditemukan di environment variables.")
        
        self.model = ChatGoogleGenerativeAI(
            model=model_name,
            google_api_key=api_key,
            temperature=0.1,
        )

        self.eval_model = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash-lite", # Paksa pakai Lite
            google_api_key=api_key,
            temperature=0.1,
        )
        
        logging.info(f"Models initialized. Main: {model_name}, Eval: gemini-2.5-flash-lite")

    def _execute_with_rotation(self, chain, invoke_params: Dict, max_retries: int = 3, is_eval: bool = False) -> str:
        """
        Eksekusi chain dengan auto-rotation. 
        Mendukung pemilihan model antara Main Model atau Eval Model saat retry.
        """
        retries = 0
        
        while retries < max_retries:
            try:
                # Ambil config untuk logging saja
                model_name, key_idx = self.rotation_service.get_current_config()
                logging.debug(f"Using Model: {model_name}, API Key: #{key_idx + 1} (Eval Mode: {is_eval})")
                
                # Eksekusi chain yang sudah dikirim
                result = chain.invoke(invoke_params)
                
                # Jika berhasil, geser counter
                self.rotation_service.increment_and_rotate()
                
                return result
                
            except ResourceExhausted as e:
                logging.error("="*80)
                logging.error(f"RESOURCE EXHAUSTED ERROR (Attempt {retries + 1}/{max_retries})")
                logging.error("="*80)
                
                # 1. Geser ke API Key berikutnya
                self.rotation_service.force_rotate_on_error(e)
                
                # 2. Re-initialize kedua model (Main & Eval) dengan API Key baru
                self._initialize_model()
                
                # 3. PERBAIKAN: Pilih model yang tepat untuk membangun ulang chain
                current_model = self.eval_model if is_eval else self.model
                
                if hasattr(chain, 'first') and hasattr(chain.first, 'template'):
                    # Jika chain menggunakan prompt template
                    template = chain.first.template
                    prompt = ChatPromptTemplate.from_template(template)
                    chain = prompt | current_model | StrOutputParser()
                
                retries += 1
                
                if retries >= max_retries:
                    raise ValueError("Semua API key telah mencapai batas quota.")
                
                logging.info(f"Retrying with new config...")
        
        raise ValueError("Unexpected error in rotation logic")

    async def decide_tool_to_use(
        self, 
        user_prompt: str, 
        tools: List[Dict], 
        conversation_history: Optional[List[Dict]] = None, 
        resources: Optional[List[Dict]] = None
    ) -> str:
        """
        Meminta LLM untuk memilih tool dengan rotasi otomatis.
        """
        history_text = json.dumps(conversation_history, indent=2, ensure_ascii=False)
        tools_as_text = json.dumps(tools, indent=2)
        resources_as_text = json.dumps(resources, indent=2)

        template = """
        Anda adalah AI router cerdas untuk Sistem Manajemen Aset Pertamina Hulu Rokan (PHR).
        
        PENGETAHUAN DOMAIN KHUSUS (Domain Knowledge Mapping):
        
        1. MAPPING LOKASI:
           - Jika user menyebut "Dumai" atau "Pesisir" atau "Bengkalis", maka area yang dimaksud adalah "COASTAL" atau "BENGKALIS".
           - Jika user menyebut "Duri" atau "Rokan", maka area yang dimaksud adalah "DURI".
           - Jika user menyebut "Minas", maka area yang dimaksud adalah "MINAS".
           - CATATAN PENTING: Database tidak memiliki area literal bernama "Dumai", jadi harus dipetakan ke "COASTAL" atau "BENGKALIS".
        
        2. MAPPING KONDISI ASET:
           - Jika user hanya menyebut "Rusak" tanpa spesifikasi, maka kondisi yang dimaksud bisa "Rusak Berat" ATAU "Rusak Ringan".
           - Anda HARUS menanyakan klarifikasi kepada user: "Apakah yang Anda maksud Rusak Berat, Rusak Ringan, atau keduanya?"
           - Jika user menyebut "Ilang" atau "Tidak ada" atau "Hilang", maka kondisi yang dimaksud adalah "Tidak Ditemukan".
           - Kondisi valid lainnya: "Baik", "Digunakan", "Cadangan", "Penghapusan".

        3. MAPPING STATUS INVENTARIS:
           - Jika user bertanya tentang "Tidak Ditemukan", ini biasanya merujuk pada kolom KONDISI.
           - Kolom HASIL INVENTORY biasanya hanya berisi "Match" atau "Not Match".
           - Jika user bertanya: "Aset yang hasil inventarisnya Tidak Ditemukan", maka Router HARUS mengisi argumen:
              {{"kondisi": "Tidak Ditemukan", "task": "filter"}} 
        
        4. LOGIKA PERBANDINGAN:
           - Jika user meminta perbandingan antara dua atau lebih entitas (misal: "Bandingkan lokasi A dan B"), Anda HARUS menggabungkan nilai tersebut dalam satu parameter menggunakan koma.
           - Contoh: "kode_lokasi_sap": "ROKFLDOFC, INDFLDOFC", "task": "get_distribution_analysis", "group_by_field": "KODE LOKASI SAP"
           - Ini jauh lebih efisien daripada memanggil tool berkali-kali.

        5. ASET LAMA/TUA:
           - Jika user menyebut "Aset tua" atau "Aset lama", gunakan filter tahun pembelian sebelum 2015 (jika kolom tersedia).

        RIWAYAT PERCAKAPAN:
        {history}

        PERTANYAAN TERBARU PENGGUNA:
        "{user_prompt}"

        TOOL YANG TERSEDIA:
        {tools_text}

        RESOURCE (FILE HASIL ANALISIS) YANG TERSEDIA:
        {resources_text}

        INSTRUKSI UTAMA:
        1.  Analisis **PERTANYAAN PENGGUNA** dan gunakan **RIWAYAT** untuk konteks.
        2.  **TERAPKAN PENGETAHUAN DOMAIN**: 
            - Jika pertanyaan menyebut "Dumai", jangan cari literal "Dumai" di database, tetapi peta ke "COASTAL" atau "BENGKALIS".
            - Jika pertanyaan hanya menyebut "Rusak", WAJIB minta klarifikasi atau sertakan KEDUA jenis rusak ("Rusak Berat, Rusak Ringan") dalam argumen.
        3.  **PRIORITAS PERTAMA:** Periksa apakah pertanyaan merujuk pada salah satu **RESOURCE** yang tersedia (misalnya dengan menyebutkan nama sheet seperti 'q2y2025' atau 'laporan sebelumnya').
        4.  PILIH TOOL:
            - Jika pertanyaan merujuk pada sebuah RESOURCE, **WAJIB** gunakan tool `query_resource`. Temukan `resource_name` yang paling cocok dari daftar.
            - Jika pertanyaan bersifat umum dan tidak merujuk pada resource, gunakan tool `query_assets`.
            - Jika pertanyaan tentang "rusak" saja tanpa spesifikasi, sertakan argumen kondisi: "Rusak Berat, Rusak Ringan".
        5.  Anda HARUS merespons HANYA dengan format JSON yang valid.

        ATURAN PRIORITAS TOOL:
        1. JANGAN PERNAH gunakan 'trigger_analysis' untuk menjawab pertanyaan spesifik atau meminta insight di dalam chat. 
        2. 'trigger_analysis' HANYA digunakan jika user secara eksplisit meminta "Jalankan analisis ulang", "Refresh dashboard", atau "Analisis sheet baru".
        3. Untuk pertanyaan tentang "insight", "kesimpulan", "distribusi", atau "ringkasan data", GUNAKAN tool 'query_assets' dengan task 'get_distribution_analysis' atau 'get_top_values'.
        4. Jika user bertanya "Apa kesimpulan data ini?", gunakan 'query_assets' untuk mengambil statistik umum (seperti distribusi kondisi aset), lalu simpulkan sendiri hasilnya.

        CONTOH:
        - Tanya: "Berikan 3 insight utama."
        - Router: {{ "tool_name": "query_assets", "arguments": {{ "task": "get_distribution_analysis", "group_by_field": "KONDISI" }} }}
        
        LOGIKA AGREGASI LANJUTAN:
        1. Jika user bertanya "Apa [X] paling banyak di setiap [Y]?" (Contoh: Apa nama aset terbanyak di setiap area?):
            - Gunakan tool: 'query_assets'
            - Task: 'get_top_per_group'
            - group_by_field: '[Y]' (misal: AREA)
            - count_field: '[X]' (misal: NAMA ASET)
        2. JANGAN gunakan 'filter' biasa untuk pertanyaan ini karena hasilnya akan terlalu banyak dan tidak memberikan kesimpulan.

        CONTOH ALUR BERPIKIR:

        Contoh 1 - Mapping Lokasi:
        -   Pertanyaan: "Aset apa saja yang ada di Dumai?"
        -   Analisis: User menyebut "Dumai". Dari PENGETAHUAN DOMAIN, "Dumai" adalah bagian dari area "COASTAL" atau "BENGKALIS". Database tidak memiliki "Dumai" literal.
        -   Pilihan Tool: 'query_assets'
        -   JSON Respons: {{"tool_name": "query_assets", "arguments": {{"area": "COASTAL", "limit": 20}}}}

        Contoh 2 - Klarifikasi Kondisi Rusak:
        -   Pertanyaan: "Berapa jumlah aset rusak di Duri?"
        -   Analisis: User menyebut "rusak" tanpa spesifikasi. Harus mencakup "Rusak Berat" dan "Rusak Ringan". Area "Duri" sudah jelas.
        -   Pilihan Tool: 'query_assets'
        -   JSON Respons: {{"tool_name": "query_assets", "arguments": {{"area": "DURI", "kondisi": "Rusak Berat, Rusak Ringan", "task": "filter"}}}}

        Contoh 3 - Resource Spesifik:
        -   Pertanyaan: "dari laporan q2y2025, aset mana saja yang rusak?"
        -   Analisis: Pengguna menyebut 'q2y2025'. Di daftar RESOURCE, ada file "data_q2y2025_...json". Ini cocok.
        -   Pilihan Tool: 'query_resource'
        -   JSON Respons: {{"tool_name": "query_resource", "arguments": {{"resource_name": "data_q2y2025_20250816_133418.json", "kondisi": "Rusak Berat, Rusak Ringan"}}}}

        JSON Respons Anda:
        """
        
        prompt = ChatPromptTemplate.from_template(template)
        chain = prompt | self.model | StrOutputParser()

        llm_response = await self._execute_with_rotation_async(chain, {
            "history": history_text,
            "tools_text": tools_as_text,
            "resources_text": resources_as_text,
            "user_prompt": user_prompt
        })

        cleaned_response = llm_response.strip().replace("```json", "").replace("```", "").strip()
        return cleaned_response

    async def _execute_with_rotation_async(self, chain, invoke_params: Dict, max_retries: int = 3) -> str:
        """Async version of execute_with_rotation."""
        retries = 0
        
        while retries < max_retries:
            try:
                # PERBAIKAN: Gunakan key_idx yang benar (integer)
                model, key_idx = self.rotation_service.get_current_config()
                logging.debug(f"Using Model: {model}, API Key: #{key_idx + 1}")
                
                result = await chain.ainvoke(invoke_params)
                self.rotation_service.increment_and_rotate()
                return result
                
            except ResourceExhausted as e:
                logging.error("="*80)
                logging.error(f"RESOURCE EXHAUSTED ERROR (Attempt {retries + 1}/{max_retries})")
                logging.error(f"Error: {str(e)}")
                logging.error("="*80)
                
                self.rotation_service.force_rotate_on_error(e)
                self._initialize_model()
                
                # Rebuild chain
                template = list(invoke_params.values())[0] if invoke_params else ""
                prompt = ChatPromptTemplate.from_template(template)
                chain = prompt | self.model | StrOutputParser()
                
                retries += 1
                
                if retries >= max_retries:
                    logging.error("="*80)
                    logging.error("FATAL: All models and API keys exhausted!")
                    logging.error("="*80)
                    raise ValueError(
                        "Semua model dan API key telah mencapai batas quota. "
                        "Silakan coba lagi nanti atau tambahkan API key baru."
                    )
                
                logging.info(f"Retrying with new config...")

    async def summarize_tool_result(
        self, 
        user_prompt: str, 
        tool_result: str, 
        conversation_history: Optional[List[Dict]] = None
    ) -> str:
        """
        Meringkas hasil data mentah dari tool menjadi jawaban naratif.
        Setiap pemanggilan method ini = 2x LLM call (summary + evaluation).
        """
        history_text = json.dumps(conversation_history, indent=2, ensure_ascii=False)
        
        template = """
        ANDA ADALAH: Asisten AI yang sangat membantu untuk sistem manajemen aset Pertamina Hulu Rokan.
        
        LOGIKA PENANGANAN DATA KOSONG (Smart Empty Response):
        
        Jika HASIL DATA MENTAH berisi 'Tidak ada data' atau 'tidak ditemukan' atau kosong:
        1. Jangan langsung menyerah. Edukasi user tentang kemungkinan penyebabnya.
        2. Contoh kasus:
        - Jika user bertanya tentang "Dumai" dan tidak ada data: 
            Jelaskan bahwa "Dumai biasanya tercatat dalam sistem sebagai area COASTAL atau BENGKALIS. Mungkin Anda ingin mencoba mencari dengan kata kunci 'COASTAL' atau 'BENGKALIS'?"
        - Jika user bertanya tentang "Rusak" dan tidak ada data:
            Jelaskan bahwa "Sistem kami membedakan kondisi rusak menjadi dua kategori: Rusak Berat dan Rusak Ringan. Tidak ada data dengan kondisi 'Rusak' saja. Apakah Anda ingin melihat data Rusak Berat, Rusak Ringan, atau keduanya?"
        3. Berikan saran pencarian alternatif yang lebih spesifik dan sesuai dengan struktur database.
        4. Tetap ramah dan membantu, jangan terkesan menyalahkan user.
        
        RIWAYAT PERCAKAPAN (untuk konteks):
        {history}

        PERTANYAAN PENGGUNA: "{user_prompt}"
        
        HASIL DATA MENTAH DARI TOOL:
        ---
        {tool_result}
        ---

        TUGAS ANDA:
        1.  Berdasarkan RIWAYAT dan PERTANYAAN PENGGUNA, rangkum HASIL DATA menjadi jawaban yang relevan dan mudah dipahami.
        2.  Jika hasilnya kosong atau tidak ditemukan:
            - Terapkan LOGIKA PENANGANAN DATA KOSONG.
            - Berikan penjelasan edukatif tentang kemungkinan penyebabnya.
            - Tawarkan saran pencarian alternatif yang lebih tepat.
            - Jangan hanya bilang "tidak ada data", tetapi bantu user memahami kenapa dan apa yang bisa dilakukan.
        3.  Jika ada data, sajikan dengan jelas dan terstruktur.
        4.  Selalu akhiri dengan bagian "Opsi Selanjutnya:" yang memberikan 2-3 saran pertanyaan lanjutan yang relevan.
        
        ATURAN FORMAT SANGAT KETAT:
        -   Jawab HANYA dalam format teks biasa.
        -   JANGAN gunakan karakter `*` (asterisk) atau `**` (dobel asterisk) sama sekali. Untuk penekanan, gunakan HURUF KAPITAL jika perlu.
        -   Untuk daftar poin, selalu awali setiap baris dengan tanda hubung dan spasi (contoh: "- Item satu").
        -   Gunakan bahasa yang profesional namun tetap ramah dan membantu.

        ATURAN KETAT ANTI-HALUSINASI:
        1. HANYA gunakan data yang ada di bagian [HASIL DATA MENTAH DARI TOOL].
        2. JANGAN PERNAH menyertakan nomor aset, nama aset, atau detail lain yang berasal dari [RIWAYAT PERCAKAPAN] jika data tersebut tidak muncul di hasil tool terbaru.
        3. Jika data dari tool hanya berisi 5 aset padahal user minta 10, sebutkan hanya 5 saja. JANGAN mengarang sisanya.
        """
        
        prompt = ChatPromptTemplate.from_template(template)
        chain = prompt | self.model | StrOutputParser()

        print("\n" + "="*80)
        print(">>> LLM CALL #1: GENERATING SUMMARY")
        print("="*80)
        
        summary = await self._execute_with_rotation_async(chain, {
            "history": history_text,
            "user_prompt": user_prompt,
            "tool_result": tool_result
        })
        
        print(f">>> Summary created: {len(summary)} characters")
        print("-"*80)
        print(">>> LLM CALL #2: EVALUATING SUMMARY")
        print("-"*80)
        
        # Evaluation
        evaluation_result = self.evaluate_summary_factualness(
            source_document=tool_result,
            summary_to_evaluate=summary,
            user_prompt=user_prompt
        )
        
        print("\n" + "="*80)
        print(">>> EVALUATION RESULT:")
        print("="*80)
        is_correct = evaluation_result.get('factual_accuracy', {}).get('is_correct')
        print(f"Factual Accuracy: {'CORRECT ✓' if is_correct else 'INCORRECT ✗'}")
        print(f"Completeness: {evaluation_result.get('completeness_score', 'N/A')}/5")
        print(f"Relevance: {evaluation_result.get('relevance_score', 'N/A')}/5")
        print(f"Final Score: {evaluation_result.get('final_score', 'N/A')}")
        print(f"Reasoning: {evaluation_result.get('reasoning', 'N/A')}")
        print("="*80 + "\n")

        return summary

    def generate_summary(self, document_text: str) -> str:
        """
        Menghasilkan ringkasan eksekutif berbasis AI.
        Ini adalah LLM Call #1 untuk Trigger Analysis.
        """
        template = """
        ANDA ADALAH: Seorang Analis Aset senior di Pertamina Hulu Rokan.
        TUJUAN ANDA: Membuat ringkasan eksekutif singkat untuk manajemen.
        TUGAS: Buat bagian 'RINGKASAN EKSEKUTIF' berdasarkan data. Fokus pada metrik kunci: distribusi aset, kondisi kritis, dan potensi risiko. Sajikan dalam daftar bernomor (1., 2., dst.). JANGAN berikan rekomendasi. JANGAN gunakan markdown.
        DATA:
        ---
        {document}
        ---
        """
        prompt = ChatPromptTemplate.from_template(template)
        chain = prompt | self.model | StrOutputParser()
        
        # Log untuk tracking
        logging.info("="*80)
        logging.info("LLM CALL #1 (Dashboard Analysis): Generating Executive Summary...")
        logging.info("="*80)
        
        # Menggunakan rotasi untuk summary generation
        summary = self._execute_with_rotation(chain, {"document": document_text})
        
        logging.info(f"Executive Summary Generated (length: {len(summary)} chars)")
        
        return summary

    def evaluate_summary_factualness(
        self, 
        source_document: str, 
        summary_to_evaluate: str, 
        user_prompt: str
    ) -> Dict:
        """Mengevaluasi kebenaran faktual menggunakan Flash Lite."""
        print(">>> Calling LLM (Flash Lite) for evaluation...")
        
        evaluation_response_str = ""
        try:
            # Gunakan model Lite khusus evaluasi
            prompt = ChatPromptTemplate.from_template(EVALUATION_PROMPT_TEMPLATE)
            chain = prompt | self.eval_model | StrOutputParser()
            
            # Eksekusi dengan wrapper rotasi
            evaluation_response_str = self._execute_with_rotation(
                chain, 
                {
                    "source_document": source_document[:5000],
                    "summary_to_evaluate": summary_to_evaluate,
                    "user_prompt": user_prompt or "Tidak ada prompt.",
                    "prompt_template": EVALUATION_PROMPT_TEMPLATE 
                },
                is_eval=True 
            )

            # Pembersihan dan Parsing JSON
            cleaned_str = evaluation_response_str.strip()
            if cleaned_str.startswith("```json"):
                cleaned_str = cleaned_str[7:]
            if cleaned_str.endswith("```"):
                cleaned_str = cleaned_str[:-3]

            evaluation_json = json.loads(cleaned_str.strip())
            print(">>> JSON parsed successfully")
            return evaluation_json
            
        except json.JSONDecodeError as je:
            print(f">>> ERROR: Invalid JSON from LLM")
            print(f">>> Raw response: {evaluation_response_str[:200]}...")
            return {
                "factual_accuracy": {"is_correct": None, "notes": []},
                "completeness_score": 0,
                "relevance_score": 0,
                "final_score": 0.0, 
                "reasoning": "Gagal memproses respons evaluasi dari LLM (Invalid JSON)."
            }
        except Exception as e:
            print(f">>> ERROR: {type(e).__name__} - {str(e)}")
            return {
                "factual_accuracy": {"is_correct": None, "notes": []},
                "completeness_score": 0,
                "relevance_score": 0,
                "final_score": 0.0, 
                "reasoning": f"Terjadi kesalahan teknis: {str(e)}"
            }

    def _log_evaluation_result(self, evaluation_result: Dict, context: str):
        """
        Helper method untuk logging hasil evaluasi dengan format yang konsisten dan jelas.
        UPGRADE: Format yang sangat eye-catching agar mudah ditemukan di log.
        """
        logging.info("╔" + "="*78 + "╗")
        logging.info(f"║ {'LLM EVALUATION RESULT':^76} ║")
        logging.info(f"║ {context:^76} ║")
        logging.info("╠" + "="*78 + "╣")
        
        # Factual Accuracy
        is_correct = evaluation_result.get('factual_accuracy', {}).get('is_correct')
        if is_correct is True:
            logging.info(f"║ Factual Accuracy: CORRECT {' '*55}║")
        elif is_correct is False:
            logging.info(f"║ Factual Accuracy: INCORRECT {' '*53}║")
        else:
            logging.info(f"║ Factual Accuracy: UNKNOWN {' '*55}║")
        
        # Scores
        completeness = evaluation_result.get('completeness_score', 'N/A')
        relevance = evaluation_result.get('relevance_score', 'N/A')
        final_score = evaluation_result.get('final_score', 'N/A')
        
        logging.info("╠" + "-"*78 + "╣")
        logging.info(f"║ Completeness Score: {str(completeness):>3}/5 {' '*54}║")
        logging.info(f"║ Relevance Score:    {str(relevance):>3}/5 {' '*54}║")
        logging.info(f"║ Final Score:        {str(final_score):>4} {' '*55}║")
        
        # Reasoning
        logging.info("╠" + "-"*78 + "╣")
        reasoning = evaluation_result.get('reasoning', 'N/A')
        
        # Word wrap reasoning untuk muat dalam box
        max_line_length = 74
        reasoning_lines = []
        words = reasoning.split()
        current_line = ""
        
        for word in words:
            if len(current_line) + len(word) + 1 <= max_line_length:
                current_line += (" " if current_line else "") + word
            else:
                reasoning_lines.append(current_line)
                current_line = word
        
        if current_line:
            reasoning_lines.append(current_line)
        
        logging.info(f"║ Reasoning: {' '*64}║")
        for line in reasoning_lines[:5]:  # Max 5 lines
            logging.info(f"║   {line:<74}║")
        
        # Notes (if any)
        notes = evaluation_result.get('factual_accuracy', {}).get('notes', [])
        if notes:
            logging.info("╠" + "-"*78 + "╣")
            logging.info(f"║ Notes: {' '*68}║")
            for note in notes[:3]:  # Max 3 notes
                note_short = (note[:70] + "...") if len(note) > 70 else note
                logging.info(f"║   • {note_short:<72}║")
        
        logging.info("╚" + "="*78 + "╝")
        logging.info("")  # Empty line untuk spacing

    def generate_duplicate_report(self, df: pd.DataFrame) -> str:
        """Membuat laporan teks mengenai data aset yang terduplikasi."""
        duplicate_report = "HASIL PENGECEKAN DUPLIKASI\n\n"
        if self.COL_NO_ASET not in df.columns:
            return duplicate_report + f"Kolom '{self.COL_NO_ASET}' tidak ditemukan."
        
        duplicates = df[df.duplicated(subset=[self.COL_NO_ASET], keep=False)]
        if duplicates.empty:
            return duplicate_report + "Tidak ada data duplikat ditemukan."
        
        duplicates_sorted = duplicates.sort_values(by=self.COL_NO_ASET)
        summary_line = f"Ditemukan {len(duplicates_sorted)} baris data duplikat untuk {duplicates_sorted[self.COL_NO_ASET].nunique()} nomor aset yang sama.\n\n"
        
        display_cols = ['NO', self.COL_NO_ASET, 'NAMA ASET', 'KONDISI', 'LOKASI SPESIFIK PER-INVENTORY']
        existing_cols = [col for col in display_cols if col in duplicates_sorted.columns]
        table_string = duplicates_sorted[existing_cols].to_string(index=False)
        return f"{duplicate_report}{summary_line}<pre>{table_string}</pre>"

    @staticmethod
    def format_summary_to_html(summary_text: str) -> str:
        """Memformat teks ringkasan menjadi HTML untuk ditampilkan di frontend."""
        import re
        
        parts = summary_text.split('<pre>')
        processed_parts = []
        for i, part in enumerate(parts):
            if i % 2 == 1:
                if '</pre>' in part:
                    content, rest = part.split('</pre>', 1)
                    processed_parts.append('<pre>' + content + '</pre>')
                    if rest.strip():
                        processed_parts.append('<br><br>' + rest.strip().replace('\n', '<br>'))
                else:
                    processed_parts.append('<pre>' + part + '</pre>')
            else:
                if part.strip():
                    formatted_part = part.strip()
                    headers = ['DATA OVERVIEW', 'RINGKASAN EKSEKUTIF', 'INSIGHT UTAMA', 
                              'HASIL PENGECEKAN DUPLIKASI', 'ANALISA KEUANGAN ASET']
                    for header in headers:
                        pattern = r'(^|\n\n)(' + re.escape(header) + r')'
                        formatted_part = re.sub(pattern, r'\1<strong>\2</strong>', formatted_part)
                    
                    formatted_part = formatted_part.replace('\n\n', '<br><br>').replace('\n', '<br>')
                    processed_parts.append(formatted_part)
        
        html_content = ''.join(processed_parts)
        return re.sub(r'(<br\s*/?>\s*){3,}', '<br><br>', html_content)
    
    def get_rotation_stats(self) -> Dict:
        """Dapatkan statistik rotasi untuk monitoring."""
        return self.rotation_service.get_stats()