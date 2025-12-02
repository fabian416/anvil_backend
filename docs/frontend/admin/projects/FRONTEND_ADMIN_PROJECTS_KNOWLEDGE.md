# FRONTEND_ADMIN_PROJECTS_KNOWLEDGE

## Admin Project Knowledge Base Module

**User Type:** Admin  
**Module:** Knowledge Base Management  
**Route:** `/admin/projects/:id/knowledge`  
**Access Level:** Full CRUD (Admin)

---

## 📋 Module Overview

### Title
**Knowledge Base** - Project-Specific RAG Content Management

### Description
Document and content management interface for project knowledge bases. Enables administrators to upload, organize, and manage documents that provide contextual information for AI responses within specific projects. Supports RAG (Retrieval Augmented Generation) with vector embeddings for semantic search.

### Key Capabilities
- Upload and manage documents (guides, FAQs, references, data sheets)
- Automatic text chunking and embedding generation
- Semantic search testing for query relevance
- Document priority and categorization
- Version history and rollback
- Bulk import/export functionality
- Reindexing management

---

## 👤 User Stories

### US-ADMIN-KB-001: View Knowledge Base Overview
**As a** platform administrator  
**I want to** see all documents in a project's knowledge base  
**So that** I can understand what information is available to the AI

**Acceptance Criteria:**
- List view of all documents with metadata
- Document count, total chunks, and storage usage
- Last indexed timestamp
- Filter by document type, status, and tags
- Search documents by title or content
- Sort by date, priority, or size

### US-ADMIN-KB-002: Add New Document
**As a** platform administrator  
**I want to** add documents to the knowledge base  
**So that** the AI has more context for user queries

**Acceptance Criteria:**
- Multiple input methods: paste text, upload file, URL import
- Supported formats: TXT, MD, PDF, DOCX, HTML
- Required fields: title, type, content
- Optional: tags, priority, source URL
- Automatic chunking preview before save
- Estimated embedding generation time shown
- Progress indicator during processing

### US-ADMIN-KB-003: Edit Document Content
**As a** platform administrator  
**I want to** modify existing documents  
**So that** I can keep information current

**Acceptance Criteria:**
- Inline content editor with markdown support
- Side-by-side preview option
- Track changes highlighting
- Auto-save drafts
- Require re-indexing after significant changes
- Version history with diff view
- Rollback capability

### US-ADMIN-KB-004: Test Knowledge Retrieval
**As a** platform administrator  
**I want to** test how queries retrieve knowledge  
**So that** I can verify the system is finding relevant content

**Acceptance Criteria:**
- Query input field
- Display retrieved chunks with relevance scores
- Show which documents were matched
- Adjust similarity threshold for testing
- Compare results with different top_k values
- Highlight matched sections in original document

### US-ADMIN-KB-005: Manage Document Organization
**As a** platform administrator  
**I want to** organize documents with tags and priorities  
**So that** important content is weighted appropriately

**Acceptance Criteria:**
- Drag-and-drop priority reordering
- Multi-tag assignment with autocomplete
- Bulk tag operations
- Document type categorization
- Archive without deleting
- Collection/folder organization

### US-ADMIN-KB-006: Trigger Reindexing
**As a** platform administrator  
**I want to** manually trigger reindexing  
**So that** I can ensure embeddings are up-to-date

**Acceptance Criteria:**
- Reindex single document or entire knowledge base
- Progress indicator with estimated time
- Background processing with notification on completion
- Option to cancel in-progress reindex
- Show last successful index timestamp
- Error reporting for failed chunks

### US-ADMIN-KB-007: Import/Export Documents
**As a** platform administrator  
**I want to** bulk import and export documents  
**So that** I can migrate content between projects

**Acceptance Criteria:**
- Export as ZIP with metadata JSON
- Import from ZIP maintaining structure
- CSV import for simple documents
- Duplicate detection on import
- Import preview with conflict resolution
- Progress tracking for large imports

---

## 🖼️ Views & Wireframes

