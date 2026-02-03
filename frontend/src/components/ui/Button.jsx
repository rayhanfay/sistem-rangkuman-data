import React from 'react';

const Button = ({ 
    children, 
    variant = 'primary', 
    size = 'md', 
    disabled = false, 
    loading = false,
    className = '',
    onClick,
    type = 'button',
    ...props 
}) => {
    const baseClasses = 'inline-flex items-center justify-center font-medium rounded-lg transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2';
    
    const variants = {
        primary: 'bg-brand-blue text-white hover:bg-opacity-90 focus:ring-brand-blue',
        secondary: 'bg-text-secondary text-white hover:bg-opacity-90 focus:ring-text-secondary',
        outline: 'border-2 border-brand-blue text-brand-blue hover:bg-brand-blue/10 focus:ring-brand-blue',
        danger: 'bg-brand-red text-white hover:bg-opacity-90 focus:ring-brand-red',
        success: 'bg-brand-green text-white hover:bg-opacity-90 focus:ring-brand-green',
        ghost: 'text-gray-600 hover:bg-gray-100 focus:ring-gray-500',
    };

    const sizes = {
        sm: 'px-3 py-2 text-sm',
        md: 'px-4 py-2 text-base',
        lg: 'px-6 py-3 text-lg',
        xl: 'px-8 py-4 text-xl',
    };

    const disabledClasses = disabled || loading ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer';

    return (
        <button
            type={type}
            onClick={disabled || loading ? undefined : onClick}
            disabled={disabled || loading}
            className={`${baseClasses} ${variants[variant]} ${sizes[size]} ${disabledClasses} ${className}`}
            {...props}
        >
            {loading && (
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
            )}
            {children}
        </button>
    );
};

export default Button;