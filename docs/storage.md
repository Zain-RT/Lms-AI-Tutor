# Storage Strategy and Scale

## Directory Sharding (future)
- Use hash-based shards to avoid huge directories:
  - `storage/v1/indices/ab/cd/course_<id>/...`
  - `storage/v1/lessons/ef/01/lesson_<id>.json.gz`

## Manifest (SQLite)
- `storage/manifest.sqlite` tables:
  - `courses(id, shard_path, bytes_used, doc_count, created_at, updated_at)`
  - `documents(doc_id, course_id, source_url, content_hash, bytes, created_at)`
  - `indices(course_id, last_compacted_at, vector_count, index_version)`

## Deduplication
- Compute SHA256 for each ingested file/chunk
- Skip duplicates per course; update references only

## Compaction and GC
- Periodic job:
  - Recompute `bytes_used`, `vector_count`
  - Compact large/fragmented indices
  - Delete orphaned files not in manifest

## Concurrency
- Per-course file locks for index writes
- Atomic writes (write temp → fsync → rename)

## Compression
- Compress large JSON/text artifacts to `.gz` 