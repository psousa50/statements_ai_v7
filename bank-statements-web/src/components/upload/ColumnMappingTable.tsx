import React from 'react'
import {
  Box,
  FormControl,
  MenuItem,
  Paper,
  Select,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography,
  SelectChangeEvent,
} from '@mui/material'

interface ColumnMappingTableProps {
  sampleData: string[][]
  columnMapping: Record<string, string>
  headerRowIndex: number
  dataStartRowIndex: number
  onColumnMappingChange: (newMapping: Record<string, string>) => void
  onHeaderRowIndexChange: (index: number) => void
  onDataStartRowIndexChange: (index: number) => void
}

export const ColumnMappingTable: React.FC<ColumnMappingTableProps> = ({
  sampleData,
  columnMapping,
  headerRowIndex,
  dataStartRowIndex,
  onColumnMappingChange,
  onHeaderRowIndexChange,
  onDataStartRowIndexChange,
}) => {
  // Get the number of columns from the sample data
  const columns = React.useMemo(() => {
    if (!sampleData || sampleData.length === 0) return []
    // Find the row with the most columns to ensure we display all data
    const maxColumns = Math.max(...sampleData.map((row) => row.length))
    return Array.from({ length: maxColumns }, (_, i) => i.toString())
  }, [sampleData])

  const handleColumnTypeChange = (columnIndex: string, columnType: string) => {
    const newMapping = { ...columnMapping }

    // Get the column name from the header row using props value, not metadata
    const columnName =
      headerRowIndex >= 0 && headerRowIndex < sampleData.length
        ? sampleData[headerRowIndex][parseInt(columnIndex)] || `Column ${columnIndex}`
        : `Column ${columnIndex}`

    // Remove the column from any existing mapping
    Object.entries(newMapping).forEach(([type, col]) => {
      if (col === columnName) {
        delete newMapping[type]
      }
    })

    // Add the new mapping if not "ignore"
    if (columnType !== 'ignore') {
      newMapping[columnType] = columnName
    }

    onColumnMappingChange(newMapping)
  }

  const getColumnType = (columnIndex: string): string => {
    // Get the column name from the header row using props value, not metadata
    const columnName =
      headerRowIndex >= 0 && headerRowIndex < sampleData.length
        ? sampleData[headerRowIndex][parseInt(columnIndex)] || `Column ${columnIndex}`
        : `Column ${columnIndex}`

    for (const [type, col] of Object.entries(columnMapping)) {
      if (col === columnName) {
        return type
      }
    }

    return 'ignore'
  }

  // Display all rows including the first row with account information
  const renderTableRows = () => {
    return sampleData.map((row, rowIndex) => {
      // Highlight the header and data start rows based on the props values, not metadata
      const isHeaderRow = rowIndex === headerRowIndex
      const isDataStartRow = rowIndex === dataStartRowIndex

      return (
        <TableRow
          key={rowIndex}
          sx={{
            backgroundColor: isHeaderRow
              ? 'rgba(25, 118, 210, 0.3)'
              : isDataStartRow
                ? 'rgba(76, 175, 80, 0.3)'
                : 'inherit',
            fontWeight: isHeaderRow ? 'bold' : 'normal',
            color: '#000000',
            // Override any zebra-striping for special rows only
            '&:nth-of-type(odd)': {
              backgroundColor: isHeaderRow
                ? 'rgba(25, 118, 210, 0.3)'
                : isDataStartRow
                  ? 'rgba(76, 175, 80, 0.3)'
                  : 'rgba(0, 0, 0, 0.04)',
            },
            '&:nth-of-type(even)': {
              backgroundColor: isHeaderRow
                ? 'rgba(25, 118, 210, 0.3)'
                : isDataStartRow
                  ? 'rgba(76, 175, 80, 0.3)'
                  : '#ffffff',
            },
          }}
        >
          <TableCell
            sx={{
              color: '#000000',
              padding: '4px 8px',
              textAlign: 'center',
              cursor: 'pointer',
              fontSize: '0.75rem',
              backgroundColor: isHeaderRow
                ? 'rgba(25, 118, 210, 0.5)'
                : isDataStartRow
                  ? 'rgba(76, 175, 80, 0.5)'
                  : 'inherit',
              '&:hover': {
                backgroundColor: 'rgba(156, 39, 176, 0.2)',
              },
            }}
            onClick={(e) => {
              e.stopPropagation()
              // Regular click for header row
              onHeaderRowIndexChange(rowIndex)
              // If new header is at or after current data start, adjust data start
              if (rowIndex >= dataStartRowIndex) {
                const newDataStartRow = Math.min(rowIndex + 1, sampleData.length - 1)
                onDataStartRowIndexChange(newDataStartRow)
              }
            }}
            onContextMenu={(e) => {
              e.preventDefault()
              e.stopPropagation()
              // Right-click for data start row
              onDataStartRowIndexChange(rowIndex)
              // If new data start is at or before current header, adjust header
              if (rowIndex <= headerRowIndex) {
                const newHeaderRow = Math.max(0, rowIndex - 1)
                onHeaderRowIndexChange(newHeaderRow)
              }
            }}
          >
            {rowIndex + 1}
          </TableCell>
          {columns.map((_, cellIndex) => {
            // Ensure we don't try to access cells that don't exist in this row
            const cellValue = cellIndex < row.length ? row[cellIndex] : ''
            const columnType = getColumnType(cellIndex.toString())
            const isAssigned = columnType !== 'ignore'

            return (
              <TableCell
                key={`${rowIndex}-${cellIndex}`}
                sx={{
                  color: '#000000',
                  whiteSpace: 'nowrap',
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                  maxWidth: '200px',
                  backgroundColor: isAssigned ? 'rgba(144, 202, 249, 0.1)' : 'inherit',
                  borderLeft: isAssigned ? '2px solid #90caf9' : 'none',
                  borderRight: isAssigned ? '2px solid #90caf9' : 'none',
                }}
              >
                {cellValue || ''}
              </TableCell>
            )
          })}
        </TableRow>
      )
    })
  }

  return (
    <Box sx={{ mb: 4 }}>
      <Typography variant="h6" gutterBottom>
        Column Mapping
      </Typography>

      <Typography variant="body2" sx={{ mb: 2, color: 'text.secondary' }}>
        Click row numbers to set header, right-click for data start: H{headerRowIndex + 1} (blue), D
        {dataStartRowIndex + 1} (green)
      </Typography>

      {/* Sample Data Table with Column Selectors */}
      <TableContainer component={Paper} sx={{ mb: 3 }}>
        <Table
          size="small"
          sx={{
            minWidth: 650,
            backgroundColor: '#ffffff',
          }}
          // Disable the default zebra-striping behavior
          stickyHeader
        >
          <TableHead>
            <TableRow sx={{ backgroundColor: '#f5f5f5' }}>
              <TableCell sx={{ backgroundColor: '#f5f5f5', padding: '8px', width: '60px' }}>
                <Typography variant="body2" sx={{ fontWeight: 'bold', color: '#000000' }}>
                  Row
                </Typography>
              </TableCell>
              {columns.map((columnIndex) => {
                // Get the column name from the header row using props value, not metadata
                const columnName =
                  headerRowIndex >= 0 && headerRowIndex < sampleData.length
                    ? sampleData[headerRowIndex][parseInt(columnIndex)] || `Column ${columnIndex}`
                    : `Column ${columnIndex}`

                const columnType = getColumnType(columnIndex)
                const isAssigned = columnType !== 'ignore'

                return (
                  <TableCell
                    key={columnIndex}
                    sx={{
                      backgroundColor: isAssigned ? 'rgba(144, 202, 249, 0.3)' : '#f5f5f5',
                      padding: '8px',
                      border: isAssigned ? '2px solid #90caf9' : '1px solid #e0e0e0',
                    }}
                  >
                    <Typography variant="body2" sx={{ fontWeight: 'bold', mb: 1, color: isAssigned ? '#ffffff' : '#000000' }}>
                      {columnName}
                    </Typography>
                    <FormControl fullWidth size="small" sx={{ backgroundColor: '#ffffff' }}>
                      <Select
                        labelId={`column-type-label-${columnIndex}`}
                        value={columnType}
                        onChange={(e: SelectChangeEvent) => handleColumnTypeChange(columnIndex, e.target.value)}
                      >
                        <MenuItem value="date">Date</MenuItem>
                        <MenuItem value="amount">Amount</MenuItem>
                        <MenuItem value="debit_amount">Debit Amount</MenuItem>
                        <MenuItem value="credit_amount">Credit Amount</MenuItem>
                        <MenuItem value="description">Description</MenuItem>
                        <MenuItem value="category">Category</MenuItem>
                        <MenuItem value="balance">Balance</MenuItem>
                        <MenuItem value="ignore">Ignore</MenuItem>
                      </Select>
                    </FormControl>
                  </TableCell>
                )
              })}
            </TableRow>
          </TableHead>
          <TableBody>{renderTableRows()}</TableBody>
        </Table>
      </TableContainer>
    </Box>
  )
}
