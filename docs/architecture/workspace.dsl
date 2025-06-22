workspace "Bank Statement Analyzer" "C4 Architecture Model for Bank Statement Analyzer System" {

    model {
        # People
        user = person "User" "Individual managing personal finances who uploads and analyzes bank statements"
        
        # External Systems
        bankSystems = softwareSystem "Bank Systems" "Banking institutions that provide CSV/XLSX statement exports" "External System"
        geminiAI = softwareSystem "Google Gemini AI" "AI service for transaction categorization and schema detection" "External System"
        fileSystemExternal = softwareSystem "File System" "Operating system file storage for uploaded documents" "External System"
        
        # Main System
        bankStatementAnalyzer = softwareSystem "Bank Statement Analyzer" "Web application for importing, categorizing, and analyzing bank statements" {
            
            # Containers
            webApp = container "React Web Application" "Single-page application providing user interface for bank statement management" "React, TypeScript, Vite" "Web Browser"
            
            apiBackend = container "FastAPI Backend" "RESTful API handling business logic, file processing, and AI integration" "Python, FastAPI, SQLAlchemy" "Application Server" {
                
                # Components - API Layer
                apiRoutes = component "API Routes" "HTTP endpoints for transactions, categories, statements, and accounts" "FastAPI Router"
                requestValidation = component "Request Validation" "Pydantic models for request/response validation" "Pydantic"
                
                # Components - Service Layer (Hexagonal Architecture Core)
                transactionService = component "Transaction Service" "Business logic for transaction operations" "Python Service"
                categoryService = component "Category Service" "Business logic for category management" "Python Service"
                statementService = component "Statement Service" "Business logic for statement processing" "Python Service"
                accountService = component "Account Service" "Business logic for account management" "Python Service"
                backgroundJobService = component "Background Job Service" "Async task management and orchestration" "Python Service"
                
                # Components - File Processing
                fileTypeDetector = component "File Type Detector" "Detects CSV/XLSX file formats and validates structure" "Python"
                statementParser = component "Statement Parser" "Parses bank statement files into transaction data" "Python, Pandas"
                schemaDetector = component "Schema Detector" "Heuristic and LLM-based column mapping detection" "Python"
                transactionNormalizer = component "Transaction Normalizer" "Normalizes transaction data and handles deduplication" "Python"
                
                # Components - AI Services
                llmTransactionCategorizer = component "LLM Transaction Categorizer" "AI-powered transaction categorization" "Python"
                llmSchemaDetector = component "LLM Schema Detector" "AI-powered bank statement schema detection" "Python"
                llmCounterpartyExtractor = component "LLM Counterparty Extractor" "AI-powered counterparty identification" "Python"
                
                # Components - Rule Engine
                ruleBasedCategorizer = component "Rule-Based Categorizer" "Pattern matching for automatic categorization" "Python"
                ruleBasedCounterparty = component "Rule-Based Counterparty" "Rule-based counterparty identification" "Python"
                
                # Components - Repository Ports (Hexagonal Architecture)
                transactionPort = component "Transaction Repository Port" "Abstract interface for transaction data access" "Python Interface"
                categoryPort = component "Category Repository Port" "Abstract interface for category data access" "Python Interface"
                statementPort = component "Statement Repository Port" "Abstract interface for statement data access" "Python Interface"
                accountPort = component "Account Repository Port" "Abstract interface for account data access" "Python Interface"
                backgroundJobPort = component "Background Job Repository Port" "Abstract interface for job data access" "Python Interface"
                
                # Components - Repository Adapters (Hexagonal Architecture)
                transactionAdapter = component "Transaction Repository Adapter" "SQLAlchemy implementation for transaction data access" "SQLAlchemy"
                categoryAdapter = component "Category Repository Adapter" "SQLAlchemy implementation for category data access" "SQLAlchemy"
                statementAdapter = component "Statement Repository Adapter" "SQLAlchemy implementation for statement data access" "SQLAlchemy"
                accountAdapter = component "Account Repository Adapter" "SQLAlchemy implementation for account data access" "SQLAlchemy"
                backgroundJobAdapter = component "Background Job Repository Adapter" "SQLAlchemy implementation for job data access" "SQLAlchemy"
                
                # Components - Processing Orchestration
                transactionProcessingOrchestrator = component "Transaction Processing Orchestrator" "Coordinates transaction import and categorization workflow" "Python"
                statementUploadService = component "Statement Upload Service" "Orchestrates complete statement upload process" "Python"
            }
            
            database = container "PostgreSQL Database" "Stores transactions, categories, accounts, statements, and processing metadata" "PostgreSQL" "Database"
            
            backgroundWorker = container "Background Job Processor" "Processes long-running AI categorization and counterparty identification tasks" "Python, Celery-like"
        }
        
        # Relationships - User to System
        user -> webApp "Uses to upload statements, view transactions, manage categories" "HTTPS"
        user -> bankSystems "Downloads bank statement files" "HTTPS/Banking Portal"
        
        # Relationships - System to External
        apiBackend -> geminiAI "Sends transaction data for categorization and schema detection" "HTTPS/JSON API"
        apiBackend -> fileSystemExternal "Stores uploaded files and retrieves for processing" "File I/O"
        
        # Relationships - Container Level
        webApp -> apiBackend "Makes API calls for all operations" "JSON/HTTPS"
        apiBackend -> database "Reads from and writes to" "SQL/TCP"
        apiBackend -> backgroundWorker "Queues background jobs" "In-process"
        backgroundWorker -> database "Updates job status and results" "SQL/TCP"
        backgroundWorker -> geminiAI "Processes AI categorization requests" "HTTPS/JSON API"
        
        # Relationships - Component Level (API Routes)
        webApp -> apiRoutes "HTTP requests to REST endpoints"
        apiRoutes -> requestValidation "Validates incoming requests"
        apiRoutes -> transactionService "Delegates transaction operations"
        apiRoutes -> categoryService "Delegates category operations"
        apiRoutes -> statementService "Delegates statement operations"
        apiRoutes -> accountService "Delegates account operations"
        
        # Relationships - Service to Port (Hexagonal Architecture)
        transactionService -> transactionPort "Uses for data access"
        categoryService -> categoryPort "Uses for data access"
        statementService -> statementPort "Uses for data access"
        accountService -> accountPort "Uses for data access"
        backgroundJobService -> backgroundJobPort "Uses for data access"
        
        # Relationships - Port to Adapter (Hexagonal Architecture)
        transactionPort -> transactionAdapter "Implemented by"
        categoryPort -> categoryAdapter "Implemented by"
        statementPort -> statementAdapter "Implemented by"
        accountPort -> accountAdapter "Implemented by"
        backgroundJobPort -> backgroundJobAdapter "Implemented by"
        
        # Relationships - Adapter to Database
        transactionAdapter -> database "Executes SQL queries"
        categoryAdapter -> database "Executes SQL queries"
        statementAdapter -> database "Executes SQL queries"
        accountAdapter -> database "Executes SQL queries"
        backgroundJobAdapter -> database "Executes SQL queries"
        
        # Relationships - File Processing Flow
        statementService -> statementUploadService "Orchestrates upload process"
        statementService -> fileTypeDetector "Uses for file type detection"
        statementService -> schemaDetector "Uses for schema detection"
        statementService -> statementParser "Uses for parsing"
        statementService -> transactionNormalizer "Uses for normalization"
        statementService -> transactionProcessingOrchestrator "Uses for processing"
        statementUploadService -> fileTypeDetector "Detects file format"
        statementUploadService -> schemaDetector "Detects column mapping"
        statementUploadService -> statementParser "Parses statement data"
        statementUploadService -> transactionNormalizer "Normalizes transaction data"
        statementUploadService -> transactionProcessingOrchestrator "Processes transactions"
        
        # Relationships - Schema Detection
        schemaDetector -> llmSchemaDetector "Uses for complex schema detection"
        llmSchemaDetector -> geminiAI "Sends schema detection requests"
        
        # Relationships - Categorization Flow
        transactionProcessingOrchestrator -> ruleBasedCategorizer "Applies categorization rules"
        transactionProcessingOrchestrator -> backgroundJobService "Creates AI categorization jobs"
        backgroundJobService -> llmTransactionCategorizer "Performs AI categorization"
        llmTransactionCategorizer -> geminiAI "Sends categorization requests"
        
        # Relationships - Counterparty Identification
        transactionProcessingOrchestrator -> ruleBasedCounterparty "Applies counterparty rules"
        backgroundJobService -> llmCounterpartyExtractor "Performs AI counterparty extraction"
        backgroundJobService -> ruleBasedCategorizer "Applies rule-based categorization"
        llmTransactionCategorizer -> llmCounterpartyExtractor "Coordinates counterparty extraction"
        llmCounterpartyExtractor -> geminiAI "Sends counterparty extraction requests"
    }

    views {
        # System Context View
        systemContext bankStatementAnalyzer "SystemContext" {
            include *
            autoLayout
            title "Bank Statement Analyzer - System Context"
            description "Shows the system boundaries and external actors that interact with the Bank Statement Analyzer."
        }
        
        # Container View
        container bankStatementAnalyzer "Container" {
            include *
            autoLayout
            title "Bank Statement Analyzer - Container View"
            description "Shows the major application components and their interactions."
        }
        
        # Component View - API Backend
        component apiBackend "BackendComponents" {
            include *
            autoLayout lr
            title "FastAPI Backend - Component View"
            description "Shows the internal structure of the backend following hexagonal architecture principles."
        }
        
        # Dynamic Views - Container Level
        dynamic bankStatementAnalyzer "StatementUploadFlow" "Statement Upload and Processing Flow" {
            user -> webApp "1. Upload statement file"
            webApp -> apiBackend "2. POST /statements/upload"
            apiBackend -> geminiAI "3. AI schema analysis"
            apiBackend -> database "4. Save transactions"
            apiBackend -> backgroundWorker "5. Queue categorization job"
            autoLayout
        }
        
        dynamic bankStatementAnalyzer "CategorizationFlow" "Transaction Categorization Flow" {
            backgroundWorker -> apiBackend "1. Get uncategorized transactions"
            backgroundWorker -> geminiAI "2. AI categorization requests"
            backgroundWorker -> database "3. Update categorizations"
            backgroundWorker -> geminiAI "4. Counterparty identification"
            backgroundWorker -> database "5. Update counterparty data"
            autoLayout
        }
        
        # Dynamic Views - Component Level (Backend Internal Flow)
        dynamic apiBackend "BackendStatementProcessing" "Internal Backend Statement Processing" {
            apiRoutes -> statementService "1. Process upload request"
            statementService -> fileTypeDetector "2. Detect file type"
            statementService -> schemaDetector "3. Detect schema"
            statementService -> statementParser "4. Parse statement"
            statementService -> transactionNormalizer "5. Normalize transactions"
            statementService -> transactionProcessingOrchestrator "6. Process transactions"
            transactionProcessingOrchestrator -> backgroundJobService "7. Create categorization job"
            autoLayout
        }
        
        dynamic apiBackend "BackendCategorizationProcessing" "Internal Backend Categorization Processing" {
            backgroundJobService -> ruleBasedCategorizer "1. Apply categorization rules"
            backgroundJobService -> llmTransactionCategorizer "2. AI categorize remaining"
            llmTransactionCategorizer -> llmCounterpartyExtractor "3. Extract counterparties"
            autoLayout
        }
        
        # Styling
        styles {
            element "Person" {
                color #ffffff
                fontSize 22
                shape Person
            }
            element "External System" {
                background #999999
                color #ffffff
            }
            element "Web Browser" {
                shape WebBrowser
            }
            element "Application Server" {
                shape Cylinder
            }
            element "Database" {
                shape Cylinder
            }
        }
        
        # Themes
        theme default
    }
    
    configuration {
        # Allow multiple scope levels for comprehensive views
    }
}