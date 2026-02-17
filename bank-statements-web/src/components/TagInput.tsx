import { useRef, useState, useEffect } from 'react'
import Autocomplete, { createFilterOptions } from '@mui/material/Autocomplete'
import Chip from '@mui/material/Chip'
import TextField from '@mui/material/TextField'
import { Tag } from '../types/Transaction'

interface TagOption {
  id?: string
  name: string
  isNew?: boolean
}

const filter = createFilterOptions<TagOption>()

interface TagInputProps {
  transactionId: string
  currentTags: Tag[]
  allTags: Tag[]
  onAddTag: (transactionId: string, tagId: string) => Promise<unknown>
  onRemoveTag: (transactionId: string, tagId: string) => Promise<unknown>
  onCreateTag: (name: string) => Promise<Tag | null>
  compact?: boolean
  autoFocus?: boolean
}

export const TagInput = ({
  transactionId,
  currentTags,
  allTags,
  onAddTag,
  onRemoveTag,
  onCreateTag,
  compact = false,
  autoFocus = false,
}: TagInputProps) => {
  const [inputValue, setInputValue] = useState('')
  const inputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    if (autoFocus) {
      const timer = setTimeout(() => inputRef.current?.focus(), 0)
      return () => clearTimeout(timer)
    }
  }, [autoFocus])

  const currentTagIds = new Set(currentTags.map((t) => t.id))

  const handleSelect = async (_event: unknown, value: TagOption | string | null) => {
    if (!value) return

    if (typeof value === 'string') {
      const trimmed = value.trim()
      if (!trimmed) return
      const existing = allTags.find((t) => t.name.toLowerCase() === trimmed.toLowerCase())
      if (existing && !currentTagIds.has(existing.id)) {
        await onAddTag(transactionId, existing.id)
      } else if (!existing) {
        const newTag = await onCreateTag(trimmed)
        if (newTag) await onAddTag(transactionId, newTag.id)
      }
    } else if (value.isNew) {
      const newTag = await onCreateTag(value.name)
      if (newTag) await onAddTag(transactionId, newTag.id)
    } else if (value.id) {
      await onAddTag(transactionId, value.id)
    }

    setInputValue('')
  }

  const handleRemove = async (tagId: string) => {
    await onRemoveTag(transactionId, tagId)
  }

  const options: TagOption[] = allTags.filter((t) => !currentTagIds.has(t.id)).map((t) => ({ id: t.id, name: t.name }))

  return (
    <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4, alignItems: 'center' }}>
      {currentTags.map((tag) => (
        <Chip
          key={tag.id}
          label={tag.name}
          variant="outlined"
          size="small"
          onDelete={() => handleRemove(tag.id)}
          sx={{ height: 22, fontSize: '0.75rem' }}
        />
      ))}
      <Autocomplete
        size="small"
        options={options}
        getOptionLabel={(option) => {
          if (typeof option === 'string') return option
          return option.isNew ? `Create "${option.name}"` : option.name
        }}
        inputValue={inputValue}
        onInputChange={(_event, newValue) => setInputValue(newValue)}
        onChange={handleSelect}
        value={undefined}
        filterOptions={(opts, params) => {
          const filtered = filter(opts, params)
          const inputTrimmed = params.inputValue.trim()
          if (inputTrimmed !== '' && !allTags.some((t) => t.name.toLowerCase() === inputTrimmed.toLowerCase())) {
            filtered.push({ name: inputTrimmed, isNew: true })
          }
          return filtered
        }}
        renderInput={(params) => (
          <TextField
            {...params}
            inputRef={inputRef}
            placeholder={compact ? '+' : 'Add tag...'}
            variant="standard"
            sx={{
              minWidth: compact ? 60 : 120,
              '& .MuiInput-underline:before': { borderBottom: 'none' },
              '& .MuiInput-underline:hover:before': { borderBottom: '1px solid' },
              '& .MuiInputBase-input': { fontSize: '0.75rem', padding: '2px 0' },
            }}
          />
        )}
        renderOption={(props, option) => (
          <li {...props} key={option.isNew ? `new-${option.name}` : option.id}>
            {option.isNew ? `Create "${option.name}"` : option.name}
          </li>
        )}
        selectOnFocus
        clearOnBlur
        handleHomeEndKeys
        freeSolo
        disableClearable
        sx={{
          flex: compact ? '0 0 auto' : '1 1 auto',
          '& .MuiAutocomplete-endAdornment': { display: 'none' },
        }}
      />
    </div>
  )
}
