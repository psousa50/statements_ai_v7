# Bank Statement Analyzer Frontend

Frontend web application for the Bank Statement Analyzer.

## Features

- View and manage transactions
- Upload bank statements with drag-and-drop functionality
- Customize column mappings for uploaded files
- Select transaction sources (banks)
- Categorize transactions
- Responsive design with Material UI

## Technology Stack

- React
- TypeScript
- Vite
- Material UI for components
- Axios for API communication
- React Router for navigation
- React Dropzone for file uploads
- Vitest for unit testing
- Playwright for end-to-end testing

## Setup

### Prerequisites

- Node.js 14+
- npm or yarn

### Installation

1. Clone the repository
2. Install dependencies:
   ```
   npm install
   ```
   or
   ```
   yarn
   ```

## Development

Run the development server:

```
npm run dev
```

or

```
yarn dev
```

The application will be available at http://localhost:5173.

## Building for Production

```
npm run build
```

or

```
yarn build
```

## Project Structure

- `src/components/`: Reusable UI components
  - `TransactionForm.tsx`: Form for adding transactions
  - `TransactionTable.tsx`: Table for displaying transactions
  - `upload/`: File upload components
    - `FileUploadZone.tsx`: Drag-and-drop file upload
    - `ColumnMappingTable.tsx`: Column mapping customization
    - `SourceSelector.tsx`: Source selection
    - `AnalysisSummary.tsx`: File analysis results
    - `ValidationMessages.tsx`: Validation feedback
    - `UploadFooter.tsx`: Upload actions
- `src/pages/`: Page components
  - `Transactions.tsx`: Transactions page
  - `Upload.tsx`: File upload page
- `src/services/`: API clients and hooks
  - `api/`: API clients
  - `hooks/`: React hooks
- `src/types/`: TypeScript interfaces and types
- `tests/`: Unit and integration tests

## Key Components

### File Upload Workflow

The file upload workflow consists of several steps:

1. **File Selection**: Users can drag and drop files or browse for them
2. **File Analysis**: The system analyzes the file and detects column mappings
3. **Column Mapping**: Users can customize the column mappings
4. **Source Selection**: Users can select the bank or financial institution
5. **Validation**: The system validates the mappings and provides feedback
6. **Finalization**: Users can finalize the upload and process the file

### Transaction Management

The transaction management includes:

1. **Transaction Table**: Displays transactions with sorting and filtering
2. **Transaction Form**: Allows adding new transactions manually
3. **Categorization**: Displays and allows editing transaction categories
