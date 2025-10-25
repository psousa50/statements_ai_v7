declare module 'react-dropzone' {
  import { DragEvent, ChangeEvent } from 'react'

  export interface FileRejection {
    file: File
    errors: Array<{ code: string; message: string }>
  }

  export interface DropzoneProps {
    accept?: Record<string, string[]>
    disabled?: boolean
    maxFiles?: number
    maxSize?: number
    minSize?: number
    multiple?: boolean
    onDrop?: (acceptedFiles: File[], rejectedFiles: FileRejection[], event: DragEvent | ChangeEvent) => void
    onDropAccepted?: (files: File[], event: DragEvent | ChangeEvent) => void
    onDropRejected?: (files: FileRejection[], event: DragEvent | ChangeEvent) => void
    onFileDialogCancel?: () => void
    preventDropOnDocument?: boolean
  }

  export interface DropzoneRootProps {
    onKeyDown: (event: React.KeyboardEvent) => void
    onFocus: () => void
    onBlur: () => void
    onClick: () => void
    onDragEnter: (event: DragEvent) => void
    onDragOver: (event: DragEvent) => void
    onDragLeave: (event: DragEvent) => void
    onDrop: (event: DragEvent) => void
    tabIndex?: number
  }

  export interface DropzoneInputProps {
    accept?: string
    multiple?: boolean
    type: string
    style: { display: string }
    onChange: (event: ChangeEvent<HTMLInputElement>) => void
    onClick: (event: React.MouseEvent) => void
    tabIndex: number
  }

  export interface DropzoneState {
    acceptedFiles: File[]
    getRootProps: <T extends DropzoneRootProps>(props?: T) => T & DropzoneRootProps
    getInputProps: <T extends DropzoneInputProps>(props?: T) => T & DropzoneInputProps
    isDragActive: boolean
    isDragAccept: boolean
    isDragReject: boolean
    open: () => void
  }

  export function useDropzone(props?: DropzoneProps): DropzoneState
}
