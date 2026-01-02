import { useMemo, useState } from 'react'
import { PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts'
import { RecurringPattern } from '../api/TransactionClient'
import { Category } from '../types/Transaction'
import { formatCurrency } from '../utils/format'
import { getCategoryColorById } from '../utils/categoryColors'

const UNCATEGORIZED_COLOR = '#EF4444'

interface RecurringExpensesChartsProps {
  patterns: RecurringPattern[]
  categories: Category[]
  totalMonthlyRecurring: number
}

type ChartType = 'pie' | 'bar'

export const RecurringExpensesCharts = ({
  patterns,
  categories,
  totalMonthlyRecurring,
}: RecurringExpensesChartsProps) => {
  const [chartType, setChartType] = useState<ChartType>('pie')

  const categoryChartData = useMemo(() => {
    const categoryTotals = new Map<string, { name: string; value: number; categoryId: string | null }>()

    patterns.forEach((pattern) => {
      const category = pattern.category_id ? categories.find((c) => c.id === pattern.category_id) : null
      const categoryName = category?.name || (pattern.category_id ? 'Unknown' : 'Uncategorised')
      const key = pattern.category_id || 'uncategorised'

      const existing = categoryTotals.get(key)
      if (existing) {
        existing.value += pattern.average_amount
      } else {
        categoryTotals.set(key, {
          name: categoryName,
          value: pattern.average_amount,
          categoryId: pattern.category_id || null,
        })
      }
    })

    return Array.from(categoryTotals.values())
      .sort((a, b) => b.value - a.value)
      .map((item) => ({
        ...item,
        color: item.categoryId ? getCategoryColorById(item.categoryId).solid : UNCATEGORIZED_COLOR,
      }))
  }, [patterns, categories])

  const categoryBarChartData = useMemo(() => {
    return [...categoryChartData]
      .sort((a, b) => a.value - b.value)
      .map((item) => ({
        name: item.name.length > 15 ? item.name.slice(0, 15) + '...' : item.name,
        fullName: item.name,
        value: item.value,
        color: item.color,
      }))
  }, [categoryChartData])

  return (
    <div className="recurring-charts-container">
      <div className="recurring-patterns-summary">
        <h3>Summary</h3>
        <div className="summary-stats">
          <div className="stat-card">
            <span className="stat-label">Total Monthly Recurring</span>
            <span className="stat-value">{formatCurrency(totalMonthlyRecurring)}</span>
          </div>
          <div className="stat-card">
            <span className="stat-label">Number of Patterns</span>
            <span className="stat-value">{patterns.length}</span>
          </div>
          <div className="stat-card">
            <span className="stat-label">Annual Cost</span>
            <span className="stat-value">{formatCurrency(totalMonthlyRecurring * 12)}</span>
          </div>
        </div>
      </div>

      <div className="recurring-charts-section">
        <div className="chart-type-toggle">
          <button className={`toggle-btn ${chartType === 'pie' ? 'active' : ''}`} onClick={() => setChartType('pie')}>
            Pie Chart
          </button>
          <button className={`toggle-btn ${chartType === 'bar' ? 'active' : ''}`} onClick={() => setChartType('bar')}>
            Bar Chart
          </button>
        </div>

        {chartType === 'pie' && (
          <div className="chart-card">
            <h4>By Category</h4>
            <ResponsiveContainer width="100%" height={350}>
              <PieChart>
                <Pie
                  data={categoryChartData}
                  cx="50%"
                  cy="50%"
                  outerRadius={120}
                  dataKey="value"
                  label={({ name, percent }) => (percent >= 0.05 ? `${name} (${(percent * 100).toFixed(0)}%)` : '')}
                  labelLine={false}
                >
                  {categoryChartData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip
                  formatter={(value: number) => formatCurrency(value)}
                  contentStyle={{
                    backgroundColor: 'var(--bg-secondary)',
                    border: '1px solid var(--border-primary)',
                    borderRadius: '4px',
                    color: 'var(--text-primary)',
                  }}
                  labelStyle={{ color: 'var(--text-primary)', fontWeight: 600 }}
                  itemStyle={{ color: 'var(--text-primary)' }}
                />
              </PieChart>
            </ResponsiveContainer>
            <p className="chart-hint">Hover over slices to see smaller categories</p>
          </div>
        )}

        {chartType === 'bar' && (
          <div className="chart-card">
            <h4>Monthly Cost by Category</h4>
            <ResponsiveContainer width="100%" height={Math.max(350, categoryBarChartData.length * 35)}>
              <BarChart data={categoryBarChartData} layout="vertical" margin={{ left: 20, right: 20 }}>
                <XAxis type="number" tickFormatter={(value) => formatCurrency(value)} />
                <YAxis type="category" dataKey="name" width={120} tick={{ fontSize: 12 }} />
                <Tooltip
                  formatter={(value: number) => formatCurrency(value)}
                  labelFormatter={(label, payload) => payload?.[0]?.payload?.fullName || label}
                  contentStyle={{
                    backgroundColor: 'var(--bg-secondary)',
                    border: '1px solid var(--border-primary)',
                    borderRadius: '4px',
                    color: 'var(--text-primary)',
                  }}
                  labelStyle={{ color: 'var(--text-primary)', fontWeight: 600 }}
                  itemStyle={{ color: 'var(--text-primary)' }}
                />
                <Bar dataKey="value" radius={[0, 4, 4, 0]}>
                  {categoryBarChartData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>

      <style>{`
        .recurring-charts-container {
          display: flex;
          flex-direction: column;
          gap: 24px;
        }

        .recurring-patterns-summary {
          background: var(--bg-secondary);
          border-radius: 8px;
          padding: 20px;
        }

        .recurring-patterns-summary h3 {
          margin: 0 0 16px 0;
          font-size: 18px;
          font-weight: 600;
        }

        .summary-stats {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
          gap: 16px;
        }

        .stat-card {
          background: var(--bg-primary);
          border-radius: 8px;
          padding: 16px;
          display: flex;
          flex-direction: column;
          gap: 8px;
        }

        .stat-label {
          font-size: 14px;
          color: var(--text-secondary);
        }

        .stat-value {
          font-size: 24px;
          font-weight: 600;
          color: var(--text-primary);
        }

        .recurring-charts-section {
          display: flex;
          flex-direction: column;
          gap: 16px;
        }

        .chart-type-toggle {
          display: flex;
          gap: 8px;
        }

        .toggle-btn {
          padding: 8px 16px;
          border: 1px solid var(--border-primary);
          border-radius: 6px;
          background: var(--bg-primary);
          color: var(--text-secondary);
          font-size: 14px;
          cursor: pointer;
          transition: all 0.2s;
        }

        .toggle-btn:hover {
          background: var(--bg-secondary);
          color: var(--text-primary);
        }

        .toggle-btn.active {
          background: var(--button-primary);
          color: white;
          border-color: var(--button-primary);
        }

        .chart-card {
          background: var(--bg-secondary);
          border-radius: 8px;
          padding: 20px;
        }

        .chart-card h4 {
          margin: 0 0 16px 0;
          font-size: 16px;
          font-weight: 600;
          color: var(--text-primary);
        }

        .chart-hint {
          margin: 8px 0 0 0;
          font-size: 12px;
          color: var(--text-secondary);
          text-align: center;
        }

        .recharts-text {
          fill: var(--text-primary);
        }

        .recharts-cartesian-axis-tick-value {
          fill: var(--text-secondary);
        }

      `}</style>
    </div>
  )
}
