interface LoadingSpinnerProps {
  size?: 'sm' | 'md' | 'lg' | 'xl'
  variant?: 'jarvis' | 'stark' | 'white'
  className?: string
  text?: string
}

const sizeConfig = {
  sm: 'w-4 h-4',
  md: 'w-6 h-6',
  lg: 'w-8 h-8',
  xl: 'w-12 h-12'
}

const variantConfig = {
  jarvis: 'border-jarvis-500 border-t-transparent',
  stark: 'border-stark-400 border-t-transparent',
  white: 'border-white border-t-transparent'
}

const textSizeConfig = {
  sm: 'text-xs',
  md: 'text-sm',
  lg: 'text-base',
  xl: 'text-lg'
}

export default function LoadingSpinner({
  size = 'md',
  variant = 'jarvis',
  className = '',
  text
}: LoadingSpinnerProps) {
  const sizeClass = sizeConfig[size]
  const variantClass = variantConfig[variant]
  const textSizeClass = textSizeConfig[size]
  
  return (
    <div className={`flex items-center justify-center space-x-2 ${className}`}>
      <div
        className={`
          ${sizeClass} ${variantClass}
          border-2 border-solid rounded-full animate-spin
        `}
        role="status"
        aria-label="Loading"
      />
      {text && (
        <span className={`text-stark-400 ${textSizeClass}`}>
          {text}
        </span>
      )}
    </div>
  )
}

export function FullPageLoader({
  text = "Loading strategic intelligence..."
}: {
  text?: string
}) {
  return (
    <div className="fixed inset-0 bg-stark-900/80 backdrop-blur-sm flex items-center justify-center z-50">
      <div className="text-center">
        <LoadingSpinner size="xl" text={text} />
      </div>
    </div>
  )
}

export function InlineLoader({
  text,
  size = 'sm'
}: {
  text?: string
  size?: 'sm' | 'md'
}) {
  return (
    <div className="flex items-center justify-center py-8">
      <LoadingSpinner size={size} text={text} />
    </div>
  )
}