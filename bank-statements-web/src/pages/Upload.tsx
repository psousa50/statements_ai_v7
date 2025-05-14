import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Box, Container, Paper, Snackbar, Typography, Alert, Divider } from '@mui/material'
import { defaultApiClient } from '../api/createApiClient'
import { SampleData, StatementAnalysisResponse } from '../api/StatementClient'
import { FileUploadZone } from '../components/upload/FileUploadZone'
import { AnalysisSummary } from '../components/upload/AnalysisSummary'
import { ColumnMappingTable } from '../components/upload/ColumnMappingTable'
import { ValidationMessages } from '../components/upload/ValidationMessages'
import { UploadFooter } from '../components/upload/UploadFooter'
import { SourceSelector } from '../components/upload/SourceSelector'

export const Upload: React.FC = () => {
  const navigate = useNavigate()
  
  // State for file upload and analysis
  const [file, setFile] = useState<File | null>(null)
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [isUploading, setIsUploading] = useState(false)
  const [analysisResult, setAnalysisResult] = useState<StatementAnalysisResponse | null>(null)
  const [selectedSource, setSelectedSource] = useState<string>("")
  
  // State for user edits
  const [columnMapping, setColumnMapping] = useState<Record<string, string>>({
    date: '',
    amount: '',
    description: '',
  })
  const [headerRowIndex, setHeaderRowIndex] = useState(0)
  const [dataStartRowIndex, setDataStartRowIndex] = useState(1)
  
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
    return (
      !!columnMapping.date &&
      !!columnMapping.amount &&
      !!columnMapping.description
    )
  }, [columnMapping])

  // Handle finalize upload
  const handleFinalize = async () => {
    if (!analysisResult) return
    
    setIsUploading(true)
    
    try {
      const result = await defaultApiClient.statements.uploadStatement({
        uploaded_file_id: analysisResult.uploaded_file_id,
        file_type: analysisResult.file_type,
        column_mapping: columnMapping,
        header_row_index: headerRowIndex,
        data_start_row_index: dataStartRowIndex,
        file_hash: analysisResult.file_hash,
        source: selectedSource || (file?.name || 'Unknown'),
      })
      
      // If sample_data is returned, use it for display
      if (result.sample_data) {
        console.log('Using sample_data from upload response:', result.sample_data)
      }
      
      setNotification({
        open: true,
        message: `Successfully uploaded ${result.transactions_saved} transactions`,
        severity: 'success',
      })
      
      // Navigate to transactions page after successful upload
      setTimeout(() => {
        navigate('/transactions')
      }, 2000)
    } catch (error) {
      console.error('Error uploading file:', error)
      setNotification({
        open: true,
        message: 'Error uploading file. Please try again.',
        severity: 'error',
      })
    } finally {
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
    // Don't reset the source selection to maintain user preference
  }

  return (
    <Container maxWidth="lg">
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
              <AnalysisSummary
                fileType={analysisResult.file_type}
                sampleData={analysisResult.sample_data}
              />
              
              <Paper sx={{ p: 3, mt: 3, mb: 3, bgcolor: '#f8f9fa' }}>
                <Typography variant="h6" gutterBottom>
                  Select Source Bank
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                  Choose the bank or financial institution that issued this statement.
                </Typography>
                <SourceSelector 
                  value={selectedSource} 
                  onChange={setSelectedSource} 
                />
              </Paper>
              
              <ColumnMappingTable
                sampleData={analysisResult.sample_data}
                columnMapping={columnMapping}
                headerRowIndex={headerRowIndex}
                dataStartRowIndex={dataStartRowIndex}
                onColumnMappingChange={setColumnMapping}
                onHeaderRowIndexChange={setHeaderRowIndex}
                onDataStartRowIndexChange={setDataStartRowIndex}
              />
              
              <ValidationMessages
                columnMapping={columnMapping}
                sampleData={analysisResult.sample_data}
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
