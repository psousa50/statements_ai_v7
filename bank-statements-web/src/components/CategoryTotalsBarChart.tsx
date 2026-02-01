import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts'

interface ChartData {
  name: string
  value: number
  count: number
  id: string
  color: string
}

interface NoDataMessage {
  title: string
  description: string
}

interface CategoryTotalsBarChartProps {
  data: ChartData[]
  loading?: boolean
  onBarClick?: (data: ChartData) => void
  noDataMessage?: NoDataMessage
}

export const CategoryTotalsBarChart = ({ data, loading, onBarClick, noDataMessage }: CategoryTotalsBarChartProps) => {
  if (loading) {
    return <div className="loading-indicator">Loading chart data...</div>
  }

  if (data.length === 0) {
    return (
      <div className="no-data-message">
        <strong>{noDataMessage?.title || 'No data available'}</strong>
        <p>{noDataMessage?.description || 'No transaction data available for the selected filters.'}</p>
      </div>
    )
  }

  const sortedData = [...data].sort((a, b) => b.value - a.value)

  const handleClick = (entry: ChartData) => {
    if (onBarClick) {
      onBarClick(entry)
    }
  }

  return (
    <div style={{ width: '100%', height: 500 }}>
      <ResponsiveContainer>
        <BarChart data={sortedData} layout="vertical" margin={{ top: 10, right: 30, left: 120, bottom: 10 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255, 255, 255, 0.06)" horizontal={true} vertical={false} />
          <XAxis
            type="number"
            stroke="var(--text-muted)"
            style={{ fontSize: 12 }}
            tickFormatter={(value) => `$${value.toLocaleString()}`}
            axisLine={{ stroke: 'rgba(255, 255, 255, 0.1)' }}
            tickLine={{ stroke: 'rgba(255, 255, 255, 0.1)' }}
          />
          <YAxis
            type="category"
            dataKey="name"
            stroke="var(--text-muted)"
            style={{ fontSize: 12 }}
            width={110}
            tick={{ fill: 'var(--text-primary)' }}
            axisLine={{ stroke: 'rgba(255, 255, 255, 0.1)' }}
            tickLine={false}
          />
          <Tooltip
            cursor={{ fill: 'rgba(255, 255, 255, 0.05)' }}
            content={({ active, payload }) => {
              if (!active || !payload || !payload[0]) return null
              const data = payload[0].payload as ChartData
              return (
                <div
                  style={{
                    backgroundColor: 'rgba(30, 41, 59, 0.9)',
                    backdropFilter: 'blur(8px)',
                    border: '1px solid rgba(255, 255, 255, 0.1)',
                    borderRadius: '12px',
                    padding: '12px 16px',
                    boxShadow: '0 8px 32px rgba(0, 0, 0, 0.3)',
                  }}
                >
                  <div style={{ color: '#f1f5f9', fontWeight: 600, marginBottom: '4px' }}>{data.name}</div>
                  <div style={{ color: '#f1f5f9', fontSize: '16px', fontWeight: 600 }}>
                    ${data.value.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                  </div>
                  <div style={{ color: '#94a3b8', fontSize: '12px', marginTop: '4px' }}>{data.count} transactions</div>
                </div>
              )
            }}
          />
          <Bar
            dataKey="value"
            onClick={(data) => handleClick(data as ChartData)}
            style={{ cursor: 'pointer' }}
            animationDuration={300}
            radius={[0, 8, 8, 0]}
            activeBar={false}
          >
            {sortedData.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={entry.color} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}
