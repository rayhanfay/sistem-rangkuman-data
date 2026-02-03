import React from 'react';
import { Link } from 'react-router-dom';
import { AlertTriangle, Home } from 'lucide-react';

const NotFound = () => {
  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-background text-center px-4">
      <AlertTriangle className="w-24 h-24 text-brand-red mb-6 animate-bounce" />
      
      <h1 className="text-6xl font-extrabold text-text-primary">404</h1>
      <h2 className="text-3xl font-semibold text-text-primary mt-4">
        Halaman Tidak Ditemukan
      </h2>
      
      <p className="text-text-secondary mt-4 max-w-md">
        Maaf, halaman yang Anda cari tidak ada atau mungkin telah dipindahkan.
      </p>

      <Link
        to="/"
        className="mt-8 inline-flex items-center px-6 py-3 bg-brand-blue text-white font-semibold rounded-lg shadow-md hover:bg-opacity-90 transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-brand-blue"
      >
        <Home className="mr-2" size={20} />
        Kembali ke Beranda
      </Link>
    </div>
  );
};

export default NotFound;