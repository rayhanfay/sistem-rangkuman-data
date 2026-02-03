import React, { createContext, useState, useCallback, useContext } from 'react';
import Toast from '../components/common/Toast';

const ToastContext = createContext(null);

export const useToast = () => useContext(ToastContext);

export const ToastProvider = ({ children }) => {
    const [toasts, setToasts] = useState([]);

    const showToast = useCallback((message, type = 'info') => {
        const id = Date.now() + Math.random();
        setToasts(prevToasts => [...prevToasts, { id, message, type }]);
    }, []);

    const removeToast = useCallback((id) => {
        setToasts(prevToasts => prevToasts.filter(toast => toast.id !== id));
    }, []);

    return (
        <ToastContext.Provider value={{ showToast }}>
            {children}
            <div className="fixed top-5 right-5 z-50 space-y-2 w-full max-w-sm">
                {toasts.map(toast => (
                    <Toast 
                        key={toast.id} 
                        id={toast.id}
                        message={toast.message} 
                        type={toast.type} 
                        onClose={removeToast} 
                    />
                ))}
            </div>
        </ToastContext.Provider>
    );
};