### View 1: Knowledge Base Overview

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  📚 Knowledge Base: Aave Project                          [+ Add Document] [⋮ More] │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  ┌─ Summary ───────────────────────────────────────────────────────────────────────┐│
│  │  📄 12 Documents    🧩 847 Chunks    💾 2.4 MB    🕐 Indexed: 2h ago            ││
│  │     3 pending          Avg: 71/doc       Total       All documents current      ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│                                                                                      │
│  ┌─ Filters ───────────────────────────────────────────────────────────────────────┐│
│  │ [🔍 Search documents...]   Type: [All ▼]   Status: [All ▼]   Tags: [Select ▼]  ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│                                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │ □ │ DOCUMENT                        │ TYPE      │ CHUNKS │ PRIORITY │ UPDATED   ││
│  ├───┼─────────────────────────────────┼───────────┼────────┼──────────┼───────────┤│
│  │ □ │ 📘 Aave V3 Complete Guide       │ 📖 Guide  │ 245    │ ⭐⭐⭐   │ 3 days    ││
│  │   │ Comprehensive guide to Aave V3   │           │        │          │           ││
│  │   │ 🏷️ lending, borrowing, v3       │           │        │          │           ││
│  ├───┼─────────────────────────────────┼───────────┼────────┼──────────┼───────────┤│
│  │ □ │ 📘 Health Factor Explained      │ 📖 Guide  │ 89     │ ⭐⭐⭐   │ 1 week    ││
│  │   │ Understanding liquidation risks  │           │        │          │           ││
│  │   │ 🏷️ health, liquidation, risk    │           │        │          │           ││
│  ├───┼─────────────────────────────────┼───────────┼────────┼──────────┼───────────┤│
│  │ □ │ ❓ Aave FAQ                     │ 💬 FAQ    │ 156    │ ⭐⭐     │ 2 weeks   ││
│  │   │ Frequently asked questions       │           │        │          │           ││
│  │   │ 🏷️ faq, common-questions        │           │        │          │           ││
│  ├───┼─────────────────────────────────┼───────────┼────────┼──────────┼───────────┤│
│  │ □ │ 📊 Interest Rate Models         │ 📋 Ref    │ 67     │ ⭐⭐     │ 1 month   ││
│  │   │ Technical reference for rates    │           │        │          │           ││
│  │   │ 🏷️ rates, technical, models     │           │        │          │           ││
│  ├───┼─────────────────────────────────┼───────────┼────────┼──────────┼───────────┤│
│  │ □ │ 📈 Current APY Rates            │ 📊 Data   │ 12     │ ⭐       │ Auto-sync ││
│  │   │ Live rate data from DeFi Llama   │           │        │          │           ││
│  │   │ 🏷️ apy, rates, live-data        │           │        │          │ 🔄 Live   ││
│  ├───┼─────────────────────────────────┼───────────┼────────┼──────────┼───────────┤│
│  │ □ │ 📢 GHO Stablecoin Launch        │ 📣 News   │ 45     │ ⭐       │ 2 months  ││
│  │   │ Announcement about GHO           │           │        │          │           ││
│  │   │ 🏷️ gho, stablecoin, news        │           │        │          │           ││
│  └───┴─────────────────────────────────┴───────────┴────────┴──────────┴───────────┘│
│                                                                                      │
│  ┌─ Selected: 0 ───────────────────────────────────────────────────────────────────┐│
│  │ [Select All]  [🗑️ Delete]  [🏷️ Add Tags]  [⭐ Set Priority]  [📤 Export]       ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│                                                                                      │
│  Showing 6 of 12 documents                                      [< 1 2 >] [20 ▼]   │
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### View 2: Add/Edit Document

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  📄 Add Document to Knowledge Base                                          [✕]     │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  INPUT METHOD                                                                       │
│  ┌───────────────────────────────────────────────────────────────────────────────┐  │
│  │  [✓ Paste Text]    [ Upload File]    [ Import URL]                           │  │
│  └───────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                      │
│  DOCUMENT DETAILS                                                                   │
│  ┌───────────────────────────────────────────────────────────────────────────────┐  │
│  │                                                                               │  │
│  │  Title *                                                                      │  │
│  │  ┌─────────────────────────────────────────────────────────────────────────┐  │  │
│  │  │ Flash Loans: Complete Guide                                             │  │  │
│  │  └─────────────────────────────────────────────────────────────────────────┘  │  │
│  │                                                                               │  │
│  │  Type *                                    Priority                          │  │
│  │  ┌─────────────────────────┐              ┌─────────────────────────┐        │  │
│  │  │ [📖 Guide ▼]           │              │ [⭐⭐ Medium ▼]        │        │  │
│  │  └─────────────────────────┘              └─────────────────────────┘        │  │
│  │                                                                               │  │
│  │  Tags                                                                        │  │
│  │  ┌─────────────────────────────────────────────────────────────────────────┐  │  │
│  │  │ [flash-loans ×] [advanced ×] [+ Add tag...]                            │  │  │
│  │  └─────────────────────────────────────────────────────────────────────────┘  │  │
│  │                                                                               │  │
│  │  Source URL (optional)                                                       │  │
│  │  ┌─────────────────────────────────────────────────────────────────────────┐  │  │
│  │  │ https://docs.aave.com/developers/guides/flash-loans                     │  │  │
│  │  └─────────────────────────────────────────────────────────────────────────┘  │  │
│  │                                                                               │  │
│  └───────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                      │
│  CONTENT                                                                            │
│  ┌───────────────────────────────────────────────────────────────────────────────┐  │
│  │                                                            Tokens: 2,450      │  │
│  │  # Flash Loans in Aave                                                       │  │
│  │                                                                               │  │
│  │  Flash loans are uncollateralized loans that must be borrowed and repaid    │  │
│  │  within a single transaction. They are a powerful DeFi primitive that       │  │
│  │  enables:                                                                    │  │
│  │                                                                               │  │
│  │  - Arbitrage opportunities                                                   │  │
│  │  - Collateral swaps                                                         │  │
│  │  - Self-liquidation                                                         │  │
│  │                                                                               │  │
│  │  ## How Flash Loans Work                                                     │  │
│  │                                                                               │  │
│  │  1. User requests a flash loan                                              │  │
│  │  2. Aave transfers the requested amount                                     │  │
│  │  3. User executes their logic                                               │  │
│  │  4. User repays loan + fee (0.09%)                                          │  │
│  │  5. Transaction completes or reverts entirely                               │  │
│  │                                                                               │  │
│  │  [Markdown supported • Drag files to upload]                                │  │
│  └───────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                      │
│  CHUNKING PREVIEW                                                                   │
│  ┌───────────────────────────────────────────────────────────────────────────────┐  │
│  │  Estimated Chunks: 5                                                         │  │
│  │  Chunk Size: 500 tokens │ Overlap: 50 tokens                                │  │
│  │                                                                               │  │
│  │  [Chunk 1] "# Flash Loans in Aave\n\nFlash loans are..." (498 tokens)      │  │
│  │  [Chunk 2] "...enables:\n\n- Arbitrage opportunities..." (502 tokens)       │  │
│  │  [Chunk 3] "## How Flash Loans Work\n\n1. User..." (487 tokens)            │  │
│  │  [Chunk 4] "...4. User repays loan + fee..." (445 tokens)                  │  │
│  │  [Chunk 5] "...Transaction completes or reverts..." (518 tokens)           │  │
│  │                                                                               │  │
│  │  ⏱️ Estimated processing time: ~15 seconds                                  │  │
│  └───────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                      │
│  ─────────────────────────────────────────────────────────────────────────────────  │
│                                                                                      │
│  [Cancel]                            [Save as Draft]         [Add & Index →]        │
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### View 3: Test Knowledge Retrieval

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  🔍 Test Knowledge Retrieval                                                [✕]     │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  Enter a query to see what knowledge would be retrieved:                            │
│                                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │ How do flash loans work in Aave and what are the fees?                          ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│                                                                                      │
│  ┌───────────────────────────────────────────────────────────────────────────────┐  │
│  │  Top K: [5 ▼]     Similarity Threshold: [0.70]    [🔍 Search]                │  │
│  └───────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                      │
│  RETRIEVAL RESULTS                                             Latency: 45ms        │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │                                                                                  ││
│  │  🥇 Chunk from "Flash Loans: Complete Guide"                                    ││
│  │  ┌───────────────────────────────────────────────────────────────────────────┐  ││
│  │  │ Similarity: 0.94 │ Chunk #3 │ Priority: ⭐⭐                              │  ││
│  │  │                                                                           │  ││
│  │  │ ## How Flash Loans Work                                                  │  ││
│  │  │                                                                           │  ││
│  │  │ 1. User requests a flash loan                                            │  ││
│  │  │ 2. Aave transfers the requested amount                                   │  ││
│  │  │ 3. User executes their logic                                             │  ││
│  │  │ 4. User repays loan + fee (0.09%)                                        │  ││
│  │  │ 5. Transaction completes or reverts entirely                             │  ││
│  │  │                                                                           │  ││
│  │  │ [View Full Document →]                                                    │  ││
│  │  └───────────────────────────────────────────────────────────────────────────┘  ││
│  │                                                                                  ││
│  │  🥈 Chunk from "Flash Loans: Complete Guide"                                    ││
│  │  ┌───────────────────────────────────────────────────────────────────────────┐  ││
│  │  │ Similarity: 0.89 │ Chunk #1 │ Priority: ⭐⭐                              │  ││
│  │  │                                                                           │  ││
│  │  │ # Flash Loans in Aave                                                    │  ││
│  │  │                                                                           │  ││
│  │  │ Flash loans are uncollateralized loans that must be borrowed and         │  ││
│  │  │ repaid within a single transaction. They are a powerful DeFi primitive   │  ││
│  │  │ that enables: - Arbitrage opportunities - Collateral swaps...            │  ││
│  │  │                                                                           │  ││
│  │  │ [View Full Document →]                                                    │  ││
│  │  └───────────────────────────────────────────────────────────────────────────┘  ││
│  │                                                                                  ││
│  │  🥉 Chunk from "Aave FAQ"                                                       ││
│  │  ┌───────────────────────────────────────────────────────────────────────────┐  ││
│  │  │ Similarity: 0.78 │ Chunk #42 │ Priority: ⭐⭐                             │  ││
│  │  │                                                                           │  ││
│  │  │ Q: What are the fees for flash loans?                                    │  ││
│  │  │ A: Flash loans charge a flat fee of 0.09% of the borrowed amount. This   │  ││
│  │  │ fee goes to liquidity providers as an additional reward for...           │  ││
│  │  │                                                                           │  ││
│  │  └───────────────────────────────────────────────────────────────────────────┘  ││
│  │                                                                                  ││
│  │  + 2 more results below threshold                            [Show All →]       ││
│  │                                                                                  ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│                                                                                      │
│  RETRIEVAL SUMMARY                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │  Documents matched: 2 of 12                                                      ││
│  │  Chunks retrieved: 5 (showing top 3)                                            ││
│  │  Avg similarity: 0.82                                                           ││
│  │  Coverage: Good - Multiple relevant sources found                               ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### View 4: Document Versions

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  📜 Version History: Flash Loans Complete Guide                             [✕]     │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │ VERSION │ UPDATED          │ AUTHOR           │ CHANGES        │ ACTIONS        ││
│  ├─────────┼──────────────────┼──────────────────┼────────────────┼────────────────┤│
│  │ v3      │ Dec 1, 2025      │ admin@anvil.com  │ +2 paragraphs  │ Current        ││
│  │ (curr)  │ 2:45 PM          │                  │ Updated fees   │ [View]         ││
│  ├─────────┼──────────────────┼──────────────────┼────────────────┼────────────────┤│
│  │ v2      │ Nov 28, 2025     │ admin@anvil.com  │ Fixed typos    │ [View] [Diff]  ││
│  │         │ 10:30 AM         │                  │ Minor updates  │ [Restore]      ││
│  ├─────────┼──────────────────┼──────────────────┼────────────────┼────────────────┤│
│  │ v1      │ Nov 15, 2025     │ admin@anvil.com  │ Initial        │ [View] [Diff]  ││
│  │         │ 3:00 PM          │                  │ version        │ [Restore]      ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│                                                                                      │
│  DIFF: v2 → v3                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │ @@ -15,7 +15,9 @@                                                               ││
│  │                                                                                  ││
│  │  ## Fee Structure                                                               ││
│  │                                                                                  ││
│  │ -Flash loans charge a flat fee of 0.09%.                                        ││
│  │ +Flash loans charge a flat fee of 0.09% of the borrowed amount.                 ││
│  │ +This fee is distributed to liquidity providers as additional yield.            ││
│  │ +For premium users, the fee may be reduced to 0.05%.                            ││
│  │                                                                                  ││
│  │  ## Use Cases                                                                    ││
│  │                                                                                  ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 🔌 API Endpoints

