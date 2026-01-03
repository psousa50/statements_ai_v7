import { Category } from '../types/Transaction'

export interface CategoryColorConfig {
  gradient: string
  solid: string
}

export const PRESET_COLORS = [
  '#a78bfa',
  '#60a5fa',
  '#34d399',
  '#fbbf24',
  '#f472b6',
  '#22d3ee',
  '#fb7185',
  '#818cf8',
]

interface HSL {
  h: number
  s: number
  l: number
}

export function hexToHsl(hex: string): HSL {
  const r = parseInt(hex.slice(1, 3), 16) / 255
  const g = parseInt(hex.slice(3, 5), 16) / 255
  const b = parseInt(hex.slice(5, 7), 16) / 255

  const max = Math.max(r, g, b)
  const min = Math.min(r, g, b)
  const l = (max + min) / 2

  if (max === min) {
    return { h: 0, s: 0, l: l * 100 }
  }

  const d = max - min
  const s = l > 0.5 ? d / (2 - max - min) : d / (max + min)

  let h = 0
  switch (max) {
    case r:
      h = ((g - b) / d + (g < b ? 6 : 0)) / 6
      break
    case g:
      h = ((b - r) / d + 2) / 6
      break
    case b:
      h = ((r - g) / d + 4) / 6
      break
  }

  return { h: h * 360, s: s * 100, l: l * 100 }
}

export function hslToHex(h: number, s: number, l: number): string {
  const sNorm = s / 100
  const lNorm = l / 100

  const c = (1 - Math.abs(2 * lNorm - 1)) * sNorm
  const x = c * (1 - Math.abs(((h / 60) % 2) - 1))
  const m = lNorm - c / 2

  let r = 0,
    g = 0,
    b = 0

  if (h >= 0 && h < 60) {
    r = c
    g = x
    b = 0
  } else if (h >= 60 && h < 120) {
    r = x
    g = c
    b = 0
  } else if (h >= 120 && h < 180) {
    r = 0
    g = c
    b = x
  } else if (h >= 180 && h < 240) {
    r = 0
    g = x
    b = c
  } else if (h >= 240 && h < 300) {
    r = x
    g = 0
    b = c
  } else {
    r = c
    g = 0
    b = x
  }

  const toHex = (n: number) => {
    const hex = Math.round((n + m) * 255).toString(16)
    return hex.length === 1 ? '0' + hex : hex
  }

  return `#${toHex(r)}${toHex(g)}${toHex(b)}`
}

export function generateGradient(solidColor: string): string {
  const hsl = hexToHsl(solidColor)
  const darkerColor = hslToHex(hsl.h, hsl.s, Math.max(hsl.l - 15, 10))
  return `linear-gradient(135deg, ${solidColor}, ${darkerColor})`
}

export const CATEGORY_GRADIENT_COLORS: CategoryColorConfig[] = PRESET_COLORS.map((solid) => ({
  gradient: generateGradient(solid),
  solid,
}))

export function deriveChildColor(parentColor: string, childIndex: number, totalChildren: number): string {
  const hsl = hexToHsl(parentColor)
  const lightnessRange = 30
  const offset = totalChildren > 1 ? ((childIndex / (totalChildren - 1)) - 0.5) * lightnessRange : 0
  const newLightness = Math.min(Math.max(hsl.l + offset, 25), 75)
  return hslToHex(hsl.h, hsl.s * 0.9, newLightness)
}

function getFallbackColor(id: string): string {
  const hash = id.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0)
  return PRESET_COLORS[hash % PRESET_COLORS.length]
}

export function getCategoryColor(category: Category, allCategories: Category[]): CategoryColorConfig {
  let solidColor: string

  if (category.color) {
    solidColor = category.color
  } else if (category.parent_id) {
    const parent = allCategories.find((c) => c.id === category.parent_id)
    if (parent?.color) {
      const siblings = allCategories.filter((c) => c.parent_id === parent.id)
      const childIndex = siblings.findIndex((c) => c.id === category.id)
      solidColor = deriveChildColor(parent.color, Math.max(childIndex, 0), siblings.length)
    } else {
      solidColor = getFallbackColor(category.id)
    }
  } else {
    solidColor = getFallbackColor(category.id)
  }

  return {
    solid: solidColor,
    gradient: generateGradient(solidColor),
  }
}

export const getCategoryColorByIndex = (index: number): CategoryColorConfig => {
  return CATEGORY_GRADIENT_COLORS[index % CATEGORY_GRADIENT_COLORS.length]
}

export const getCategoryColorByName = (name: string): CategoryColorConfig => {
  const hash = name.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0)
  return getCategoryColorByIndex(hash)
}

export const getCategoryColorById = (id: number | string): CategoryColorConfig => {
  if (typeof id === 'number') {
    return getCategoryColorByIndex(id)
  }
  const numericId = parseInt(id, 10)
  if (!isNaN(numericId)) {
    return getCategoryColorByIndex(numericId)
  }
  const hash = id.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0)
  return getCategoryColorByIndex(hash)
}
