# DevFlow - AI-Powered Coding Knowledge Base

<h3>

**Your Personal AI Assistant for Managing Coding Resources**</h3>

[Live Demo](https://devflow-sriram.web.app/)

---

## 📋 Table of Contents

- [Problem Statement](#-problem-statement)
- [Solution](#-solution)
- [Key Features](#-key-features)
- [Tech Stack](#️-tech-stack)
- [Architecture](#️-architecture)
- [Usage](#-usage)
- [Performance Metrics](#-performance-metrics)
- [Challenges & Solutions](#-challenges--solutions)
- [Roadmap](#️-roadmap)


---

## 🎯 Problem Statement

Developers face a common challenge:

> **"I saved that article somewhere... but where?"**

### The Pain Points:
- 📂 **Scattered Resources** - Bookmarks, notes, PDFs, and articles across multiple platforms
- 🔍 **Poor Search** - Browser bookmarks don't understand context or meaning
- ⏰ **Time Waste** - Spending 10-15 minutes searching for a tutorial you read last month
- 🧠 **Knowledge Loss** - Can't remember exact keywords from resources saved weeks ago
- 🔗 **Link Rot** - Saved URLs that no longer work

### The Question:
**"What if you could ask questions in natural language and get answers from ALL your saved resources instantly?"**

---

## 💡 Solution

DevFlow is an **AI-powered knowledge management system** that transforms how developers organize and retrieve coding information.

### How It Works:
1. **Ingest** - Upload PDFs, paste content, or save web articles
2. **Index** - Content is chunked and embedded using RAG architecture
3. **Search** - Ask questions in natural language
4. **Retrieve** - AI finds relevant content using semantic search
5. **Generate** - Google Gemini creates comprehensive answers with source citations

### Why DevFlow?
- ✅ **Semantic Search** - Find information by meaning, not just keywords
- ✅ **Hybrid Intelligence** - Combines your docs + real-time web search
- ✅ **Source Attribution** - Always know where answers came from
- ✅ **Manual Control** - Choose what to save from web results
- ✅ **Cost Efficient** - Uses free tier APIs for learning and personal use

---

### Quick Start:
1. Visit the live demo
2. Go to **Sources** tab → Upload a PDF or add content manually
3. Go to **Search** tab → Ask: *"What are React hooks?"*
4. Enable **"Search web if not in documents"** to try hybrid search
5. Save useful web results to your knowledge base

---

## ✨ Key Features

### 📂 Multiple Input Methods
- **File Upload** - PDF, DOCX, TXT
- **Manual Entry** - Paste content directly
- **Web Scraping** - Save articles from search results

### 🔍 Intelligent Search System
- **Semantic Search** - Uses RAG (Retrieval-Augmented Generation) with vector embeddings
- **Hybrid Search** - Searches your documents first, then the web if needed
- **Source Citations** - Every answer includes references to source documents
- **Web Integration** - Real-time web search via Brave Search API

### 🌐 Web Search & Save
- Toggle web search on/off per query
- Get results from both your docs and the internet
- Manual save option - **you choose** what to add to your knowledge base
- Automatic text extraction from web pages

### 📊 Analytics & Management
- View all sources with document counts
- Track total searches and indexed content
- Delete unwanted sources
- Real-time statistics

### 🎨 Modern UI/UX
- Clean, responsive design
- Real-time loading states
- Source badges (📄 Your Docs / 🌐 Web)
- Success notifications

---

## 🛠️ Tech Stack

### Frontend
| Technology | Purpose | Why? |
|------------|---------|------|
| **React 18.3.1** | UI Framework | Component reusability, virtual DOM performance |
| **Axios** | HTTP Client | Promise-based API calls with interceptors |
| **Lucide React** | Icons | Lightweight, customizable icon library |
| **Firebase Hosting** | Deployment | Free hosting with CDN, automatic SSL |

### Backend
| Technology | Purpose | Why? |
|------------|---------|------|
| **FastAPI** | Web Framework | Async support, automatic API docs, type safety |
| **Python 3.11** | Runtime | Latest features, performance improvements |
| **Google Gemini** | LLM | Free tier, strong reasoning, long context window |
| **ChromaDB** | Vector DB | In-memory embeddings, easy setup, no external dependencies |
| **SQLite** | Metadata Storage | Lightweight, serverless, perfect for demos |
| **BeautifulSoup4** | Web Scraping | HTML parsing for content extraction |
| **PyPDF2** | PDF Processing | Extract text from PDF uploads |
| **python-docx** | DOCX Processing | Extract text from Word documents |

---

## 🏗️ Architecture

### System Architecture
```
┌─────────────────────────────────────────────────────────────┐
│                    User Interface (React)                    │
│              Hosted on Firebase (Global CDN)                 │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTPS REST API
                         │ (CORS Enabled)
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              FastAPI Backend (Render Cloud)                  │
│  ┌────────────────────────────────────────────────────────┐ │
│  │             Request Router & Handlers                   │ │
│  │  • /api/search/hybrid  • /api/upload                   │ │
│  │  • /api/save-web-result • /api/sources                 │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   Indexer    │  │  Retriever   │  │  Generator   │     │
│  │  (Chunking)  │  │  (Search)    │  │   (RAG)      │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└───────┬────────────────┬─────────────────┬─────────────────┘
        │                │                 │
        ▼                ▼                 ▼
┌──────────────┐  ┌──────────────┐  ┌─────────────────┐
│  ChromaDB    │  │    SQLite    │  │  External APIs  │
│  (Vectors)   │  │  (Metadata)  │  │  • Gemini       │
│              │  │              │  │  • Brave Search │
│  • Embeddings│  │  • Sources   │  │  • Web Scraping │
│  • Semantic  │  │  • Documents │  └─────────────────┘
│    Search    │  │  • Searches  │
└──────────────┘  └──────────────┘
```

### Data Flow

#### 1. Document Ingestion Pipeline
```
User Upload (PDF/DOCX/TXT)
        ↓
Text Extraction (PyPDF2/python-docx)
        ↓
Chunking (500 chars, 50 overlap)
        ↓
Embedding Generation (Sentence Transformers)
        ↓
Storage:
├─ ChromaDB (vectors + chunks)
└─ SQLite (metadata)
```

#### 2. Search & Answer Generation (RAG)
```
User Query
        ↓
┌───────┴────────┐
│  Local Search  │ (ChromaDB vector similarity)
└───────┬────────┘
        │
        ├─ If sufficient results (≥2) ──→ Generate Answer
        │
        └─ If insufficient (< 2)
                ↓
        ┌───────────────┐
        │  Web Search   │ (Brave API)
        └───────┬───────┘
                ↓
        Content Extraction (BeautifulSoup)
                ↓
        Combine: Local + Web Results
                ↓
        ┌──────────────────────────┐
        │  Context Assembly        │
        │  (Top 5 chunks + web)    │
        └──────────┬───────────────┘
                   ↓
        ┌──────────────────────────┐
        │  Google Gemini (RAG)     │
        │  Prompt: Query + Context │
        └──────────┬───────────────┘
                   ↓
        Answer + Source Citations
                   ↓
        User + Optional Save Web Results
```

#### 3. Web Result Saving
```
User Clicks "Save" on Web Result
        ↓
Content + Metadata
        ↓
Same as Document Ingestion Pipeline
        ↓
Now searchable in future queries!
```

---

## 💡 Usage

### 1. Adding Documents

#### Method A: File Upload
1. Navigate to **Sources** tab
2. Click **"Choose File (PDF, DOCX, TXT)"**
3. Select your file
4. File is automatically processed and indexed
5. Success message appears with chunk count

#### Method B: Manual Entry
1. Go to **Sources** tab
2. Scroll to **"Or Add Manually"** section
3. Fill in:
   - **Title** (required)
   - **Content** (required)
   - **URL** (optional)
4. Click **"Add Document"**

### 2. Searching Your Knowledge Base

#### Basic Search (Documents Only)
1. Go to **Search** tab
2. Uncheck **"Search web if not in my documents"**
3. Enter query: *"How do I use React hooks?"*
4. Get AI-generated answer with document citations

#### Hybrid Search (Documents + Web)
1. Go to **Search** tab
2. Keep **"Search web if not in my documents"** checked
3. Enter query: *"What's new in TypeScript 5.3?"*
4. Receive:
   - Results from your documents (if any)
   - Results from the web (if needed)
   - Combined AI answer with source labels

### 3. Saving Web Results

1. After hybrid search, see web sources with:
   - Title and description
   - Source URL (clickable)
   - **"Save"** button
2. Click **"Save"** on useful results
3. Content is added to your knowledge base
4. Button changes to **"Saved"** ✓
5. Future searches will include this content!

### 4. Managing Sources

- View all sources in **Sources** tab
- See document count per source
- Click **"Delete"** to remove sources
- Stats update in real-time

---

## 🐛 Challenges & Solutions

### Challenge 1: Understanding RAG Architecture
**Problem:** First time implementing Retrieval-Augmented Generation - confusing how to combine document retrieval with AI generation  
**Solution:** 
- Broke down into smaller steps: chunking → embedding → retrieval → context assembly → generation
- Studied existing RAG implementations and documentation
- Tested each component independently before integration

### Challenge 2: CORS Errors During Development
**Problem:** Frontend couldn't communicate with backend due to CORS policy blocks  
**Solution:**
- Added CORS middleware in FastAPI with proper configuration
- Set `allow_origins=["*"]` for development
- Tested API endpoints with Postman before frontend integration

### Challenge 3: ChromaDB Integration
**Problem:** Vector database concept was new - unclear how embeddings and similarity search worked  
**Solution:**
- Read ChromaDB documentation thoroughly
- Started with simple examples before full integration
- Tested search relevance with sample documents
- Adjusted chunk size and overlap for better results

### Challenge 4: Web Scraping Reliability
**Problem:** Some websites block scraping or have JavaScript-heavy content  
**Solution:**
- Added User-Agent headers to appear as browser
- Implemented try-catch blocks for graceful failures
- Fallback to search result descriptions when scraping fails
- Set timeout limits to prevent hanging requests

### Challenge 5: State Management in React
**Problem:** Managing search results, loading states, and errors across components  
**Solution:**
- Used React hooks (useState, useEffect) effectively
- Lifted state to App.jsx for shared data
- Passed callbacks for child-to-parent communication
- Kept component state minimal and focused

---

## 📊 Performance Metrics

### Response Times (Average)
- **Document Upload:** 2-5 seconds
- **Local Search:** 0.5-1 second
- **Hybrid Search:** 3-8 seconds (includes web scraping)
- **Web Scraping:** 1-3 seconds per URL

### Accuracy
- **Document Retrieval:** ~90% relevance (semantic search)
- **Answer Quality:** Depends on Gemini model and source quality
- **Source Attribution:** 100% (always cites sources used)

---

## 🗺️ Roadmap

### ✅ Completed (v1.0)
- [x] Document upload (PDF, DOCX, TXT)
- [x] Manual document entry
- [x] Semantic search with RAG
- [x] Web search integration (Brave API)
- [x] Hybrid search (docs + web)
- [x] Manual save for web results
- [x] Source management
- [x] Real-time statistics

---
