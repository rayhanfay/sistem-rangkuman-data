import React from 'react';
import Card from '../ui/Card';
import Button from '../ui/Button';
import { AlertTriangle } from 'lucide-react';

const ConfirmationModal = ({ isOpen, onClose, onConfirm, title, message }) => {
    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
            <Card className="w-full max-w-md" shadow="xl">
                <div className="flex items-start">
                    <div className="mx-auto flex-shrink-0 flex items-center justify-center h-12 w-12 rounded-full bg-red-100 sm:mx-0 sm:h-10 sm:w-10">
                        <AlertTriangle className="h-6 w-6 text-red-600" aria-hidden="true" />
                    </div>
                    <div className="mt-3 text-center sm:mt-0 sm:ml-4 sm:text-left">
                        <h3 className="text-lg leading-6 font-medium text-gray-900">{title}</h3>
                        <div className="mt-2">
                            <p className="text-sm text-gray-500">{message}</p>
                        </div>
                    </div>
                </div>
                <div className="mt-5 sm:mt-4 sm:flex sm:flex-row-reverse">
                    <Button
                        variant="danger"
                        onClick={onConfirm}
                        className="w-full sm:ml-3 sm:w-auto"
                    >
                        Hapus
                    </Button>
                    <Button
                        variant="ghost"
                        onClick={onClose}
                        className="mt-3 w-full sm:mt-0 sm:w-auto"
                    >
                        Batal
                    </Button>
                </div>
            </Card>
        </div>
    );
};

export default ConfirmationModal;