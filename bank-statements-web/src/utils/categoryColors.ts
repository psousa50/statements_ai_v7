export interface CategoryColorConfig {
  gradient: string
  solid: string
}

export const CATEGORY_GRADIENT_COLORS: CategoryColorConfig[] = [
  { gradient: 'linear-gradient(135deg, #a78bfa, #7c3aed)', solid: '#a78bfa' },
  { gradient: 'linear-gradient(135deg, #60a5fa, #3b82f6)', solid: '#60a5fa' },
  { gradient: 'linear-gradient(135deg, #34d399, #10b981)', solid: '#34d399' },
  { gradient: 'linear-gradient(135deg, #fbbf24, #f59e0b)', solid: '#fbbf24' },
  { gradient: 'linear-gradient(135deg, #f472b6, #ec4899)', solid: '#f472b6' },
  { gradient: 'linear-gradient(135deg, #22d3ee, #06b6d4)', solid: '#22d3ee' },
  { gradient: 'linear-gradient(135deg, #fb7185, #f43f5e)', solid: '#fb7185' },
  { gradient: 'linear-gradient(135deg, #818cf8, #6366f1)', solid: '#818cf8' },
]

export const getCategoryColor = (index: number): CategoryColorConfig => {
  return CATEGORY_GRADIENT_COLORS[index % CATEGORY_GRADIENT_COLORS.length]
}

export const getCategoryColorByName = (name: string): CategoryColorConfig => {
  const hash = name.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0)
  return getCategoryColor(hash)
}

export const getCategoryColorById = (id: number | string): CategoryColorConfig => {
  const numericId = typeof id === 'string' ? parseInt(id, 10) : id
  return getCategoryColor(numericId)
}