### Get Knowledge Base

```typescript
// GET /admin/projects/{id}/knowledge
// Get knowledge base overview

interface GetKnowledgeBaseResponse {
  success: true;
  data: {
    knowledge_base: {
      id: string;
      project_id: string;
      embedding_model: string;
      chunk_size: number;
      chunk_overlap: number;
      total_documents: number;
      total_chunks: number;
      total_size_bytes: number;
      last_indexed_at: string;
      indexing_status: 'idle' | 'indexing' | 'failed';
    };
    documents: KnowledgeDocument[];
  };
}

interface KnowledgeDocument {
  id: string;
  title: string;
  doc_type: 'guide' | 'faq' | 'reference' | 'data' | 'announcement';
  content_preview: string;
  source_url?: string;
  tags: string[];
  priority: number;                // 1-3
  chunk_count: number;
  token_count: number;
  status: 'draft' | 'indexed' | 'needs_reindex' | 'failed';
  is_live_data: boolean;
  created_at: string;
  updated_at: string;
}
```

### Add Document

```typescript
// POST /admin/projects/{id}/knowledge/documents
// Add new document

interface AddDocumentRequest {
  title: string;
  doc_type: 'guide' | 'faq' | 'reference' | 'data' | 'announcement';
  content: string;
  source_url?: string;
  tags?: string[];
  priority?: number;
  auto_index?: boolean;
}

// Validation
const addDocumentValidation = {
  title: { required: true, minLength: 2, maxLength: 200 },
  doc_type: { required: true, enum: ['guide', 'faq', 'reference', 'data', 'announcement'] },
  content: { required: true, minLength: 50, maxLength: 500000 },
  priority: { min: 1, max: 3 }
};

interface AddDocumentResponse {
  success: true;
  data: {
    document: KnowledgeDocument;
    indexing_job_id?: string;
    estimated_chunks: number;
    estimated_processing_seconds: number;
  };
}
```

