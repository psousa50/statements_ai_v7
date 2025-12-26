import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts'

interface ChartData {
  name: string
  value: number
  count: number
  id: string
  color: string
}

interface CategoryTotalsBarChartProps {
  data: ChartData[]
  loading?: boolean
  onBarClick?: (data: ChartData) => void
}

export const CategoryTotalsBarChart = ({ data, loading, onBarClick }: CategoryTotalsBarChartProps) => {
  if (loading) {
    return <div className="loading-indicator">Loading chart data...</div>
  }

  if (data.length === 0) {
    return <div className="no-data-message">No transaction data available for the selected filters.</div>
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
          <CartesianGrid strokeDasharray="3 3" stroke="var(--border-secondary)" horizontal={true} vertical={false} />
          <XAxis
            type="number"
            stroke="var(--text-secondary)"
            style={{ fontSize: 12 }}
            tickFormatter={(value) => `$${value.toLocaleString()}`}
          />
          <YAxis
            type="category"
            dataKey="name"
            stroke="var(--text-secondary)"
            style={{ fontSize: 12 }}
            width={110}
            tick={{ fill: 'var(--text-primary)' }}
          />
          <Tooltip
            cursor={{ fill: 'rgba(255, 255, 255, 0.1)' }}
            contentStyle={{
              backgroundColor: 'var(--bg-primary)',
              border: '1px solid var(--border-primary)',
              borderRadius: '4px',
              boxShadow: '0 4px 6px var(--shadow-light)',
            }}
            content={({ active, payload }) => {
              if (!active || !payload || !payload[0]) return null
              const data = payload[0].payload as ChartData
              return (
                <div
                  style={{
                    backgroundColor: 'var(--bg-primary)',
                    border: '1px solid var(--border-primary)',
                    borderRadius: '4px',
                    padding: '8px 12px',
                    boxShadow: '0 4px 6px var(--shadow-light)',
                  }}
                >
                  <div style={{ color: 'var(--text-primary)', fontWeight: 'bold', marginBottom: '4px' }}>
                    {data.name}
                  </div>
                  <div style={{ color: 'var(--text-primary)' }}>
                    ${data.value.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                  </div>
                  <div style={{ color: 'var(--text-secondary)', fontSize: '12px' }}>{data.count} transactions</div>
                </div>
              )
            }}
          />
          <Bar
            dataKey="value"
            onClick={(data) => handleClick(data as ChartData)}
            style={{ cursor: 'pointer' }}
            animationDuration={300}
            radius={[0, 4, 4, 0]}
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
