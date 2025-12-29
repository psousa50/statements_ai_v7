import React, { useState, useCallback, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Box, Container, Paper, Snackbar, Typography, Alert } from '@mui/material'
import { defaultApiClient } from '../api/createApiClient'
import { StatementAnalysisResponse, StatisticsPreviewResponse } from '../api/StatementClient'
import { FileUploadZone } from '../components/upload/FileUploadZone'
import { AnalysisSummary } from '../components/upload/AnalysisSummary'
import { ColumnMappingTable } from '../components/upload/ColumnMappingTable'
import { ValidationMessages } from '../components/upload/ValidationMessages'
import { UploadFooter } from '../components/upload/UploadFooter'
import { AccountSelector } from '../components/upload/AccountSelector'
import { RowFilterPanel, FilterPreview } from '../components/upload/RowFilterPanel'
import { DroppedRowsWarning } from '../components/upload/DroppedRowsWarning'
import { AnalysisErrorPanel } from '../components/upload/AnalysisErrorPanel'
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
  const [previewStats, setPreviewStats] = useState<StatisticsPreviewResponse | null>(null)
  const [isLoadingPreview, setIsLoadingPreview] = useState(false)

  // State for analysis errors
  const [analysisError, setAnalysisError] = useState<{ message: string; fileName: string } | null>(null)

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
    setAnalysisError(null)

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
      const axiosError = error as { response?: { data?: { detail?: string } } }
      const errorDetail = axiosError.response?.data?.detail || 'Unknown error occurred while analysing the file.'
      setAnalysisError({
        message: errorDetail,
        fileName: selectedFile.name,
      })
      setFile(null)
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

  const handleUpdatePreview = useCallback(async () => {
    if (!analysisResult || !rowFilter?.conditions?.length) {
      setPreviewStats(null)
      setFilterPreview(null)
      return
    }

    const validConditions = rowFilter.conditions.filter((c) => c.column_name && c.column_name.trim() !== '')
    if (validConditions.length === 0) {
      setPreviewStats(null)
      setFilterPreview(null)
      return
    }

    setIsLoadingPreview(true)
    try {
      const result = await defaultApiClient.statements.previewStatistics(analysisResult.uploaded_file_id, {
        column_mapping: columnMapping,
        header_row_index: headerRowIndex,
        data_start_row_index: dataStartRowIndex,
        row_filters: { ...rowFilter, conditions: validConditions },
        account_id: selectedAccount || undefined,
      })
      setPreviewStats(result)
      if (result.filter_preview) {
        setFilterPreview({
          total_rows: result.filter_preview.total_rows,
          included_rows: result.filter_preview.included_rows,
          excluded_rows: result.filter_preview.excluded_rows,
          included_row_indices: result.filter_preview.included_row_indices,
          excluded_row_indices: result.filter_preview.excluded_row_indices,
        })
      }
    } catch (error) {
      console.error('Error previewing statistics:', error)
    } finally {
      setIsLoadingPreview(false)
    }
  }, [analysisResult, rowFilter, columnMapping, headerRowIndex, dataStartRowIndex, selectedAccount])

  const handleClearPreview = useCallback(() => {
    setPreviewStats(null)
    setFilterPreview(null)
  }, [])

  const refreshStatsForAccount = useCallback(async () => {
    if (!analysisResult || !selectedAccount) return

    setIsLoadingPreview(true)
    try {
      const validConditions = rowFilter?.conditions?.filter((c) => c.column_name && c.column_name.trim() !== '') || []
      const result = await defaultApiClient.statements.previewStatistics(analysisResult.uploaded_file_id, {
        column_mapping: columnMapping,
        header_row_index: headerRowIndex,
        data_start_row_index: dataStartRowIndex,
        row_filters: validConditions.length > 0 ? { ...rowFilter!, conditions: validConditions } : null,
        account_id: selectedAccount,
      })
      setPreviewStats(result)
      if (result.filter_preview) {
        setFilterPreview({
          total_rows: result.filter_preview.total_rows,
          included_rows: result.filter_preview.included_rows,
          excluded_rows: result.filter_preview.excluded_rows,
          included_row_indices: result.filter_preview.included_row_indices,
          excluded_row_indices: result.filter_preview.excluded_row_indices,
        })
      } else {
        setFilterPreview(null)
      }
    } catch (error) {
      console.error('Error refreshing statistics:', error)
    } finally {
      setIsLoadingPreview(false)
    }
  }, [analysisResult, selectedAccount, rowFilter, columnMapping, headerRowIndex, dataStartRowIndex])

  useEffect(() => {
    if (analysisResult && selectedAccount) {
      refreshStatsForAccount()
    }
  }, [selectedAccount])

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

      let message = `Successfully uploaded ${result.transactions_saved} transactions`
      if (result.duplicated_transactions > 0) {
        message += `. ${result.duplicated_transactions} duplicates were skipped`
      }
      if (result.dropped_rows_count > 0) {
        message += `. ${result.dropped_rows_count} rows with invalid dates were skipped`
      }

      setNotification({
        open: true,
        message,
        severity: result.dropped_rows_count > 0 ? 'warning' : 'success',
      })

      setTimeout(() => {
        const params = new URLSearchParams()
        if (selectedAccount) {
          params.set('account_id', selectedAccount)
        }
        if (analysisResult?.date_range?.[0] && analysisResult?.date_range?.[1]) {
          params.set('start_date', analysisResult.date_range[0])
          params.set('end_date', analysisResult.date_range[1])
        }
        const queryString = params.toString()
        navigate(`/transactions${queryString ? `?${queryString}` : ''}`)
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
    setPreviewStats(null)
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
              {analysisError && (
                <AnalysisErrorPanel
                  errorMessage={analysisError.message}
                  fileName={analysisError.fileName}
                  onDismiss={() => setAnalysisError(null)}
                />
              )}
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
                  <AnalysisSummary
                    analysisData={analysisResult}
                    previewStats={previewStats}
                    isLoadingPreview={isLoadingPreview}
                  />
                </Paper>
              </Box>

              {analysisResult.dropped_rows_count > 0 && (
                <DroppedRowsWarning droppedRows={analysisResult.dropped_rows} />
              )}

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
                onUpdatePreview={handleUpdatePreview}
                onClearPreview={handleClearPreview}
                isLoadingPreview={isLoadingPreview}
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
