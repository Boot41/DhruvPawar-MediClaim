import React from 'react';
import { clsx } from 'clsx';

const Input = React.forwardRef(({ 
  className, 
  type = 'text',
  error = false,
  label,
  placeholder,
  disabled = false,
  ...props 
}, ref) => {
  const baseStyles = 'flex h-10 w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm placeholder:text-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:cursor-not-allowed disabled:opacity-50 transition-all duration-200';
  
  const errorStyles = error ? 'border-red-500 focus:ring-red-500' : '';

  return (
    <div className="w-full">
      {label && (
        <label className="block text-sm font-medium text-gray-700 mb-1">
          {label}
        </label>
      )}
      <input
        type={type}
        className={clsx(baseStyles, errorStyles, className)}
        ref={ref}
        placeholder={placeholder}
        disabled={disabled}
        {...props}
      />
      {error && typeof error === 'string' && (
        <p className="mt-1 text-sm text-red-600">{error}</p>
      )}
    </div>
  );
});

Input.displayName = 'Input';

export default Input;
