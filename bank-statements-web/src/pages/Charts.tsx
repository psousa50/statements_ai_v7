import { useState, useCallback, useEffect, useRef, useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from 'recharts'
import { useCategoryTotals } from '../services/hooks/useTransactions'
import { useCategories } from '../services/hooks/useCategories'
import { useSources } from '../services/hooks/useSources'
import { TransactionFilters } from '../components/TransactionFilters'
import { CategorizationStatus, Category } from '../types/Transaction'
import { TransactionFilters as FilterType } from '../api/TransactionClient'
import './ChartsPage.css'

interface ChartData {
  name: string
  value: number
  count: number
  id: string
  color: string
  parent_id?: string
}

interface LabelProps {
  cx: number
  cy: number
  midAngle: number
  innerRadius: number
  outerRadius: number
  percent: number
  name: string
  value: number
}

const COLORS = [
  '#0088FE',
  '#00C49F',
  '#FFBB28',
  '#FF8042',
  '#8884D8',
  '#82CA9D',
  '#FFC658',
  '#FF7C7C',
  '#8DD1E1',
  '#D084D0',
  '#FFB347',
  '#87CEEB',
  '#DDA0DD',
  '#98FB98',
  '#F0E68C',
]

export const ChartsPage = () => {
  const navigate = useNavigate()
  const [filters, setFilters] = useState<Omit<FilterType, 'page' | 'page_size'>>({})
  const [chartType, setChartType] = useState<'root' | 'sub'>('root')
  const [selectedRootCategory, setSelectedRootCategory] = useState<string | null>(null)

  // Local state for debounced inputs
  const [localDescriptionSearch, setLocalDescriptionSearch] = useState<string>('')
  const [localMinAmount, setLocalMinAmount] = useState<number | undefined>()
  const [localMaxAmount, setLocalMaxAmount] = useState<number | undefined>()
  const [localStartDate, setLocalStartDate] = useState<string>('')
  const [localEndDate, setLocalEndDate] = useState<string>('')

  const debounceTimeoutRef = useRef<NodeJS.Timeout>()

  const {
    categoryTotals,
    loading: categoryTotalsLoading,
    error: categoryTotalsError,
    fetchCategoryTotals,
  } = useCategoryTotals()

  const { categories, loading: categoriesLoading, error: categoriesError } = useCategories()
  const { sources, loading: sourcesLoading, error: sourcesError } = useSources()

  const loading = categoryTotalsLoading || categoriesLoading || sourcesLoading
  const error = categoryTotalsError || categoriesError || sourcesError

  // Debounced filter update for search, amount, and date inputs
  useEffect(() => {
    if (debounceTimeoutRef.current) {
      clearTimeout(debounceTimeoutRef.current)
    }

    debounceTimeoutRef.current = setTimeout(() => {
      const needsUpdate =
        localDescriptionSearch !== (filters.description_search || '') ||
        localMinAmount !== filters.min_amount ||
        localMaxAmount !== filters.max_amount ||
        localStartDate !== (filters.start_date || '') ||
        localEndDate !== (filters.end_date || '')

      if (needsUpdate) {
        const updatedFilters = {
          ...filters,
          description_search: localDescriptionSearch || undefined,
          min_amount: localMinAmount,
          max_amount: localMaxAmount,
          start_date: localStartDate || undefined,
          end_date: localEndDate || undefined,
        }
        setFilters(updatedFilters)
        fetchCategoryTotals(updatedFilters)
      }
    }, 500) // 500ms debounce

    return () => {
      if (debounceTimeoutRef.current) {
        clearTimeout(debounceTimeoutRef.current)
      }
    }
  }, [
    localDescriptionSearch,
    localMinAmount,
    localMaxAmount,
    localStartDate,
    localEndDate,
    filters,
    fetchCategoryTotals,
  ])

  const handleFilterChange = useCallback(
    (newFilters: Partial<Omit<FilterType, 'page' | 'page_size'>>) => {
      const updatedFilters = { ...filters, ...newFilters }
      setFilters(updatedFilters)
      fetchCategoryTotals(updatedFilters)
    },
    [filters, fetchCategoryTotals]
  )

  // Immediate updates (no debouncing needed)
  const handleCategoryFilter = useCallback(
    (categoryIds: string[]) => {
      handleFilterChange({ category_ids: categoryIds })
    },
    [handleFilterChange]
  )

  const handleStatusFilter = useCallback(
    (status?: CategorizationStatus) => {
      handleFilterChange({ status })
    },
    [handleFilterChange]
  )

  const handleSourceFilter = useCallback(
    (sourceId?: string) => {
      handleFilterChange({ source_id: sourceId })
    },
    [handleFilterChange]
  )

  // Debounced updates
  const handleAmountRangeFilter = useCallback((minAmount?: number, maxAmount?: number) => {
    setLocalMinAmount(minAmount)
    setLocalMaxAmount(maxAmount)
  }, [])

  const handleDescriptionSearchFilter = useCallback((search?: string) => {
    setLocalDescriptionSearch(search || '')
  }, [])

  const handleDateRangeFilter = useCallback((startDate?: string, endDate?: string) => {
    setLocalStartDate(startDate || '')
    setLocalEndDate(endDate || '')
  }, [])

  const handleClearFilters = useCallback(() => {
    setFilters({})
    setLocalDescriptionSearch('')
    setLocalMinAmount(undefined)
    setLocalMaxAmount(undefined)
    setLocalStartDate('')
    setLocalEndDate('')
    fetchCategoryTotals({})
  }, [fetchCategoryTotals])

  // Process chart data
  const chartData = useMemo(() => {
    if (!categoryTotals || !categories) return []

    const categoryMap = new Map<string, Category>()
    categories.forEach((cat) => categoryMap.set(cat.id, cat))

    // Get root categories
    const rootCategories = categories.filter((cat) => !cat.parent_id)

    if (chartType === 'root') {
      // Group by root categories
      const rootCategoryData = new Map<string, { value: number; count: number }>()

      // Initialize all root categories with 0
      rootCategories.forEach((cat) => {
        rootCategoryData.set(cat.id, { value: 0, count: 0 })
      })

      // Add uncategorized
      rootCategoryData.set('uncategorized', { value: 0, count: 0 })

      categoryTotals.totals.forEach((total) => {
        if (!total.category_id) {
          // Uncategorized transaction
          const existing = rootCategoryData.get('uncategorized')!
          existing.value += total.total_amount
          existing.count += total.transaction_count
          return
        }

        const category = categoryMap.get(total.category_id)
        if (!category) return

        // Find root category
        let rootCategory = category
        while (rootCategory.parent_id) {
          const parent = categoryMap.get(rootCategory.parent_id)
          if (!parent) break
          rootCategory = parent
        }

        const existing = rootCategoryData.get(rootCategory.id)
        if (existing) {
          existing.value += total.total_amount
          existing.count += total.transaction_count
        }
      })

      return Array.from(rootCategoryData.entries())
        .filter(([_, data]) => data.value > 0)
        .map(([id, data], index) => ({
          id,
          name: id === 'uncategorized' ? 'Uncategorized' : categoryMap.get(id)?.name || 'Unknown',
          value: data.value,
          count: data.count,
          color: COLORS[index % COLORS.length],
        }))
    } else {
      // Show subcategories of selected root category
      if (!selectedRootCategory) return []

      const subcategories =
        selectedRootCategory === 'uncategorized'
          ? []
          : categories.filter((cat) => cat.parent_id === selectedRootCategory)

      const subcategoryData = new Map<string, { value: number; count: number }>()

      // Initialize subcategories
      subcategories.forEach((cat) => {
        subcategoryData.set(cat.id, { value: 0, count: 0 })
      })

      // For uncategorized, just show uncategorized transactions
      if (selectedRootCategory === 'uncategorized') {
        subcategoryData.set('uncategorized', { value: 0, count: 0 })
      }

      categoryTotals.totals.forEach((total) => {
        if (selectedRootCategory === 'uncategorized') {
          if (!total.category_id) {
            const existing = subcategoryData.get('uncategorized')!
            existing.value += total.total_amount
            existing.count += total.transaction_count
          }
          return
        }

        if (!total.category_id) return

        const category = categoryMap.get(total.category_id)
        if (!category) return

        // Check if this transaction belongs to the selected root category
        let rootCategory = category
        while (rootCategory.parent_id) {
          const parent = categoryMap.get(rootCategory.parent_id)
          if (!parent) break
          rootCategory = parent
        }

        if (rootCategory.id !== selectedRootCategory) return

        // If the transaction's category is the root category itself, group as "Other"
        if (category.id === selectedRootCategory) {
          if (!subcategoryData.has('other')) {
            subcategoryData.set('other', { value: 0, count: 0 })
          }
          const existing = subcategoryData.get('other')!
          existing.value += total.total_amount
          existing.count += total.transaction_count
        } else {
          // Find the direct subcategory under the root
          let directSubcategory = category
          while (directSubcategory.parent_id && directSubcategory.parent_id !== selectedRootCategory) {
            const parent = categoryMap.get(directSubcategory.parent_id)
            if (!parent) break
            directSubcategory = parent
          }

          const existing = subcategoryData.get(directSubcategory.id)
          if (existing) {
            existing.value += total.total_amount
            existing.count += total.transaction_count
          }
        }
      })

      return Array.from(subcategoryData.entries())
        .filter(([_, data]) => data.value > 0)
        .map(([id, data], index) => ({
          id,
          name:
            id === 'uncategorized'
              ? 'Uncategorized'
              : id === 'other'
                ? 'Other'
                : categoryMap.get(id)?.name || 'Unknown',
          value: data.value,
          count: data.count,
          color: COLORS[index % COLORS.length],
        }))
    }
  }, [categoryTotals, categories, chartType, selectedRootCategory])

  const handleChartClick = useCallback(
    (data: ChartData) => {
      if (chartType === 'root' && data.id !== 'uncategorized') {
        setSelectedRootCategory(data.id)
        setChartType('sub')
      } else if (chartType === 'sub') {
        // Navigate to transactions page with current filters plus the selected category
        const params = new URLSearchParams()
        
        // Add current filters
        if (filters.description_search) params.set('description_search', filters.description_search)
        if (filters.min_amount !== undefined) params.set('min_amount', filters.min_amount.toString())
        if (filters.max_amount !== undefined) params.set('max_amount', filters.max_amount.toString())
        if (filters.start_date) params.set('start_date', filters.start_date)
        if (filters.end_date) params.set('end_date', filters.end_date)
        if (filters.status) params.set('status', filters.status)
        if (filters.source_id) params.set('source_id', filters.source_id)
        
        // Add category filter - for sub-categories, use the specific category ID
        if (data.id !== 'uncategorized' && data.id !== 'other') {
          params.set('category_ids', data.id)
        } else if (data.id === 'uncategorized') {
          // For uncategorized, we need to filter by status instead
          params.set('status', 'UNCATEGORIZED')
        }
        
        navigate(`/transactions?${params.toString()}`)
      }
    },
    [chartType, filters, navigate]
  )

  const handleBackToRoot = useCallback(() => {
    setChartType('root')
    setSelectedRootCategory(null)
  }, [])

  const renderCustomizedLabel = ({
    cx,
    cy,
    midAngle,
    innerRadius: _innerRadius,
    outerRadius,
    percent,
    name,
    value,
  }: LabelProps) => {
    const RADIAN = Math.PI / 180
    // Position labels outside the pie chart
    const radius = outerRadius + 30
    const x = cx + radius * Math.cos(-midAngle * RADIAN)
    const y = cy + radius * Math.sin(-midAngle * RADIAN)

    if (percent < 0.03) return null // Don't show labels for slices less than 3%

    const isRightSide = x > cx
    const textAnchor = isRightSide ? 'start' : 'end'

    return (
      <g>
        {/* Draw a line from the pie slice to the label */}
        <path
          d={`M${cx + (outerRadius + 5) * Math.cos(-midAngle * RADIAN)},${cy + (outerRadius + 5) * Math.sin(-midAngle * RADIAN)}L${cx + (outerRadius + 25) * Math.cos(-midAngle * RADIAN)},${cy + (outerRadius + 25) * Math.sin(-midAngle * RADIAN)}`}
          stroke="var(--text-secondary)"
          strokeWidth={1}
          fill="none"
        />
        {/* Category name */}
        <text
          x={x}
          y={y - 8}
          fill="var(--text-primary)"
          textAnchor={textAnchor}
          dominantBaseline="central"
          fontSize={12}
          fontWeight="bold"
        >
          {name}
        </text>
        {/* Amount and percentage */}
        <text
          x={x}
          y={y + 8}
          fill="var(--text-secondary)"
          textAnchor={textAnchor}
          dominantBaseline="central"
          fontSize={10}
        >
          ${value.toFixed(0)} ({(percent * 100).toFixed(1)}%)
        </text>
      </g>
    )
  }

  const totalAmount = chartData.reduce((sum, item) => sum + item.value, 0)
  const totalTransactions = chartData.reduce((sum, item) => sum + item.count, 0)

  // Initial load
  useEffect(() => {
    fetchCategoryTotals({})
  }, [fetchCategoryTotals])

  return (
    <div className="charts-page transactions-page">
      <header className="page-header">
        <h1>Charts & Analytics</h1>
        <p className="page-description">
          Visualize your spending patterns with interactive charts and advanced filtering
        </p>
      </header>

      {error && (
        <div className="error-message">
          <strong>Error:</strong> {error}
        </div>
      )}

      <div className="transactions-layout">
        <div className="filters-sidebar">
          <TransactionFilters
            categories={categories || []}
            sources={sources || []}
            selectedCategoryIds={filters.category_ids}
            selectedStatus={filters.status}
            selectedSourceId={filters.source_id}
            minAmount={localMinAmount}
            maxAmount={localMaxAmount}
            descriptionSearch={localDescriptionSearch}
            startDate={localStartDate}
            endDate={localEndDate}
            onCategoryChange={handleCategoryFilter}
            onStatusChange={handleStatusFilter}
            onSourceChange={handleSourceFilter}
            onAmountRangeChange={handleAmountRangeFilter}
            onDescriptionSearchChange={handleDescriptionSearchFilter}
            onDateRangeChange={handleDateRangeFilter}
            onClearFilters={handleClearFilters}
          />
        </div>

        <div className="charts-content">
          <div className="charts-header">
            <div className="charts-summary">
              <h2>
                {chartType === 'root'
                  ? 'Spending by Category'
                  : selectedRootCategory === 'uncategorized'
                    ? 'Uncategorized Transactions'
                    : `${categories?.find((c) => c.id === selectedRootCategory)?.name || ''} Breakdown`}
              </h2>
              {!loading && (
                <div className="chart-stats">
                  <span className="stat">
                    <strong>Total Amount:</strong> ${totalAmount.toFixed(2)}
                  </span>
                  <span className="stat">
                    <strong>Transactions:</strong> {totalTransactions}
                  </span>
                </div>
              )}
            </div>

            {chartType === 'sub' && (
              <button onClick={handleBackToRoot} className="back-button">
                ← Back to All Categories
              </button>
            )}
          </div>

          <div className="chart-container">
            {loading ? (
              <div className="loading-indicator">Loading chart data...</div>
            ) : chartData.length === 0 ? (
              <div className="no-data-message">No transaction data available for the selected filters.</div>
            ) : (
              <ResponsiveContainer width="100%" height={500}>
                <PieChart>
                  <Pie
                    data={chartData}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={renderCustomizedLabel}
                    outerRadius={180}
                    fill="#8884d8"
                    dataKey="value"
                    onClick={handleChartClick}
                    style={{ cursor: 'pointer' }}
                  >
                    {chartData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip
                    formatter={(value: number, name: string, props: unknown) => {
                      const payload = (props as { payload: ChartData }).payload
                      return [
                        [`$${value.toFixed(2)}`, 'Amount'],
                        [`${payload.count} transactions`, 'Count'],
                      ]
                    }}
                    labelFormatter={(label: string) => `Category: ${label}`}
                    contentStyle={{
                      backgroundColor: 'var(--bg-primary)',
                      border: '1px solid var(--border-primary)',
                      borderRadius: '4px',
                      color: 'var(--text-primary)',
                      boxShadow: '0 4px 6px var(--shadow-light)',
                    }}
                    labelStyle={{
                      color: 'var(--text-primary)',
                    }}
                    itemStyle={{
                      color: 'var(--text-secondary)',
                    }}
                  />
                </PieChart>
              </ResponsiveContainer>
            )}
          </div>

          <div className="chart-help">
            {chartType === 'root' ? (
              <p>💡 Click on any category slice to see its subcategories breakdown</p>
            ) : (
              <p>💡 Click on any subcategory slice to view its transactions</p>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
