import { useState, useCallback, useEffect, useRef, useMemo } from 'react'
import { useSearchParams } from 'react-router-dom'
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from 'recharts'
import { useCategoryTotals, useCategoryTimeSeries } from '../services/hooks/useTransactions'
import { useCategories } from '../services/hooks/useCategories'
import { useAccounts } from '../services/hooks/useAccounts'
import { TransactionFilters, CategorizationFilter } from '../components/TransactionFilters'
import { CategoryTimeSeriesChart } from '../components/CategoryTimeSeriesChart'
import { CategoryTotalsBarChart } from '../components/CategoryTotalsBarChart'
import { Category } from '../types/Transaction'
import { TransactionFilters as FilterType } from '../api/TransactionClient'
import { getCategoryColor } from '../utils/categoryColors'
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

const UNCATEGORIZED_COLOR = '#EF4444'

export const ChartsPage = () => {
  const [searchParams, setSearchParams] = useSearchParams()

  const getInitialFilters = (): Omit<FilterType, 'page' | 'page_size'> => {
    const urlDescriptionSearch = searchParams.get('description_search')
    const urlMinAmount = searchParams.get('min_amount')
    const urlMaxAmount = searchParams.get('max_amount')
    const urlStartDate = searchParams.get('start_date')
    const urlEndDate = searchParams.get('end_date')
    const urlAccountId = searchParams.get('account_id')
    const urlCategoryIds = searchParams.get('category_ids')
    const urlExcludeTransfers = searchParams.get('exclude_transfers')
    const urlTransactionType = searchParams.get('transaction_type')

    return {
      description_search: urlDescriptionSearch || undefined,
      min_amount: urlMinAmount ? parseFloat(urlMinAmount) : undefined,
      max_amount: urlMaxAmount ? parseFloat(urlMaxAmount) : undefined,
      start_date: urlStartDate || undefined,
      end_date: urlEndDate || undefined,
      account_id: urlAccountId || undefined,
      category_ids: urlCategoryIds ? urlCategoryIds.split(',') : undefined,
      exclude_transfers: urlExcludeTransfers === 'false' ? false : true,
      transaction_type: (urlTransactionType as 'all' | 'debit' | 'credit') || 'all',
    }
  }

  const [filters, setFilters] = useState<Omit<FilterType, 'page' | 'page_size'>>(getInitialFilters)
  const [chartType, setChartType] = useState<'root' | 'sub'>('root')
  const [selectedRootCategory, setSelectedRootCategory] = useState<string | null>(null)
  const [transactionType, setTransactionType] = useState<'all' | 'debit' | 'credit'>(
    () => (searchParams.get('transaction_type') as 'all' | 'debit' | 'credit') || 'all'
  )
  const [categorizationFilter, setCategorizationFilter] = useState<CategorizationFilter>('categorized')
  const [viewMode, setViewMode] = useState<'pie' | 'bar' | 'timeseries'>(
    () => (searchParams.get('view') as 'pie' | 'bar' | 'timeseries') || 'bar'
  )
  const [timeSeriesPeriod, setTimeSeriesPeriod] = useState<'month' | 'week'>(
    () => (searchParams.get('period') as 'month' | 'week') || 'month'
  )

  const [localDescriptionSearch, setLocalDescriptionSearch] = useState<string>(
    searchParams.get('description_search') || ''
  )
  const [localMinAmount, setLocalMinAmount] = useState<number | undefined>(
    searchParams.get('min_amount') ? parseFloat(searchParams.get('min_amount')!) : undefined
  )
  const [localMaxAmount, setLocalMaxAmount] = useState<number | undefined>(
    searchParams.get('max_amount') ? parseFloat(searchParams.get('max_amount')!) : undefined
  )
  const [localStartDate, setLocalStartDate] = useState<string>(searchParams.get('start_date') || '')
  const [localEndDate, setLocalEndDate] = useState<string>(searchParams.get('end_date') || '')

  const debounceTimeoutRef = useRef<NodeJS.Timeout>()

  const {
    categoryTotals,
    loading: categoryTotalsLoading,
    error: categoryTotalsError,
    fetchCategoryTotals,
  } = useCategoryTotals()

  const {
    timeSeriesData,
    loading: timeSeriesLoading,
    error: timeSeriesError,
    fetchCategoryTimeSeries,
  } = useCategoryTimeSeries()

  const { categories, loading: categoriesLoading, error: categoriesError } = useCategories()
  const { accounts, loading: accountsLoading, error: accountsError } = useAccounts()

  const loading = categoryTotalsLoading || categoriesLoading || accountsLoading || timeSeriesLoading
  const error = categoryTotalsError || categoriesError || accountsError || timeSeriesError

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
          transaction_type: transactionType,
          exclude_transfers: filters.exclude_transfers,
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
    transactionType,
  ])

  useEffect(() => {
    const params = new URLSearchParams()

    if (filters.description_search) params.set('description_search', filters.description_search)
    if (filters.category_ids?.length) params.set('category_ids', filters.category_ids.join(','))
    if (filters.account_id) params.set('account_id', filters.account_id)
    if (filters.min_amount !== undefined) params.set('min_amount', filters.min_amount.toString())
    if (filters.max_amount !== undefined) params.set('max_amount', filters.max_amount.toString())
    if (filters.start_date) params.set('start_date', filters.start_date)
    if (filters.end_date) params.set('end_date', filters.end_date)
    if (filters.exclude_transfers === false) params.set('exclude_transfers', 'false')
    if (filters.transaction_type && filters.transaction_type !== 'all')
      params.set('transaction_type', filters.transaction_type)
    if (viewMode !== 'bar') params.set('view', viewMode)
    if (timeSeriesPeriod !== 'month') params.set('period', timeSeriesPeriod)

    setSearchParams(params, { replace: true })
  }, [filters, viewMode, timeSeriesPeriod, setSearchParams])

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

  const handleAccountFilter = useCallback(
    (accountId?: string) => {
      handleFilterChange({ account_id: accountId })
    },
    [handleFilterChange]
  )

  const handleExcludeTransfersFilter = useCallback(
    (excludeTransfers: boolean) => {
      handleFilterChange({ exclude_transfers: excludeTransfers })
    },
    [handleFilterChange]
  )

  const handleCategorizationFilterChange = useCallback((filter: CategorizationFilter) => {
    setCategorizationFilter(filter)
  }, [])

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

  const handleTransactionTypeFilter = useCallback(
    (type: 'all' | 'debit' | 'credit') => {
      setTransactionType(type)
      handleFilterChange({ transaction_type: type })
    },
    [handleFilterChange]
  )

  const handleClearFilters = useCallback(() => {
    const defaultFilters = {
      exclude_transfers: true,
      transaction_type: 'all' as const,
    }
    setFilters(defaultFilters)
    setLocalDescriptionSearch('')
    setLocalMinAmount(undefined)
    setLocalMaxAmount(undefined)
    setLocalStartDate('')
    setLocalEndDate('')
    setTransactionType('all')
    setCategorizationFilter('categorized')
    fetchCategoryTotals(defaultFilters)
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
        .filter(([id, _]) => !(categorizationFilter === 'categorized' && id === 'uncategorized'))
        .map(([id, data]) => ({
          id,
          name: id === 'uncategorized' ? 'Uncategorized' : categoryMap.get(id)?.name || 'Unknown',
          value: data.value,
          count: data.count,
          color:
            id === 'uncategorized' ? UNCATEGORIZED_COLOR : getCategoryColor(categoryMap.get(id)!, categories).solid,
        }))
    } else {
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
        .filter(([id, _]) => !(categorizationFilter === 'categorized' && id === 'uncategorized'))
        .map(([id, data]) => ({
          id,
          name:
            id === 'uncategorized'
              ? 'Uncategorized'
              : id === 'other'
                ? 'Other'
                : categoryMap.get(id)?.name || 'Unknown',
          value: data.value,
          count: data.count,
          color:
            id === 'uncategorized' || id === 'other'
              ? UNCATEGORIZED_COLOR
              : getCategoryColor(categoryMap.get(id)!, categories).solid,
        }))
    }
  }, [categoryTotals, categories, chartType, selectedRootCategory, categorizationFilter])

  const noDataMessage = useMemo(() => {
    if (!categoryTotals) {
      return { title: 'Loading...', description: 'Fetching transaction data.' }
    }

    if (categoryTotals.totals.length === 0) {
      return {
        title: 'No transactions found',
        description: 'Upload a bank statement or add transactions manually to see spending charts.',
      }
    }

    const totalSpending = categoryTotals.totals.reduce((sum, t) => sum + t.total_amount, 0)
    const totalCount = categoryTotals.totals.reduce((sum, t) => sum + t.transaction_count, 0)

    if (totalSpending <= 0) {
      return {
        title: 'No spending to display',
        description: `You have ${totalCount} transaction${totalCount !== 1 ? 's' : ''}, but they are all income or transfers. This chart shows spending (debits) only.`,
      }
    }

    if (categorizationFilter === 'categorized') {
      const uncategorizedTotal = categoryTotals.totals.find((t) => !t.category_id)
      if (uncategorizedTotal && uncategorizedTotal.total_amount === totalSpending) {
        return {
          title: 'All transactions are uncategorised',
          description: 'Categorise your transactions or change the Status filter to "All" to see them here.',
        }
      }
    }

    return {
      title: 'No data for selected filters',
      description: 'Try adjusting your filters or date range to see more transactions.',
    }
  }, [categoryTotals, categorizationFilter])

  const openTransactionsWindow = useCallback(
    (categoryId: string) => {
      const params = new URLSearchParams()

      if (filters.description_search) params.set('description_search', filters.description_search)
      if (filters.min_amount !== undefined) params.set('min_amount', filters.min_amount.toString())
      if (filters.max_amount !== undefined) params.set('max_amount', filters.max_amount.toString())
      if (filters.start_date) params.set('start_date', filters.start_date)
      if (filters.end_date) params.set('end_date', filters.end_date)
      if (filters.account_id) params.set('account_id', filters.account_id)
      if (filters.exclude_transfers) params.set('exclude_transfers', 'true')
      if (filters.transaction_type && filters.transaction_type !== 'all')
        params.set('transaction_type', filters.transaction_type)

      if (categoryId === 'uncategorized') {
        params.set('status', 'UNCATEGORIZED')
      } else if (categoryId !== 'other') {
        params.set('category_ids', categoryId)
      }

      window.open(`/transactions?${params.toString()}`, '_blank')
    },
    [filters]
  )

  const handleChartClick = useCallback(
    (data: ChartData) => {
      if (data.id === 'uncategorized') {
        openTransactionsWindow(data.id)
        return
      }

      if (chartType === 'root') {
        setSelectedRootCategory(data.id)
        setChartType('sub')
      } else {
        openTransactionsWindow(data.id)
      }
    },
    [chartType, openTransactionsWindow]
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

    if (percent < 0.01) return null // Don't show labels for slices less than 1%

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

  const handleViewModeChange = useCallback(
    (mode: 'pie' | 'bar' | 'timeseries') => {
      setViewMode(mode)
      if (mode === 'timeseries') {
        fetchCategoryTimeSeries(undefined, timeSeriesPeriod, filters)
      }
    },
    [timeSeriesPeriod, filters, fetchCategoryTimeSeries]
  )

  const handlePeriodChange = useCallback(
    (period: 'month' | 'week') => {
      setTimeSeriesPeriod(period)
      if (viewMode === 'timeseries') {
        fetchCategoryTimeSeries(undefined, period, filters)
      }
    },
    [viewMode, filters, fetchCategoryTimeSeries]
  )

  useEffect(() => {
    if (viewMode === 'timeseries') {
      fetchCategoryTimeSeries(undefined, timeSeriesPeriod, filters)
    }
  }, [viewMode, timeSeriesPeriod, filters, fetchCategoryTimeSeries])

  useEffect(() => {
    fetchCategoryTotals(filters)
  }, [])

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
            accounts={accounts || []}
            selectedCategoryIds={filters.category_ids}
            selectedAccountId={filters.account_id}
            minAmount={localMinAmount}
            maxAmount={localMaxAmount}
            descriptionSearch={localDescriptionSearch}
            startDate={localStartDate}
            endDate={localEndDate}
            excludeTransfers={filters.exclude_transfers}
            categorizationFilter={categorizationFilter}
            hideUncategorizedOnlyOption={true}
            transactionType={transactionType}
            transactionTypeDisabled={true}
            defaultTransactionType="all"
            defaultCategorizationFilter="categorized"
            defaultExcludeTransfers={true}
            onCategoryChange={handleCategoryFilter}
            onAccountChange={handleAccountFilter}
            onAmountRangeChange={handleAmountRangeFilter}
            onDescriptionSearchChange={handleDescriptionSearchFilter}
            onDateRangeChange={handleDateRangeFilter}
            onExcludeTransfersChange={handleExcludeTransfersFilter}
            onCategorizationFilterChange={handleCategorizationFilterChange}
            onTransactionTypeChange={handleTransactionTypeFilter}
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

            <div className="charts-controls">
              <div className="view-mode-toggle">
                <button onClick={() => handleViewModeChange('bar')} className={viewMode === 'bar' ? 'active' : ''}>
                  Bar Chart
                </button>
                <button onClick={() => handleViewModeChange('pie')} className={viewMode === 'pie' ? 'active' : ''}>
                  Pie Chart
                </button>
                <button
                  onClick={() => handleViewModeChange('timeseries')}
                  className={viewMode === 'timeseries' ? 'active' : ''}
                >
                  Time Series
                </button>
              </div>
              {viewMode === 'timeseries' && (
                <div className="period-toggle">
                  <button
                    onClick={() => handlePeriodChange('month')}
                    className={timeSeriesPeriod === 'month' ? 'active' : ''}
                  >
                    Monthly
                  </button>
                  <button
                    onClick={() => handlePeriodChange('week')}
                    className={timeSeriesPeriod === 'week' ? 'active' : ''}
                  >
                    Weekly
                  </button>
                </div>
              )}
              {chartType === 'sub' && (viewMode === 'pie' || viewMode === 'bar') && (
                <button onClick={handleBackToRoot} className="back-button">
                  ← Back to All Categories
                </button>
              )}
            </div>
          </div>

          <div className="chart-container">
            {viewMode === 'pie' ? (
              loading ? (
                <div className="loading-indicator">Loading chart data...</div>
              ) : chartData.length === 0 ? (
                <div className="no-data-message">
                  <strong>{noDataMessage.title}</strong>
                  <p>{noDataMessage.description}</p>
                </div>
              ) : (
                <ResponsiveContainer width="100%" height={500}>
                  <PieChart>
                    <Pie
                      data={chartData}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      label={renderCustomizedLabel}
                      innerRadius={100}
                      outerRadius={180}
                      paddingAngle={2}
                      fill="#8884d8"
                      dataKey="value"
                      onClick={handleChartClick}
                      style={{ cursor: 'pointer' }}
                      animationDuration={300}
                    >
                      {chartData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip
                      formatter={(value: number, _name: string, props: unknown) => {
                        const payload = (props as { payload: ChartData }).payload
                        return [
                          [`$${value.toFixed(2)}`, 'Amount'],
                          [`${payload.count} transactions`, 'Count'],
                        ]
                      }}
                      labelFormatter={(label: string) => `Category: ${label}`}
                      contentStyle={{
                        backgroundColor: 'rgba(30, 41, 59, 0.9)',
                        backdropFilter: 'blur(8px)',
                        border: '1px solid rgba(255, 255, 255, 0.1)',
                        borderRadius: '12px',
                        color: '#f1f5f9',
                        boxShadow: '0 8px 32px rgba(0, 0, 0, 0.3)',
                        padding: '12px 16px',
                      }}
                      labelStyle={{
                        color: '#f1f5f9',
                        fontWeight: 600,
                        marginBottom: '4px',
                      }}
                      itemStyle={{
                        color: '#cbd5e1',
                      }}
                    />
                  </PieChart>
                </ResponsiveContainer>
              )
            ) : viewMode === 'bar' ? (
              <CategoryTotalsBarChart
                data={chartData}
                loading={loading}
                onBarClick={handleChartClick}
                noDataMessage={noDataMessage}
              />
            ) : (
              <CategoryTimeSeriesChart
                dataPoints={timeSeriesData || []}
                categories={categories || []}
                loading={timeSeriesLoading}
              />
            )}
          </div>

          <div className="chart-help">
            {viewMode === 'pie' || viewMode === 'bar' ? (
              chartType === 'root' ? (
                <p>Click on any category to see its subcategories breakdown</p>
              ) : (
                <p>Click on any subcategory to view its transactions</p>
              )
            ) : (
              <p>Showing spending over time. Use the category filter to focus on specific categories.</p>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
