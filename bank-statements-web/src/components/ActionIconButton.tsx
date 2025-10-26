import { IconButton, SxProps, Theme } from '@mui/material'

interface ActionIconButtonProps {
  onClick: () => void
  disabled?: boolean
  title: string
  icon: React.ReactElement
  color?: 'default' | 'error' | 'primary' | 'secondary' | 'info' | 'success' | 'warning'
  size?: 'small' | 'medium' | 'large'
  sx?: SxProps<Theme>
}

export const ActionIconButton = ({
  onClick,
  disabled = false,
  title,
  icon,
  color = 'default',
  size = 'small',
  sx,
}: ActionIconButtonProps) => {
  const defaultSx: SxProps<Theme> = {
    minWidth: '0 !important',
    padding: '4px !important',
    margin: '0 !important',
    width: '28px !important',
    height: '28px !important',
    transition: 'all 0.2s !important',
    '&:hover': {
      transform: 'scale(1.1)',
      backgroundColor: color === 'error' ? 'rgba(239, 68, 68, 0.08)' : undefined,
    },
  }

  return (
    <IconButton
      size={size}
      onClick={onClick}
      disabled={disabled}
      title={title}
      color={color}
      sx={{ ...defaultSx, ...sx }}
    >
      {icon}
    </IconButton>
  )
}
