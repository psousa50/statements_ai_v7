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

interface ColumnMappingTableProps {
  sampleData: Record<string, unknown>[]
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
  // Extract column names from the first row of sample data
  const columns = React.useMemo(() => {
    if (sampleData.length === 0) return []
    return Object.keys(sampleData[0])
  }, [sampleData])

  const handleColumnTypeChange = (columnName: string, columnType: string) => {
    const newMapping = { ...columnMapping }

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

  const getColumnType = (columnName: string): string => {
    for (const [type, col] of Object.entries(columnMapping)) {
      if (col === columnName) {
        return type
      }
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

      <TableContainer component={Paper}>
        <Table size="small">
          <TableHead>
            <TableRow>
              {columns.map((column) => (
                <TableCell key={column}>
                  <FormControl fullWidth size="small">
                    <InputLabel id={`column-type-label-${column}`}>Type</InputLabel>
                    <Select
                      labelId={`column-type-label-${column}`}
                      value={getColumnType(column)}
                      label="Type"
                      onChange={(e: SelectChangeEvent) => handleColumnTypeChange(column, e.target.value)}
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
                  <Typography variant="body2" sx={{ mt: 1 }}>
                    {column}
                  </Typography>
                </TableCell>
              ))}
            </TableRow>
          </TableHead>
          <TableBody>
            {sampleData.slice(0, 10).map((row, rowIndex) => (
              <TableRow key={rowIndex}>
                {columns.map((column) => (
                  <TableCell key={`${rowIndex}-${column}`}>{String(row[column] || '')}</TableCell>
                ))}
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  )
}
