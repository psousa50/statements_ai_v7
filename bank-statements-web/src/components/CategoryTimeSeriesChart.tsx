import { useMemo } from 'react'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts'
import { Category } from '../types/Transaction'
import { CategoryTimeSeriesDataPoint } from '../api/TransactionClient'
import { getCategoryColorById } from '../utils/categoryColors'

interface CategoryTimeSeriesChartProps {
  dataPoints: CategoryTimeSeriesDataPoint[]
  categories: Category[]
  loading?: boolean
}

const UNCATEGORIZED_COLOR = '#EF4444'

export const CategoryTimeSeriesChart = ({ dataPoints, categories, loading }: CategoryTimeSeriesChartProps) => {
  const chartData = useMemo(() => {
    if (!dataPoints || dataPoints.length === 0) return []

    const categoryMap = new Map<string, Category>()
    categories.forEach((cat) => categoryMap.set(cat.id, cat))

    const categoryNamesSet = new Set<string>()
    const periodMap = new Map<string, Record<string, number>>()

    dataPoints.forEach((dp) => {
      if (!periodMap.has(dp.period)) {
        periodMap.set(dp.period, {})
      }

      const periodData = periodMap.get(dp.period)!
      const category = dp.category_id ? categoryMap.get(dp.category_id) : null
      const categoryName = category ? category.name : 'Uncategorized'

      categoryNamesSet.add(categoryName)
      periodData[categoryName] = dp.total_amount
    })

    const periods = Array.from(periodMap.keys()).sort()
    const allCategoryNames = Array.from(categoryNamesSet)

    return periods.map((period) => {
      const periodData: Record<string, number | string> = { period }
      allCategoryNames.forEach((catName) => {
        periodData[catName] = periodMap.get(period)?.[catName] || 0
      })
      return periodData
    })
  }, [dataPoints, categories])

  const { categoryNames, nameToIdMap } = useMemo(() => {
    const names = new Set<string>()
    const idMap = new Map<string, string | null>()
    dataPoints.forEach((dp) => {
      const category = dp.category_id ? categories.find((c) => c.id === dp.category_id) : null
      const name = category ? category.name : 'Uncategorized'
      names.add(name)
      if (!idMap.has(name)) {
        idMap.set(name, dp.category_id || null)
      }
    })
    return { categoryNames: Array.from(names).sort(), nameToIdMap: idMap }
  }, [dataPoints, categories])

  const getCategoryColor = (name: string): string => {
    if (name === 'Uncategorized') return UNCATEGORIZED_COLOR
    const id = nameToIdMap.get(name)
    return id ? getCategoryColorById(id).solid : UNCATEGORIZED_COLOR
  }

  if (loading) {
    return <div className="loading-indicator">Loading time series data...</div>
  }

  if (chartData.length === 0) {
    return <div className="no-data-message">No time series data available for the selected category.</div>
  }

  return (
    <div style={{ width: '100%', height: 400 }}>
      <ResponsiveContainer>
        <BarChart data={chartData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--border-secondary)" />
          <XAxis dataKey="period" stroke="var(--text-secondary)" style={{ fontSize: 12 }} />
          <YAxis stroke="var(--text-secondary)" style={{ fontSize: 12 }} />
          <Tooltip
            contentStyle={{
              backgroundColor: 'var(--bg-primary)',
              border: '1px solid var(--border-primary)',
              borderRadius: '4px',
              color: 'var(--text-primary)',
              boxShadow: '0 4px 6px var(--shadow-light)',
            }}
            labelStyle={{ color: 'var(--text-primary)' }}
            itemStyle={{ color: 'var(--text-secondary)' }}
            formatter={(value: number) => `$${value.toFixed(2)}`}
            itemSorter={(item) => -(item.value as number)}
          />
          <Legend
            wrapperStyle={{
              paddingTop: '20px',
              color: 'var(--text-primary)',
            }}
          />
          {categoryNames.map((name) => (
            <Bar key={name} dataKey={name} stackId="1" fill={getCategoryColor(name)} animationDuration={300} />
          ))}
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}