### Update Document

```typescript
// PUT /admin/projects/{id}/knowledge/documents/{doc_id}
// Update document

interface UpdateDocumentRequest {
  title?: string;
  doc_type?: string;
  content?: string;
  source_url?: string;
  tags?: string[];
  priority?: number;
}

interface UpdateDocumentResponse {
  success: true;
  data: {
    document: KnowledgeDocument;
    content_changed: boolean;
    needs_reindex: boolean;
    version: number;
  };
}
```

### Test Knowledge Search

```typescript
// POST /admin/projects/{id}/knowledge/search
// Test semantic search

interface TestSearchRequest {
  query: string;
  top_k?: number;                  // default: 5
  similarity_threshold?: number;   // default: 0.7
}

interface TestSearchResponse {
  success: true;
  data: {
    query: string;
    latency_ms: number;
    results: Array<{
      chunk_id: string;
      document_id: string;
      document_title: string;
      content: string;
      similarity_score: number;
      priority: number;
      chunk_index: number;
    }>;
    documents_matched: number;
    total_chunks_searched: number;
  };
}
```

### Trigger Reindex

```typescript
// POST /admin/projects/{id}/knowledge/reindex
// Trigger reindexing

interface ReindexRequest {
  document_ids?: string[];         // Empty = all documents
  force?: boolean;                 // Reindex even if up-to-date
}

interface ReindexResponse {
  success: true;
  data: {
    job_id: string;
    documents_to_process: number;
    estimated_duration_seconds: number;
    status: 'queued';
  };
}
```

