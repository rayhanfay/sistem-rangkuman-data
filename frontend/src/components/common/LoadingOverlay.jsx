import React from 'react';
import ReactDOM from 'react-dom';

const LoadingOverlay = () => {

  const overlayUI = (
    <div 
      className="fixed inset-0 z-50 flex items-center justify-center bg-white/80 backdrop-blur-sm animate-fade-in"
      aria-label="Memuat konten..."
      role="status"
    >
      <div className="flex flex-col items-center">
        <div className="animate-spin rounded-full h-16 w-16 border-b-4 border-brand-blue"></div>
        <p className="mt-4 text-lg font-semibold text-text-primary">
          Memuat...
        </p>
      </div>
    </div>
  );

  return ReactDOM.createPortal(
    overlayUI, 
    document.getElementById('modal-root')
  );
};

export default LoadingOverlay;
