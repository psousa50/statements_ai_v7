import React from 'react'
import { Alert, Box } from '@mui/material'

interface ValidationMessagesProps {
  columnMapping: Record<string, string>
  sampleData: Record<string, unknown>[]
}

export const ValidationMessages: React.FC<ValidationMessagesProps> = ({ columnMapping, sampleData }) => {
  const errors = React.useMemo(() => {
    const errorMessages = []
    
    // Check required columns
    if (!columnMapping.date) {
      errorMessages.push('Date column is required')
    }
    
    if (!columnMapping.amount) {
      errorMessages.push('Amount column is required')
    }
    
    if (!columnMapping.description) {
      errorMessages.push('Description column is required')
    }
    
    // Check for blank values in required columns
    if (sampleData.length > 0) {
      const dateColumn = columnMapping.date
      const amountColumn = columnMapping.amount
      const descriptionColumn = columnMapping.description
      
      if (dateColumn && sampleData.some(row => !row[dateColumn])) {
        errorMessages.push('Some rows have blank date values')
      }
      
      if (amountColumn && sampleData.some(row => row[amountColumn] === null || row[amountColumn] === undefined)) {
        errorMessages.push('Some rows have blank amount values')
      }
    }
    
    return errorMessages
  }, [columnMapping, sampleData])

  const warnings = React.useMemo(() => {
    const warningMessages = []
    
    // Check for potential issues in the data
    if (sampleData.length > 0) {
      const amountColumn = columnMapping.amount
      
      if (amountColumn) {
        // Check if all amounts are positive (might indicate wrong sign convention)
        const allPositive = sampleData.every(row => {
          const amount = row[amountColumn]
          return typeof amount === 'number' ? amount >= 0 : true
        })
        
        if (allPositive && sampleData.length > 1) {
          warningMessages.push('All amounts are positive. Make sure expenses are represented as negative values.')
        }
      }
    }
    
    return warningMessages
  }, [columnMapping, sampleData])

  if (errors.length === 0 && warnings.length === 0) {
    return null
  }

  return (
    <Box sx={{ mb: 4 }}>
      {errors.map((error, index) => (
        <Alert key={`error-${index}`} severity="error" sx={{ mb: 1 }}>
          {error}
        </Alert>
      ))}
      
      {warnings.map((warning, index) => (
        <Alert key={`warning-${index}`} severity="warning" sx={{ mb: 1 }}>
          {warning}
        </Alert>
      ))}
    </Box>
  )
}
