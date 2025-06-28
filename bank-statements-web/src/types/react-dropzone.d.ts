declare module 'react-dropzone' {
  import { ComponentType } from 'react'

  export interface DropzoneProps {
    accept?: Record<string, string[]>
    disabled?: boolean
    maxFiles?: number
    maxSize?: number
    minSize?: number
    multiple?: boolean
    onDrop?: (acceptedFiles: File[], rejectedFiles: any[], event: any) => void
    onDropAccepted?: (files: File[], event: any) => void
    onDropRejected?: (files: any[], event: any) => void
    onFileDialogCancel?: () => void
    preventDropOnDocument?: boolean
    [key: string]: any
  }

  export interface DropzoneState {
    acceptedFiles: File[]
    getRootProps: (props?: any) => any
    getInputProps: (props?: any) => any
    isDragActive: boolean
    isDragAccept: boolean
    isDragReject: boolean
    open: () => void
  }

  export type DropzoneRootProps = ReturnType<DropzoneState['getRootProps']>
  export type DropzoneInputProps = ReturnType<DropzoneState['getInputProps']>

  export function useDropzone(props?: DropzoneProps): DropzoneState
}