### Get Document Versions

```typescript
// GET /admin/projects/{id}/knowledge/documents/{doc_id}/versions
// Get version history

interface GetVersionsResponse {
  success: true;
  data: {
    document_id: string;
    current_version: number;
    versions: Array<{
      version: number;
      content_hash: string;
      changes_summary: string;
      created_by: string;
      created_at: string;
      chunk_count: number;
    }>;
  };
}
```

---

## 📊 Data Structures

### Module State

```typescript
interface KnowledgeBaseState {
  // Data
  knowledgeBase: KnowledgeBase | null;
  documents: KnowledgeDocument[];
  selectedDocument: KnowledgeDocument | null;
  
  // UI State
  loading: {
    list: boolean;
    document: boolean;
    search: boolean;
    reindex: boolean;
    save: boolean;
  };
  
  errors: {
    list: Error | null;
    document: Error | null;
    search: Error | null;
  };
  
  // Filters
  filters: {
    search: string;
    type: 'all' | 'guide' | 'faq' | 'reference' | 'data' | 'announcement';
    status: 'all' | 'indexed' | 'draft' | 'needs_reindex';
    tags: string[];
  };
  
  // Sorting
  sortBy: 'updated_at' | 'priority' | 'title' | 'chunks';
  sortOrder: 'asc' | 'desc';
  
  // Selection
  selectedDocIds: string[];
  
  // Document Editor
  editorOpen: boolean;
  editorMode: 'create' | 'edit';
  editorForm: Partial<AddDocumentRequest>;
  chunkPreview: ChunkPreview | null;
  
  // Search Test
  searchTestOpen: boolean;
  searchQuery: string;
  searchResults: TestSearchResponse['data'] | null;
  
  // Versions
  versionsOpen: boolean;
  versions: GetVersionsResponse['data'] | null;
  
  // Reindex
  reindexJobId: string | null;
  reindexProgress: number;
}
```

