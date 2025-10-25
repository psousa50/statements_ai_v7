import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Box, Container, Paper, Snackbar, Typography, Alert } from '@mui/material'
import { defaultApiClient } from '../api/createApiClient'
import { StatementAnalysisResponse } from '../api/StatementClient'
import { FileUploadZone } from '../components/upload/FileUploadZone'
import { AnalysisSummary } from '../components/upload/AnalysisSummary'
import { ColumnMappingTable } from '../components/upload/ColumnMappingTable'
import { ValidationMessages } from '../components/upload/ValidationMessages'
import { UploadFooter } from '../components/upload/UploadFooter'
import { AccountSelector } from '../components/upload/AccountSelector'
import { RowFilterPanel, FilterPreview } from '../components/upload/RowFilterPanel'
import type { RowFilter } from '../components/upload/RowFilterPanel'

export const Upload: React.FC = () => {
  const navigate = useNavigate()

  // State for file upload and analysis
  const [file, setFile] = useState<File | null>(null)
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [isUploading, setIsUploading] = useState(false)
  const [analysisResult, setAnalysisResult] = useState<StatementAnalysisResponse | null>(null)
  const [selectedAccount, setSelectedAccount] = useState<string>('')

  // State for user edits
  const [columnMapping, setColumnMapping] = useState<Record<string, string>>({
    date: '',
    amount: '',
    description: '',
  })
  const [headerRowIndex, setHeaderRowIndex] = useState(0)
  const [dataStartRowIndex, setDataStartRowIndex] = useState(1)
  const [rowFilter, setRowFilter] = useState<RowFilter | null>(null)
  const [filterPreview, setFilterPreview] = useState<FilterPreview | null>(null)

  // State for notifications
  const [notification, setNotification] = useState<{
    open: boolean
    message: string
    severity: 'success' | 'error' | 'info' | 'warning'
  }>({
    open: false,
    message: '',
    severity: 'info',
  })

  // Handle file selection
  const handleFileSelected = async (selectedFile: File) => {
    setFile(selectedFile)
    setIsAnalyzing(true)

    try {
      const result = await defaultApiClient.statements.analyzeStatement(selectedFile)
      setAnalysisResult(result)

      // Set initial values from analysis
      setColumnMapping(result.column_mapping)
      setHeaderRowIndex(result.header_row_index)
      setDataStartRowIndex(result.data_start_row_index)

      if (result.account_id) {
        setSelectedAccount(result.account_id)
      }

      setNotification({
        open: true,
        message: 'File analyzed successfully',
        severity: 'success',
      })
    } catch (error) {
      console.error('Error analyzing file:', error)
      setNotification({
        open: true,
        message: 'Error analyzing file. Please try again.',
        severity: 'error',
      })
    } finally {
      setIsAnalyzing(false)
    }
  }

  // Check if the mapping is valid
  const isValid = React.useMemo(() => {
    // Check for either amount or both debit_amount and credit_amount
    const hasAmount = !!columnMapping.amount
    const hasDebitAndCredit = !!columnMapping.debit_amount && !!columnMapping.credit_amount

    return !!columnMapping.date && (hasAmount || hasDebitAndCredit) && !!columnMapping.description && !!selectedAccount
  }, [columnMapping, selectedAccount])

  // Handle finalize upload
  const handleFinalize = async () => {
    if (!analysisResult) return

    setIsUploading(true)

    try {
      const result = await defaultApiClient.statements.uploadStatement({
        uploaded_file_id: analysisResult.uploaded_file_id,
        column_mapping: columnMapping,
        header_row_index: headerRowIndex,
        data_start_row_index: dataStartRowIndex,
        account_id: selectedAccount || file?.name || 'Unknown',
        row_filters: rowFilter,
      })

      // If sample_data is returned, use it for display
      if (result.sample_data) {
        console.log('Using sample_data from upload response:', result.sample_data)
      }

      setNotification({
        open: true,
        message:
          result.duplicated_transactions > 0
            ? `Successfully uploaded ${result.transactions_saved} transactions. ${result.duplicated_transactions} duplicates were skipped.`
            : `Successfully uploaded ${result.transactions_saved} transactions`,
        severity: 'success',
      })

      setTimeout(() => {
        const url = selectedAccount
          ? `/transactions?account_id=${encodeURIComponent(selectedAccount)}`
          : '/transactions'
        navigate(url)
      }, 2000)
    } catch (error) {
      console.error('Error uploading file:', error)
      setNotification({
        open: true,
        message: 'Error uploading file. Please try again.',
        severity: 'error',
      })
      setIsUploading(false)
    }
  }

  // Handle cancel
  const handleCancel = () => {
    setFile(null)
    setAnalysisResult(null)
    setColumnMapping({
      date: '',
      amount: '',
      description: '',
    })
    setRowFilter(null)
    setFilterPreview(null)
    // Don't reset the source selection to maintain user preference
  }

  return (
    <Container maxWidth={false}>
      <Box sx={{ my: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          Upload Bank Statement
        </Typography>

        <Paper sx={{ p: 3, mb: 3 }}>
          {!analysisResult ? (
            <>
              <FileUploadZone onFileSelected={handleFileSelected} isLoading={isAnalyzing} />
            </>
          ) : (
            <>
              <Box sx={{ display: 'flex', gap: 3, mb: 3, alignItems: 'flex-start' }}>
                <Paper variant="outlined" sx={{ p: 3, flex: '0 0 300px' }}>
                  <Typography variant="h6" gutterBottom>
                    Select Account Bank
                  </Typography>
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                    Choose the bank or financial institution that issued this statement.
                  </Typography>
                  <AccountSelector value={selectedAccount} onChange={setSelectedAccount} />
                </Paper>

                <Paper variant="outlined" sx={{ p: 3, flex: 1 }}>
                  <AnalysisSummary analysisData={analysisResult} />
                </Paper>
              </Box>

              <ColumnMappingTable
                sampleData={analysisResult.sample_data}
                columnMapping={columnMapping}
                headerRowIndex={headerRowIndex}
                dataStartRowIndex={dataStartRowIndex}
                onColumnMappingChange={setColumnMapping}
                onHeaderRowIndexChange={setHeaderRowIndex}
                onDataStartRowIndexChange={setDataStartRowIndex}
              />

              <RowFilterPanel
                sampleData={analysisResult.sample_data}
                columnMapping={columnMapping}
                headerRowIndex={headerRowIndex}
                dataStartRowIndex={dataStartRowIndex}
                rowFilter={rowFilter}
                onRowFilterChange={setRowFilter}
                filterPreview={filterPreview}
                suggestedFilters={analysisResult.suggested_filters}
                savedRowFilters={analysisResult.saved_row_filters}
              />

              <ValidationMessages
                columnMapping={columnMapping}
                sampleData={analysisResult.sample_data}
                selectedAccount={selectedAccount}
              />

              <UploadFooter
                isValid={isValid}
                isUploading={isUploading}
                onFinalize={handleFinalize}
                onCancel={handleCancel}
              />
            </>
          )}
        </Paper>
      </Box>

      <Snackbar
        open={notification.open}
        autoHideDuration={6000}
        onClose={() => setNotification({ ...notification, open: false })}
      >
        <Alert severity={notification.severity} onClose={() => setNotification({ ...notification, open: false })}>
          {notification.message}
        </Alert>
      </Snackbar>
    </Container>
  )
}
