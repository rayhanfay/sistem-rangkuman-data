from typing import List, Dict, Any

class GetPromptsUseCase:
    """
    Use case untuk menyediakan daftar prompt analisis kustom yang tersedia.
    """
    def __init__(self):
        self.prompts = {
            "standard_summary": {
                "description": "Prompt standar untuk membuat ringkasan eksekutif dan rekomendasi aset.",
                "template": (
                    "Anda adalah analis data ahli. Berdasarkan data berikut, buat laporan ringkas yang terdiri dari dua bagian: "
                    "RINGKASAN EKSEKUTIF dan REKOMENDASI TINDAK LANJUT.\n\n"
                    "PENTING: Jangan gunakan format Markdown. Tulis semua output sebagai teks biasa tanpa karakter seperti '**', '*', atau '#'.\n\n"
                    "Data:\n{document}"
                )
            },
            "risk_analysis": {
                "description": "Prompt untuk menganalisis dan mengidentifikasi aset berisiko tinggi (rusak atau perlu perhatian).",
                "template": (
                    "Anda adalah manajer risiko aset. Dari data berikut, identifikasi 3-5 aset paling berisiko "
                    "berdasarkan kondisi dan keterangannya. Jelaskan mengapa aset tersebut berisiko dalam format poin.\n\n"
                    "PENTING: Jangan gunakan format Markdown. Tulis semua output sebagai teks biasa tanpa karakter seperti '**', '*', atau '#'.\n\n"
                    "Data:\n{document}"
                )
            }
        }

    def execute(self) -> List[Dict[str, Any]]:
        """
        Mengembalikan daftar prompt yang diformat untuk frontend.
        """
        formatted_prompts = [
            {"name": name, "description": data["description"]}
            for name, data in self.prompts.items()
        ]
        return formatted_prompts

    def get_prompt_template(self, name: str) -> str | None:
        """Mengambil template string dari prompt berdasarkan namanya."""
        return self.prompts.get(name, {}).get("template")