---

## 🎨 Component Specifications

### DocumentList

```typescript
interface DocumentListProps {
  documents: KnowledgeDocument[];
  selectedIds: string[];
  onSelect: (id: string, selected: boolean) => void;
  onSelectAll: (selected: boolean) => void;
  onEdit: (doc: KnowledgeDocument) => void;
  onDelete: (id: string) => void;
  onReindex: (id: string) => void;
  sortBy: string;
  sortOrder: string;
  onSort: (column: string) => void;
  loading?: boolean;
}
```

### DocumentEditor

```typescript
interface DocumentEditorProps {
  document?: KnowledgeDocument;
  mode: 'create' | 'edit';
  onSave: (data: AddDocumentRequest) => void;
  onCancel: () => void;
  loading?: boolean;
}
```

### ChunkPreview

```typescript
interface ChunkPreviewProps {
  content: string;
  chunkSize: number;
  overlap: number;
  chunks: Array<{
    index: number;
    content: string;
    tokens: number;
  }>;
}
```

### SearchTestPanel

```typescript
interface SearchTestPanelProps {
  open: boolean;
  onClose: () => void;
  onSearch: (query: string, topK: number, threshold: number) => void;
  results: TestSearchResponse['data'] | null;
  loading?: boolean;
}
```

### DocumentVersions

