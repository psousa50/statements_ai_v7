import { expect, test, describe, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, waitFor, cleanup, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ApiProvider } from '@/api/ApiContext'
import { ErrorProvider } from '@/context/ErrorContext'
import { createMockApiClient } from '../createMockApiClient'
import { TagsPage } from '@/pages/Tags'
import { TagWithUsage } from '@/types/Transaction'

const tags: TagWithUsage[] = [
  { id: 't1', name: 'holiday', created_at: '2026-01-01T00:00:00Z', transaction_count: 3 },
  { id: 't2', name: 'refund', created_at: '2026-01-02T00:00:00Z', transaction_count: 0 },
]

const renderPage = () => {
  const apiClient = createMockApiClient()
  apiClient.tags.getAll = vi.fn().mockResolvedValue({ tags, total: tags.length })
  const renameTag = vi.fn().mockResolvedValue({ ...tags[0], name: 'holidays' })
  const deleteTag = vi.fn().mockResolvedValue(undefined)
  const createTag = vi.fn().mockResolvedValue({ id: 't3', name: 'travel', created_at: '' })
  apiClient.tags.rename = renameTag
  apiClient.tags.delete = deleteTag
  apiClient.tags.create = createTag

  const user = userEvent.setup()
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>
        <ApiProvider client={apiClient}>
          <ErrorProvider>
            <TagsPage />
          </ErrorProvider>
        </ApiProvider>
      </MemoryRouter>
    </QueryClientProvider>
  )
  return { renameTag, deleteTag, createTag, user }
}

const getModal = () => document.querySelector('.modal-content') as HTMLElement

describe('TagsPage', () => {
  beforeEach(() => vi.clearAllMocks())
  afterEach(() => cleanup())

  test('lists tags with their transaction counts', async () => {
    renderPage()

    expect(await screen.findByText('holiday')).toBeInTheDocument()
    expect(screen.getByText('3 transactions')).toBeInTheDocument()
    expect(screen.getByText('refund')).toBeInTheDocument()
    expect(screen.getByText('Unused')).toBeInTheDocument()
  })

  test('the transaction count links to the filtered transactions page', async () => {
    renderPage()

    const link = await screen.findByRole('link', { name: '3 transactions' })
    expect(link).toHaveAttribute('href', '/transactions?tag_ids=t1')
  })

  test('renames a tag', async () => {
    const { renameTag, user } = renderPage()

    await user.click((await screen.findAllByTitle('Rename tag'))[0])
    const input = await screen.findByLabelText(/tag name/i)
    await user.clear(input)
    await user.type(input, 'holidays')
    await user.click(within(getModal()).getByRole('button', { name: /rename tag/i }))

    await waitFor(() => expect(renameTag).toHaveBeenCalledWith('t1', 'holidays'))
  })

  test('creates a tag', async () => {
    const { createTag, user } = renderPage()

    await user.click(await screen.findByRole('button', { name: /create tag/i }))
    await user.type(await screen.findByLabelText(/tag name/i), 'travel')

    await user.click(within(getModal()).getByRole('button', { name: /^create tag$/i }))

    await waitFor(() => expect(createTag).toHaveBeenCalledWith('travel'))
  })

  test('deleting a tag in use warns with the transaction count', async () => {
    const { deleteTag, user } = renderPage()

    await user.click((await screen.findAllByTitle('Delete tag'))[0])

    expect(await screen.findByText(/is used by 3 transactions/)).toBeInTheDocument()
    expect(deleteTag).not.toHaveBeenCalled()
  })

  test('confirming deletes the tag', async () => {
    const { deleteTag, user } = renderPage()

    await user.click((await screen.findAllByTitle('Delete tag'))[0])
    await screen.findByText('Delete Tag')
    await user.click(screen.getByRole('button', { name: /^delete$/i }))

    await waitFor(() => expect(deleteTag).toHaveBeenCalledWith('t1'))
  })

  test('cancelling the confirmation does not delete', async () => {
    const { deleteTag, user } = renderPage()

    await user.click((await screen.findAllByTitle('Delete tag'))[0])
    await screen.findByText('Delete Tag')
    await user.click(screen.getByRole('button', { name: /cancel/i }))

    await waitFor(() => expect(screen.queryByText('Delete Tag')).not.toBeInTheDocument())
    expect(deleteTag).not.toHaveBeenCalled()
  })
})
