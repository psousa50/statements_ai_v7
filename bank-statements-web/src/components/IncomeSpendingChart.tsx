import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ReferenceLine,
} from 'recharts'
import { IncomeSpendingDataPoint } from '../api/TransactionClient'

interface IncomeSpendingChartProps {
  dataPoints: IncomeSpendingDataPoint[]
  loading?: boolean
}

const INCOME_COLOR = '#22c55e'
const SPENDING_COLOR = '#ef4444'

const formatCurrency = (value: number) => {
  if (value >= 1000) return `${(value / 1000).toFixed(1)}k`
  return value.toFixed(0)
}

export const IncomeSpendingChart = ({ dataPoints, loading }: IncomeSpendingChartProps) => {
  if (loading) {
    return <div className="loading-indicator">Loading income vs spending data...</div>
  }

  if (!dataPoints || dataPoints.length === 0) {
    return (
      <div className="no-data-message">
        <strong>No data available</strong>
        <p>Upload a bank statement or adjust your filters to see income vs spending.</p>
      </div>
    )
  }

  const totalIncome = dataPoints.reduce((sum, dp) => sum + dp.income, 0)
  const totalSpending = dataPoints.reduce((sum, dp) => sum + dp.spending, 0)
  const totalNet = totalIncome - totalSpending

  return (
    <div style={{ width: '100%' }}>
      <div style={{ display: 'flex', gap: '24px', marginBottom: '16px', justifyContent: 'center' }}>
        <div style={{ textAlign: 'center' }}>
          <div style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>Total Income</div>
          <div style={{ fontSize: '18px', fontWeight: 600, color: INCOME_COLOR }}>${totalIncome.toFixed(2)}</div>
        </div>
        <div style={{ textAlign: 'center' }}>
          <div style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>Total Spending</div>
          <div style={{ fontSize: '18px', fontWeight: 600, color: SPENDING_COLOR }}>${totalSpending.toFixed(2)}</div>
        </div>
        <div style={{ textAlign: 'center' }}>
          <div style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>Net</div>
          <div style={{ fontSize: '18px', fontWeight: 600, color: totalNet >= 0 ? INCOME_COLOR : SPENDING_COLOR }}>
            {totalNet >= 0 ? '+' : ''}${totalNet.toFixed(2)}
          </div>
        </div>
      </div>
      <div style={{ width: '100%', height: 400, flex: 1, minWidth: 0 }}>
        <ResponsiveContainer>
          <BarChart data={dataPoints} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--border-secondary)" />
            <XAxis dataKey="period" stroke="var(--text-secondary)" style={{ fontSize: 12 }} />
            <YAxis stroke="var(--text-secondary)" style={{ fontSize: 12 }} tickFormatter={formatCurrency} />
            <Tooltip
              contentStyle={{
                backgroundColor: 'var(--bg-primary)',
                border: '1px solid var(--border-primary)',
                borderRadius: '4px',
                color: 'var(--text-primary)',
                boxShadow: '0 4px 6px var(--shadow-light)',
              }}
              labelStyle={{ color: 'var(--text-primary)' }}
              formatter={(value: number, name: string) => {
                const label = name === 'income' ? 'Income' : 'Spending'
                return [`$${value.toFixed(2)}`, label]
              }}
            />
            <Legend
              wrapperStyle={{ paddingTop: '20px', color: 'var(--text-primary)' }}
              formatter={(value: string) => (value === 'income' ? 'Income' : 'Spending')}
            />
            <ReferenceLine y={0} stroke="var(--border-secondary)" />
            <Bar dataKey="income" fill={INCOME_COLOR} animationDuration={300} radius={[2, 2, 0, 0]} />
            <Bar dataKey="spending" fill={SPENDING_COLOR} animationDuration={300} radius={[2, 2, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}