```typescript
interface DocumentVersionsProps {
  documentId: string;
  versions: GetVersionsResponse['data'];
  onViewVersion: (version: number) => void;
  onRestore: (version: number) => void;
  onCompare: (v1: number, v2: number) => void;
}
```

---

## 🎬 Motion Design

```typescript
const knowledgeAnimations = {
  // Document row expand
  rowExpand: {
    initial: { height: 0, opacity: 0 },
    animate: { height: 'auto', opacity: 1 },
    transition: { duration: 0.2 }
  },
  
  // Chunk preview appear
  chunkPreview: {
    initial: { opacity: 0, y: 10 },
    animate: { opacity: 1, y: 0 },
    transition: { staggerChildren: 0.05 }
  },
  
  // Search result highlight
  searchHighlight: {
    backgroundColor: ['transparent', 'rgba(59, 130, 246, 0.2)', 'transparent'],
    transition: { duration: 0.5 }
  },
  
  // Similarity score bar
  similarityBar: {
    initial: { width: 0 },
    animate: { width: '100%' },
    transition: { duration: 0.5, ease: 'easeOut' }
  },
  
  // Reindex progress
  reindexProgress: {
    width: '100%',
    transition: { duration: 0.3 }
  },
  
  // Version diff line
  diffLine: {
    initial: { opacity: 0, x: -10 },
    animate: { opacity: 1, x: 0 },
    transition: { duration: 0.2 }
  },
  
  // Tag pill
  tagPill: {
    initial: { scale: 0 },
    animate: { scale: 1 },
    exit: { scale: 0 },
    transition: { type: 'spring', stiffness: 300 }
  }
};
```

---

## ⌨️ Keyboard Shortcuts

```typescript
const knowledgeShortcuts = {
  'mod+n': 'Add new document',
  'mod+e': 'Edit selected document',
  'mod+f': 'Open search test',
  'mod+s': 'Save document',
  'mod+shift+r': 'Reindex selected',
  'del': 'Delete selected',
  'escape': 'Close editor/panel',
  't': 'Add tag to selected',
};
```

---

## ⚠️ Error Handling

```typescript
const knowledgeErrorCodes = {
  // Validation
  KB_VAL_001: 'Document title is required',
  KB_VAL_002: 'Content is too short (min 50 characters)',
  KB_VAL_003: 'Content exceeds maximum size',
  KB_VAL_004: 'Invalid document type',
  
  // Processing
  KB_PROC_001: 'Failed to generate embeddings',
  KB_PROC_002: 'Chunking failed for document',
  KB_PROC_003: 'Reindex job failed',
  KB_PROC_004: 'Document import failed',
  
  // Search
  KB_SRCH_001: 'Search query failed',
  KB_SRCH_002: 'No results above threshold',
  
  // System
  KB_SYS_001: 'Failed to load knowledge base',
  KB_SYS_002: 'Failed to save document',
  KB_SYS_003: 'Version restore failed',
};
```

---

## 📋 Field Requirements Summary

| Endpoint | Field | Type | Required | Validation |
|----------|-------|------|----------|------------|
| POST /documents | title | string | Yes | 2-200 chars |
| POST /documents | doc_type | enum | Yes | guide, faq, reference, data, announcement |
| POST /documents | content | string | Yes | 50-500000 chars |
| POST /documents | priority | number | No | 1-3 |
| POST /search | query | string | Yes | 1-500 chars |
| POST /search | top_k | number | No | 1-20 |
| POST /search | similarity_threshold | number | No | 0.0-1.0 |

---

## 🔒 Security Considerations

1. **Content Sanitization:** All uploaded content sanitized for XSS
2. **File Upload Limits:** Max 10MB per file, validated file types
3. **Access Control:** Knowledge base editing requires Admin role
4. **Version History:** Immutable, cannot delete version history
5. **PII Detection:** Warning for potential PII in documents

---

*Document Version: 1.0*  
*Last Updated: December 1, 2025*  
*Module: Knowledge Base*  
*User Type: Admin*
