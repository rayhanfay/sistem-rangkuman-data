import React, { useEffect, useState } from 'react';
import { AlertCircle, CheckCircle, XCircle, Info, X } from 'lucide-react';

const toastConfig = {
    success: { icon: CheckCircle, color: 'text-green-500' },
    error: { icon: XCircle, color: 'text-red-500' },
    info: { icon: Info, color: 'text-blue-500' },
    warning: { icon: AlertCircle, color: 'text-yellow-500' },
};

const Toast = ({ id, message, type, onClose }) => {
    const [isExiting, setIsExiting] = useState(false);
    const config = toastConfig[type] || toastConfig.info;
    const Icon = config.icon;

    useEffect(() => {
        const exitTimer = setTimeout(() => {
            setIsExiting(true);
        }, 4500); 

        const removeTimer = setTimeout(() => {
            onClose(id);
        }, 5000);

        return () => {
            clearTimeout(exitTimer);
            clearTimeout(removeTimer);
        };
    }, [id, onClose]);

    const handleClose = () => {
        setIsExiting(true);
        setTimeout(() => onClose(id), 400); 
    };

    return (
        <div 
            className={`max-w-sm w-full bg-white shadow-lg rounded-lg pointer-events-auto ring-1 ring-black ring-opacity-5 overflow-hidden ${isExiting ? 'animate-fade-out-right' : 'animate-fade-in-right'}`}
            role="alert"
        >
            <div className="p-4">
                <div className="flex items-start">
                    <div className="flex-shrink-0">
                        <Icon className={`h-6 w-6 ${config.color}`} aria-hidden="true" />
                    </div>
                    <div className="ml-3 w-0 flex-1">
                        <p className="text-sm font-medium text-gray-900 break-words">
                            {message}
                        </p>
                    </div>
                    <div className="ml-4 flex-shrink-0 flex">
                        <button
                            onClick={handleClose}
                            className="bg-white rounded-md inline-flex text-gray-400 hover:text-gray-500 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                        >
                            <span className="sr-only">Close</span>
                            <X className="h-5 w-5" aria-hidden="true" />
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Toast;