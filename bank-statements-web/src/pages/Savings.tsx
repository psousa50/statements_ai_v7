import { useEffect, useMemo, useState } from 'react'
import { useCategoryTotals } from '../services/hooks/useTransactions'
import { useCategories } from '../services/hooks/useCategories'
import { DatePeriodNavigator } from '../components/DatePeriodNavigator'
import { CATEGORY_PRIORITY_LABELS, Category, CategoryPriority } from '../types/Transaction'
import { getCategoryColor } from '../utils/categoryColors'
import ExpandMoreIcon from '@mui/icons-material/ExpandMore'
import ChevronRightIcon from '@mui/icons-material/ChevronRight'
import './SavingsPage.css'

interface CategoryRow {
  category: Category
  total: number
  count: number
  subRows: CategoryRow[]
}

const monthsInRange = (startDate?: string, endDate?: string): number => {
  if (!startDate || !endDate) return 12
  const start = new Date(startDate)
  const end = new Date(endDate)
  const ms = end.getTime() - start.getTime()
  const months = ms / (1000 * 60 * 60 * 24 * 30.4375)
  return Math.max(months, 0.25)
}

const formatCurrency = (value: number) =>
  new Intl.NumberFormat('en-IE', { style: 'currency', currency: 'EUR', maximumFractionDigits: 0 }).format(value)

const inBaseline = (p: CategoryPriority) => p === 'need' || p === 'comfort'
const inProjection = (p: CategoryPriority) => p === 'comfort' || p === 'extra'

