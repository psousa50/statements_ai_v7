import React, { useState, useEffect } from 'react'
import { 
  FormControl, 
  InputLabel, 
  Select, 
  MenuItem, 
  TextField, 
  Button, 
  Dialog, 
  DialogTitle, 
  DialogContent, 
  DialogActions,
  Box,
  Typography,
  CircularProgress
} from '@mui/material'
import { defaultApiClient } from '../../api/createApiClient'
import { Source } from '../../api/SourceClient'

interface SourceSelectorProps {
  value: string
  onChange: (value: string) => void
}

export const SourceSelector: React.FC<SourceSelectorProps> = ({ value, onChange }) => {
  const [sources, setSources] = useState<Source[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [openDialog, setOpenDialog] = useState(false)
  const [newSourceName, setNewSourceName] = useState('')
  const [creatingSource, setCreatingSource] = useState(false)

  useEffect(() => {
    const fetchSources = async () => {
      try {
        setLoading(true)
        const response = await defaultApiClient.sources.getSources()
        setSources(response.sources)
        
        // If we have sources and no value is selected, select the first one
        if (response.sources.length > 0 && !value) {
          onChange(response.sources[0].name)
        }
      } catch (error) {
        console.error('Error fetching sources:', error)
        setError('Failed to load sources. Please try again.')
      } finally {
        setLoading(false)
      }
    }

    fetchSources()
  }, [value, onChange])

  const handleOpenDialog = () => {
    setOpenDialog(true)
  }

  const handleCloseDialog = () => {
    setOpenDialog(false)
    setNewSourceName('')
  }

  const handleCreateSource = async () => {
    if (!newSourceName.trim()) return

    try {
      setCreatingSource(true)
      const newSource = await defaultApiClient.sources.createSource(newSourceName.trim())
      setSources(prevSources => [...prevSources, newSource])
      onChange(newSource.name)
      handleCloseDialog()
    } catch (error) {
      console.error('Error creating source:', error)
      setError('Failed to create source. Please try again.')
    } finally {
      setCreatingSource(false)
    }
  }

  if (loading) {
    return <CircularProgress size={24} />
  }

  if (error) {
    return <Typography color="error">{error}</Typography>
  }

  return (
    <Box sx={{ mb: 2 }}>
      <FormControl fullWidth>
        <InputLabel id="source-select-label">Source Bank</InputLabel>
        <Select
          labelId="source-select-label"
          id="source-select"
          value={value}
          label="Source Bank"
          onChange={(e) => onChange(e.target.value)}
        >
          {sources.map((source) => (
            <MenuItem key={source.id} value={source.name}>
              {source.name}
            </MenuItem>
          ))}
        </Select>
      </FormControl>
      
      <Box sx={{ mt: 1 }}>
        <Button 
          variant="outlined" 
          size="small" 
          onClick={handleOpenDialog}
        >
          Add New Source
        </Button>
      </Box>

      <Dialog open={openDialog} onClose={handleCloseDialog}>
        <DialogTitle>Add New Source</DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            margin="dense"
            id="name"
            label="Source Name"
            type="text"
            fullWidth
            variant="outlined"
            value={newSourceName}
            onChange={(e) => setNewSourceName(e.target.value)}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDialog}>Cancel</Button>
          <Button 
            onClick={handleCreateSource} 
            disabled={!newSourceName.trim() || creatingSource}
            variant="contained"
          >
            {creatingSource ? <CircularProgress size={24} /> : 'Create'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}
