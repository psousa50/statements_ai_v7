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

  const handleRowClick = (rowIndex: number) => {
    // Regular click to select header row
    if (rowIndex < dataStartRowIndex) {
      onHeaderRowIndexChange(rowIndex)
    } else {
      // If clicking on or after data start row, adjust data start row
      onHeaderRowIndexChange(rowIndex)
      const newDataStartRow = Math.min(rowIndex + 1, sampleData.length - 1)
      onDataStartRowIndexChange(newDataStartRow)
    }
  }

  const handleRowDoubleClick = (rowIndex: number) => {
    // Double-click to select data start row
    if (rowIndex > headerRowIndex) {
      onDataStartRowIndexChange(rowIndex)
    } else {
      // If double-clicking on or before header row, adjust header row first
      const newHeaderRow = Math.max(0, rowIndex - 1)
      onHeaderRowIndexChange(newHeaderRow)
      onDataStartRowIndexChange(rowIndex)
    }
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
          hover
          onClick={() => handleRowClick(rowIndex)}
          onDoubleClick={() => handleRowDoubleClick(rowIndex)}
          sx={{
            backgroundColor: isHeaderRow
              ? 'rgba(25, 118, 210, 0.3)'
              : isDataStartRow
                ? 'rgba(76, 175, 80, 0.3)'
                : 'inherit',
            fontWeight: isHeaderRow ? 'bold' : 'normal',
            color: '#000000',
            cursor: 'pointer',
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
            // Hover styles must come after zebra-striping to override them
            '&:hover': {
              backgroundColor: isHeaderRow
                ? '#bbdefb !important'
                : isDataStartRow
                  ? '#c8e6c9 !important'
                  : 'rgba(156, 39, 176, 0.1) !important',
            },
          }}
        >
          {columns.map((_, cellIndex) => {
            // Ensure we don't try to access cells that don't exist in this row
            const cellValue = cellIndex < row.length ? row[cellIndex] : ''
            return (
              <TableCell
                key={`${rowIndex}-${cellIndex}`}
                sx={{
                  color: '#000000',
                  whiteSpace: 'nowrap',
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                  maxWidth: '200px',
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

      <Typography variant="body2" sx={{ mb: 3, color: 'text.secondary' }}>
        Click on rows to select header row, double-click to select data start row: Header Row {headerRowIndex} (blue),
        Data Start Row {dataStartRowIndex} (green).
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
              {columns.map((columnIndex) => {
                // Get the column name from the header row using props value, not metadata
                const columnName =
                  headerRowIndex >= 0 && headerRowIndex < sampleData.length
                    ? sampleData[headerRowIndex][parseInt(columnIndex)] || `Column ${columnIndex}`
                    : `Column ${columnIndex}`

                return (
                  <TableCell key={columnIndex} sx={{ backgroundColor: '#f5f5f5', padding: '8px' }}>
                    <Typography variant="body2" sx={{ fontWeight: 'bold', mb: 1, color: '#000000' }}>
                      {columnName}
                    </Typography>
                    <FormControl fullWidth size="small" sx={{ backgroundColor: '#ffffff' }}>
                      <Select
                        labelId={`column-type-label-${columnIndex}`}
                        value={getColumnType(columnIndex)}
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
