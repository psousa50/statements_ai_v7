import React from 'react'
import { Alert, Box } from '@mui/material'
import { SampleData } from '../../api/StatementClient'

interface ValidationMessagesProps {
  columnMapping: Record<string, string>
  sampleData: string[][]
}

export const ValidationMessages: React.FC<ValidationMessagesProps> = ({ columnMapping, sampleData }) => {
  const errors = React.useMemo(() => {
    const errorMessages = []
    
    // Check required columns
    if (!columnMapping.date) {
      errorMessages.push('Date column is required')
    }
    
    // Check for either amount or both debit_amount and credit_amount
    const hasAmount = !!columnMapping.amount;
    const hasDebitAndCredit = !!columnMapping.debit_amount && !!columnMapping.credit_amount;
    
    if (!hasAmount && !hasDebitAndCredit) {
      errorMessages.push('Either Amount column or both Debit Amount and Credit Amount columns are required')
    }
    
    if (!columnMapping.description) {
      errorMessages.push('Description column is required')
    }
    
    // For the new format, we don't check for blank values in the validation messages
    // as that would require more complex processing of the rows data
    
    return errorMessages
  }, [columnMapping, sampleData])

  const warnings = React.useMemo((): string[] => {
    const warningMessages: string[] = []
    
    // For the new format, we don't generate warnings based on the data content
    // as that would require more complex processing of the rows data
    
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
