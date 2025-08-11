import { useState, useRef, useEffect } from 'react'

interface ChartDataPoint {
  label: string
  value: number
  color?: string
  trend?: 'up' | 'down' | 'stable'
}

interface ChartProps {
  type: 'bar' | 'line' | 'pie' | 'area'
  data: ChartDataPoint[]
  title?: string
  height?: number
  showLegend?: boolean
  showGrid?: boolean
  animate?: boolean
  className?: string
}

export default function Chart({ 
  type, 
  data, 
  title, 
  height = 200, 
  showLegend = true, 
  showGrid = true,
  animate = true,
  className = ""
}: ChartProps) {
  const svgRef = useRef<SVGSVGElement>(null)
  const [animationComplete, setAnimationComplete] = useState(false)

  useEffect(() => {
    if (animate) {
      const timer = setTimeout(() => setAnimationComplete(true), 100)
      return () => clearTimeout(timer)
    } else {
      setAnimationComplete(true)
    }
  }, [animate])

  const maxValue = Math.max(...data.map(d => d.value))
  const minValue = Math.min(...data.map(d => d.value), 0)
  const range = maxValue - minValue || 1

  const defaultColors = [
    '#00D4FF', // jarvis-blue
    '#22C55E', // green
    '#F59E0B', // amber  
    '#EF4444', // red
    '#8B5CF6', // purple
    '#06B6D4', // cyan
    '#F97316', // orange
    '#84CC16'  // lime
  ]

  const getColor = (index: number, customColor?: string) => {
    return customColor || defaultColors[index % defaultColors.length]
  }

  const formatValue = (value: number) => {
    if (Math.abs(value) >= 1000000000) {
      return `$${(value / 1000000000).toFixed(1)}B`
    } else if (Math.abs(value) >= 1000000) {
      return `$${(value / 1000000).toFixed(0)}M`
    } else if (Math.abs(value) >= 1000) {
      return `$${(value / 1000).toFixed(0)}K`
    }
    return value.toString()
  }

  const renderBarChart = () => {
    const barWidth = (100 - 10) / data.length
    const barSpacing = 10 / (data.length + 1)

    return (
      <g>
        {/* Grid lines */}
        {showGrid && (
          <g stroke="#374151" strokeWidth="0.5" opacity="0.3">
            {[0, 25, 50, 75, 100].map(y => (
              <line
                key={y}
                x1="0"
                y1={`${y}%`}
                x2="100%"
                y2={`${y}%`}
              />
            ))}
          </g>
        )}
        
        {/* Bars */}
        {data.map((item, index) => {
          const barHeight = ((item.value - minValue) / range) * 100
          const x = barSpacing + (index * (barWidth + barSpacing))
          const y = 100 - barHeight
          
          return (
            <g key={index}>
              <rect
                x={`${x}%`}
                y={`${y}%`}
                width={`${barWidth}%`}
                height={animationComplete ? `${barHeight}%` : '0%'}
                fill={getColor(index, item.color)}
                opacity="0.8"
                className="transition-all duration-1000 ease-out"
                rx="2"
              />
              {/* Value label on top of bar */}
              <text
                x={`${x + barWidth/2}%`}
                y={`${y - 2}%`}
                textAnchor="middle"
                className="fill-stark-200 text-xs"
                opacity={animationComplete ? 1 : 0}
              >
                {formatValue(item.value)}
              </text>
            </g>
          )
        })}
        
        {/* X-axis labels */}
        {data.map((item, index) => {
          const x = barSpacing + (index * (barWidth + barSpacing)) + barWidth/2
          return (
            <text
              key={index}
              x={`${x}%`}
              y="110%"
              textAnchor="middle"
              className="fill-stark-400 text-xs"
            >
              {item.label}
            </text>
          )
        })}
      </g>
    )
  }

  const renderLineChart = () => {
    const points = data.map((item, index) => {
      const x = (index / (data.length - 1 || 1)) * 100
      const y = 100 - ((item.value - minValue) / range) * 100
      return `${x},${y}`
    }).join(' ')

    const areaPoints = `0,100 ${points} 100,100`

    return (
      <g>
        {/* Grid lines */}
        {showGrid && (
          <g stroke="#374151" strokeWidth="0.5" opacity="0.3">
            {[0, 25, 50, 75, 100].map(y => (
              <line
                key={y}
                x1="0"
                y1={`${y}%`}
                x2="100%"
                y2={`${y}%`}
              />
            ))}
          </g>
        )}
        
        {/* Area fill */}
        {type === 'area' && (
          <polygon
            points={areaPoints}
            fill={getColor(0)}
            opacity="0.2"
            className={animationComplete ? "opacity-20" : "opacity-0"}
          />
        )}
        
        {/* Line */}
        <polyline
          points={points}
          fill="none"
          stroke={getColor(0)}
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeDasharray={animationComplete ? "none" : `${data.length * 10}`}
          strokeDashoffset={animationComplete ? "0" : `${data.length * 10}`}
          className="transition-all duration-1500 ease-out"
        />
        
        {/* Data points */}
        {data.map((item, index) => {
          const x = (index / (data.length - 1 || 1)) * 100
          const y = 100 - ((item.value - minValue) / range) * 100
          
          return (
            <g key={index}>
              <circle
                cx={`${x}%`}
                cy={`${y}%`}
                r="4"
                fill={getColor(index, item.color)}
                opacity={animationComplete ? 1 : 0}
                className="transition-opacity duration-1000"
              />
              {/* Value label */}
              <text
                x={`${x}%`}
                y={`${y - 10}%`}
                textAnchor="middle"
                className="fill-stark-200 text-xs"
                opacity={animationComplete ? 1 : 0}
              >
                {formatValue(item.value)}
              </text>
            </g>
          )
        })}
        
        {/* X-axis labels */}
        {data.map((item, index) => {
          const x = (index / (data.length - 1 || 1)) * 100
          return (
            <text
              key={index}
              x={`${x}%`}
              y="115%"
              textAnchor="middle"
              className="fill-stark-400 text-xs"
            >
              {item.label}
            </text>
          )
        })}
      </g>
    )
  }

  const renderPieChart = () => {
    const total = data.reduce((sum, item) => sum + item.value, 0)
    let currentAngle = 0
    const centerX = 50
    const centerY = 50
    const radius = 35

    return (
      <g>
        {data.map((item, index) => {
          const percentage = (item.value / total) * 100
          const angle = (item.value / total) * 360
          const startAngle = currentAngle
          const endAngle = currentAngle + angle
          
          const x1 = centerX + radius * Math.cos((startAngle - 90) * Math.PI / 180)
          const y1 = centerY + radius * Math.sin((startAngle - 90) * Math.PI / 180)
          const x2 = centerX + radius * Math.cos((endAngle - 90) * Math.PI / 180)
          const y2 = centerY + radius * Math.sin((endAngle - 90) * Math.PI / 180)
          
          const largeArcFlag = angle > 180 ? 1 : 0
          
          const pathData = [
            `M ${centerX} ${centerY}`,
            `L ${x1} ${y1}`,
            `A ${radius} ${radius} 0 ${largeArcFlag} 1 ${x2} ${y2}`,
            'Z'
          ].join(' ')
          
          currentAngle += angle
          
          return (
            <path
              key={index}
              d={pathData}
              fill={getColor(index, item.color)}
              opacity={animationComplete ? 0.8 : 0}
              stroke="#1F2937"
              strokeWidth="2"
              className="transition-opacity duration-1000"
              style={{
                transitionDelay: `${index * 100}ms`
              }}
            />
          )
        })}
        
        {/* Center circle for donut effect */}
        <circle
          cx={centerX}
          cy={centerY}
          r={radius * 0.4}
          fill="#111827"
          opacity={animationComplete ? 1 : 0}
          className="transition-opacity duration-1000"
        />
      </g>
    )
  }

  const renderChart = () => {
    switch (type) {
      case 'bar':
        return renderBarChart()
      case 'line':
      case 'area':
        return renderLineChart()
      case 'pie':
        return renderPieChart()
      default:
        return renderBarChart()
    }
  }

  return (
    <div className={`${className}`}>
      {title && (
        <h3 className="text-stark-100 font-medium text-sm mb-4">{title}</h3>
      )}
      
      <div className="relative">
        <svg
          ref={svgRef}
          width="100%"
          height={height}
          viewBox="0 0 100 100"
          preserveAspectRatio="none"
          className="overflow-visible"
        >
          {renderChart()}
        </svg>
      </div>

      {/* Legend */}
      {showLegend && (
        <div className="flex flex-wrap gap-4 mt-4">
          {data.map((item, index) => (
            <div key={index} className="flex items-center space-x-2">
              <div
                className="w-3 h-3 rounded"
                style={{ backgroundColor: getColor(index, item.color) }}
              />
              <span className="text-stark-300 text-xs">{item.label}</span>
              <span className="text-stark-400 text-xs">
                ({formatValue(item.value)})
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}