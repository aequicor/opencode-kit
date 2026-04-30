---
name: knowledge-graph
description: Build and query a semantic knowledge graph from project documentation using embeddings. Creates persistent vector index for cross-document navigation.
---

# Knowledge Graph Skill

Skill for building a semantic layer over project documentation. Transforms linear file hierarchies into a queryable knowledge graph.

## When to trigger

Activate when:
- @Main needs to understand relationships between multiple documents
- A question spans multiple modules or document types
- Context would benefit from semantic search beyond keyword matching
- New documents were added — rebuild the index

## Architecture

```
docs/                    kit/.opencode/knowledge-graph/
  requirements/                index.json         — document metadata
  spec/                        embeddings.json    — vector storage (if available)
  guidelines/                  graph.json         — entity relationships
  plans/
  reports/
```

## Algorithm

### 1. Index documents

```
for each document in docs/:
  1. Extract metadata (title, module, type, date, agent)
  2. Extract entities (classes, functions, APIs, concepts)
  3. Extract relationships (imports, references, "depends on", "implements")
  4. Write to index.json
```

### 2. Build embeddings (optional — requires embedding-capable model)

```
for each document:
  embedding = vectorize(content[:4096])
  store in embeddings.json with doc_id
```

### 3. Query

```json
{
  "query": "How does authentication relate to session management?",
  "top_k": 5,
  "types": ["spec", "guideline"],
  "modules": ["server"]
}
```

Returns ranked results with path, excerpt, and related entities.

### 4. Entity extraction rules

| Language | Entity pattern | Example |
|----------|--------------|---------|
| Kotlin | `class X`, `fun X`, `interface X` | `class SessionManager` |
| TypeScript | `class X`, `function X`, `interface X` | `interface AuthConfig` |
| Python | `class X:`, `def X` | `def create_token` |
| Go | `type X struct`, `func X` | `func (s *Server) Auth` |
| Rust | `struct X`, `fn X`, `trait X` | `struct AuthService` |

### 5. Relationship extraction

| Pattern | Relationship |
|---------|-------------|
| `import X` / `uses X` | depends_on |
| `implements X` / `extends X` | implements |
| `described in docs/X/` | documented_in |
| `tested in tests/X` | tested_by |
| `see ADR-NNN` | references_decision |
| `depends on X module` | module_dependency |

## Tools used

| Tool | Purpose |
|------|---------|
| `knowledge-my-app_search_docs` | Search existing docs |
| `glob` | Find documents to index |
| `read` | Read document content for extraction |
| `knowledge-my-app_write_guideline` | Persist index/graph artifacts |

## Principles

- **Build incrementally** — index new documents on each feature completion
- **Link everything** — every entity should connect to at least one other entity or document
- **Query before search** — always try graph query before grep
- **Keep index fresh** — rebuild on major spec/guideline changes
