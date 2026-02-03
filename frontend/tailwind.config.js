/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Palet warna terinspirasi dari Pertamina Hulu Rokan
        brand: {
          blue: '#003A70',      // Biru utama korporat
          red: '#E82A2A',       // Merah untuk aksen, notifikasi, atau action
          green: '#00A859',     // Hijau untuk status sukses atau data positif
        },
        // Warna dasar UI
        background: '#F0F4F8',  // Latar belakang utama yang sedikit kebiruan & bersih
        surface: '#FFFFFF',     // Warna dasar untuk kartu (card)
        sidebar: '#1A202C',     // Warna gelap untuk sidebar agar kontras
        // Warna Teks
        text: {
          primary: '#1A202C',   // Teks utama/judul (gelap)
          secondary: '#5A6474', // Teks pendukung/paragraf
          light: '#FFFFFF',     // Teks di atas latar belakang gelap
        },
      },
      fontFamily: {
        sans: ['"Inter"', 'sans-serif'],
      },
      boxShadow: {
        'subtle': '0 2px 12px rgba(0, 0, 0, 0.06)',
      }
    },
  },
  plugins: [],
}