const currentYearRange = () => {
  const now = new Date()
  const start = new Date(now.getFullYear(), 0, 1)
  const end = new Date(now.getFullYear(), 11, 31)
  const fmt = (d: Date) =>
    `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
  return { start: fmt(start), end: fmt(end) }
}

export const SavingsPage = () => {
  const initialRange = currentYearRange()
  const [startDate, setStartDate] = useState<string | undefined>(initialRange.start)
  const [endDate, setEndDate] = useState<string | undefined>(initialRange.end)
  const [expandedRoots, setExpandedRoots] = useState<Set<string>>(new Set())

  const { categoryTotals, fetchCategoryTotals, loading: totalsLoading } = useCategoryTotals()
  const { categories, updateCategory, loading: categoriesLoading } = useCategories()

  useEffect(() => {
    fetchCategoryTotals({
      start_date: startDate,
      end_date: endDate,
      exclude_uncategorized: true,
      kinds: 'expense',
    })
  }, [startDate, endDate, fetchCategoryTotals])

  const rows: CategoryRow[] = useMemo(() => {
    if (!categoryTotals || !categories) return []

    const totalByCategory = new Map<string, { value: number; count: number }>()
    categoryTotals.totals.forEach((t) => {
      if (t.category_id) {
        totalByCategory.set(t.category_id, { value: t.total_amount, count: t.transaction_count })
      }
    })

    const rootCategories = categories
      .filter((c) => !c.parent_id && c.kind === 'expense')
      .sort((a, b) => a.name.localeCompare(b.name))

    return rootCategories
      .map((root) => {
        const subs = categories
          .filter((c) => c.parent_id === root.id && c.kind === 'expense')
          .sort((a, b) => a.name.localeCompare(b.name))
          .map<CategoryRow>((sub) => {
            const t = totalByCategory.get(sub.id) ?? { value: 0, count: 0 }
            return { category: sub, total: t.value, count: t.count, subRows: [] }
          })
          .filter((sub) => sub.total > 0)
        const rootSelfTotal = totalByCategory.get(root.id) ?? { value: 0, count: 0 }
        const effectiveSubPriority = (subPriority: CategoryPriority) =>
          root.priority !== 'need' ? root.priority : subPriority
        const rootSelfCounts = inBaseline(root.priority) ? rootSelfTotal.value : 0
        const subTotalsInScope = subs.reduce(
          (s, sub) => (inBaseline(effectiveSubPriority(sub.category.priority)) ? s + sub.total : s),
          0
        )
        const totalInScope = subTotalsInScope + rootSelfCounts
        const countIncludingSubs = subs.reduce((s, r) => s + r.count, 0) + rootSelfTotal.count
        return {
          category: root,
          total: totalInScope,
          count: countIncludingSubs,
          subRows: subs,
        }
      })
      .filter((row) => row.total > 0 || row.subRows.length > 0)
      .sort((a, b) => b.total - a.total)
  }, [categoryTotals, categories])

  const effectivePriority = (row: CategoryRow, parent?: Category): CategoryPriority => {
    if (parent && parent.priority !== 'need') return parent.priority
    return row.category.priority
  }

  const baselineSpend = rows.reduce((sum, row) => {
    if (row.subRows.length === 0) {
      return inBaseline(row.category.priority) ? sum + row.total : sum
    }
    const subTotals = row.subRows.reduce(
      (s, sub) => (inBaseline(effectivePriority(sub, row.category)) ? s + sub.total : s),
      0
    )
    return sum + subTotals
  }, 0)

  const projectionTotal = rows.reduce((sum, row) => {
    if (row.subRows.length === 0) {
      return inProjection(row.category.priority) ? sum + row.total : sum
    }
    const subTotals = row.subRows.reduce(
      (s, sub) => (inProjection(effectivePriority(sub, row.category)) ? s + sub.total : s),
      0
    )
    return sum + subTotals
  }, 0)

  const totalSpend = rows.reduce((s, r) => s + r.total, 0)
  const months = monthsInRange(startDate, endDate)
  const monthlyBaseline = baselineSpend / months
  const monthlySavings = projectionTotal / months
  const annualSavings = monthlySavings * 12
  const cuttableEntries = useMemo(() => {
    type Entry = { category: Category; total: number; effective: CategoryPriority; parentName?: string }
    const entries: Entry[] = []
    rows.forEach((row) => {
      if (row.subRows.length === 0) {
        if (inProjection(row.category.priority)) {
          entries.push({ category: row.category, total: row.total, effective: row.category.priority })
        }
        return
      }
      row.subRows.forEach((sub) => {
        const eff = effectivePriority(sub, row.category)
        if (inProjection(eff)) {
          entries.push({ category: sub.category, total: sub.total, effective: eff, parentName: row.category.name })
        }
      })
    })
    return entries.sort((a, b) => b.total - a.total)
  }, [rows])

  const cuttableCount = cuttableEntries.length

  const toggleExpand = (id: string) => {
    setExpandedRoots((prev) => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }

  const changePriority = async (category: Category, priority: CategoryPriority) => {
    await updateCategory(category.id, {
      name: category.name,
      parentId: category.parent_id,
      color: category.color,
      kind: category.kind,
      priority,
      isRegular: category.is_regular,
    })
  }

  const loading = totalsLoading || categoriesLoading

  return (
    <div className="savings-page">
      <div className="page-header">
        <h1>Savings Analysis</h1>
        <p className="page-description">
          Classify each category. The baseline shows your ongoing essentials + comforts; the projection annualises what
          you'd save by cutting comforts and extras.
        </p>
      </div>

      <div className="savings-controls">
        <DatePeriodNavigator
          startDate={startDate}
          endDate={endDate}
          onChange={(s, e) => {
            setStartDate(s)
            setEndDate(e)
          }}
          defaultPeriodType="year"
        />
      </div>

      <div className="savings-summary">
        <div className="stat">
          <div className="stat-label">Baseline (Needs + Comforts)</div>
          <div className="stat-value">{formatCurrency(baselineSpend)}</div>
          <div className="stat-sub">≈ {formatCurrency(monthlyBaseline)} / month</div>
        </div>
        <div className="stat">
          <div className="stat-label">Cuttable (Comforts + Extras)</div>
          <div className="stat-value">{formatCurrency(projectionTotal)}</div>
          <div className="stat-sub">
            {cuttableCount} categor{cuttableCount === 1 ? 'y' : 'ies'}
          </div>
        </div>
        <div className="stat stat-save">
          <div className="stat-label">Projected annual savings</div>
          <div className="stat-value">{formatCurrency(annualSavings)}</div>
          <div className="stat-sub">
            ≈ {formatCurrency(monthlySavings)} / month — if you cut comforts and extras going forward
          </div>
        </div>
      </div>

      {loading && !categoryTotals ? (
        <div className="savings-loading">Loading…</div>
      ) : rows.length === 0 ? (
        <div className="savings-empty">No spending in this range.</div>
      ) : (
        <div className="savings-layout">
          <div className="savings-table">
            {rows.map((row) => {
              const isExpanded = expandedRoots.has(row.category.id)
              const hasSubs = row.subRows.length > 0
              const pct = totalSpend > 0 ? (row.total / totalSpend) * 100 : 0
              const isUnplanned = row.category.priority === 'unplanned'
              return (
                <div key={row.category.id} className="root-group">
                  <div className={`row root kind-${row.category.priority} ${isUnplanned ? 'outside-baseline' : ''}`}>
                    <button
                      type="button"
                      className="expand-btn"
                      onClick={() => hasSubs && toggleExpand(row.category.id)}
                      aria-label={isExpanded ? 'Collapse' : 'Expand'}
                      disabled={!hasSubs}
                    >
                      {hasSubs ? (
                        isExpanded ? (
                          <ExpandMoreIcon fontSize="small" />
                        ) : (
                          <ChevronRightIcon fontSize="small" />
                        )
                      ) : (
                        <span className="expand-spacer" />
                      )}
                    </button>
                    <select
                      className={`kind-select kind-${row.category.priority}`}
                      value={row.category.priority}
                      onChange={(e) => changePriority(row.category, e.target.value as CategoryPriority)}
                    >
                      {(Object.keys(CATEGORY_PRIORITY_LABELS) as CategoryPriority[]).map((p) => (
                        <option key={p} value={p}>
                          {CATEGORY_PRIORITY_LABELS[p]}
                        </option>
                      ))}
                    </select>
                    <div className="name">
                      <span
                        className="swatch"
                        style={{ background: getCategoryColor(row.category, categories).solid }}
                      />
                      {row.category.name}
                    </div>
                    <div className="amount">{formatCurrency(row.total)}</div>
                    <div className="pct">{pct.toFixed(0)}%</div>
                    <div className="bar">
                      <div className="bar-fill" style={{ width: `${Math.min(pct, 100)}%` }} />
                    </div>
                  </div>
                  {isExpanded &&
                    row.subRows.map((sub) => {
                      const subPriority = effectivePriority(sub, row.category)
                      const subPct = totalSpend > 0 ? (sub.total / totalSpend) * 100 : 0
                      const parentOverrides = row.category.priority !== 'need'
                      return (
                        <div
                          key={sub.category.id}
                          className={`row sub kind-${subPriority} ${subPriority === 'unplanned' ? 'outside-baseline' : ''}`}
                        >
                          <span className="expand-spacer" />
                          <select
                            className={`kind-select kind-${sub.category.priority}`}
                            value={sub.category.priority}
                            disabled={parentOverrides}
                            title={
                              parentOverrides
                                ? `Parent ${row.category.name} is ${CATEGORY_PRIORITY_LABELS[row.category.priority]}, which overrides.`
                                : undefined
                            }
                            onChange={(e) => changePriority(sub.category, e.target.value as CategoryPriority)}
                          >
                            {(Object.keys(CATEGORY_PRIORITY_LABELS) as CategoryPriority[]).map((p) => (
                              <option key={p} value={p}>
                                {CATEGORY_PRIORITY_LABELS[p]}
                              </option>
                            ))}
                          </select>
                          <div className="name">{sub.category.name}</div>
                          <div className="amount">{formatCurrency(sub.total)}</div>
                          <div className="pct">{subPct.toFixed(0)}%</div>
                          <div className="bar">
                            <div className="bar-fill" style={{ width: `${Math.min(subPct, 100)}%` }} />
                          </div>
                        </div>
                      )
                    })}
                </div>
              )
            })}
          </div>

          <aside className="cuttable-panel">
            <div className="cuttable-panel-header">
              <h2>Cuttable</h2>
              <span className="cuttable-panel-total">{formatCurrency(projectionTotal)}</span>
            </div>
            {cuttableEntries.length === 0 ? (
              <div className="cuttable-empty">
                Nothing marked as Comfort or Extra yet. Tag categories in the table to start.
              </div>
            ) : (
              <ul className="cuttable-list">
                {cuttableEntries.map((entry) => {
                  const pct = projectionTotal > 0 ? (entry.total / projectionTotal) * 100 : 0
                  return (
                    <li key={entry.category.id} className={`cuttable-item kind-${entry.effective}`}>
                      <div className="cuttable-item-main">
                        <div className="cuttable-item-name">
                          {entry.parentName ? <span className="parent">{entry.parentName} › </span> : null}
                          {entry.category.name}
                        </div>
                        <span className={`cuttable-kind-badge kind-${entry.effective}`}>
                          {CATEGORY_PRIORITY_LABELS[entry.effective]}
                        </span>
                      </div>
                      <div className="cuttable-item-meta">
                        <span className="cuttable-item-amount">{formatCurrency(entry.total)}</span>
                        <span className="cuttable-item-pct">{pct.toFixed(0)}%</span>
                        <button
                          type="button"
                          className="cuttable-reset"
                          onClick={() => changePriority(entry.category, 'need')}
                          title="Reset to Need (remove from cuttable)"
                        >
                          ×
                        </button>
                      </div>
                    </li>
                  )
                })}
              </ul>
            )}
          </aside>
        </div>
      )}
    </div>
  )
}
