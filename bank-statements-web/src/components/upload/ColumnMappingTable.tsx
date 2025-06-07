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
  useTheme,
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
  const theme = useTheme()

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
              ? theme.palette.primary.main + '30'
              : isDataStartRow
                ? theme.palette.success.main + '30'
                : 'inherit',
            fontWeight: isHeaderRow ? 'bold' : 'normal',
            color: theme.palette.text.primary,
            // Override any zebra-striping for special rows only
            '&:nth-of-type(odd)': {
              backgroundColor: isHeaderRow
                ? theme.palette.primary.main + '30'
                : isDataStartRow
                  ? theme.palette.success.main + '30'
                  : theme.palette.action.hover,
            },
            '&:nth-of-type(even)': {
              backgroundColor: isHeaderRow
                ? theme.palette.primary.main + '30'
                : isDataStartRow
                  ? theme.palette.success.main + '30'
                  : theme.palette.background.paper,
            },
          }}
        >
          <TableCell
            sx={{
              color: theme.palette.text.primary,
              padding: '4px 8px',
              textAlign: 'center',
              cursor: 'pointer',
              fontSize: '0.75rem',
              backgroundColor: isHeaderRow
                ? theme.palette.primary.main + '50'
                : isDataStartRow
                  ? theme.palette.success.main + '50'
                  : 'inherit',
              '&:hover': {
                backgroundColor: theme.palette.secondary.main + '20',
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
            const isAmountColumn = ['amount', 'credit_amount', 'debit_amount'].includes(columnType)

            // Determine color for amount columns based on positive/negative value
            const getAmountColor = () => {
              if (!isAmountColumn || !cellValue) return theme.palette.text.primary
              const numValue = parseFloat(cellValue.toString().replace(/[^-\d.]/g, ''))
              if (isNaN(numValue)) return theme.palette.text.primary
              return numValue < 0 ? theme.palette.error.main : theme.palette.success.main
            }

            return (
              <TableCell
                key={`${rowIndex}-${cellIndex}`}
                sx={{
                  color: isAmountColumn ? getAmountColor() : theme.palette.text.primary,
                  whiteSpace: 'nowrap',
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                  maxWidth: '200px',
                  backgroundColor: isAssigned ? theme.palette.info.main + '10' : 'inherit',
                  borderLeft: isAssigned ? `2px solid ${theme.palette.info.main}` : 'none',
                  borderRight: isAssigned ? `2px solid ${theme.palette.info.main}` : 'none',
                  textAlign: isAmountColumn ? 'right' : 'left',
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
            backgroundColor: theme.palette.background.paper,
          }}
          // Disable the default zebra-striping behavior
          stickyHeader
        >
          <TableHead>
            <TableRow sx={{ backgroundColor: theme.palette.background.default }}>
              <TableCell sx={{ backgroundColor: theme.palette.background.default, padding: '8px', width: '60px' }}>
                <Typography variant="body2" sx={{ fontWeight: 'bold', color: theme.palette.text.primary }}>
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
                      backgroundColor: isAssigned ? theme.palette.info.main + '30' : theme.palette.background.default,
                      padding: '8px',
                      border: isAssigned
                        ? `2px solid ${theme.palette.info.main}`
                        : `1px solid ${theme.palette.divider}`,
                    }}
                  >
                    <Typography variant="body2" sx={{ fontWeight: 'bold', mb: 1, color: theme.palette.text.primary }}>
                      {columnName}
                    </Typography>
                    <FormControl fullWidth size="small">
                      <Select
                        labelId={`column-type-label-${columnIndex}`}
                        value={columnType}
                        onChange={(e: SelectChangeEvent) => handleColumnTypeChange(columnIndex, e.target.value)}
                        sx={{
                          backgroundColor: theme.palette.background.paper,
                        }}
                      >
                        <MenuItem value="date">Date</MenuItem>
                        <MenuItem value="description">Description</MenuItem>
                        <MenuItem value="amount">Amount</MenuItem>
                        <MenuItem value="debit_amount">Debit Amount</MenuItem>
                        <MenuItem value="credit_amount">Credit Amount</MenuItem>
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
