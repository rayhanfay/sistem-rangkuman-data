import React from 'react';
import PropTypes from 'prop-types'; // Tambahkan ini
import Card from '../ui/Card';
import { X } from 'lucide-react';

const Modal = ({ isOpen, onClose, title, children }) => {
    if (!isOpen) return null;

    // Menangani penutupan via keyboard (Enter/Space) pada backdrop
    const handleKeyDown = (e) => {
        if (e.key === 'Enter' || e.key === ' ') {
            onClose();
        }
    };

    return (
        <div 
            className="fixed inset-0 z-40 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4 animate-fade-in"
            onClick={onClose}
            onKeyDown={handleKeyDown}
            role="button" // Menandakan elemen ini bisa diklik
            tabIndex={0}  // Agar bisa menerima fokus keyboard
            aria-label="Tutup modal"
        >
            <Card 
                className="w-full max-w-md animate-fade-in-up" 
                onClick={(e) => e.stopPropagation()} 
            >
                <div className="flex justify-between items-center p-4 border-b">
                    <h2 className="text-xl font-bold text-gray-800">{title}</h2>
                    <button 
                        onClick={onClose} 
                        className="p-1 rounded-full text-gray-400 hover:bg-gray-100 hover:text-gray-700 transition-colors"
                        aria-label="Tutup modal"
                    >
                        <X size={20} />
                    </button>
                </div>
                <div className="p-6">
                    {children}
                </div>
            </Card>
        </div>
    );
};

// Validasi Props
Modal.propTypes = {
    isOpen: PropTypes.bool.isRequired,
    onClose: PropTypes.func.isRequired,
    title: PropTypes.string.isRequired,
    children: PropTypes.node
};

export default Modal;