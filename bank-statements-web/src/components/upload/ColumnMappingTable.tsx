import React from 'react'
import {
  Box,
  FormControl,
  InputLabel,
  MenuItem,
  Paper,
  Select,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TextField,
  Typography,
  Tooltip,
  SelectChangeEvent,
} from '@mui/material'
import HelpOutlineIcon from '@mui/icons-material/HelpOutline'
import { SampleData } from '../../api/StatementClient'

interface ColumnMappingTableProps {
  sampleData: SampleData
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
    if (!sampleData.rows || sampleData.rows.length === 0) return []
    // Find the row with the most columns to ensure we display all data
    const maxColumns = Math.max(...sampleData.rows.map(row => row.length))
    return Array.from({ length: maxColumns }, (_, i) => i.toString())
  }, [sampleData])

  const handleColumnTypeChange = (columnIndex: string, columnType: string) => {
    const newMapping = { ...columnMapping }
    
    // Get the column name from the header row
    const headerRowIdx = sampleData.metadata.header_row_index
    const columnName = headerRowIdx >= 0 && headerRowIdx < sampleData.rows.length 
      ? sampleData.rows[headerRowIdx][parseInt(columnIndex)] || `Column ${columnIndex}`
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
    // Get the column name from the header row
    const headerRowIdx = sampleData.metadata.header_row_index
    const columnName = headerRowIdx >= 0 && headerRowIdx < sampleData.rows.length 
      ? sampleData.rows[headerRowIdx][parseInt(columnIndex)] || `Column ${columnIndex}`
      : `Column ${columnIndex}`
      
    for (const [type, col] of Object.entries(columnMapping)) {
      if (col === columnName) {
        return type
      }
    }
    
    // Check if this column is mapped in the metadata
    if (sampleData.metadata.column_mappings && sampleData.metadata.column_mappings[columnIndex]) {
      return sampleData.metadata.column_mappings[columnIndex]
    }
    
    return 'ignore'
  }

  const columnTypeTooltips = {
    date: 'The date when the transaction occurred',
    amount: 'The transaction amount (positive for income, negative for expenses)',
    description: 'The transaction description or memo',
    category: 'The category of the transaction (if available)',
    ignore: 'This column will be ignored during import',
  }

  // Display all rows including the first row with account information
  const renderTableRows = () => {
    return sampleData.rows.map((row, rowIndex) => {
      // Highlight the header and data start rows
      const isHeaderRow = rowIndex === sampleData.metadata.header_row_index
      const isDataStartRow = rowIndex === sampleData.metadata.data_start_row_index
      
      return (
        <TableRow 
          key={rowIndex}
          sx={{
            backgroundColor: isHeaderRow 
              ? 'rgba(25, 118, 210, 0.3)' 
              : isDataStartRow 
                ? 'rgba(76, 175, 80, 0.3)' 
                : '#ffffff',
            fontWeight: isHeaderRow ? 'bold' : 'normal',
            color: '#000000',
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

      <Box sx={{ mb: 3, display: 'flex', gap: 2 }}>
        <TextField
          label="Header Row Index"
          type="number"
          value={headerRowIndex}
          onChange={(e: React.ChangeEvent<HTMLInputElement>) => onHeaderRowIndexChange(parseInt(e.target.value, 10))}
          InputProps={{ inputProps: { min: 0 } }}
          size="small"
          sx={{ width: 150 }}
        />

        <TextField
          label="Data Start Row Index"
          type="number"
          value={dataStartRowIndex}
          onChange={(e: React.ChangeEvent<HTMLInputElement>) => onDataStartRowIndexChange(parseInt(e.target.value, 10))}
          InputProps={{ inputProps: { min: 0 } }}
          size="small"
          sx={{ width: 150 }}
        />
      </Box>

      {/* Sample Data Table with Column Selectors */}
      <TableContainer component={Paper} sx={{ mb: 3 }}>
        <Table size="small" sx={{ minWidth: 650, backgroundColor: '#ffffff' }}>
          <TableHead>
            <TableRow sx={{ backgroundColor: '#f5f5f5' }}>
              {columns.map((columnIndex) => {
                // Get the column name from the header row
                const headerRowIdx = sampleData.metadata.header_row_index
                const columnName = headerRowIdx >= 0 && headerRowIdx < sampleData.rows.length 
                  ? sampleData.rows[headerRowIdx][parseInt(columnIndex)] || `Column ${columnIndex}`
                  : `Column ${columnIndex}`
                  
                return (
                  <TableCell key={columnIndex} sx={{ backgroundColor: '#f5f5f5', padding: '8px' }}>
                    <Typography variant="body2" sx={{ fontWeight: 'bold', mb: 1 }}>
                      {columnName}
                    </Typography>
                    <FormControl fullWidth size="small" sx={{ backgroundColor: '#ffffff' }}>
                      <InputLabel id={`column-type-label-${columnIndex}`}>Type</InputLabel>
                      <Select
                        labelId={`column-type-label-${columnIndex}`}
                        value={getColumnType(columnIndex)}
                        label="Type"
                        onChange={(e: SelectChangeEvent) => handleColumnTypeChange(columnIndex, e.target.value)}
                      >
                        <MenuItem value="date">
                          Date
                          <Tooltip title={columnTypeTooltips.date}>
                            <HelpOutlineIcon fontSize="small" sx={{ ml: 1 }} />
                          </Tooltip>
                        </MenuItem>
                        <MenuItem value="amount">
                          Amount
                          <Tooltip title={columnTypeTooltips.amount}>
                            <HelpOutlineIcon fontSize="small" sx={{ ml: 1 }} />
                          </Tooltip>
                        </MenuItem>
                        <MenuItem value="description">
                          Description
                          <Tooltip title={columnTypeTooltips.description}>
                            <HelpOutlineIcon fontSize="small" sx={{ ml: 1 }} />
                          </Tooltip>
                        </MenuItem>
                        <MenuItem value="category">
                          Category
                          <Tooltip title={columnTypeTooltips.category}>
                            <HelpOutlineIcon fontSize="small" sx={{ ml: 1 }} />
                          </Tooltip>
                        </MenuItem>
                        <MenuItem value="ignore">
                          Ignore
                          <Tooltip title={columnTypeTooltips.ignore}>
                            <HelpOutlineIcon fontSize="small" sx={{ ml: 1 }} />
                          </Tooltip>
                        </MenuItem>
                      </Select>
                    </FormControl>
                  </TableCell>
                )
              })}
            </TableRow>
          </TableHead>
          <TableBody>
            {renderTableRows()}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  )
}
